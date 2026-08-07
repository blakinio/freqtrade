from __future__ import annotations

import argparse
import json
import os
import tempfile
import time
from collections.abc import Callable
from pathlib import Path
from typing import Any

from ai_platform.wickhunter.candidate_paper_runtime_operator import (
    DEFAULT_MAX_SOURCE_AGE_MS,
    DEFAULT_PUBLIC_MARKET_BASE_URL,
    CandidatePaperRuntimeOperator,
    CandidatePaperRuntimeOperatorError,
    _assert_regular_absolute,
    _boolean,
    _runtime_policy,
    assert_closed_authority_environment,
)
from ai_platform.wickhunter.candidate_paper_runtime_service import CandidatePaperRuntimeService
from ai_platform.wickhunter.candidate_runtime_binding import build_candidate_paper_runtime_binding
from ai_platform.wickhunter.canonical import canonical_json, canonical_sha256
from ai_platform.wickhunter.contracts import DriftState
from ai_platform.wickhunter.shadow_runtime_common import ShadowRuntimeError


TELEMETRY_SCHEMA_VERSION = "wickhunter-paper-runtime-cycle-telemetry-v1"
EARLY_FAIL_SCHEMA_VERSION = "wickhunter-paper-runtime-early-fail-v1"
DEFAULT_POLL_SECONDS = 120
MAX_CYCLE_ATTEMPTS = 3
RETRY_DELAY_SECONDS = 5
MAX_TELEMETRY_RECORDS = 256
MAX_TELEMETRY_BYTES = 512 * 1024
MAX_ERROR_MESSAGE_CHARS = 240
TRANSIENT_SHADOW_RUNTIME_MESSAGES = frozenset({"source state is observed in the future"})
ZERO_AUTHORITY = {
    "protected_holdout_accessed": False,
    "automatic_promotion_enabled": False,
    "trading_credentials_present": False,
    "order_adapter_present": False,
    "execution_enabled": False,
    "orders_submitted": 0,
    "live_capital_authorized": False,
}


class CandidatePaperRuntimeSupervisorError(RuntimeError):
    """Raised when the WH-09 runtime supervisor must fail closed."""


class CandidatePaperRuntimeEarlyFail(CandidatePaperRuntimeSupervisorError):
    """Raised when the prospective PAPER window is already irrecoverably invalid."""


def _now_ms() -> int:
    return time.time_ns() // 1_000_000


def _self_hashed(
    schema_version: str,
    payload: dict[str, object],
    *,
    hash_field: str,
) -> dict[str, object]:
    value: dict[str, object] = {"schema_version": schema_version, **payload}
    value[hash_field] = canonical_sha256({"schema_version": schema_version, "payload": payload})
    return value


def _verify_self_hash(
    payload: dict[str, Any],
    *,
    schema_version: str,
    hash_field: str,
    label: str,
) -> None:
    if payload.get("schema_version") != schema_version:
        raise CandidatePaperRuntimeSupervisorError(f"{label} schema mismatch")
    claimed = payload.get(hash_field)
    body = {
        key: value for key, value in payload.items() if key not in {"schema_version", hash_field}
    }
    expected = canonical_sha256({"schema_version": schema_version, "payload": body})
    if claimed != expected:
        raise CandidatePaperRuntimeSupervisorError(f"{label} self-hash mismatch")


def _assert_zero_authority(payload: dict[str, Any], *, field: str) -> None:
    for key, expected in ZERO_AUTHORITY.items():
        if payload.get(key) != expected:
            raise CandidatePaperRuntimeSupervisorError(f"{field} contains forbidden authority")


def _read_json(path: Path, *, field: str) -> dict[str, Any]:
    if path.is_symlink() or not path.is_file():
        raise CandidatePaperRuntimeSupervisorError(f"{field} must be a regular file")
    if path.stat().st_size > MAX_TELEMETRY_BYTES:
        raise CandidatePaperRuntimeSupervisorError(f"{field} exceeds bounded size")
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise CandidatePaperRuntimeSupervisorError(f"unable to read {field}") from exc
    if not isinstance(payload, dict):
        raise CandidatePaperRuntimeSupervisorError(f"{field} must contain an object")
    return payload


