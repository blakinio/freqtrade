from __future__ import annotations

import json
import os
import signal
import sys
import time
from pathlib import Path
from typing import Any

from ai_platform.wickhunter import production_market_evidence as core
from ai_platform.wickhunter.market_evidence_readiness import collector_health_payload
from ai_platform.wickhunter.production_market_evidence_service import (
    PACKAGE_DIR_NAME,
    MarketEvidencePublicationError,
    collect_due_sample,
    initialize_capture,
    verify_immutable_package,
)


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


def _active_pointer(root: Path) -> Path:
    return root / core.ACTIVE_POINTER_NAME


def _initialize_if_needed(
    *,
    durable_root: Path,
    request_path: Path,
    collector_commit: str,
) -> dict[str, object] | None:
    if not request_path.is_file() or request_path.is_symlink():
        return {
            "status": "blocked",
            "reason_code": "CAPTURE_REQUEST_UNAVAILABLE",
            "detail": "No immutable capture request is mounted.",
        }
    try:
        request = core.load_capture_request(request_path)
    except (core.ProductionMarketEvidenceError, OSError, ValueError, json.JSONDecodeError):
        return {
            "status": "blocked",
            "reason_code": "CAPTURE_REQUEST_UNAVAILABLE",
            "detail": "The immutable capture request is unreadable or invalid.",
        }
    if _active_pointer(durable_root).exists():
        return None
    run_root = durable_root / str(request["run_id"])
    if run_root.exists():
        return {
            "status": "published",
            **verify_immutable_package(run_root / PACKAGE_DIR_NAME),
        }
    return initialize_capture(
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
    return collect_due_sample(durable_root=durable_root)


def main() -> int:
    signal.signal(signal.SIGTERM, _signal_handler)
    signal.signal(signal.SIGINT, _signal_handler)
    try:
        durable_root = _required_path("MARKET_EVIDENCE_DURABLE_ROOT")
        request_path = _required_path("MARKET_EVIDENCE_REQUEST_PATH")
        collector_commit = os.environ.get("COLLECTOR_COMMIT", "").strip().lower()
        interval_seconds = _positive_integer("MARKET_EVIDENCE_LOOP_SECONDS", 60)
        if len(collector_commit) != 40 or any(
            character not in "0123456789abcdef" for character in collector_commit
        ):
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
                    collector_health_payload(
                        schema_version=1,
                        observed_at_ms=observed_at_ms,
                        result=result,
                        authority={
                            "execution_enabled": False,
                            "orders_submitted": 0,
                            "trading_credentials_present": False,
                            "model_execution_authorized": False,
                            "replay_authorized": False,
                            "performance_research_authorized": False,
                            "live_capital_authorized": False,
                        },
                    ),
                )
            except (
                core.ProductionMarketEvidenceError,
                MarketEvidencePublicationError,
                OSError,
            ) as exc:
                _atomic_health(
                    health_path,
                    collector_health_payload(
                        schema_version=1,
                        observed_at_ms=observed_at_ms,
                        result={
                            "status": "failed",
                            "reason_code": "COLLECTOR_FAIL_CLOSED",
                            "detail": f"{type(exc).__name__}: {exc}",
                        },
                        authority={
                            "execution_enabled": False,
                            "orders_submitted": 0,
                            "trading_credentials_present": False,
                            "model_execution_authorized": False,
                            "replay_authorized": False,
                            "performance_research_authorized": False,
                            "live_capital_authorized": False,
                        },
                    ),
                )
            for _ in range(interval_seconds):
                if _STOP:
                    break
                time.sleep(1)
        return 0
    except RuntimeError as exc:
        print(f"WickHunter market evidence daemon configuration failed: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
