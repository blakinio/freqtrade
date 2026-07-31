from __future__ import annotations

import json
from pathlib import Path

import pytest

from ai_platform.market_data import binance_spot_instrument_acceptance_daemon as daemon


REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
DEPLOY_ROOT = REPOSITORY_ROOT / "deploy/synology/binance-spot-instrument-acceptance"
DEPLOY_WORKFLOW = (
    REPOSITORY_ROOT
    / ".github/workflows/ai-platform-binance-spot-instrument-persistent-sampler-deploy.yml"
)
RUN_ID = "binance-spot-instrument-shadow-acceptance-20260729-v3-r1"


def test_daemon_advances_only_an_existing_active_run(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    durable_root = tmp_path / "durable"
    durable_root.mkdir()
    (durable_root / daemon.ACTIVE_POINTER_NAME).write_text("{}\n", encoding="utf-8")
    policy_path = tmp_path / "policy.json"
    policy_path.write_text("{}\n", encoding="utf-8")
    observed: dict[str, Path] = {}

    def fake_collect(*, policy_path: Path, durable_root: Path) -> dict[str, object]:
        observed["policy"] = policy_path
        observed["root"] = durable_root
        return {
            "status": "sampled",
            "run_id": RUN_ID,
            "next_sample_index": 25,
        }

    monkeypatch.setattr(daemon, "collect_due_incremental_sample", fake_collect)

    result = daemon.run_once(
        durable_root=durable_root,
        policy_path=policy_path,
    )

    assert result["status"] == "sampled"
    assert observed == {"policy": policy_path, "root": durable_root}


def test_daemon_reports_existing_terminal_result_without_new_run(tmp_path: Path) -> None:
    durable_root = tmp_path / "durable"
    run_root = durable_root / RUN_ID
    run_root.mkdir(parents=True)
    (run_root / daemon.TERMINAL_REPORT_NAME).write_text(
        json.dumps(
            {
                "outcome": "accepted",
                "source_acceptance": True,
                "production_source_enabled": False,
                "orders_submitted": 0,
            }
        )
        + "\n",
        encoding="utf-8",
    )

    result = daemon.run_once(
        durable_root=durable_root,
        policy_path=tmp_path / "unused-policy.json",
    )

    assert result == {
        "status": "finalized",
        "run_id": RUN_ID,
        "run_root": str(run_root),
        "outcome": "accepted",
        "source_acceptance": True,
        "production_source_enabled": False,
        "orders_submitted": 0,
    }


def test_daemon_fails_closed_without_active_or_terminal_state(tmp_path: Path) -> None:
    with pytest.raises(RuntimeError, match="active pointer and terminal report"):
        daemon.run_once(
            durable_root=tmp_path,
            policy_path=tmp_path / "policy.json",
        )


def test_persistent_sampler_deployment_is_hardened_and_request_gated() -> None:
    compose = (DEPLOY_ROOT / "compose.yaml").read_text(encoding="utf-8")
    dockerfile = (DEPLOY_ROOT / "Dockerfile").read_text(encoding="utf-8")
    healthcheck = (DEPLOY_ROOT / "binance_acceptance_healthcheck.py").read_text(encoding="utf-8")
    workflow = DEPLOY_WORKFLOW.read_text(encoding="utf-8")

    assert "container_name: binance-v3-acceptance-sampler" in compose
    assert "restart: always" in compose
    assert 'user: "${PUID:-1026}:${PGID:-100}"' in compose
    assert "read_only: true" in compose
    assert "cap_drop:" in compose and "- ALL" in compose
    assert "no-new-privileges:true" in compose
    assert "ports:" not in compose
    assert "BINANCE_ACCEPTANCE_LOOP_SECONDS" in compose
    assert "jsonschema==4.26.0" in dockerfile
    assert "binance_spot_instrument_acceptance_daemon" in dockerfile
    assert "orders_submitted" in healthcheck
    assert "production source must remain disabled" in healthcheck

    request = (
        "deploy/synology/binance-spot-instrument-acceptance/run-requests/"
        "activate-existing-v3-run-20260731-v1.json"
    )
    assert f'- "{request}"' in workflow
    assert f"expected=$'A\\t{request}'" in workflow
    assert "target_run_id" in workflow
    assert "initialize_new_run" in workflow
    assert '"initialize_new_run": False' in workflow
    assert "reset_or_delete_state" in workflow
    assert "collect_due_incremental_sample" not in workflow
    assert " init " not in workflow
    assert 'docker compose -f "$COMPOSE_FILE" up -d --build' in workflow
    assert "freqtrade-synology-staging-runner" in workflow
    assert "Hand existing state to hardened sampler identity" in workflow
    assert "Verify health and real sample advancement" in workflow
    assert "pull_request_target" not in workflow
    assert "workflow_dispatch" not in workflow
