from __future__ import annotations

import subprocess
from pathlib import Path


REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
DEPLOYMENT_ROOT = REPOSITORY_ROOT / "deploy" / "synology" / "liquid20"
WORKFLOW = REPOSITORY_ROOT / ".github" / "workflows" / "liquidations-live-synology.yml"


def test_live_entrypoint_and_deploy_script_have_valid_shell_syntax() -> None:
    for path in (DEPLOYMENT_ROOT / "live-entrypoint.sh", DEPLOYMENT_ROOT / "deploy-live.sh"):
        subprocess.run(
            ["bash" if path.name == "deploy-live.sh" else "sh", "-n", str(path)],
            check=True,
            capture_output=True,
            text=True,
        )


def test_compose_separates_restartable_live_service_from_evidence_profile() -> None:
    compose = (DEPLOYMENT_ROOT / "compose.yaml").read_text(encoding="utf-8")
    assert "liquid20-live:" in compose
    assert "restart: unless-stopped" in compose
    assert 'entrypoint: ["/usr/local/bin/liquid20-live-entrypoint"]' in compose
    assert "liquid20-evidence:" in compose
    assert 'profiles: ["evidence"]' in compose
    assert 'restart: "no"' in compose
    assert 'entrypoint: ["/usr/local/bin/liquid20-entrypoint"]' in compose
    assert "./data:/data:rw" in compose
    assert "read_only: true" in compose
    assert "no-new-privileges:true" in compose
    assert "ports:" not in compose
    assert "/var/run/docker.sock" not in compose


def test_live_entrypoint_refuses_credentials_and_stays_data_only() -> None:
    entrypoint = (DEPLOYMENT_ROOT / "live-entrypoint.sh").read_text(encoding="utf-8")
    assert "ai_platform.scripts.liquidation_live_stream" in entrypoint
    assert "LIQUID20_DATA_ROOT" in entrypoint
    assert "--maximum-symbols" in entrypoint
    for variable in (
        "BYBIT_API_KEY",
        "BYBIT_API_SECRET",
        "BINANCE_API_KEY",
        "BINANCE_API_SECRET",
        "OKX_API_KEY",
        "OKX_API_SECRET",
        "FREQTRADE__EXCHANGE__KEY",
        "FREQTRADE__EXCHANGE__SECRET",
    ):
        assert variable in entrypoint
    assert "freqtrade trade" not in entrypoint
    assert "order" not in entrypoint.lower()


def test_controlled_deployment_is_exact_sha_candidate_first_and_rollback_capable() -> None:
    script = (DEPLOYMENT_ROOT / "deploy-live.sh").read_text(encoding="utf-8")
    assert 'commit_sha="${GITHUB_SHA:?' in script
    assert 'image="${image_name}:sha-${commit_sha}"' in script
    assert "candidate_first" in script
    assert "production_first" in script
    assert "Restoring previous live collector image" in script
    assert "previous_commit" in script
    assert "COLLECTOR_COMMIT=${selected_commit}" in script
    assert "history_before" in script
    assert 'test "$history_before" = "$history_after"' in script
    assert '--restart "$restart_policy"' in script
    assert '--user "${puid}:${pgid}"' in script
    assert '--mount "type=bind,src=/var/run/docker.sock' not in script
    assert "chmod" not in script
    assert "chown" not in script
    assert "refs/heads/develop" in script


def test_synology_workflow_mutates_production_only_from_develop() -> None:
    workflow = WORKFLOW.read_text(encoding="utf-8")
    assert "push:" in workflow
    assert "- develop" in workflow
    assert "pull_request:" not in workflow
    assert "persist-credentials: false" in workflow
    assert "deploy/synology/liquid20/deploy-live.sh" in workflow
    assert "liquidations-live-synology-report.json" in workflow
    assert "workflow_dispatch:" in workflow