def _atomic_json(path: Path, payload: object) -> None:
    if path.is_symlink():
        raise CandidatePaperRuntimeSupervisorError("atomic destination cannot be a symlink")
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(
        prefix=f".{path.name}.",
        suffix=".tmp",
        dir=path.parent,
    )
    temporary = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
            handle.write(canonical_json(payload) + "\n")
            handle.flush()
            os.fsync(handle.fileno())
        temporary.replace(path)
    except Exception:
        temporary.unlink(missing_ok=True)
        raise


def _write_new_json(path: Path, payload: object) -> None:
    if path.exists() or path.is_symlink():
        raise CandidatePaperRuntimeSupervisorError(f"refusing to overwrite {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    content = (canonical_json(payload) + "\n").encode("utf-8")
    try:
        with path.open("xb") as handle:
            handle.write(content)
            handle.flush()
            os.fsync(handle.fileno())
    except FileExistsError as exc:
        raise CandidatePaperRuntimeSupervisorError(f"refusing to overwrite {path}") from exc


def _is_retryable_cycle_error(error: BaseException) -> bool:
    if isinstance(error, CandidatePaperRuntimeOperatorError):
        return True
    current: BaseException | None = error
    seen: set[int] = set()
    while current is not None and id(current) not in seen:
        seen.add(id(current))
        if (
            isinstance(current, ShadowRuntimeError)
            and str(current) in TRANSIENT_SHADOW_RUNTIME_MESSAGES
        ):
            return True
        current = current.__cause__ if current.__cause__ is not None else current.__context__
    return False


def _bounded_error(error: BaseException) -> dict[str, object]:
    message = " ".join(str(error).split())
    return {
        "code": type(error).__name__,
        "message": message[:MAX_ERROR_MESSAGE_CHARS],
        "retryable": _is_retryable_cycle_error(error),
    }


class CycleTelemetryStore:
    def __init__(
        self,
        *,
        path: Path,
        binding_id: str,
        run_id: str,
        operator_commit: str,
    ) -> None:
        if not path.is_absolute():
            raise CandidatePaperRuntimeSupervisorError("telemetry path must be absolute")
        if path.parent.is_symlink():
            raise CandidatePaperRuntimeSupervisorError("telemetry root cannot be a symlink")
        path.parent.mkdir(parents=True, exist_ok=True)
        self.path = path
        self.binding_id = binding_id
        self.run_id = run_id
        self.operator_commit = operator_commit
        if path.exists() or path.is_symlink():
            self._load_verified()

    def _identity(self) -> dict[str, object]:
        return {
            "binding_id": self.binding_id,
            "run_id": self.run_id,
            "operator_commit": self.operator_commit,
            **ZERO_AUTHORITY,
        }

    def _load_verified(self) -> dict[str, Any]:
        payload = _read_json(self.path, field="cycle telemetry")
        _verify_self_hash(
            payload,
            schema_version=TELEMETRY_SCHEMA_VERSION,
            hash_field="telemetry_sha256",
            label="cycle telemetry",
        )
        _assert_zero_authority(payload, field="cycle telemetry")
        for key, expected in self._identity().items():
            if payload.get(key) != expected:
                raise CandidatePaperRuntimeSupervisorError(
                    f"cycle telemetry identity mismatch: {key}"
                )
        records = payload.get("records")
        if not isinstance(records, list) or len(records) > MAX_TELEMETRY_RECORDS:
            raise CandidatePaperRuntimeSupervisorError("cycle telemetry records are invalid")
        previous: int | None = None
        for record in records:
            if not isinstance(record, dict):
                raise CandidatePaperRuntimeSupervisorError("cycle telemetry record is invalid")
            sequence = record.get("sequence")
            if not isinstance(sequence, int) or sequence < 1:
                raise CandidatePaperRuntimeSupervisorError("cycle telemetry sequence is invalid")
            if previous is not None and sequence != previous + 1:
                raise CandidatePaperRuntimeSupervisorError(
                    "cycle telemetry sequence is not contiguous"
                )
            previous = sequence
            _assert_zero_authority(record, field="cycle telemetry record")
        claimed_last = payload.get("last_sequence")
        expected_last = records[-1]["sequence"] if records else 0
        if claimed_last != expected_last:
            raise CandidatePaperRuntimeSupervisorError("cycle telemetry last sequence mismatch")
        return payload

    def append(
        self,
        *,
        cycle_started_at_ms: int,
        cycle_completed_at_ms: int,
        attempt_count: int,
        outcome: str,
        generation: int | None,
        errors: list[dict[str, object]],
    ) -> None:
        if outcome not in {"success", "fail_closed"}:
            raise CandidatePaperRuntimeSupervisorError("unsupported cycle telemetry outcome")
        current: dict[str, Any] = (
            self._load_verified()
            if self.path.exists()
            else {
                "records": [],
                "last_sequence": 0,
            }
        )
        last_sequence = current.get("last_sequence")
        current_records = current.get("records")
        if not isinstance(last_sequence, int) or not isinstance(current_records, list):
            raise CandidatePaperRuntimeSupervisorError("cycle telemetry state is invalid")
        sequence = last_sequence + 1
        record: dict[str, object] = {
            "sequence": sequence,
            "cycle_started_at_ms": cycle_started_at_ms,
            "cycle_completed_at_ms": cycle_completed_at_ms,
            "elapsed_ms": max(0, cycle_completed_at_ms - cycle_started_at_ms),
            "attempt_count": attempt_count,
            "transient_failure_count": len(errors),
            "outcome": outcome,
            "generation": generation,
            "errors": errors,
            **ZERO_AUTHORITY,
        }
        records = [*current_records, record][-MAX_TELEMETRY_RECORDS:]
        body: dict[str, object] = {
            **self._identity(),
            "retained_record_count": len(records),
            "first_retained_sequence": records[0]["sequence"] if records else 0,
            "last_sequence": sequence,
            "records": records,
        }
        document = _self_hashed(
            TELEMETRY_SCHEMA_VERSION,
            body,
            hash_field="telemetry_sha256",
        )
        encoded = canonical_json(document).encode("utf-8")
        if len(encoded) > MAX_TELEMETRY_BYTES:
            raise CandidatePaperRuntimeSupervisorError(
                "cycle telemetry cannot be persisted within bounded size"
            )
        _atomic_json(self.path, document)
        self._load_verified()


class EarlyFailStore:
    def __init__(
        self,
        *,
        path: Path,
        binding_id: str,
        run_id: str,
        operator_commit: str,
    ) -> None:
        if not path.is_absolute():
            raise CandidatePaperRuntimeSupervisorError("early-fail path must be absolute")
        if path.parent.is_symlink():
            raise CandidatePaperRuntimeSupervisorError("early-fail root cannot be a symlink")
        path.parent.mkdir(parents=True, exist_ok=True)
        self.path = path
        self.binding_id = binding_id
        self.run_id = run_id
        self.operator_commit = operator_commit
        if path.exists() or path.is_symlink():
            self.load_verified()

    def load_verified(self) -> dict[str, Any] | None:
        if not self.path.exists() and not self.path.is_symlink():
            return None
        payload = _read_json(self.path, field="early-fail sentinel")
        _verify_self_hash(
            payload,
            schema_version=EARLY_FAIL_SCHEMA_VERSION,
            hash_field="sentinel_sha256",
            label="early-fail sentinel",
        )
        _assert_zero_authority(payload, field="early-fail sentinel")
        for key, expected in (
            ("binding_id", self.binding_id),
            ("run_id", self.run_id),
            ("operator_commit", self.operator_commit),
        ):
            if payload.get(key) != expected:
                raise CandidatePaperRuntimeSupervisorError(
                    f"early-fail sentinel identity mismatch: {key}"
                )
        if payload.get("blocker_code") != "maximum_snapshot_gap_exceeded":
            raise CandidatePaperRuntimeSupervisorError("early-fail blocker is unsupported")
        return payload

    def seal(self, *, detected_at_ms: int, actual_gap_ms: int) -> dict[str, object]:
        existing = self.load_verified()
        if existing is not None:
            return existing
        body: dict[str, object] = {
            "binding_id": self.binding_id,
            "run_id": self.run_id,
            "operator_commit": self.operator_commit,
            "detected_at_ms": detected_at_ms,
            "blocker_code": "maximum_snapshot_gap_exceeded",
            "actual_gap_ms": actual_gap_ms,
            "recoverable": False,
            **ZERO_AUTHORITY,
        }
        document = _self_hashed(
            EARLY_FAIL_SCHEMA_VERSION,
            body,
            hash_field="sentinel_sha256",
        )
        _write_new_json(self.path, document)
        return document


class CandidatePaperRuntimeSupervisor:
    def __init__(
        self,
        *,
        operator: CandidatePaperRuntimeOperator,
        state_root: Path,
        max_attempts: int = MAX_CYCLE_ATTEMPTS,
        retry_delay_seconds: int = RETRY_DELAY_SECONDS,
        sleep: Callable[[float], None] = time.sleep,
        wall_clock_ms: Callable[[], int] = _now_ms,
        monotonic: Callable[[], float] = time.monotonic,
    ) -> None:
        if not 1 <= max_attempts <= MAX_CYCLE_ATTEMPTS:
            raise CandidatePaperRuntimeSupervisorError("max attempts must be within 1..3")
        if not 0 <= retry_delay_seconds <= 30:
            raise CandidatePaperRuntimeSupervisorError("retry delay must be within 0..30 seconds")
        if not state_root.is_absolute():
            raise CandidatePaperRuntimeSupervisorError("state root must be absolute")
        if state_root.is_symlink():
            raise CandidatePaperRuntimeSupervisorError("state root cannot be a symlink")
        state_root.mkdir(parents=True, exist_ok=True)
        self.operator = operator
        self.max_attempts = max_attempts
        self.retry_delay_seconds = retry_delay_seconds
        self.sleep = sleep
        self.wall_clock_ms = wall_clock_ms
        self.monotonic = monotonic
        binding = operator.service.binding
        self.telemetry = CycleTelemetryStore(
            path=state_root / "cycle-telemetry.json",
            binding_id=binding.binding_id,
            run_id=binding.request.run_id,
            operator_commit=operator.operator_commit,
        )
        self.early_fail = EarlyFailStore(
            path=state_root / "early-fail.json",
            binding_id=binding.binding_id,
            run_id=binding.request.run_id,
            operator_commit=operator.operator_commit,
        )

    def _irrecoverable_gap_ms(self, *, checked_at_ms: int) -> int | None:
        observations = self.operator.service.journal.observations()
        maximum_gap_ms = self.operator.service.binding.policy.maximum_snapshot_gap_ms
        previous_at_ms: int | None = None
        for observation in observations:
            if previous_at_ms is not None:
                gap_ms = observation.observed_at_ms - previous_at_ms
                if gap_ms > maximum_gap_ms:
                    return gap_ms
            previous_at_ms = observation.observed_at_ms
        if observations:
            latest_at_ms = observations[-1].observed_at_ms
            current_gap_ms = checked_at_ms - latest_at_ms
            if current_gap_ms > maximum_gap_ms:
                return current_gap_ms
        return None

    def _check_early_fail(self, *, checked_at_ms: int) -> None:
        existing = self.early_fail.load_verified()
        if existing is not None:
            raise CandidatePaperRuntimeEarlyFail(
                "prospective PAPER window already sealed as irrecoverably invalid"
            )
        actual_gap_ms = self._irrecoverable_gap_ms(checked_at_ms=checked_at_ms)
        if actual_gap_ms is None:
            return
        self.early_fail.seal(
            detected_at_ms=checked_at_ms,
            actual_gap_ms=actual_gap_ms,
        )
        error = CandidatePaperRuntimeEarlyFail(
            f"maximum snapshot gap irrecoverably exceeded: {actual_gap_ms} ms"
        )
        self.operator.publish_failure(error, checked_at_ms=checked_at_ms)
        raise error

    def run_cycle(self) -> bool:
        cycle_started_at_ms = self.wall_clock_ms()
        self._check_early_fail(checked_at_ms=cycle_started_at_ms)
        errors: list[dict[str, object]] = []
        generation: int | None = None
        for attempt in range(1, self.max_attempts + 1):
            attempt_at_ms = self.wall_clock_ms()
            self._check_early_fail(checked_at_ms=attempt_at_ms)
            try:
                generation = self.operator.run_once(observed_at_ms=attempt_at_ms)
            except CandidatePaperRuntimeEarlyFail:
                raise
            except Exception as exc:
                errors.append(_bounded_error(exc))
                retryable = _is_retryable_cycle_error(exc)
                if retryable and attempt < self.max_attempts:
                    self.sleep(self.retry_delay_seconds)
                    continue
                completed_at_ms = self.wall_clock_ms()
                self.operator.publish_failure(exc, checked_at_ms=completed_at_ms)
                self.telemetry.append(
                    cycle_started_at_ms=cycle_started_at_ms,
                    cycle_completed_at_ms=completed_at_ms,
                    attempt_count=attempt,
                    outcome="fail_closed",
                    generation=None,
                    errors=errors,
                )
                self._check_early_fail(checked_at_ms=completed_at_ms)
                return False
            completed_at_ms = self.wall_clock_ms()
            self.telemetry.append(
                cycle_started_at_ms=cycle_started_at_ms,
                cycle_completed_at_ms=completed_at_ms,
                attempt_count=attempt,
                outcome="success",
                generation=generation,
                errors=errors,
            )
            self._check_early_fail(checked_at_ms=completed_at_ms)
            return True
        raise CandidatePaperRuntimeSupervisorError("unreachable retry state")

    def run(self, *, poll_seconds: int, cycles: int = 0) -> bool:
        if not 60 <= poll_seconds <= 900:
            raise CandidatePaperRuntimeSupervisorError(
                "poll cadence must be within 60..900 seconds"
            )
        if not 0 <= cycles <= 30:
            raise CandidatePaperRuntimeSupervisorError("cycles must be within 0..30")
        completed_cycles = 0
        while True:
            cycle_started = self.monotonic()
            succeeded = self.run_cycle()
            completed_cycles += 1
            if cycles and not succeeded:
                return False
            if cycles and completed_cycles >= cycles:
                return True
            elapsed = max(0.0, self.monotonic() - cycle_started)
            self.sleep(max(0.0, poll_seconds - elapsed))


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Restart-safe fail-closed WickHunter candidate PAPER runtime supervisor"
    )
    parser.add_argument("--candidate-root", type=Path, required=True)
    parser.add_argument("--activation-root", type=Path, required=True)
    parser.add_argument("--journal-root", type=Path, required=True)
    parser.add_argument("--liquid20-root", type=Path, required=True)
    parser.add_argument("--health-root", type=Path, required=True)
    parser.add_argument("--operator-commit", required=True)
    parser.add_argument("--public-market-base-url", default=DEFAULT_PUBLIC_MARKET_BASE_URL)
    parser.add_argument("--poll-seconds", type=int, default=DEFAULT_POLL_SECONDS)
    parser.add_argument("--maximum-source-age-ms", type=int, default=DEFAULT_MAX_SOURCE_AGE_MS)
    parser.add_argument(
        "--model-drift",
        choices=tuple(item.value for item in DriftState),
        default=DriftState.HEALTHY.value,
    )
    parser.add_argument(
        "--data-drift",
        choices=tuple(item.value for item in DriftState),
        default=DriftState.HEALTHY.value,
    )
    parser.add_argument("--circuit-breaker-active", type=_boolean, default=False)
    parser.add_argument(
        "--cycles",
        type=int,
        default=0,
        help="0 runs continuously; 1..30 provides a bounded burn-in/preflight mode",
    )
    return parser


