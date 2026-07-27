from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[4]
WORKFLOW = ROOT / ".github/workflows/repair-freqtrade-synology-runner-orphan.yml"


def test_runner_name_repair_is_trusted_develop_only() -> None:
    text = WORKFLOW.read_text(encoding="utf-8")

    assert "workflow_dispatch:" in text
    assert "      - develop" in text
    assert "if: github.ref == 'refs/heads/develop'" in text
    assert "runs-on: [freqtrade-staging]" in text
    assert "permissions:\n  contents: read" in text


def test_runner_name_repair_is_exact_and_fail_closed() -> None:
    text = WORKFLOW.read_text(encoding="utf-8")

    assert 'project="freqtrade-deploy-runner"' in text
    assert 'service="runner"' in text
    assert 'canonical="freqtrade-synology-staging-runner"' in text
    assert '^[[0-9a-f]{12}_${canonical}$' not in text
    assert '^[0-9a-f]{12}_${canonical}$' in text
    assert 'com.docker.compose.project' in text
    assert 'com.docker.compose.service' in text
    assert "More than one prefixed runner candidate exists" in text
    assert (
        "Canonical runner container already exists; refusing to overwrite it." in text
    )
    assert 'docker rename "$candidate_id" "$canonical"' in text


def test_runner_name_repair_does_not_restart_or_remove_runtime() -> None:
    text = WORKFLOW.read_text(encoding="utf-8").casefold()

    assert "docker stop" not in text
    assert "docker restart" not in text
    assert "docker rm" not in text
    assert "docker compose down" not in text
    assert "docker volume" not in text
    assert "oteryn" not in text
