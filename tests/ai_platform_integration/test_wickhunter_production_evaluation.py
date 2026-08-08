from __future__ import annotations

import json
from decimal import Decimal
from pathlib import Path

import pytest

from ai_platform.research.liquidations.historical.manifests import sha256_file
from ai_platform.wickhunter.baseline_strategy import BaselineEvaluationError
from ai_platform.wickhunter.canonical import canonical_json, canonical_sha256
from ai_platform.wickhunter.contracts import (
    AvailableMetric,
    LiquidationFeatureVector,
    SourceLiquidationAggregate,
    TradeDirection,
)
from ai_platform.wickhunter.dataset import DATASET_SCHEMA_VERSION, DatasetRow
from ai_platform.wickhunter.deterministic_replay import (
    LABEL_SCHEMA_VERSION,
    CandidateLabel,
    DeterministicReplayError,
    LabelOutcome,
)
from ai_platform.wickhunter.production_evaluation import (
    EVALUATION_DATASET_SCHEMA_VERSION,
    ProductionEvaluationError,
    load_verified_evaluation_dataset,
)


DATASET_ID = "wickhunter-production-evaluation-test"
DATASET_SHA = "a" * 64
MARKET_SHA = "b" * 64
SPLIT_SHA = "c" * 64
PRICE_PATH_SHA = "d" * 64
POLICY_SHA = "e" * 64
CODE_SHA = "f" * 40
START_MS = 1_000_000


def _feature() -> LiquidationFeatureVector:
    long_notional = Decimal("800")
    short_notional = Decimal("200")
    total = long_notional + short_notional
    return LiquidationFeatureVector(
        feature_schema_version="wickhunter-liquidation-features-v1",
        symbol="BTCUSDT",
        decision_timestamp_ms=START_MS,
        decision_price=Decimal("100"),
        event_count=2,
        total_notional_usd=total,
        liquidated_long_notional_usd=long_notional,
        liquidated_short_notional_usd=short_notional,
        long_short_imbalance=(short_notional - long_notional) / total,
        maximum_event_notional_usd=long_notional,
        maximum_event_percentile=Decimal("0.9"),
        maximum_event_zscore=Decimal("2.5"),
        liquidation_burst_intensity=Decimal("3"),
        time_since_previous_burst_ms=60_000,
        ingest_latency_ms=100,
        source_coverage_ratio=Decimal("1"),
        source_aggregates=(
            SourceLiquidationAggregate(
                source="binance",
                event_count=2,
                total_notional_usd=total,
                liquidated_long_notional_usd=long_notional,
                liquidated_short_notional_usd=short_notional,
                maximum_event_notional_usd=long_notional,
                maximum_ingest_latency_ms=100,
                latest_received_at_ms=START_MS - 1,
            ),
        ),
        market_metrics=(
            AvailableMetric(
                name="quote_volume_24h_usd",
                value=Decimal("100000000"),
                available_at_ms=START_MS,
                source="test",
            ),
            AvailableMetric(
                name="trend_return_ratio",
                value=Decimal("-0.02"),
                available_at_ms=START_MS,
                source="test",
            ),
        ),
        feature_available_at_ms=START_MS,
        input_event_ids=("binance:event-1",),
        history_id="history-1",
        history_sha256=canonical_sha256({"history": 1}),
    )


def _row() -> DatasetRow:
    feature = _feature()
    return DatasetRow(
        schema_version=DATASET_SCHEMA_VERSION,
        dataset_version=DATASET_ID,
        split_name="train",
        symbol=feature.symbol,
        decision_timestamp_ms=feature.decision_timestamp_ms,
        feature_available_at_ms=feature.feature_available_at_ms,
        feature=feature,
        universe_snapshot_sha256=canonical_sha256({"universe": 1}),
        market_context_sha256=canonical_sha256({"market": 1}),
        source_selection_sha256s=(canonical_sha256({"selection": 1}),),
        historical_provider_ids=("binance",),
        import_run_ids=("run-1",),
    )


