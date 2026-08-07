from __future__ import annotations

import argparse
import json
import os
import re
import tempfile
import time
from collections.abc import Callable
from pathlib import Path
from typing import Any

from ai_platform.wickhunter.candidate_paper_runtime_operator import (
    CandidatePaperRuntimeOperator,
    CandidatePaperRuntimeOperatorError,
    ZERO_AUTHORITY,
    _assert_regular_absolute,
    _parser as operator_parser,
    _runtime_policy,
    assert_closed_authority_environment,
)
from ai_platform.wickhunter.candidate_paper_runtime_service import CandidatePaperRuntimeService
from ai_platform.wickhunter.candidate_runtime_binding import build_candidate_paper_runtime_binding
from ai_platform.wickhunter.canonical import canonical_json, canonical_sha256
from ai_platform.wickhunter.contracts import DriftState


CYCLE_HISTORY_SCHEMA_VERSION = "wickhunter-paper-runtime-cycle-history-v1"
CYCLE_RECORD_SCHEMA_VERSION = "wickhunter-paper-runtime-cycle-record-v1"
DEFAULT_RESILIENT_POLL_SECONDS = 120
DEFAULT_CYCLE_RETRY_ATTEMPTS = 3
DEFAULT_CYCLE_RETRY_DELAY_SECONDS = 10
DEFAULT_CYCLE_HISTORY_LIMIT = 512
MAX_CYCLE_RETRY_ATTEMPTS = 5
MAX_CYCLE_RETRY_DELAY_SECONDS = 60
MIN_CYCLE_HISTORY_LIMIT = 64
MAX_CYCLE_HISTORY_LIMIT = 2048
_SECRET_RE = re.compile(
    r"(?i)(api[_-]?key|secret|token|password|authorization)(\s*[:=]\s*)([^\s,&;]+)"
)
_URL_CREDENTIAL_RE = re.compile(r"(?i)(https?://)([^/@\s]+)@")


class CandidatePaperRuntimeSupervisorError(RuntimeError):
    """Raised when resilient WH09 supervision cannot proceed safely."""


