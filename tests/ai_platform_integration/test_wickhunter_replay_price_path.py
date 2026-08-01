from __future__ import annotations

import hashlib
import json
import zipfile
from dataclasses import replace
from pathlib import Path

import pytest

from ai_platform.wickhunter import replay_price_path as subject
from ai_platform.wickhunter.canonical import canonical_json, canonical_sha256


DAY = "2026-07-31"
START = 1_785_484_800_000
DECISION_ONE = START + 10_000
DECISION_TWO = START + 320_000
HORIZON = 900_000
END = DECISION_TWO + HORIZON
HOLDOUT = 1_785_542_400_000
SYMBOL = "BTCUSDT"
DATASET_ID = "wickhunter-wh01-production-dataset-test"
MARKET_HASH = "a" * 64
CODE_SHA = "b" * 40


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(canonical_json(payload) + "\n", encoding="utf-8")


def _materialization_root(root: Path) -> tuple[Path, str]:
    materialization = root / DATASET_ID
    dataset = materialization / subject.DATASET_DIR_NAME
    partition = dataset / "features" / "split=train" / f"symbol={SYMBOL}" / "part.jsonl"
    rows: list[dict[str, object]] = []
    for decision in (DECISION_ONE, DECISION_TWO):
        seed: dict[str, object] = {
            "schema_version": "wickhunter-dataset-v1",
            "dataset_version": "test-dataset-v1",
            "split_name": "train",
            "symbol": SYMBOL,
            "decision_timestamp_ms": decision,
            "feature_available_at_ms": decision,
        }
        rows.append({**seed, "row_sha256": canonical_sha256(seed)})
    partition.parent.mkdir(parents=True, exist_ok=True)
    partition.write_text(
        "".join(canonical_json(row) + "\n" for row in rows),
        encoding="utf-8",
    )
    manifest_seed: dict[str, object] = {
        "schema_version": "wickhunter-dataset-manifest-v1",
        "dataset_version": "test-dataset-v1",
        "dataset_request_sha256": "c" * 64,
        "code_sha": CODE_SHA,
        "split_geometry_sha256": "d" * 64,
        "source_selections": [{"selection_sha256": "e" * 64}],
        "universe_snapshot_sha256s": ["f" * 64],
        "partitions": [
            {
                "relative_path": partition.relative_to(dataset).as_posix(),
                "split_name": "train",
                "symbol": SYMBOL,
                "bucket_start_ms": START,
                "row_count": len(rows),
                "earliest_decision_timestamp_ms": DECISION_ONE,
                "latest_decision_timestamp_ms": DECISION_TWO,
                "sha256": _sha(partition),
            }
        ],
        "total_rows": len(rows),
        "earliest_decision_timestamp_ms": DECISION_ONE,
        "latest_decision_timestamp_ms": DECISION_TWO,
        "model_execution_authorized": False,
    }
    manifest = {
        **manifest_seed,
        "manifest_sha256": canonical_sha256(manifest_seed),
    }
    _write_json(dataset / "manifest.json", manifest)
    return materialization, str(manifest["manifest_sha256"])


def _archive_paths(input_root: Path) -> tuple[Path, Path]:
    archive = input_root / "raw" / f"{SYMBOL}-aggTrades-{DAY}.zip"
    return archive, archive.with_name(archive.name + ".CHECKSUM")


def _write_archive(
    input_root: Path,
    *,
    timestamps: list[int] | None = None,
    checksum_override: str | None = None,
    member_name: str | None = None,
    include_header: bool = True,
) -> tuple[Path, Path]:
    archive, checksum = _archive_paths(input_root)
    archive.parent.mkdir(parents=True, exist_ok=True)
    expected_member = f"{SYMBOL}-aggTrades-{DAY}.csv"
    member = member_name or expected_member
    timestamps = timestamps or list(range(START, END + 2_000, 1_000))
    lines: list[str] = []
    if include_header:
        lines.append(
            "agg_trade_id,price,quantity,first_trade_id,last_trade_id,timestamp,is_buyer_maker"
        )
    for index, timestamp in enumerate(timestamps, 1):
        lines.append(f"{index},100.5,2.0,{index},{index},{timestamp},false")
    with zipfile.ZipFile(archive, "w", compression=zipfile.ZIP_DEFLATED) as handle:
        handle.writestr(member, "\n".join(lines) + "\n")
    digest = checksum_override or _sha(archive)
    checksum.write_text(f"{digest}  {archive.name}\n", encoding="utf-8")
    return archive, checksum


