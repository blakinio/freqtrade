from __future__ import annotations

import json
import os
import subprocess
import sys
import time
from pathlib import Path

import pytest

from ai_platform.wickhunter import production_market_evidence_daemon as daemon_v1
from ai_platform.wickhunter import production_market_evidence_daemon_v2 as daemon_v2
from ai_platform.wickhunter.market_evidence_readiness import (
    collector_health_payload,
    health_payload_is_ready,
    result_is_ready,
)


REPO_ROOT = Path(__file__).resolve().parents[2]
V1_HEALTHCHECK = REPO_ROOT / "deploy/synology/wickhunter-market-evidence/healthcheck.py"
V2_HEALTHCHECK = REPO_ROOT / "deploy/synology/wickhunter-market-evidence-v2/healthcheck_v2.py"
V1_WORKFLOW = REPO_ROOT / ".github/workflows/ai-platform-wickhunter-production-market-evidence.yml"
V2_WORKFLOW = (
    REPO_ROOT / ".github/workflows/ai-platform-wickhunter-production-market-evidence-v2.yml"
)
AUTHORITY = {
    "execution_enabled": False,
    "orders_submitted": 0,
    "trading_credentials_present": False,
    "model_execution_authorized": False,
    "replay_authorized": False,
    "performance_research_authorized": False,
    "live_capital_authorized": False,
}


@pytest.mark.parametrize(
    ("daemon", "root_name", "request_name", "loop_name"),
    [
        (
            daemon_v1,
            "MARKET_EVIDENCE_DURABLE_ROOT",
            "MARKET_EVIDENCE_REQUEST_PATH",
            "MARKET_EVIDENCE_LOOP_SECONDS",
        ),
        (
            daemon_v2,
            "MARKET_EVIDENCE_V2_DURABLE_ROOT",
            "MARKET_EVIDENCE_V2_REQUEST_PATH",
            "MARKET_EVIDENCE_V2_LOOP_SECONDS",
        ),
    ],
)
def test_missing_request_loop_is_live_but_not_ready(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    daemon: object,
    root_name: str,
    request_name: str,
    loop_name: str,
) -> None:
    captured: list[dict[str, object]] = []
    monkeypatch.setenv(root_name, str(tmp_path / "state"))
    monkeypatch.setenv(request_name, str(tmp_path / "missing.json"))
    monkeypatch.setenv(loop_name, "1")
    monkeypatch.setenv("COLLECTOR_COMMIT", "a" * 40)
    monkeypatch.setattr(daemon.signal, "signal", lambda *_args: None)
    monkeypatch.setattr(daemon, "_atomic_health", lambda _path, payload: captured.append(payload))
    monkeypatch.setattr(daemon.time, "sleep", lambda _seconds: setattr(daemon, "_STOP", True))
    monkeypatch.setattr(daemon, "_STOP", False)

    assert daemon.main() == 0
    assert len(captured) == 1
    payload = captured[0]
    assert payload["live"] is True
    assert payload["ready"] is False
    assert payload["healthy"] is False
    assert payload["result"] == {
        "status": "blocked",
        "reason_code": "CAPTURE_REQUEST_UNAVAILABLE",
        "detail": payload["result"]["detail"],
    }
    assert payload["execution_enabled"] is False
    assert payload["orders_submitted"] == 0
    assert payload["live_capital_authorized"] is False


@pytest.mark.parametrize(
    ("script", "root_name", "schema_version"),
    [
        (V1_HEALTHCHECK, "MARKET_EVIDENCE_DURABLE_ROOT", 1),
        (V2_HEALTHCHECK, "MARKET_EVIDENCE_V2_DURABLE_ROOT", 2),
    ],
)
def test_deployment_healthcheck_rejects_blocked_unavailable(
    tmp_path: Path,
    script: Path,
    root_name: str,
    schema_version: int,
) -> None:
    root = tmp_path / "state"
    root.mkdir()
    (root / "collector-health.json").write_text(
        json.dumps(
            {
                "schema_version": schema_version,
                "observed_at_ms": time.time_ns() // 1_000_000,
                "live": True,
                "ready": False,
                "healthy": True,
                "result": {
                    "status": "blocked",
                    "reason_code": "CAPTURE_REQUEST_UNAVAILABLE",
                },
                "execution_enabled": False,
                "orders_submitted": 0,
                "trading_credentials_present": False,
                "model_execution_authorized": False,
                "replay_authorized": False,
                "performance_research_authorized": False,
                "live_capital_authorized": False,
            }
        ),
        encoding="utf-8",
    )
    environment = {**os.environ, root_name: str(root), "PYTHONPATH": str(REPO_ROOT)}
    assert (
        subprocess.run([sys.executable, str(script)], env=environment, check=False).returncode == 1
    )