def _label(row: DatasetRow, side: TradeDirection) -> CandidateLabel:
    label_id = canonical_sha256(
        {
            "policy_sha256": POLICY_SHA,
            "dataset_row_sha256": row.row_sha256,
            "price_path_manifest_sha256": PRICE_PATH_SHA,
            "side": side.value,
            "decision_timestamp_ms": START_MS,
        }
    )
    return CandidateLabel(
        schema_version=LABEL_SCHEMA_VERSION,
        label_id=label_id,
        policy_version="wickhunter-production-replay-policy-v1",
        policy_sha256=POLICY_SHA,
        dataset_id=DATASET_ID,
        dataset_manifest_sha256=DATASET_SHA,
        market_manifest_sha256=MARKET_SHA,
        split_geometry_sha256=SPLIT_SHA,
        dataset_row_sha256=row.row_sha256,
        price_path_manifest_sha256=PRICE_PATH_SHA,
        source_commit_sha=CODE_SHA,
        split_name="train",
        symbol="BTCUSDT",
        side=side,
        decision_timestamp_ms=START_MS,
        label_end_ms=START_MS + 60_000,
        outcome=LabelOutcome.TAKE_PROFIT,
        entry_timestamp_ms=START_MS,
        entry_aggregate_trade_id=1,
        entry_trade_sha256=canonical_sha256({"entry": side.value}),
        raw_entry_price=Decimal("100"),
        executed_entry_price=Decimal("100.1"),
        exit_timestamp_ms=START_MS + 1_000,
        exit_aggregate_trade_id=2,
        exit_trade_sha256=canonical_sha256({"exit": side.value}),
        raw_exit_price=Decimal("110"),
        executed_exit_price=Decimal("109.89"),
        gross_return_ratio=Decimal("0.10"),
        net_return_ratio=Decimal("0.098"),
        maximum_favorable_excursion_ratio=Decimal("0.10"),
        maximum_adverse_excursion_ratio=Decimal("0.01"),
        time_to_outcome_ms=1_000,
        fee_ratio=Decimal("0.001"),
        slippage_ratio=Decimal("0.001"),
        take_profit_ratio=Decimal("0.085"),
        stop_loss_ratio=Decimal("0.05"),
        entry_delay_ms=0,
        maximum_entry_delay_ms=20_000,
        protected_holdout_accessed=False,
        immutable_inputs_mutated=False,
        model_execution_authorized=False,
        performance_research_authorized=False,
        execution_enabled=False,
        live_capital_authorized=False,
        trading_credentials_present=False,
        orders_submitted=0,
    )


def _write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(canonical_json(payload) + "\n", encoding="utf-8")


