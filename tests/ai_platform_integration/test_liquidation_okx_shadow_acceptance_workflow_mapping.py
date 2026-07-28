from __future__ import annotations

from pathlib import Path


WORKFLOW_PATH = Path(".github/workflows/ai-platform-okx-liquidation-shadow-acceptance.yml")
DOCUMENTATION_PATH = Path("docs/ai_platform/LIQUIDATION_OKX_SHADOW_ACCEPTANCE_EXECUTION.md")


def test_okx_acceptance_uses_verified_freqtrade_staging_mapping() -> None:
    workflow = WORKFLOW_PATH.read_text(encoding="utf-8")

    assert "runs-on: [freqtrade-staging]" in workflow
    assert "environment: synology-staging" in workflow
    assert "ACCEPTANCE_HOST_ID: freqtrade-synology-staging" in workflow
    assert "DURABLE_ROOT: /var/lib/freqtrade-staging-state/okx-liquidation-acceptance" in workflow
    assert (
        "DURABLE_URI: file:///var/lib/freqtrade-staging-state/okx-liquidation-acceptance"
        in workflow
    )
    assert "RUNNER_NAME_VALUE: ${{ runner.name }}" in workflow
    assert 'test "$RUNNER_NAME_VALUE" = "$ACCEPTANCE_HOST_ID"' in workflow
    assert 'test "$RUNNER_OS_VALUE" = "Linux"' in workflow


def test_okx_acceptance_rejects_legacy_mapping_and_mutable_variables() -> None:
    workflow = WORKFLOW_PATH.read_text(encoding="utf-8")

    assert "okx-liquidation-staging" not in workflow
    assert "vars.OKX_ACCEPTANCE_HOST_ID" not in workflow
    assert "vars.OKX_ACCEPTANCE_DURABLE_ROOT" not in workflow
    assert "vars.OKX_ACCEPTANCE_DURABLE_URI" not in workflow
    assert "self-hosted" not in workflow


def test_okx_acceptance_documentation_matches_workflow_mapping() -> None:
    documentation = DOCUMENTATION_PATH.read_text(encoding="utf-8")

    for expected in (
        "freqtrade-synology-staging",
        "freqtrade-staging",
        "synology-staging",
        "/var/lib/freqtrade-staging-state/okx-liquidation-acceptance",
        "file:///var/lib/freqtrade-staging-state/okx-liquidation-acceptance",
        "30308573877",
    ):
        assert expected in documentation

    assert "OKX_ACCEPTANCE_*" in documentation
    assert "does not depend" in documentation