@pytest.mark.parametrize("daemon", [daemon_v1, daemon_v2])
def test_request_symlink_and_invalid_json_are_blocked(
    tmp_path: Path,
    daemon: object,
) -> None:
    durable_root = tmp_path / "state"
    target = tmp_path / "target.json"
    target.write_text("{}", encoding="utf-8")
    link = tmp_path / "request-link.json"
    try:
        link.symlink_to(target)
    except OSError as exc:
        pytest.skip(f"symlinks unavailable: {exc}")

    linked = daemon.run_once(
        durable_root=durable_root,
        request_path=link,
        collector_commit="a" * 40,
    )
    assert linked["status"] == "blocked"
    assert linked["reason_code"] == "CAPTURE_REQUEST_UNAVAILABLE"

    invalid = tmp_path / "invalid.json"
    invalid.write_text("{", encoding="utf-8")
    rejected = daemon.run_once(
        durable_root=durable_root,
        request_path=invalid,
        collector_commit="a" * 40,
    )
    assert rejected["status"] == "blocked"
    assert rejected["reason_code"] == "CAPTURE_REQUEST_UNAVAILABLE"


@pytest.mark.parametrize("daemon", [daemon_v1, daemon_v2])
def test_unreadable_request_is_blocked_even_with_an_active_pointer(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    daemon: object,
) -> None:
    durable_root = tmp_path / "state"
    durable_root.mkdir()
    pointer_name = daemon.core.ACTIVE_POINTER_NAME
    (durable_root / pointer_name).write_text("{}", encoding="utf-8")
    request = tmp_path / "request.json"
    request.write_text("{}", encoding="utf-8")
    monkeypatch.setattr(
        daemon.core,
        "load_capture_request",
        lambda _path: (_ for _ in ()).throw(PermissionError("unreadable")),
    )

    result = daemon.run_once(
        durable_root=durable_root,
        request_path=request,
        collector_commit="a" * 40,
    )

    assert result["status"] == "blocked"
    assert result["reason_code"] == "CAPTURE_REQUEST_UNAVAILABLE"


@pytest.mark.parametrize("daemon", [daemon_v1, daemon_v2])
def test_valid_request_and_successful_initialization_are_ready(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    daemon: object,
) -> None:
    request = tmp_path / "request.json"
    request.write_text("{}", encoding="utf-8")
    request_value: object = {"run_id": "run-1"} if daemon is daemon_v1 else object()
    monkeypatch.setattr(daemon.core, "load_capture_request", lambda _path: request_value)

    def initializer(**_kwargs: object) -> dict[str, object]:
        return {"status": "initialized", "run_id": "run-1"}

    if daemon is daemon_v1:
        monkeypatch.setattr(daemon, "initialize_capture", initializer)
    else:
        monkeypatch.setattr(daemon.core, "initialize_capture", initializer)

    result = daemon.run_once(
        durable_root=tmp_path / "state",
        request_path=request,
        collector_commit="a" * 40,
    )
    payload = collector_health_payload(
        schema_version=1 if daemon is daemon_v1 else 2,
        observed_at_ms=time.time_ns() // 1_000_000,
        result=result,
        authority=AUTHORITY,
    )

    assert result["status"] == "initialized"
    assert payload["live"] is True
    assert payload["ready"] is True
    assert payload["healthy"] is True


