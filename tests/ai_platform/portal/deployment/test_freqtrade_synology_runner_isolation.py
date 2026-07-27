from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[4]
RUNNER_ROOT = ROOT / "deploy" / "synology" / "freqtrade-runner"
COMPOSE = RUNNER_ROOT / "compose.yml"
DOCKERFILE = RUNNER_ROOT / "Dockerfile"
ENTRYPOINT = RUNNER_ROOT / "entrypoint.sh"
ENV_EXAMPLE = RUNNER_ROOT / ".env.example"
BUILD_WORKFLOW = ROOT / ".github" / "workflows" / "freqtrade-synology-runner-image.yml"
PI06_WORKFLOW = ROOT / ".github" / "workflows" / "portal-authentik-synology-target-preflight.yml"
PI06_PREFLIGHT = ROOT / "deploy" / "synology" / "portal-authentik" / "target_preflight.py"
OKX_WORKFLOW = (
    ROOT / ".github/workflows/ai-platform-okx-liquidation-shadow-acceptance-staging-preflight.yml"
)


def test_runner_compose_is_owned_only_by_freqtrade() -> None:
    text = COMPOSE.read_text(encoding="utf-8")
    assert "name: freqtrade-deploy-runner" in text
    assert "ghcr.io/blakinio/freqtrade-deploy-runner:develop" in text
    assert "https://github.com/blakinio/freqtrade" in text
    assert "freqtrade-synology-staging" in text
    assert "freqtrade-staging" in text
    assert "FREQTRADE_STATE_HOST_PATH" in text
    assert "/volume1/docker/freqtrade/state" in text
    assert "/var/lib/freqtrade-staging-state" in text
    assert "oteryn" not in text.casefold()


def test_runner_image_contains_preflight_tools_and_freqtrade_entrypoint() -> None:
    dockerfile = DOCKERFILE.read_text(encoding="utf-8")
    entrypoint = ENTRYPOINT.read_text(encoding="utf-8")
    assert "age ca-certificates coreutils curl openssl python3" in dockerfile
    assert "/usr/local/bin/freqtrade-runner-entrypoint" in dockerfile
    assert "https://github.com/blakinio/freqtrade" in entrypoint
    assert "freqtrade-synology-staging" in entrypoint
    assert "freqtrade-staging" in entrypoint
    assert "oteryn" not in (dockerfile + entrypoint).casefold()


def test_runner_environment_example_is_freqtrade_specific() -> None:
    text = ENV_EXAMPLE.read_text(encoding="utf-8")
    assert "RUNNER_IMAGE=ghcr.io/blakinio/freqtrade-deploy-runner:develop" in text
    assert "RUNNER_NAME=freqtrade-synology-staging" in text
    assert "FREQTRADE_STATE_HOST_PATH=/volume1/docker/freqtrade/state" in text
    assert "oteryn" not in text.casefold()


def test_runner_build_workflow_publishes_only_freqtrade_image() -> None:
    text = BUILD_WORKFLOW.read_text(encoding="utf-8")
    assert "ghcr.io/blakinio/freqtrade-deploy-runner" in text
    assert "deploy/synology/freqtrade-runner/Dockerfile" in text
    assert "age --version" in text
    assert "openssl version" in text
    assert "packages: write" in text
    assert "oteryn-deploy-runner" not in text.casefold()


def test_active_staging_workflows_use_freqtrade_owned_state_contract() -> None:
    pi06 = PI06_WORKFLOW.read_text(encoding="utf-8") + PI06_PREFLIGHT.read_text(encoding="utf-8")
    okx = OKX_WORKFLOW.read_text(encoding="utf-8")
    for text in (pi06, okx):
        assert "FREQTRADE_STAGING_STATE_DIR" in text
        assert "/var/lib/freqtrade-staging-state" in text
        assert "OTERYN_STAGING_STATE_DIR" not in text
        assert "/var/lib/oteryn-staging-state" not in text
