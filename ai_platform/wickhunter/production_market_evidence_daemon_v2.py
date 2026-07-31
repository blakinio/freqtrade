from __future__ import annotations

import json
import os
import signal
import sys
import time
from pathlib import Path
from typing import Any

from ai_platform.wickhunter import production_market_evidence_v2 as core


_STOP = False


def _signal_handler(signum: int, frame: object) -> None:
    del signum, frame
    global _STOP
    _STOP = True


def _positive_integer(name: str, default: int) -> int:
    raw = os.environ.get(name, str(default)).strip()
    try:
        value = int(raw)
    except ValueError as exc:
        raise RuntimeError(f"{name} must be an integer") from exc
    if value < 1:
        raise RuntimeError(f"{name} must be positive")
    return value


def _required_path(name: str) -> Path:
    raw = os.environ.get(name, "").strip()
    if not raw:
        raise RuntimeError(f"{name} is required")
    path = Path(raw)
    if not path.is_absolute():
        raise RuntimeError(f"{name} must be absolute")
    return path


def _atomic_health(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.tmp")
    content = json.dumps(payload, indent=2, sort_keys=True).encode("utf-8") + b"\n"
    with temporary.open("wb") as handle:
        handle.write(content)
        handle.flush()
        os.fsync(handle.fileno())
    temporary.replace(path)


def _initialize_if_needed(
    *,
    durable_root: Path,
    request_path: Path,
    collector_commit: str,
) -> dict[str, object] | None:
    if (durable_root / core.ACTIVE_POINTER_NAME).exists():
        return None
    if not request_path.is_file() or request_path.is_symlink():
        return {
            "status": "blocked",
            "reason_code": "CAPTURE_REQUEST_UNAVAILABLE",
            "detail": "No immutable v2 capture request is mounted.",
        }
    return core.initialize_capture(
        request_path=request_path,
        durable_root=durable_root,
        collector_commit=collector_commit,
    )


def run_once(
    *,
    durable_root: Path,
    request_path: Path,
    collector_commit: str,
) -> dict[str, object]:
    initialized = _initialize_if_needed(
        durable_root=durable_root,
        request_path=request_path,
        collector_commit=collector_commit,
    )
    if initialized is not None:
        return initialized
    return core.collect_due_sample(durable_root=durable_root)


def main() -> int:
    signal.signal(signal.SIGTERM, _signal_handler)
    signal.signal(signal.SIGINT, _signal_handler)
    try:
        durable_root = _required_path("MARKET_EVIDENCE_V2_DURABLE_ROOT")
        request_path = _required_path("MARKET_EVIDENCE_V2_REQUEST_PATH")
        collector_commit = os.environ.get("COLLECTOR_COMMIT", "").strip().lower()
        interval_seconds = _positive_integer("MARKET_EVIDENCE_V2_LOOP_SECONDS", 60)
        valid_commit = len(collector_commit) == 40 and all(
            character in "0123456789abcdef" for character in collector_commit
        )
        if not valid_commit:
            raise RuntimeError("COLLECTOR_COMMIT must be a lowercase 40-character Git SHA")
        health_path = durable_root / "collector-health.json"
        while not _STOP:
            observed_at_ms = time.time_ns() // 1_000_000
            try:
                result = run_once(
                    durable_root=durable_root,
                    request_path=request_path,
                    collector_commit=collector_commit,
                )
                _atomic_health(
                    health_path,
                    {
                        "schema_version": 2,
                        "observed_at_ms": observed_at_ms,
                        "healthy": result.get("status") not in {"rejected", "failed"},
                        "result": result,
                        **core.AUTHORITY,
                    },
                )
            except (core.ProductionMarketEvidenceV2Error, OSError) as exc:
                _atomic_health(
                    health_path,
                    {
                        "schema_version": 2,
                        "observed_at_ms": observed_at_ms,
                        "healthy": False,
                        "result": {
                            "status": "failed",
                            "reason_code": "COLLECTOR_FAIL_CLOSED",
                            "detail": f"{type(exc).__name__}: {exc}",
                        },
                        **core.AUTHORITY,
                    },
                )
            for _ in range(interval_seconds):
                if _STOP:
                    break
                time.sleep(1)
        return 0
    except RuntimeError as exc:
        print(
            f"WickHunter market evidence v2 daemon configuration failed: {exc}",
            file=sys.stderr,
        )
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