def test_v1_completed_valid_capture_remains_ready(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    durable_root = tmp_path / "state"
    run_root = durable_root / "run-1"
    run_root.mkdir(parents=True)
    request = tmp_path / "request.json"
    request.write_text("{}", encoding="utf-8")
    monkeypatch.setattr(daemon_v1.core, "load_capture_request", lambda _path: {"run_id": "run-1"})
    monkeypatch.setattr(
        daemon_v1,
        "verify_immutable_package",
        lambda _path: {"outcome": "accepted", "run_id": "run-1"},
    )

    result = daemon_v1.run_once(
        durable_root=durable_root,
        request_path=request,
        collector_commit="a" * 40,
    )

    assert result == {"status": "published", "outcome": "accepted", "run_id": "run-1"}
    assert result_is_ready(result)


def test_v2_completed_valid_capture_is_reverified_before_readiness(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    durable_root = tmp_path / "state"
    durable_root.mkdir()
    (durable_root / daemon_v2.core.ACTIVE_POINTER_NAME).write_text("{}", encoding="utf-8")
    request = tmp_path / "request.json"
    request.write_text("{}", encoding="utf-8")
    monkeypatch.setattr(daemon_v2.core, "load_capture_request", lambda _path: object())
    monkeypatch.setattr(
        daemon_v2.core,
        "collect_due_sample",
        lambda **_kwargs: {"status": "supplement_completed", "run_id": "run-2"},
    )
    monkeypatch.setattr(
        daemon_v2.core,
        "verify_supplement",
        lambda _path: {
            "status": "supplement_completed",
            "outcome": "accepted",
            "run_id": "run-2",
        },
    )

    result = daemon_v2.run_once(
        durable_root=durable_root,
        request_path=request,
        collector_commit="a" * 40,
    )

    assert result["outcome"] == "accepted"
    assert result_is_ready(result)


@pytest.mark.parametrize(
    ("result", "expected"),
    [
        ({"status": "blocked", "reason_code": "CAPTURE_REQUEST_UNAVAILABLE"}, False),
        ({"status": "failed"}, False),
        ({"status": "rejected"}, False),
        ({"status": "sampled", "sample_status": "fail"}, False),
        ({"status": "initialized"}, True),
        ({"status": "not_due"}, True),
        ({"status": "waiting"}, True),
        ({"status": "sampled", "sample_status": "pass"}, True),
        ({"status": "sampled"}, True),
        ({"status": "published", "outcome": "accepted"}, True),
        ({"status": "supplement_completed", "outcome": "accepted"}, True),
    ],
)
def test_ready_lifecycle_states_use_an_explicit_allowlist(
    result: dict[str, object],
    expected: bool,
) -> None:
    assert result_is_ready(result) is expected


@pytest.mark.parametrize(
    ("script", "root_name", "schema_version"),
    [
        (V1_HEALTHCHECK, "MARKET_EVIDENCE_DURABLE_ROOT", 1),
        (V2_HEALTHCHECK, "MARKET_EVIDENCE_V2_DURABLE_ROOT", 2),
    ],
)
def test_healthcheck_accepts_only_fresh_well_formed_matching_ready_payload(
    tmp_path: Path,
    script: Path,
    root_name: str,
    schema_version: int,
) -> None:
    root = tmp_path / "state"
    root.mkdir()
    path = root / "collector-health.json"
    environment = {**os.environ, root_name: str(root), "PYTHONPATH": str(REPO_ROOT)}
    current_ms = time.time_ns() // 1_000_000
    ready = collector_health_payload(
        schema_version=schema_version,
        observed_at_ms=current_ms,
        result={"status": "initialized"},
        authority=AUTHORITY,
    )

    path.write_text(json.dumps(ready), encoding="utf-8")
    assert (
        subprocess.run([sys.executable, str(script)], env=environment, check=False).returncode == 0
    )

    stale = {**ready, "observed_at_ms": current_ms - 601_000}
    path.write_text(json.dumps(stale), encoding="utf-8")
    assert (
        subprocess.run([sys.executable, str(script)], env=environment, check=False).returncode == 1
    )

    mismatch = {**ready, "schema_version": 2 if schema_version == 1 else 1}
    path.write_text(json.dumps(mismatch), encoding="utf-8")
    assert (
        subprocess.run([sys.executable, str(script)], env=environment, check=False).returncode == 1
    )

    path.write_text("{", encoding="utf-8")
    assert (
        subprocess.run([sys.executable, str(script)], env=environment, check=False).returncode == 1
    )


def test_readiness_requires_zero_authority_and_zero_orders() -> None:
    payload = collector_health_payload(
        schema_version=1,
        observed_at_ms=1_000_000,
        result={"status": "initialized"},
        authority=AUTHORITY,
    )
    assert health_payload_is_ready(
        payload,
        expected_schema_version=1,
        maximum_age_seconds=60,
        now_ms=1_000_001,
    )
    assert not health_payload_is_ready(
        {**payload, "orders_submitted": 1},
        expected_schema_version=1,
        maximum_age_seconds=60,
        now_ms=1_000_001,
    )
    assert not health_payload_is_ready(
        {**payload, "live_capital_authorized": True},
        expected_schema_version=1,
        maximum_age_seconds=60,
        now_ms=1_000_001,
    )


@pytest.mark.parametrize("daemon", [daemon_v1, daemon_v2])
def test_daemon_health_files_remain_atomically_written(
    tmp_path: Path,
    daemon: object,
) -> None:
    path = tmp_path / "collector-health.json"
    payload = {"live": True, "ready": False}

    daemon._atomic_health(path, payload)

    assert json.loads(path.read_text(encoding="utf-8")) == payload
    assert not (tmp_path / ".collector-health.json.tmp").exists()


def test_workflow_probes_use_the_shared_explicit_readiness_gate() -> None:
    for workflow in (V1_WORKFLOW, V2_WORKFLOW):
        source = workflow.read_text(encoding="utf-8")
        assert "ai_platform.wickhunter.market_evidence_readiness" in source
        assert 'result.get("status") in {"failed", "rejected"}' not in source