def main() -> int:
    args = _parser().parse_args()
    assert_closed_authority_environment()
    for path, field in (
        (args.candidate_root, "candidate root"),
        (args.activation_root, "activation root"),
        (args.journal_root, "journal root"),
        (args.liquid20_root, "Liquid20 root"),
        (args.health_root, "health root"),
    ):
        _assert_regular_absolute(
            path,
            field=field,
            must_exist=field not in {"journal root", "health root"},
        )
    if not args.liquid20_root.is_dir():
        raise CandidatePaperRuntimeOperatorError("Liquid20 root must be a regular directory")
    args.journal_root.mkdir(parents=True, exist_ok=True)
    args.health_root.mkdir(parents=True, exist_ok=True)
    binding = build_candidate_paper_runtime_binding(
        candidate_root=args.candidate_root,
        activation_root=args.activation_root,
    )
    service = CandidatePaperRuntimeService(
        binding=binding,
        runtime_policy=_runtime_policy(),
        journal_root=args.journal_root,
    )
    operator = CandidatePaperRuntimeOperator(
        service=service,
        liquid20_root_path=args.liquid20_root,
        health_path=args.health_root / "health.json",
        operator_commit=args.operator_commit,
        public_market_base_url=args.public_market_base_url,
        maximum_source_age_ms=args.maximum_source_age_ms,
        model_drift=DriftState(args.model_drift),
        data_drift=DriftState(args.data_drift),
        circuit_breaker_active=args.circuit_breaker_active,
    )
    supervisor = CandidatePaperRuntimeSupervisor(
        operator=operator,
        state_root=args.health_root,
    )
    try:
        succeeded = supervisor.run(
            poll_seconds=args.poll_seconds,
            cycles=args.cycles,
        )
    except CandidatePaperRuntimeEarlyFail:
        return 2
    return 0 if succeeded else 1


if __name__ == "__main__":
    raise SystemExit(main())
