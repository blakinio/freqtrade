from __future__ import annotations

from decimal import Decimal
from pathlib import Path

import pytest

from ai_platform.wickhunter import deterministic_replay as subject
from ai_platform.wickhunter import replay_price_path as price_path
from ai_platform.wickhunter.canonical import canonical_json, canonical_sha256
from ai_platform.wickhunter.contracts import TradeDirection


DATASET_ID = "wickhunter-wh01-production-dataset-test"
MARKET_HASH = "a" * 64
SPLIT_HASH = "b" * 64
PRICE_PATH_HASH = "c" * 64
CODE_SHA = "d" * 40
ARCHIVE_HASH = "e" * 64
START = 1_000_000
HOLDOUT = 10_000_000
SYMBOL = "BTCUSDT"


def _trade(
    trade_id: int,
    timestamp_ms: int,
    price: str,
) -> price_path.ReplayAggregateTrade:
    return price_path.ReplayAggregateTrade(
        schema_version=price_path.TRADE_SCHEMA_VERSION,
        source=price_path.SOURCE_ID,
        symbol=SYMBOL,
        aggregate_trade_id=trade_id,
        price=Decimal(price),
        quantity=Decimal("1"),
        first_trade_id=trade_id,
        last_trade_id=trade_id,
        occurred_at_ms=timestamp_ms,
        buyer_is_maker=False,
        archive_sha256=ARCHIVE_HASH,
        raw_row_number=trade_id,
    )


def _policy(**overrides: object) -> subject.ReplayPolicy:
    values: dict[str, object] = {
        "schema_version": subject.POLICY_SCHEMA_VERSION,
        "policy_version": "wickhunter-replay-policy-test-v1",
        "entry_delay_ms": 0,
        "maximum_entry_delay_ms": 2_000,
        "fee_ratio": Decimal("0.001"),
        "slippage_ratio": Decimal("0.001"),
        "take_profit_ratio": Decimal("0.05"),
        "stop_loss_ratio": Decimal("0.03"),
        "label_horizon_ms": 10_000,
        "protected_holdout_start_ms": HOLDOUT,
    }
    values.update(overrides)
    return subject.ReplayPolicy(**values)  # type: ignore[arg-type]


def _decision(side: TradeDirection, *, decision_ms: int = START) -> subject.ReplayDecision:
    return subject.ReplayDecision(
        dataset_id=DATASET_ID,
        dataset_manifest_sha256="1" * 64,
        market_manifest_sha256=MARKET_HASH,
        split_geometry_sha256=SPLIT_HASH,
        dataset_row_sha256="2" * 64,
        price_path_manifest_sha256=PRICE_PATH_HASH,
        source_commit_sha=CODE_SHA,
        split_name="train",
        symbol=SYMBOL,
        decision_timestamp_ms=decision_ms,
        side=side,
    )


def test_long_take_profit_uses_exact_trade_order_and_costs() -> None:
    trades = (
        _trade(1, START, "100"),
        _trade(2, START + 1_000, "102"),
        _trade(3, START + 2_000, "106"),
        _trade(4, START + 10_000, "104"),
    )

    label = subject.replay_event_label(
        decision=_decision(TradeDirection.LONG),
        trades=trades,
        policy=_policy(),
    )

    assert label.outcome is subject.LabelOutcome.TAKE_PROFIT
    assert label.entry_aggregate_trade_id == 1
    assert label.exit_aggregate_trade_id == 3
    assert label.executed_entry_price == Decimal("100.100")
    assert label.executed_exit_price == Decimal("105.894")
    assert label.time_to_outcome_ms == 2_000
    assert label.maximum_favorable_excursion_ratio == (
        Decimal("106") - Decimal("100.100")
    ) / Decimal("100.100")
    assert label.maximum_adverse_excursion_ratio == (Decimal("100.100") - Decimal("100")) / Decimal(
        "100.100"
    )
    gross = Decimal("105.894") / Decimal("100.100") - Decimal("1")
    assert label.gross_return_ratio == gross
    assert label.net_return_ratio == gross - Decimal("0.001") - (
        Decimal("0.001") * (Decimal("105.894") / Decimal("100.100"))
    )
    assert label.protected_holdout_accessed is False
    assert label.orders_submitted == 0


def test_short_stop_loss_respects_same_timestamp_aggregate_trade_order() -> None:
    trades = (
        _trade(1, START, "100"),
        _trade(2, START + 1_000, "94"),
        _trade(3, START + 1_000, "104"),
        _trade(4, START + 10_000, "100"),
    )

    label = subject.replay_event_label(
        decision=_decision(TradeDirection.SHORT),
        trades=trades,
        policy=_policy(take_profit_ratio=Decimal("0.07"), stop_loss_ratio=Decimal("0.03")),
    )

    assert label.outcome is subject.LabelOutcome.STOP_LOSS
    assert label.exit_aggregate_trade_id == 3
    assert label.time_to_outcome_ms == 1_000


