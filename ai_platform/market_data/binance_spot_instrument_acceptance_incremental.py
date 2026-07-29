from __future__ import annotations

import argparse
import fcntl
import os
import time
import urllib.parse
from collections.abc import Iterator, Mapping
from contextlib import contextmanager
from pathlib import Path
from typing import IO, Protocol

from ai_platform.market_data.binance_spot_instrument_acceptance import (
    POLICY_NAME,
    REQUEST_NAME,
    SAMPLES_DIR_NAME,
    BinanceSpotInstrumentAcceptancePolicy,
    _decode_object,
    _fetch_once,
    _load_object,
    _sample_failure_report,
    _sample_paths,
    _sample_success_report,
    _seal_package,
    _summarize,
    _write_atomic,
    _write_json_atomic,
    evaluate_package,
    refuse_proxy_environment,
    validate_request,
)
from ai_platform.market_data.binance_spot_instrument_smoke import (
    REDUCED_PAYLOAD_POLICY_VERSION,
    SmokePolicy,
    UrlOpener,
)
from ai_platform.market_data.common import (
    canonical_json_bytes,
    canonical_sha256,
    refuse_trading_credentials,
    validate_commit,
)
from ai_platform.market_data.instrument_adapters import parse_binance_spot_catalog


REQUEST_PATH = Path(
    "ai_platform/market_data/run-requests/"
    "binance-spot-instrument-shadow-acceptance-20260729-v3.json"
)
POLICY_PATH = Path(
    "ai_platform/market_data/binance-spot-instrument-shadow-acceptance-policy-v1.json"
)
ACTIVE_POINTER_NAME = "active-binance-spot-instrument-acceptance-v3.json"
INCREMENTAL_STATE_NAME = "incremental-state.json"
LOCK_NAME = ".binance-spot-instrument-acceptance-v3.lock"
ATTEMPT_MARKER_NAME = "attempt-started.json"
STATE_VERSION = "binance-spot-instrument-acceptance-incremental-state-v1"
POINTER_VERSION = "binance-spot-instrument-acceptance-active-pointer-v1"
STATE_HASH_FIELD = "state_sha256"
POINTER_HASH_FIELD = "pointer_sha256"
EXPECTED_REQUEST: dict[str, object] = {
    "schema_version": 1,
    "request_id": "binance-spot-instrument-shadow-acceptance-20260729-v3",
    "run_id": "binance-spot-instrument-shadow-acceptance-20260729-v3-r1",
    "policy_id": "binance-spot-instrument-shadow-acceptance-v1",
    "source_id": "binance-spot",
    "request_url": (
        "https://api.binance.com/api/v3/exchangeInfo?showPermissionSets=false"
    ),
    "duration_seconds": 86400,
    "sample_interval_seconds": 900,
    "host_id": "freqtrade-synology-staging",
    "host_class": "always_on_nonrestricted_linux_staging",
    "github_hosted_runner": False,
    "durable_storage_uri": (
        "file:///var/lib/freqtrade-staging-state/"
        "binance-spot-instrument-acceptance"
    ),
    "baseline_artifact_id": 8686988992,
    "baseline_artifact_digest": (
        "sha256:1862d17e8c117e31eec6688c8f34c32cce4a505ec125805cd095df6894cc4f6e"
    ),
    "public_only": True,
    "execution_enabled": False,
    "trading_credentials_present": False,
    "proxy_routing_present": False,
    "performance_research_authorized": False,
    "replay_authorized": False,
    "model_training_authorized": False,
    "strategy_research_authorized": False,
    "orders_submitted": 0,
    "production_source_enabled": False,
}


class WallClockNs(Protocol):
    def __call__(self) -> int: ...


def _hashed(seed: Mapping[str, object], *, hash_field: str) -> dict[str, object]:
    return {**seed, hash_field: canonical_sha256(seed)}


def _verify_hash(
    value: Mapping[str, object],
    *,
    hash_field: str,
    field: str,
) -> None:
    claimed = value.get(hash_field)
    if not isinstance(claimed, str) or not claimed:
        raise ValueError(f"{field}.{hash_field} must be a non-empty string")
    seed = dict(value)
    seed.pop(hash_field, None)
    if canonical_sha256(seed) != claimed:
        raise ValueError(f"{field} self hash mismatch")


