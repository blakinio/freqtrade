from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest

from ai_platform.wickhunter.canonical import canonical_sha256


MODULE_PATH = (
    Path(__file__).resolve().parents[2]
    / "deploy"
    / "synology"
    / "wickhunter-paper-runtime"
    / "paper_runtime_healthcheck.py"
)
OPERATOR_COMMIT = "a" * 40
NOW_MS = 2_000_000_000_000


def _load_healthcheck_module():
    spec = importlib.util.spec_from_file_location(
        "wickhunter_paper_runtime_healthcheck", MODULE_PATH
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _health_payload(runtime_health: str) -> dict[str, object]:
    payload: dict[str, object] = {
        "schema_version": "wickhunter-paper-runtime-operator-health-v1",
        "status": "healthy",
        "operator_commit": OPERATOR_COMMIT,
        "protected_holdout_accessed": False,
        "automatic_promotion_enabled": False,
        "trading_credentials_present": False,
        "order_adapter_present": False,
        "execution_enabled": False,
        "orders_submitted": 0,
        "live_capital_authorized": False,
        "runtime_health": runtime_health,
        "model_drift": "healthy",
        "data_drift": "healthy",
        "circuit_breaker_reasons": [],
        "circuit_breaker_active": False,
        "liquid20_snapshot_id": "b" * 64,
        "checked_at_ms": NOW_MS,
        "last_success_at_ms": NOW_MS,
        "last_observed_at_ms": NOW_MS,
        "window_start_ms": NOW_MS - 60_000,
        "window_end_ms": NOW_MS + 60_000,
        "generation": 1,
        "binding_id": "c" * 64,
        "run_id": "d" * 64,
    }
    payload["health_sha256"] = canonical_sha256(payload)
    return payload


def _run_healthcheck(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, runtime_health: str) -> int:
    module = _load_healthcheck_module()
    health_path = tmp_path / "health.json"
    health_path.write_text(json.dumps(_health_payload(runtime_health)), encoding="utf-8")
    monkeypatch.setenv("HEALTH_PATH", str(health_path))
    monkeypatch.setenv("OPERATOR_COMMIT", OPERATOR_COMMIT)
    monkeypatch.setattr(module.time, "time_ns", lambda: NOW_MS * 1_000_000)
    return module.main()


def test_healthcheck_accepts_genuinely_healthy_runtime(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    assert _run_healthcheck(tmp_path, monkeypatch, "healthy") == 0


@pytest.mark.parametrize("runtime_health", ["degraded", "fail_closed"])
def test_healthcheck_rejects_nonhealthy_runtime(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    runtime_health: str,
) -> None:
    assert _run_healthcheck(tmp_path, monkeypatch, runtime_health) == 1
    assert "runtime health is not healthy" in capsys.readouterr().err