def test_timeout_excursions_and_replay_shadow_parity() -> None:
    trades = (
        _trade(1, START, "100"),
        _trade(2, START + 2_000, "103"),
        _trade(3, START + 5_000, "98"),
        _trade(4, START + 10_000, "101"),
        _trade(5, START + 10_001, "120"),
    )
    policy = _policy(take_profit_ratio=Decimal("0.20"), stop_loss_ratio=Decimal("0.20"))

    replay_label = subject.replay_event_label(
        decision=_decision(TradeDirection.LONG),
        trades=trades,
        policy=policy,
    )
    shadow_label = subject.replay_event_label(
        decision=_decision(TradeDirection.LONG),
        trades=trades,
        policy=policy,
    )

    assert replay_label == shadow_label
    assert replay_label.outcome is subject.LabelOutcome.TIMEOUT
    assert replay_label.exit_aggregate_trade_id == 4
    assert replay_label.raw_exit_price == Decimal("101")
    assert replay_label.time_to_outcome_ms == 10_000


def test_missing_entry_is_explicit_and_contains_no_execution_values() -> None:
    trades = (
        _trade(1, START + 5_000, "100"),
        _trade(2, START + 10_000, "101"),
    )

    label = subject.replay_event_label(
        decision=_decision(TradeDirection.LONG),
        trades=trades,
        policy=_policy(maximum_entry_delay_ms=2_000),
    )

    assert label.outcome is subject.LabelOutcome.MISSING_ENTRY
    assert label.entry_timestamp_ms is None
    assert label.exit_timestamp_ms is None
    assert label.net_return_ratio is None


def test_rejects_unordered_trade_path_and_holdout_overlap() -> None:
    with pytest.raises(subject.DeterministicReplayError, match="strictly ordered"):
        subject.replay_event_label(
            decision=_decision(TradeDirection.LONG),
            trades=(
                _trade(2, START + 1_000, "101"),
                _trade(1, START, "100"),
                _trade(3, START + 10_000, "102"),
            ),
            policy=_policy(),
        )

    with pytest.raises(subject.DeterministicReplayError, match="protected holdout"):
        subject.replay_event_label(
            decision=_decision(TradeDirection.LONG, decision_ms=HOLDOUT - 5_000),
            trades=(
                _trade(1, HOLDOUT - 5_000, "100"),
                _trade(2, HOLDOUT + 5_000, "101"),
            ),
            policy=_policy(),
        )


