from __future__ import annotations

import json
import os
import signal
import sys
import time
from pathlib import Path
from typing import Any

from ai_platform.market_data.binance_spot_instrument_acceptance_incremental import (
    ACTIVE_POINTER_NAME,
    EXPECTED_REQUEST,
    collect_due_incremental_sample,
)


_STOP = False
TERMINAL_REPORT_NAME = "binance-spot-instrument-acceptance-report.json"
HEALTH_NAME = "binance-v3-persistent-sampler-health.json"


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


def _atomic_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.tmp")
    content = json.dumps(payload, indent=2, sort_keys=True).encode("utf-8") + b"\n"
    with temporary.open("wb") as handle:
        handle.write(content)
        handle.flush()
        os.fsync(handle.fileno())
    temporary.replace(path)


def _terminal_result(durable_root: Path) -> dict[str, object] | None:
    run_id = str(EXPECTED_REQUEST["run_id"])
    report_path = durable_root / run_id / TERMINAL_REPORT_NAME
    if not report_path.is_file() or report_path.is_symlink():
        return None
    report = json.loads(report_path.read_text(encoding="utf-8"))
    if report.get("source_acceptance") not in {True, False}:
        raise ValueError("terminal report source_acceptance is invalid")
    if report.get("production_source_enabled") is not False:
        raise ValueError("terminal report production_source_enabled must remain false")
    if report.get("orders_submitted") != 0:
        raise ValueError("terminal report orders_submitted must remain zero")
    outcome = report.get("outcome")
    if outcome not in {"accepted", "rejected", "inconclusive_incomplete_window"}:
        raise ValueError("terminal report outcome is invalid")
    return {
        "status": "finalized",
        "run_id": run_id,
        "run_root": str(report_path.parent),
        "outcome": outcome,
        "source_acceptance": report.get("source_acceptance"),
        "production_source_enabled": False,
        "orders_submitted": 0,
    }


def run_once(*, durable_root: Path, policy_path: Path) -> dict[str, object]:
    pointer = durable_root / ACTIVE_POINTER_NAME
    if pointer.exists():
        return collect_due_incremental_sample(
            policy_path=policy_path,
            durable_root=durable_root,
        )
    terminal = _terminal_result(durable_root)
    if terminal is not None:
        return terminal
    raise RuntimeError("active pointer and terminal report are both absent")


def _healthy(result: dict[str, object]) -> bool:
    if result.get("status") not in {"sampled", "not_due", "finalized"}:
        return False
    if result.get("production_source_enabled", False) is not False:
        return False
    return result.get("orders_submitted", 0) == 0


def main() -> int:
    signal.signal(signal.SIGTERM, _signal_handler)
    signal.signal(signal.SIGINT, _signal_handler)
    try:
        durable_root = _required_path("BINANCE_ACCEPTANCE_DURABLE_ROOT")
        policy_path = _required_path("BINANCE_ACCEPTANCE_POLICY_PATH")
        loop_seconds = _positive_integer("BINANCE_ACCEPTANCE_LOOP_SECONDS", 15)
        health_path = durable_root / HEALTH_NAME
        while not _STOP:
            observed_at_ns = time.time_ns()
            try:
                result = run_once(
                    durable_root=durable_root,
                    policy_path=policy_path,
                )
                health = {
                    "schema_version": 1,
                    "observed_at_ns": observed_at_ns,
                    "healthy": _healthy(result),
                    "result": result,
                    "execution_enabled": False,
                    "trading_credentials_present": False,
                    "production_source_enabled": False,
                    "orders_submitted": 0,
                    "replay_authorized": False,
                    "model_training_authorized": False,
                    "strategy_research_authorized": False,
                    "live_capital_authorized": False,
                }
            except (OSError, RuntimeError, TypeError, ValueError) as exc:
                health = {
                    "schema_version": 1,
                    "observed_at_ns": observed_at_ns,
                    "healthy": False,
                    "result": {
                        "status": "failed",
                        "reason_code": "BINANCE_ACCEPTANCE_PERSISTENT_SAMPLER_FAILED",
                        "detail": f"{type(exc).__name__}: {exc}",
                    },
                    "execution_enabled": False,
                    "trading_credentials_present": False,
                    "production_source_enabled": False,
                    "orders_submitted": 0,
                    "replay_authorized": False,
                    "model_training_authorized": False,
                    "strategy_research_authorized": False,
                    "live_capital_authorized": False,
                }
            _atomic_json(health_path, health)
            for _ in range(loop_seconds):
                if _STOP:
                    break
                time.sleep(1)
        return 0
    except RuntimeError as exc:
        print(f"Binance v3 persistent sampler configuration failed: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