def _write_jsonl(path: Path, payloads: tuple[dict[str, object], ...]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    content = "".join(canonical_json(payload) + "\n" for payload in payloads)
    path.write_text(content, encoding="utf-8")


def _roots(tmp_path: Path, *, labels: tuple[CandidateLabel, ...] | None = None):
    materialization_root = tmp_path / DATASET_ID
    dataset_root = materialization_root / "dataset"
    price_path_root = tmp_path / "price-path"
    replay_root = tmp_path / "replay"
    price_path_root.mkdir()

    row = _row()
    dataset_partition = dataset_root / "partitions" / "train" / "BTCUSDT.jsonl"
    _write_jsonl(dataset_partition, (row.as_json_dict(),))
    dataset_manifest = {
        "manifest_sha256": DATASET_SHA,
        "partitions": (
            {
                "relative_path": dataset_partition.relative_to(dataset_root).as_posix(),
                "row_count": 1,
                "sha256": sha256_file(dataset_partition),
            },
        ),
        "total_rows": 1,
    }
    _write_json(dataset_root / "manifest.json", dataset_manifest)

    selected_labels = labels or (
        _label(row, TradeDirection.LONG),
        _label(row, TradeDirection.SHORT),
    )
    replay_partition = replay_root / "labels" / "train" / "BTCUSDT.jsonl"
    _write_jsonl(
        replay_partition,
        tuple(label.as_json_dict() for label in selected_labels),
    )
    replay_manifest = {
        "package_id": "wickhunter-replay-test",
        "manifest_sha256": canonical_sha256({"replay": 1}),
        "policy_sha256": POLICY_SHA,
        "dataset_id": DATASET_ID,
        "dataset_manifest_sha256": DATASET_SHA,
        "source_commit_sha": CODE_SHA,
        "partitions": (
            {
                "relative_path": replay_partition.relative_to(replay_root).as_posix(),
                "row_count": len(selected_labels),
                "sha256": sha256_file(replay_partition),
            },
        ),
        "decision_count": 1,
        "label_count": len(selected_labels),
    }
    _write_json(replay_root / "manifest.json", replay_manifest)
    return materialization_root, price_path_root, replay_root, row


def _accepted_verifiers(monkeypatch) -> None:
    monkeypatch.setattr(
        "ai_platform.wickhunter.production_evaluation.verify_production_materialization",
        lambda _root: {"outcome": "accepted"},
    )
    monkeypatch.setattr(
        "ai_platform.wickhunter.production_evaluation.verify_deterministic_replay_package",
        lambda **_kwargs: {"outcome": "accepted"},
    )


def test_load_verified_evaluation_dataset_joins_exact_contracts(tmp_path, monkeypatch) -> None:
    _accepted_verifiers(monkeypatch)
    materialization_root, price_path_root, replay_root, row = _roots(tmp_path)

    result = load_verified_evaluation_dataset(
        materialization_root=materialization_root,
        price_path_root=price_path_root,
        replay_root=replay_root,
    )

    assert result.schema_version == EVALUATION_DATASET_SCHEMA_VERSION
    assert result.dataset_id == DATASET_ID
    assert len(result.cases) == 1
    assert result.cases[0].dataset_row_sha256 == row.row_sha256
    assert tuple(label.side for label in result.cases[0].labels) == (
        TradeDirection.LONG,
        TradeDirection.SHORT,
    )
    assert len(result.evaluation_sha256) == 64
    assert not result.execution_enabled
    assert not result.live_capital_authorized
    assert result.orders_submitted == 0


def test_missing_directional_label_is_rejected(tmp_path, monkeypatch) -> None:
    _accepted_verifiers(monkeypatch)
    row = _row()
    materialization_root, price_path_root, replay_root, _ = _roots(
        tmp_path,
        labels=(_label(row, TradeDirection.LONG),),
    )

    with pytest.raises(BaselineEvaluationError, match="one long and one short"):
        load_verified_evaluation_dataset(
            materialization_root=materialization_root,
            price_path_root=price_path_root,
            replay_root=replay_root,
        )


def test_dataset_row_identity_tampering_is_rejected(tmp_path, monkeypatch) -> None:
    _accepted_verifiers(monkeypatch)
    materialization_root, price_path_root, replay_root, _ = _roots(tmp_path)
    partition = materialization_root / "dataset" / "partitions" / "train" / "BTCUSDT.jsonl"
    payload = json.loads(partition.read_text(encoding="utf-8"))
    payload["symbol"] = "ETHUSDT"
    partition.write_text(canonical_json(payload) + "\n", encoding="utf-8")
    manifest_path = materialization_root / "dataset" / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["partitions"][0]["sha256"] = sha256_file(partition)
    _write_json(manifest_path, manifest)

    with pytest.raises(ProductionEvaluationError, match="invalid dataset row"):
        load_verified_evaluation_dataset(
            materialization_root=materialization_root,
            price_path_root=price_path_root,
            replay_root=replay_root,
        )


def test_unsafe_label_authority_is_rejected(tmp_path, monkeypatch) -> None:
    _accepted_verifiers(monkeypatch)
    materialization_root, price_path_root, replay_root, _ = _roots(tmp_path)
    partition = replay_root / "labels" / "train" / "BTCUSDT.jsonl"
    payloads = [json.loads(line) for line in partition.read_text(encoding="utf-8").splitlines()]
    payloads[0]["execution_enabled"] = True
    _write_jsonl(partition, tuple(payloads))
    manifest_path = replay_root / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["partitions"][0]["sha256"] = sha256_file(partition)
    _write_json(manifest_path, manifest)

    with pytest.raises(DeterministicReplayError, match="unsafe authority"):
        load_verified_evaluation_dataset(
            materialization_root=materialization_root,
            price_path_root=price_path_root,
            replay_root=replay_root,
        )


def test_boundary_excluded_dataset_rows_are_not_required_for_evaluation_join(
    tmp_path, monkeypatch
) -> None:
    from dataclasses import replace

    _accepted_verifiers(monkeypatch)
    materialization_root, price_path_root, replay_root, row = _roots(tmp_path)
    excluded_row = replace(row, source_selection_sha256s=(canonical_sha256({"selection": 2}),))
    dataset_partition = materialization_root / "dataset" / "partitions" / "train" / "BTCUSDT.jsonl"
    _write_jsonl(dataset_partition, (row.as_json_dict(), excluded_row.as_json_dict()))
    dataset_manifest_path = materialization_root / "dataset" / "manifest.json"
    dataset_manifest = json.loads(dataset_manifest_path.read_text(encoding="utf-8"))
    dataset_manifest["partitions"][0]["row_count"] = 2
    dataset_manifest["partitions"][0]["sha256"] = sha256_file(dataset_partition)
    dataset_manifest["total_rows"] = 2
    _write_json(dataset_manifest_path, dataset_manifest)
    replay_manifest_path = replay_root / "manifest.json"
    replay_manifest = json.loads(replay_manifest_path.read_text(encoding="utf-8"))
    replay_manifest["source_decision_count"] = 2
    replay_manifest["decision_count"] = 1
    replay_manifest["excluded_split_boundary_decision_count"] = 1
    _write_json(replay_manifest_path, replay_manifest)

    result = load_verified_evaluation_dataset(
        materialization_root=materialization_root,
        price_path_root=price_path_root,
        replay_root=replay_root,
    )

    assert len(result.cases) == 1
    assert result.cases[0].dataset_row_sha256 == row.row_sha256