def test_split_windows_require_horizon_sized_purge_and_embargo() -> None:
    with pytest.raises(subject.DeterministicReplayError, match="purge/embargo"):
        subject.ReplayRequest(
            schema_version=subject.REQUEST_SCHEMA_VERSION,
            package_id="replay-test",
            dataset_id=DATASET_ID,
            dataset_manifest_sha256="1" * 64,
            market_manifest_sha256=MARKET_HASH,
            price_path_package_id="price-path-test",
            price_path_manifest_sha256=PRICE_PATH_HASH,
            source_commit_sha=CODE_SHA,
            split_geometry_sha256=SPLIT_HASH,
            split_windows=(
                subject.ReplaySplitWindow("train", START, START + 20_000),
                subject.ReplaySplitWindow("validation", START + 25_000, START + 45_000),
            ),
            sides=(TradeDirection.LONG,),
            policy=_policy(),
            protected_holdout_excluded=True,
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


def _sha(path: Path) -> str:
    import hashlib

    return hashlib.sha256(path.read_bytes()).hexdigest()


def _materialization(root: Path) -> tuple[Path, str]:
    materialization = root / DATASET_ID
    dataset = materialization / subject.DATASET_DIR_NAME
    partition = dataset / "features" / "split=train" / f"symbol={SYMBOL}" / "part.jsonl"
    decision = START + 10_000
    row_seed: dict[str, object] = {
        "schema_version": "wickhunter-dataset-v1",
        "dataset_version": "test-v1",
        "split_name": "train",
        "symbol": SYMBOL,
        "decision_timestamp_ms": decision,
        "feature_available_at_ms": decision,
    }
    row = {**row_seed, "row_sha256": canonical_sha256(row_seed)}
    partition.parent.mkdir(parents=True, exist_ok=True)
    partition.write_text(canonical_json(row) + "\n", encoding="utf-8")
    manifest_seed: dict[str, object] = {
        "schema_version": "wickhunter-dataset-manifest-v1",
        "dataset_version": "test-v1",
        "dataset_request_sha256": "3" * 64,
        "code_sha": CODE_SHA,
        "split_geometry_sha256": SPLIT_HASH,
        "source_selections": [{"selection_sha256": "4" * 64}],
        "universe_snapshot_sha256s": ["5" * 64],
        "partitions": [
            {
                "relative_path": partition.relative_to(dataset).as_posix(),
                "split_name": "train",
                "symbol": SYMBOL,
                "bucket_start_ms": START,
                "row_count": 1,
                "earliest_decision_timestamp_ms": decision,
                "latest_decision_timestamp_ms": decision,
                "sha256": _sha(partition),
            }
        ],
        "total_rows": 1,
        "earliest_decision_timestamp_ms": decision,
        "latest_decision_timestamp_ms": decision,
        "model_execution_authorized": False,
    }
    manifest = {**manifest_seed, "manifest_sha256": canonical_sha256(manifest_seed)}
    _write_json(dataset / subject.MANIFEST_NAME, manifest)
    return materialization, str(manifest["manifest_sha256"])


def _price_path(root: Path, dataset_manifest_sha256: str) -> tuple[Path, str]:
    price_root = root / "price-path"
    partition = price_root / price_path.TRADES_DIR_NAME / f"{SYMBOL}.jsonl"
    trades = [
        _trade(1, START + 10_000, "100"),
        _trade(2, START + 12_000, "106"),
        _trade(3, START + 20_000, "104"),
    ]
    partition.parent.mkdir(parents=True, exist_ok=True)
    partition.write_text(
        "".join(canonical_json(trade.as_json_dict()) + "\n" for trade in trades),
        encoding="utf-8",
    )
    manifest_seed: dict[str, object] = {
        "schema_version": price_path.MANIFEST_SCHEMA_VERSION,
        "package_id": "price-path-test-v1",
        "request_sha256": "6" * 64,
        "dataset_id": DATASET_ID,
        "dataset_manifest_sha256": dataset_manifest_sha256,
        "market_manifest_sha256": MARKET_HASH,
        "source_commit_sha": CODE_SHA,
        "provider_id": price_path.PROVIDER_ID,
        "source": price_path.SOURCE_ID,
        "data_kind": price_path.DATA_KIND,
        "requested_date": "1970-01-01",
        "requested_start_ms": START,
        "requested_end_ms": START + 20_000,
        "label_horizon_ms": 10_000,
        "protected_holdout_start_ms": HOLDOUT,
        "symbols": [SYMBOL],
        "decision_count": 1,
        "archive_evidence": [{"symbol": SYMBOL}],
        "partitions": [
            {
                "symbol": SYMBOL,
                "relative_path": partition.relative_to(price_root).as_posix(),
                "row_count": len(trades),
                "first_timestamp_ms": trades[0].occurred_at_ms,
                "last_timestamp_ms": trades[-1].occurred_at_ms,
                "first_aggregate_trade_id": trades[0].aggregate_trade_id,
                "last_aggregate_trade_id": trades[-1].aggregate_trade_id,
                "sha256": _sha(partition),
            }
        ],
        "total_trade_rows": len(trades),
        "maximum_entry_delay_ms": 0,
        "public_only": True,
        "protected_holdout_accessed": False,
        "immutable_inputs_mutated": False,
        "replay_authorized": False,
        "model_execution_authorized": False,
        "performance_research_authorized": False,
        "execution_enabled": False,
        "live_capital_authorized": False,
        "trading_credentials_present": False,
        "orders_submitted": 0,
    }
    manifest = {**manifest_seed, "manifest_sha256": canonical_sha256(manifest_seed)}
    _write_json(price_root / subject.MANIFEST_NAME, manifest)
    return price_root, str(manifest["manifest_sha256"])


def _request(
    dataset_manifest_sha256: str,
    price_path_manifest_sha256: str,
) -> subject.ReplayRequest:
    return subject.ReplayRequest(
        schema_version=subject.REQUEST_SCHEMA_VERSION,
        package_id="deterministic-replay-test-v1",
        dataset_id=DATASET_ID,
        dataset_manifest_sha256=dataset_manifest_sha256,
        market_manifest_sha256=MARKET_HASH,
        price_path_package_id="price-path-test-v1",
        price_path_manifest_sha256=price_path_manifest_sha256,
        source_commit_sha=CODE_SHA,
        split_geometry_sha256=SPLIT_HASH,
        split_windows=(subject.ReplaySplitWindow("train", START, START + 100_000),),
        sides=(TradeDirection.LONG, TradeDirection.SHORT),
        policy=_policy(),
        protected_holdout_excluded=True,
        immutable_inputs_mutated=False,
        model_execution_authorized=False,
        performance_research_authorized=False,
        execution_enabled=False,
        live_capital_authorized=False,
        trading_credentials_present=False,
        orders_submitted=0,
    )


def test_build_labels_passes_only_the_exact_replay_window(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    decision_timestamp_ms = START + 10_000
    trades = (
        _trade(1, START, "99"),
        _trade(2, decision_timestamp_ms, "100"),
        _trade(3, decision_timestamp_ms + 5_000, "101"),
        _trade(4, decision_timestamp_ms + 10_000, "102"),
        _trade(5, decision_timestamp_ms + 10_000, "103"),
        _trade(6, decision_timestamp_ms + 11_000, "104"),
    )
    request = _request("1" * 64, PRICE_PATH_HASH)
    observed_windows: list[tuple[subject.ReplayAggregateTrade, ...]] = []
    original = subject.replay_event_label

    def observe_window(
        *,
        decision: subject.ReplayDecision,
        trades: tuple[subject.ReplayAggregateTrade, ...],
        policy: subject.ReplayPolicy,
    ) -> subject.CandidateLabel:
        observed_windows.append(tuple(trades))
        return original(decision=decision, trades=trades, policy=policy)

    monkeypatch.setattr(subject, "replay_event_label", observe_window)
    labels = subject._build_labels(
        rows=(
            subject._DatasetRow(
                split_name="train",
                symbol=SYMBOL,
                decision_timestamp_ms=decision_timestamp_ms,
                row_sha256="2" * 64,
            ),
        ),
        trades_by_symbol={SYMBOL: trades},
        request=request,
    )

    assert len(labels) == 2
    assert len(observed_windows) == 2
    for window in observed_windows:
        assert tuple(item.aggregate_trade_id for item in window) == (2, 3, 4, 5)
        assert window[0].occurred_at_ms == decision_timestamp_ms
        assert window[-1].occurred_at_ms == decision_timestamp_ms + 10_000


def test_builds_verifies_reproduces_and_rejects_tampering(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    materialization, dataset_manifest_sha256 = _materialization(tmp_path)
    price_root, price_manifest_sha256 = _price_path(tmp_path, dataset_manifest_sha256)
    request = _request(dataset_manifest_sha256, price_manifest_sha256)
    output = tmp_path / "output"
    monkeypatch.setattr(
        subject,
        "verify_production_materialization",
        lambda _: {"wh01_ready": True},
    )
    monkeypatch.setattr(
        subject,
        "verify_replay_price_path_package",
        lambda **_: {"outcome": "accepted"},
    )

    result = subject.build_deterministic_replay_package(
        materialization_root=materialization,
        price_path_root=price_root,
        output_root=output,
        request=request,
    )

    assert result["outcome"] == "accepted"
    assert result["decision_count"] == 1
    assert result["label_count"] == 2
    assert result["orders_submitted"] == 0
    assert (
        subject.build_deterministic_replay_package(
            materialization_root=materialization,
            price_path_root=price_root,
            output_root=output,
            request=request,
        )
        == result
    )
    label_path = next((output / subject.LABELS_DIR_NAME).rglob("*.jsonl"))
    original = label_path.read_text(encoding="utf-8")
    label_path.write_text(original.replace("take_profit", "timeout", 1), encoding="utf-8")
    with pytest.raises(subject.DeterministicReplayError):
        subject.verify_deterministic_replay_package(
            materialization_root=materialization,
            price_path_root=price_root,
            output_root=output,
        )


def test_build_labels_excludes_only_split_boundary_ineligible_rows() -> None:
    decision_timestamp_ms = START + 10_000
    eligible_row = subject._DatasetRow("train", SYMBOL, decision_timestamp_ms, "1" * 64)
    ineligible_row = subject._DatasetRow("train", SYMBOL, START + 95_000, "2" * 64)
    request = subject.ReplayRequest(
        schema_version=subject.REQUEST_SCHEMA_VERSION,
        package_id="boundary-filter-test",
        dataset_id=DATASET_ID,
        dataset_manifest_sha256="3" * 64,
        market_manifest_sha256=MARKET_HASH,
        price_path_package_id="price-path-boundary-test",
        price_path_manifest_sha256=PRICE_PATH_HASH,
        source_commit_sha=CODE_SHA,
        split_geometry_sha256=SPLIT_HASH,
        split_windows=(subject.ReplaySplitWindow("train", START, START + 100_000),),
        sides=(TradeDirection.LONG, TradeDirection.SHORT),
        policy=_policy(),
        protected_holdout_excluded=True,
        immutable_inputs_mutated=False,
        model_execution_authorized=False,
        performance_research_authorized=False,
        execution_enabled=False,
        live_capital_authorized=False,
        trading_credentials_present=False,
        orders_submitted=0,
    )
    trades = {
        SYMBOL: (
            _trade(1, decision_timestamp_ms, "100"),
            _trade(2, decision_timestamp_ms + 10_000, "101"),
        )
    }

    labels = subject._build_labels(
        rows=(eligible_row, ineligible_row), trades_by_symbol=trades, request=request
    )

    assert len(labels) == 2
    assert {label.dataset_row_sha256 for label in labels} == {"1" * 64}
