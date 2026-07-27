from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[4]
WORKFLOW = ROOT / ".github" / "workflows" / "diag-freqtrade-synology-cutover-run.yml"


def test_diagnostic_is_pull_request_only_and_hosted() -> None:
    text = WORKFLOW.read_text(encoding="utf-8")

    assert "pull_request:" in text
    assert "runs-on: ubuntu-latest" in text
    assert "workflow_dispatch:" not in text
    assert "runs-on: [freqtrade-staging]" not in text


def test_diagnostic_targets_exact_failed_run_and_comment() -> None:
    text = WORKFLOW.read_text(encoding="utf-8")

    assert "3127b1826d6e0827be6e1636ee5745d75583d9a3" in text
    assert "Retry Freqtrade Synology Runner Cutover" in text
    assert 'TARGET_PR: "509"' in text
    assert "actions: read" in text
    assert "issues: write" in text


def test_diagnostic_does_not_mutate_synology() -> None:
    text = WORKFLOW.read_text(encoding="utf-8").casefold()

    assert "docker stop" not in text
    assert "docker rm" not in text
    assert "docker compose" not in text
    assert "/var/run/docker.sock" not in text
    assert "oteryn" not in text