def _request(manifest_sha256: str) -> subject.ReplayPricePathRequest:
    archive, checksum = _archive_paths(Path())
    return subject.ReplayPricePathRequest(
        schema_version=subject.REQUEST_SCHEMA_VERSION,
        package_id="wickhunter-replay-price-path-test-v1",
        dataset_id=DATASET_ID,
        dataset_manifest_sha256=manifest_sha256,
        market_manifest_sha256=MARKET_HASH,
        source_commit_sha=CODE_SHA,
        requested_date=DAY,
        requested_start_ms=DECISION_ONE,
        requested_end_ms=END,
        label_horizon_ms=HORIZON,
        protected_holdout_start_ms=HOLDOUT,
        symbols=(SYMBOL,),
        archives=(
            subject.ReplayArchiveInput(
                symbol=SYMBOL,
                archive_relative_path=archive.as_posix(),
                checksum_relative_path=checksum.as_posix(),
            ),
        ),
        public_only=True,
        protected_holdout_excluded=True,
        replay_authorized=False,
        model_execution_authorized=False,
        performance_research_authorized=False,
        execution_enabled=False,
        live_capital_authorized=False,
        trading_credentials_present=False,
        orders_submitted=0,
    )


@pytest.fixture
def accepted_materialization(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        subject,
        "verify_production_materialization",
        lambda _: {"wh01_ready": True},
    )


def test_builds_and_independently_verifies_exact_trade_path(
    tmp_path: Path,
    accepted_materialization: None,
) -> None:
    materialization, manifest_sha256 = _materialization_root(tmp_path)
    input_root = tmp_path / "input"
    _write_archive(input_root)
    output = tmp_path / "output"
    request = _request(manifest_sha256)

    result = subject.build_replay_price_path_package(
        input_root=input_root,
        materialization_root=materialization,
        output_root=output,
        request=request,
    )

    assert result["outcome"] == "accepted"
    assert result["decision_count"] == 2
    assert result["symbol_count"] == 1
    assert result["exact_trade_sequence_available"] is True
    assert result["protected_holdout_accessed"] is False
    manifest = json.loads((output / subject.MANIFEST_NAME).read_text(encoding="utf-8"))
    assert manifest["dataset_manifest_sha256"] == manifest_sha256
    assert manifest["request_sha256"] == request.request_sha256
    assert manifest["replay_authorized"] is False
    assert manifest["orders_submitted"] == 0
    assert (
        subject.verify_replay_price_path_package(
            output_root=output,
            materialization_root=materialization,
            input_root=input_root,
        )
        == result
    )
    assert (
        subject.build_replay_price_path_package(
            input_root=input_root,
            materialization_root=materialization,
            output_root=output,
            request=request,
        )
        == result
    )


def test_output_identity_is_deterministic(
    tmp_path: Path,
    accepted_materialization: None,
) -> None:
    materialization, manifest_sha256 = _materialization_root(tmp_path)
    input_root = tmp_path / "input"
    _write_archive(input_root, include_header=False)
    request = _request(manifest_sha256)

    first = tmp_path / "first"
    second = tmp_path / "second"
    subject.build_replay_price_path_package(
        input_root=input_root,
        materialization_root=materialization,
        output_root=first,
        request=request,
    )
    subject.build_replay_price_path_package(
        input_root=input_root,
        materialization_root=materialization,
        output_root=second,
        request=request,
    )

    first_manifest = json.loads((first / subject.MANIFEST_NAME).read_text(encoding="utf-8"))
    second_manifest = json.loads((second / subject.MANIFEST_NAME).read_text(encoding="utf-8"))
    assert first_manifest["manifest_sha256"] == second_manifest["manifest_sha256"]
    assert (first / subject.CHECKSUM_INDEX_NAME).read_bytes() == (
        second / subject.CHECKSUM_INDEX_NAME
    ).read_bytes()