def _load_hashed(path: Path, *, hash_field: str, field: str) -> dict[str, object]:
    value = _load_object(path)
    _verify_hash(value, hash_field=hash_field, field=field)
    return value


def _validate_exact_request(mapping: Mapping[str, object]) -> None:
    if dict(mapping) != EXPECTED_REQUEST:
        raise ValueError("Binance acceptance v3 request contract mismatch")


def _durable_root_from_request(mapping: Mapping[str, object]) -> Path:
    value = mapping.get("durable_storage_uri")
    if not isinstance(value, str):
        raise TypeError("durable_storage_uri must be a string")
    parsed = urllib.parse.urlsplit(value)
    return Path(parsed.path)


def _align_to_next_interval(now_ns: int, interval_seconds: int) -> int:
    interval_ns = interval_seconds * 1_000_000_000
    return ((now_ns + interval_ns - 1) // interval_ns) * interval_ns


def _active_pointer_path(durable_root: Path) -> Path:
    return durable_root / ACTIVE_POINTER_NAME


def _lock_path(durable_root: Path) -> Path:
    return durable_root / LOCK_NAME


@contextmanager
def _exclusive_lock(durable_root: Path) -> Iterator[IO[bytes]]:
    durable_root.mkdir(parents=True, exist_ok=True)
    handle = _lock_path(durable_root).open("a+b")
    try:
        fcntl.flock(handle.fileno(), fcntl.LOCK_EX)
        yield handle
    finally:
        fcntl.flock(handle.fileno(), fcntl.LOCK_UN)
        handle.close()


def _write_github_outputs(result: Mapping[str, object]) -> None:
    output_path = os.environ.get("GITHUB_OUTPUT", "").strip()
    if not output_path:
        return
    allowed = {
        "status",
        "run_id",
        "run_root",
        "sample_index",
        "next_sample_index",
        "due_ns",
        "outcome",
    }
    with Path(output_path).open("a", encoding="utf-8") as output:
        for key in sorted(allowed):
            value = result.get(key)
            if value is not None:
                output.write(f"{key}={value}\n")


def _smoke_policy(
    policy: BinanceSpotInstrumentAcceptancePolicy,
) -> SmokePolicy:
    smoke_policy = SmokePolicy(
        version=REDUCED_PAYLOAD_POLICY_VERSION,
        source_id=policy.source_id,
        request_url=policy.request_url,
        timeout_seconds=policy.timeout_seconds,
        max_response_bytes=policy.max_response_bytes,
        allow_redirects=policy.allow_redirects,
        retries=policy.retries_per_sample,
        source_acceptance=False,
    )
    smoke_policy.validate()
    return smoke_policy


def _collect_sample(
    *,
    run_root: Path,
    index: int,
    request_interval_seconds: int,
    policy: BinanceSpotInstrumentAcceptancePolicy,
    opener: UrlOpener | None,
) -> dict[str, object]:
    raw_path, snapshot_path, report_path = _sample_paths(run_root, index)
    marker_path = report_path.parent / ATTEMPT_MARKER_NAME
    if report_path.exists():
        report = _load_object(report_path)
        if report.get("status") == "pass":
            if not raw_path.is_file() or not snapshot_path.is_file():
                raise ValueError("completed successful sample evidence is incomplete")
        elif report.get("status") == "fail":
            raw_path.unlink(missing_ok=True)
            snapshot_path.unlink(missing_ok=True)
        else:
            raise ValueError("completed sample report has invalid status")
        marker_path.unlink(missing_ok=True)
        return report
    if marker_path.exists():
        raw_path.unlink(missing_ok=True)
        snapshot_path.unlink(missing_ok=True)
        report = _sample_failure_report(
            index=index,
            scheduled_offset_seconds=index * request_interval_seconds,
            error=RuntimeError("previous sample attempt was interrupted"),
            stage="interrupted",
        )
        _write_json_atomic(report_path, report)
        marker_path.unlink()
        return report
    if raw_path.exists() or snapshot_path.exists():
        raise ValueError("sample evidence exists without attempt marker or report")

    _write_json_atomic(
        marker_path,
        {
            "sample_index": index,
            "attempt_count": 1,
            "attempt_started_ns": time.time_ns(),
            "source_acceptance": False,
            "production_source_enabled": False,
            "orders_submitted": 0,
        },
    )
    stage = "transport"
    smoke_policy = _smoke_policy(policy)
    try:
        if opener is None:
            raw, status, content_type, final_url, sample_started, sample_ended = (
                _fetch_once(smoke_policy)
            )
        else:
            raw, status, content_type, final_url, sample_started, sample_ended = (
                _fetch_once(smoke_policy, opener=opener)
            )
        stage = "decode"
        payload = _decode_object(raw)
        stage = "parse_and_normalize"
        snapshot = parse_binance_spot_catalog(
            payload,
            captured_at_ms=sample_ended // 1_000_000,
            request_url=policy.request_url,
        )
        report = _sample_success_report(
            index=index,
            scheduled_offset_seconds=index * request_interval_seconds,
            raw_payload=raw,
            snapshot=snapshot,
            status=status,
            content_type=content_type,
            final_url=final_url,
            started_ns=sample_started,
            ended_ns=sample_ended,
            required_symbols=policy.thresholds.required_active_native_symbols,
        )
    except Exception as exc:
        report = _sample_failure_report(
            index=index,
            scheduled_offset_seconds=index * request_interval_seconds,
            error=exc,
            stage=stage,
        )
        _write_json_atomic(report_path, report)
    else:
        _write_atomic(raw_path, raw)
        _write_json_atomic(snapshot_path, snapshot.as_json_dict())
        _write_json_atomic(report_path, report)
    marker_path.unlink()
    return report


def initialize_incremental_acceptance(
    *,
    request_path: Path,
    policy_path: Path,
    durable_root: Path,
    collector_commit: str,
    environment: Mapping[str, str] | None = None,
    wall_clock_ns: WallClockNs = time.time_ns,
) -> dict[str, object]:
    env = environment if environment is not None else os.environ
    refuse_trading_credentials(env)
    refuse_proxy_environment(env)
    commit = validate_commit(collector_commit, field="collector_commit")
    policy_mapping = _load_object(policy_path)
    policy = BinanceSpotInstrumentAcceptancePolicy.load(policy_path)
    request_mapping = _load_object(request_path)
    _validate_exact_request(request_mapping)
    request = validate_request(request_mapping, policy=policy)
    if _durable_root_from_request(request_mapping) != durable_root:
        raise ValueError("request durable root does not match runtime durable root")
    durable_root.mkdir(parents=True, exist_ok=True)

    with _exclusive_lock(durable_root):
        pointer_path = _active_pointer_path(durable_root)
        if pointer_path.exists():
            raise FileExistsError("an active Binance acceptance v3 run already exists")
        run_root = durable_root / request.run_id
        if run_root.exists():
            raise FileExistsError(f"run root already exists: {run_root}")
        run_root.mkdir(parents=True, exist_ok=False)
        (run_root / SAMPLES_DIR_NAME).mkdir()
        _write_json_atomic(run_root / REQUEST_NAME, request_mapping)
        _write_json_atomic(run_root / POLICY_NAME, policy_mapping)

        now_ns = wall_clock_ns()
        window_started_ns = _align_to_next_interval(
            now_ns,
            request.sample_interval_seconds,
        )
        expected_samples = (
            request.duration_seconds // request.sample_interval_seconds + 1
        )
        state_seed: dict[str, object] = {
            "state_version": STATE_VERSION,
            "status": "active",
            "request_id": request.request_id,
            "run_id": request.run_id,
            "collector_commit": commit,
            "window_started_ns": window_started_ns,
            "ended_ns": None,
            "next_sample_index": 0,
            "expected_sample_count": expected_samples,
            "sample_interval_seconds": request.sample_interval_seconds,
            "last_sample_completed_ns": None,
            "source_acceptance": False,
            "production_source_enabled": False,
            "orders_submitted": 0,
        }
        state = _hashed(state_seed, hash_field=STATE_HASH_FIELD)
        _write_json_atomic(run_root / INCREMENTAL_STATE_NAME, state)
        pointer_seed: dict[str, object] = {
            "pointer_version": POINTER_VERSION,
            "request_id": request.request_id,
            "run_id": request.run_id,
            "run_root": str(run_root),
            "state_sha256": state[STATE_HASH_FIELD],
        }
        pointer = _hashed(pointer_seed, hash_field=POINTER_HASH_FIELD)
        _write_json_atomic(pointer_path, pointer)

    return {
        "status": "initialized",
        "run_id": request.run_id,
        "run_root": str(run_root),
        "next_sample_index": 0,
        "due_ns": window_started_ns,
    }


def _load_active_run(
    *,
    durable_root: Path,
) -> tuple[Path, dict[str, object], dict[str, object]]:
    pointer_path = _active_pointer_path(durable_root)
    pointer = _load_hashed(
        pointer_path,
        hash_field=POINTER_HASH_FIELD,
        field="active_pointer",
    )
    run_id = pointer.get("run_id")
    if not isinstance(run_id, str) or not run_id:
        raise ValueError("active pointer run_id is invalid")
    run_root = Path(str(pointer.get("run_root", "")))
    if run_root != durable_root / run_id:
        raise ValueError("active pointer run root escapes durable root")
    state = _load_hashed(
        run_root / INCREMENTAL_STATE_NAME,
        hash_field=STATE_HASH_FIELD,
        field="incremental_state",
    )
    if state.get("run_id") != run_id:
        raise ValueError("active pointer and state run_id differ")
    if pointer.get("state_sha256") != state.get(STATE_HASH_FIELD):
        pointer_seed: dict[str, object] = {
            "pointer_version": POINTER_VERSION,
            "request_id": state["request_id"],
            "run_id": state["run_id"],
            "run_root": str(run_root),
            "state_sha256": state[STATE_HASH_FIELD],
        }
        pointer = _hashed(pointer_seed, hash_field=POINTER_HASH_FIELD)
        _write_json_atomic(pointer_path, pointer)
    return run_root, pointer, state


def _rewrite_state_and_pointer(
    *,
    durable_root: Path,
    run_root: Path,
    state_seed: Mapping[str, object],
) -> dict[str, object]:
    state = _hashed(state_seed, hash_field=STATE_HASH_FIELD)
    _write_json_atomic(run_root / INCREMENTAL_STATE_NAME, state)
    pointer_seed: dict[str, object] = {
        "pointer_version": POINTER_VERSION,
        "request_id": state["request_id"],
        "run_id": state["run_id"],
        "run_root": str(run_root),
        "state_sha256": state[STATE_HASH_FIELD],
    }
    pointer = _hashed(pointer_seed, hash_field=POINTER_HASH_FIELD)
    _write_json_atomic(_active_pointer_path(durable_root), pointer)
    return state


def _finalize(
    *,
    durable_root: Path,
    run_root: Path,
    state: Mapping[str, object],
    policy_path: Path,
) -> dict[str, object]:
    policy = BinanceSpotInstrumentAcceptancePolicy.load(policy_path)
    request_mapping = _load_object(run_root / REQUEST_NAME)
    _validate_exact_request(request_mapping)
    request = validate_request(request_mapping, policy=policy)
    policy_mapping = _load_object(run_root / POLICY_NAME)
    reports = [
        _load_object(path)
        for path in sorted(
            (run_root / SAMPLES_DIR_NAME).glob("*/sample-report.json")
        )
    ]
    expected_samples = int(state["expected_sample_count"])
    if len(reports) != expected_samples:
        raise ValueError("cannot finalize an incomplete incremental sample set")
    started_ns = int(state["window_started_ns"])
    ended_ns = int(state["ended_ns"])
    summary = _summarize(
        request=request,
        started_ns=started_ns,
        ended_ns=ended_ns,
        observed_duration_seconds=max(0.0, (ended_ns - started_ns) / 1_000_000_000),
        reports=reports,
    )
    collector_commit = str(state["collector_commit"])
    _seal_package(
        root=run_root,
        request_mapping=request_mapping,
        policy_mapping=policy_mapping,
        summary=summary,
        collector_commit=collector_commit,
        policy=policy,
    )
    report = evaluate_package(run_root=run_root, policy_path=policy_path)
    _active_pointer_path(durable_root).unlink()
    return {
        "status": "finalized",
        "run_id": request.run_id,
        "run_root": str(run_root),
        "next_sample_index": expected_samples,
        "outcome": report["outcome"],
    }


def collect_due_incremental_sample(
    *,
    policy_path: Path,
    durable_root: Path,
    environment: Mapping[str, str] | None = None,
    opener: UrlOpener | None = None,
    wall_clock_ns: WallClockNs = time.time_ns,
) -> dict[str, object]:
    env = environment if environment is not None else os.environ
    refuse_trading_credentials(env)
    refuse_proxy_environment(env)
    pointer_path = _active_pointer_path(durable_root)
    if not pointer_path.exists():
        return {"status": "idle"}

    with _exclusive_lock(durable_root):
        if not pointer_path.exists():
            return {"status": "idle"}
        run_root, _, state = _load_active_run(durable_root=durable_root)
        status = state.get("status")
        if status == "completed":
            return _finalize(
                durable_root=durable_root,
                run_root=run_root,
                state=state,
                policy_path=policy_path,
            )
        if status != "active":
            raise ValueError("incremental acceptance state is not active")

        policy = BinanceSpotInstrumentAcceptancePolicy.load(policy_path)
        request_mapping = _load_object(run_root / REQUEST_NAME)
        _validate_exact_request(request_mapping)
        request = validate_request(request_mapping, policy=policy)
        packaged_policy = _load_object(run_root / POLICY_NAME)
        if canonical_json_bytes(packaged_policy) != canonical_json_bytes(
            _load_object(policy_path)
        ):
            raise ValueError("packaged policy differs from scheduler policy")

        index = int(state["next_sample_index"])
        expected_samples = int(state["expected_sample_count"])
        if index >= expected_samples:
            raise ValueError("incremental sample index exceeds expected count")
        interval_ns = request.sample_interval_seconds * 1_000_000_000
        due_ns = int(state["window_started_ns"]) + index * interval_ns
        last_completed = state.get("last_sample_completed_ns")
        if last_completed is not None:
            due_ns = max(due_ns, int(last_completed) + interval_ns)
        now_ns = wall_clock_ns()
        if now_ns < due_ns:
            return {
                "status": "not_due",
                "run_id": request.run_id,
                "run_root": str(run_root),
                "next_sample_index": index,
                "due_ns": due_ns,
            }

        _collect_sample(
            run_root=run_root,
            index=index,
            request_interval_seconds=request.sample_interval_seconds,
            policy=policy,
            opener=opener,
        )
        completed_ns = wall_clock_ns()
        next_index = index + 1
        state_seed = dict(state)
        state_seed.pop(STATE_HASH_FIELD, None)
        state_seed["next_sample_index"] = next_index
        state_seed["last_sample_completed_ns"] = completed_ns
        if next_index == expected_samples:
            state_seed["status"] = "completed"
            state_seed["ended_ns"] = completed_ns
        updated_state = _rewrite_state_and_pointer(
            durable_root=durable_root,
            run_root=run_root,
            state_seed=state_seed,
        )
        if next_index == expected_samples:
            return _finalize(
                durable_root=durable_root,
                run_root=run_root,
                state=updated_state,
                policy_path=policy_path,
            )
        return {
            "status": "sampled",
            "run_id": request.run_id,
            "run_root": str(run_root),
            "sample_index": index,
            "next_sample_index": next_index,
        }


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Initialize or advance non-blocking Binance Spot instrument acceptance"
        )
    )
    subparsers = parser.add_subparsers(dest="command", required=True)
    init_parser = subparsers.add_parser("init")
    init_parser.add_argument("--request", type=Path, required=True)
    init_parser.add_argument("--policy", type=Path, default=POLICY_PATH)
    init_parser.add_argument("--durable-root", type=Path, required=True)
    init_parser.add_argument("--collector-commit", required=True)
    sample_parser = subparsers.add_parser("sample")
    sample_parser.add_argument("--policy", type=Path, default=POLICY_PATH)
    sample_parser.add_argument("--durable-root", type=Path, required=True)
    return parser


def main() -> int:
    args = _parser().parse_args()
    if args.command == "init":
        result = initialize_incremental_acceptance(
            request_path=args.request,
            policy_path=args.policy,
            durable_root=args.durable_root,
            collector_commit=args.collector_commit,
        )
    else:
        result = collect_due_incremental_sample(
            policy_path=args.policy,
            durable_root=args.durable_root,
        )
    _write_github_outputs(result)
    print(canonical_json_bytes(result).decode("utf-8"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