def _bounded_integer(
    value: str,
    *,
    minimum: int,
    maximum: int,
    field: str,
) -> int:
    try:
        parsed = int(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError(f"{field} must be an integer") from exc
    if not minimum <= parsed <= maximum:
        raise argparse.ArgumentTypeError(
            f"{field} must be between {minimum} and {maximum}"
        )
    return parsed


def _redact_error_message(error: BaseException) -> str:
    text = str(error)
    text = _SECRET_RE.sub(r"\1\2[redacted]", text)
    text = _URL_CREDENTIAL_RE.sub(r"\1[redacted]@", text)
    return text[:240]


def _atomic_json(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.parent.is_symlink() or path.is_symlink():
        raise CandidatePaperRuntimeSupervisorError("cycle history path cannot be a symlink")
    descriptor, temporary_name = tempfile.mkstemp(
        prefix=f".{path.name}.", suffix=".tmp", dir=path.parent
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


class CycleHistory:
    def __init__(self, path: Path, *, limit: int = DEFAULT_CYCLE_HISTORY_LIMIT) -> None:
        if not path.is_absolute():
            raise CandidatePaperRuntimeSupervisorError("cycle history path must be absolute")
        if not MIN_CYCLE_HISTORY_LIMIT <= limit <= MAX_CYCLE_HISTORY_LIMIT:
            raise CandidatePaperRuntimeSupervisorError("cycle history limit is outside bounds")
        self.path = path
        self.limit = limit
        self._records: list[dict[str, object]] = []
        self._dropped_record_count = 0
        self._load()

    @property
    def records(self) -> tuple[dict[str, object], ...]:
        return tuple(dict(item) for item in self._records)

    @property
    def dropped_record_count(self) -> int:
        return self._dropped_record_count

    def _payload(self) -> dict[str, object]:
        body: dict[str, object] = {
            "schema_version": CYCLE_HISTORY_SCHEMA_VERSION,
            "history_limit": self.limit,
            "dropped_record_count": self._dropped_record_count,
            "records": self._records,
            **ZERO_AUTHORITY,
        }
        return {**body, "history_sha256": canonical_sha256(body)}

    def _load(self) -> None:
        if not self.path.exists():
            return
        if self.path.is_symlink() or not self.path.is_file():
            raise CandidatePaperRuntimeSupervisorError("cycle history must be a regular file")
        try:
            payload = json.loads(self.path.read_text(encoding="utf-8"))
        except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise CandidatePaperRuntimeSupervisorError("cycle history is unreadable") from exc
        if not isinstance(payload, dict):
            raise CandidatePaperRuntimeSupervisorError("cycle history must contain an object")
        claimed = payload.pop("history_sha256", None)
        if claimed != canonical_sha256(payload):
            raise CandidatePaperRuntimeSupervisorError("cycle history self-hash mismatch")
        if payload.get("schema_version") != CYCLE_HISTORY_SCHEMA_VERSION:
            raise CandidatePaperRuntimeSupervisorError("cycle history schema mismatch")
        if payload.get("history_limit") != self.limit:
            raise CandidatePaperRuntimeSupervisorError("cycle history limit substitution")
        for key, expected in ZERO_AUTHORITY.items():
            if payload.get(key) != expected:
                raise CandidatePaperRuntimeSupervisorError(
                    f"cycle history authority mismatch: {key}"
                )
        dropped = payload.get("dropped_record_count")
        records = payload.get("records")
        if not isinstance(dropped, int) or dropped < 0 or not isinstance(records, list):
            raise CandidatePaperRuntimeSupervisorError("cycle history counters are invalid")
        if len(records) > self.limit:
            raise CandidatePaperRuntimeSupervisorError("cycle history exceeds bounded limit")
        expected_sequence = dropped + 1
        normalized: list[dict[str, object]] = []
        for record in records:
            if not isinstance(record, dict):
                raise CandidatePaperRuntimeSupervisorError("cycle history record is invalid")
            record = dict(record)
            claimed_record_hash = record.pop("record_sha256", None)
            if claimed_record_hash != canonical_sha256(record):
                raise CandidatePaperRuntimeSupervisorError("cycle record self-hash mismatch")
            if record.get("schema_version") != CYCLE_RECORD_SCHEMA_VERSION:
                raise CandidatePaperRuntimeSupervisorError("cycle record schema mismatch")
            if record.get("sequence") != expected_sequence:
                raise CandidatePaperRuntimeSupervisorError("cycle history sequence mismatch")
            for key, expected in ZERO_AUTHORITY.items():
                if record.get(key) != expected:
                    raise CandidatePaperRuntimeSupervisorError(
                        f"cycle record authority mismatch: {key}"
                    )
            normalized.append({**record, "record_sha256": claimed_record_hash})
            expected_sequence += 1
        self._dropped_record_count = dropped
        self._records = normalized

    def append(
        self,
        *,
        cycle_started_at_ms: int,
        checked_at_ms: int,
        attempt: int,
        outcome: str,
        generation_before: int,
        generation_after: int,
        retry_scheduled: bool,
        elapsed_ms: int,
        error: BaseException | None,
    ) -> dict[str, object]:
        if outcome not in {"success", "failure"}:
            raise CandidatePaperRuntimeSupervisorError("cycle outcome is invalid")
        if attempt < 1 or generation_before < 0 or generation_after < 0 or elapsed_ms < 0:
            raise CandidatePaperRuntimeSupervisorError("cycle record counters are invalid")
        sequence = self._dropped_record_count + len(self._records) + 1
        body: dict[str, object] = {
            "schema_version": CYCLE_RECORD_SCHEMA_VERSION,
            "sequence": sequence,
            "cycle_started_at_ms": cycle_started_at_ms,
            "checked_at_ms": checked_at_ms,
            "attempt": attempt,
            "outcome": outcome,
            "generation_before": generation_before,
            "generation_after": generation_after,
            "retry_scheduled": retry_scheduled,
            "elapsed_ms": elapsed_ms,
            "error_code": None if error is None else type(error).__name__,
            "error_message": None if error is None else _redact_error_message(error),
            **ZERO_AUTHORITY,
        }
        record = {**body, "record_sha256": canonical_sha256(body)}
        self._records.append(record)
        if len(self._records) > self.limit:
            dropped_now = len(self._records) - self.limit
            self._records = self._records[dropped_now:]
            self._dropped_record_count += dropped_now
        _atomic_json(self.path, self._payload())
        return dict(record)


def _retry_allowed(
    operator: CandidatePaperRuntimeOperator,
    *,
    checked_at_ms: int,
    error: BaseException,
) -> bool:
    request = operator.service.binding.request
    if not request.window_start_ms <= checked_at_ms < request.window_end_ms:
        return False
    if isinstance(error, CandidatePaperRuntimeOperatorError) and (
        "outside the immutable activation window" in str(error)
    ):
        return False
    return True


def run_resilient_cycle(
    operator: CandidatePaperRuntimeOperator,
    history: CycleHistory,
    *,
    retry_attempts: int = DEFAULT_CYCLE_RETRY_ATTEMPTS,
    retry_delay_seconds: int = DEFAULT_CYCLE_RETRY_DELAY_SECONDS,
    now_ms: Callable[[], int] | None = None,
    monotonic_ns: Callable[[], int] | None = None,
    sleep: Callable[[float], None] | None = None,
) -> bool:
    if not 1 <= retry_attempts <= MAX_CYCLE_RETRY_ATTEMPTS:
        raise CandidatePaperRuntimeSupervisorError("retry attempts are outside bounds")
    if not 1 <= retry_delay_seconds <= MAX_CYCLE_RETRY_DELAY_SECONDS:
        raise CandidatePaperRuntimeSupervisorError("retry delay is outside bounds")
    current_ms = now_ms or (lambda: time.time_ns() // 1_000_000)
    monotonic = monotonic_ns or time.monotonic_ns
    sleeper = sleep or time.sleep
    cycle_started_at_ms = current_ms()

    for attempt in range(1, retry_attempts + 1):
        checked_at_ms = current_ms()
        generation_before = operator.service.runtime.state.generation
        started_ns = monotonic()
        try:
            generation_after = operator.run_once(observed_at_ms=checked_at_ms)
        except Exception as exc:
            elapsed_ms = max(0, (monotonic() - started_ns) // 1_000_000)
            generation_after = operator.service.runtime.state.generation
            retry_scheduled = attempt < retry_attempts and _retry_allowed(
                operator,
                checked_at_ms=checked_at_ms,
                error=exc,
            )
            try:
                operator.publish_failure(exc, checked_at_ms=checked_at_ms)
            finally:
                history.append(
                    cycle_started_at_ms=cycle_started_at_ms,
                    checked_at_ms=checked_at_ms,
                    attempt=attempt,
                    outcome="failure",
                    generation_before=generation_before,
                    generation_after=generation_after,
                    retry_scheduled=retry_scheduled,
                    elapsed_ms=elapsed_ms,
                    error=exc,
                )
            if not retry_scheduled:
                return False
            sleeper(float(retry_delay_seconds))
            continue

        elapsed_ms = max(0, (monotonic() - started_ns) // 1_000_000)
        history.append(
            cycle_started_at_ms=cycle_started_at_ms,
            checked_at_ms=checked_at_ms,
            attempt=attempt,
            outcome="success",
            generation_before=generation_before,
            generation_after=generation_after,
            retry_scheduled=False,
            elapsed_ms=elapsed_ms,
            error=None,
        )
        return True
    return False


def run_resilient_forever(
    operator: CandidatePaperRuntimeOperator,
    history: CycleHistory,
    *,
    poll_seconds: int,
    retry_attempts: int,
    retry_delay_seconds: int,
    monotonic_ns: Callable[[], int] | None = None,
    sleep: Callable[[float], None] | None = None,
) -> None:
    if not 60 <= poll_seconds <= 900:
        raise CandidatePaperRuntimeSupervisorError("poll cadence must be within 60..900 seconds")
    monotonic = monotonic_ns or time.monotonic_ns
    sleeper = sleep or time.sleep
    while True:
        cycle_started_ns = monotonic()
        run_resilient_cycle(
            operator,
            history,
            retry_attempts=retry_attempts,
            retry_delay_seconds=retry_delay_seconds,
            monotonic_ns=monotonic,
            sleep=sleeper,
        )
        elapsed_seconds = max(0.0, (monotonic() - cycle_started_ns) / 1_000_000_000)
        sleeper(max(0.0, poll_seconds - elapsed_seconds))


def _build_parser() -> argparse.ArgumentParser:
    parser = operator_parser()
    parser.set_defaults(poll_seconds=DEFAULT_RESILIENT_POLL_SECONDS)
    parser.add_argument(
        "--cycle-retry-attempts",
        type=lambda value: _bounded_integer(
            value,
            minimum=1,
            maximum=MAX_CYCLE_RETRY_ATTEMPTS,
            field="cycle retry attempts",
        ),
        default=DEFAULT_CYCLE_RETRY_ATTEMPTS,
    )
    parser.add_argument(
        "--cycle-retry-delay-seconds",
        type=lambda value: _bounded_integer(
            value,
            minimum=1,
            maximum=MAX_CYCLE_RETRY_DELAY_SECONDS,
            field="cycle retry delay",
        ),
        default=DEFAULT_CYCLE_RETRY_DELAY_SECONDS,
    )
    parser.add_argument(
        "--cycle-history-limit",
        type=lambda value: _bounded_integer(
            value,
            minimum=MIN_CYCLE_HISTORY_LIMIT,
            maximum=MAX_CYCLE_HISTORY_LIMIT,
            field="cycle history limit",
        ),
        default=DEFAULT_CYCLE_HISTORY_LIMIT,
    )
    return parser


def _build_operator(args: argparse.Namespace) -> CandidatePaperRuntimeOperator:
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
        raise CandidatePaperRuntimeSupervisorError("Liquid20 root must be a regular directory")
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
    return CandidatePaperRuntimeOperator(
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


def main() -> int:
    args = _build_parser().parse_args()
    operator = _build_operator(args)
    history = CycleHistory(
        (args.health_root / "cycle-history.json").resolve(),
        limit=args.cycle_history_limit,
    )
    if args.once:
        return (
            0
            if run_resilient_cycle(
                operator,
                history,
                retry_attempts=args.cycle_retry_attempts,
                retry_delay_seconds=args.cycle_retry_delay_seconds,
            )
            else 1
        )
    run_resilient_forever(
        operator,
        history,
        poll_seconds=args.poll_seconds,
        retry_attempts=args.cycle_retry_attempts,
        retry_delay_seconds=args.cycle_retry_delay_seconds,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