def test_rejects_checksum_mismatch(
    tmp_path: Path,
    accepted_materialization: None,
) -> None:
    materialization, manifest_sha256 = _materialization_root(tmp_path)
    input_root = tmp_path / "input"
    _write_archive(input_root, checksum_override="0" * 64)

    with pytest.raises(subject.ReplayPricePathError, match="does not match CHECKSUM"):
        subject.build_replay_price_path_package(
            input_root=input_root,
            materialization_root=materialization,
            output_root=tmp_path / "output",
            request=_request(manifest_sha256),
        )


def test_rejects_zip_member_traversal(
    tmp_path: Path,
    accepted_materialization: None,
) -> None:
    materialization, manifest_sha256 = _materialization_root(tmp_path)
    input_root = tmp_path / "input"
    _write_archive(
        input_root,
        member_name=f"../{SYMBOL}-aggTrades-{DAY}.csv",
    )

    with pytest.raises(subject.ReplayPricePathError, match="member identity"):
        subject.build_replay_price_path_package(
            input_root=input_root,
            materialization_root=materialization,
            output_root=tmp_path / "output",
            request=_request(manifest_sha256),
        )


def test_accepts_one_safe_nested_csv_member(
    tmp_path: Path,
    accepted_materialization: None,
) -> None:
    materialization, manifest_sha256 = _materialization_root(tmp_path)
    input_root = tmp_path / "input"
    _write_archive(
        input_root,
        member_name=f"nested/{SYMBOL}-aggTrades-{DAY}.csv",
    )

    result = subject.build_replay_price_path_package(
        input_root=input_root,
        materialization_root=materialization,
        output_root=tmp_path / "output",
        request=_request(manifest_sha256),
    )

    assert result["outcome"] == "accepted"


def test_rejects_path_without_trade_inside_horizon(
    tmp_path: Path,
    accepted_materialization: None,
) -> None:
    materialization, manifest_sha256 = _materialization_root(tmp_path)
    input_root = tmp_path / "input"
    _write_archive(
        input_root,
        timestamps=[START, END],
    )

    with pytest.raises(subject.ReplayPricePathError, match="contains no aggregate trade"):
        subject.build_replay_price_path_package(
            input_root=input_root,
            materialization_root=materialization,
            output_root=tmp_path / "output",
            request=_request(manifest_sha256),
        )


def test_rejects_dataset_partition_tampering(
    tmp_path: Path,
    accepted_materialization: None,
) -> None:
    materialization, manifest_sha256 = _materialization_root(tmp_path)
    input_root = tmp_path / "input"
    _write_archive(input_root)
    partition = next((materialization / subject.DATASET_DIR_NAME / "features").rglob("*.jsonl"))
    partition.write_text("tampered\n", encoding="utf-8")

    with pytest.raises(subject.ReplayPricePathError, match="partition hash mismatch"):
        subject.build_replay_price_path_package(
            input_root=input_root,
            materialization_root=materialization,
            output_root=tmp_path / "output",
            request=_request(manifest_sha256),
        )


def test_verifier_rejects_normalized_trade_tampering(
    tmp_path: Path,
    accepted_materialization: None,
) -> None:
    materialization, manifest_sha256 = _materialization_root(tmp_path)
    input_root = tmp_path / "input"
    _write_archive(input_root)
    output = tmp_path / "output"
    subject.build_replay_price_path_package(
        input_root=input_root,
        materialization_root=materialization,
        output_root=output,
        request=_request(manifest_sha256),
    )
    path = output / subject.TRADES_DIR_NAME / f"{SYMBOL}.jsonl"
    path.write_text("tampered\n", encoding="utf-8")

    with pytest.raises(subject.ReplayPricePathError, match="partition hash mismatch"):
        subject.verify_replay_price_path_package(
            output_root=output,
            materialization_root=materialization,
            input_root=input_root,
        )


def test_request_rejects_holdout_overlap() -> None:
    base = _request("1" * 64)

    with pytest.raises(subject.ReplayPricePathError, match="protected holdout"):
        replace(base, requested_end_ms=HOLDOUT)


def test_request_json_requires_explicit_disabled_authority() -> None:
    payload = json.loads(canonical_json(_request("1" * 64)))
    payload.pop("replay_authorized")

    with pytest.raises(subject.ReplayPricePathError, match="replay_authorized must be false"):
        subject.request_from_json(payload)
