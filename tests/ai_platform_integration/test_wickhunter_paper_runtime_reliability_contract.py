from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
DOCKERFILE = ROOT / "deploy/synology/wickhunter-paper-runtime/Dockerfile"
COMPOSE = ROOT / "deploy/synology/wickhunter-paper-runtime/compose.yaml"
RUNNER_PREFLIGHT = ROOT / ".github/workflows/freqtrade-synology-runner-cutover-preflight.yml"


def test_wickhunter_runtime_healthcheck_has_project_import_path() -> None:
    dockerfile = DOCKERFILE.read_text(encoding="utf-8")
    compose = COMPOSE.read_text(encoding="utf-8")

    assert "PYTHONPATH=/app" in dockerfile
    assert "/app/deploy/synology/wickhunter-paper-runtime/paper_runtime_healthcheck.py" in compose


def test_wickhunter_runtime_default_cadence_is_one_minute() -> None:
    compose = COMPOSE.read_text(encoding="utf-8")

    assert "${POLL_SECONDS:-60}" in compose
    assert "${MAXIMUM_SOURCE_AGE_MS:-300000}" in compose


def test_consumed_wh09_terminal_collector_is_not_registered() -> None:
    workflow = RUNNER_PREFLIGHT.read_text(encoding="utf-8")

    assert "wh09-terminal-collect" not in workflow
    assert "wickhunter-wh09-collect-v12" not in workflow
    assert "pull_request:" not in workflow
    assert "statuses: write" in workflow
