from __future__ import annotations

from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
WORKFLOW_PATH = (
    REPO_ROOT
    / ".github/workflows/ai-platform-okx-liquidation-shadow-acceptance-staging-preflight.yml"
)
REQUEST_PATH = (
    "ai_platform/research/liquidations/run-requests/"
    "okx-shadow-acceptance-staging-preflight-20260727-v1.json"
)


def test_staging_preflight_targets_existing_synology_runner_without_collection() -> None:
    workflow = WORKFLOW_PATH.read_text(encoding="utf-8")

    assert f'      - "{REQUEST_PATH}"' in workflow
    assert "runs-on: [self-hosted, Linux, oteryn-staging]" in workflow
    assert "environment: synology-staging" in workflow
    assert "STAGING_STATE_DIR: ${{ vars.OTERYN_STAGING_STATE_DIR }}" in workflow
    assert '"expected_runner_name": "oteryn-synology-staging"' in workflow
    assert '"expected_state_dir": "/var/lib/oteryn-staging-state"' in workflow
    assert (
        '"expected_durable_root": "/var/lib/oteryn-staging-state/okx-liquidation-acceptance"'
    ) in workflow
    assert (
        '"expected_durable_uri": "file:///var/lib/oteryn-staging-state/okx-liquidation-acceptance"'
    ) in workflow
    assert "liquidation_okx_shadow_acceptance" not in workflow
    assert "collect_okx_liquidations" not in workflow
    assert '"collection_authorized": False' in workflow
    assert '"collection_executed": False' in workflow
    assert '"execution_enabled": False' in workflow
    assert '"orders_submitted": 0' in workflow


def test_staging_preflight_is_exact_one_file_and_credential_free() -> None:
    workflow = WORKFLOW_PATH.read_text(encoding="utf-8")

    assert "github.event.pull_request.head.repo.full_name == github.repository" in workflow
    assert "github.event.pull_request.base.ref == 'develop'" in workflow
    assert f"expected=$'A\\t{REQUEST_PATH}'" in workflow
    assert "if request != expected:" in workflow
    assert "persist-credentials: false" in workflow
    assert "OKX_API_KEY" in workflow
    assert "OKX_API_SECRET" in workflow
    assert "FREQTRADE__EXCHANGE__KEY" in workflow
    assert "FREQTRADE__EXCHANGE__SECRET" in workflow
    assert "actions/upload-artifact@043fb46d1a93c77aae656e7c1c64a875d1fc6a0a" in workflow
    assert "retention-days: 30" in workflow
    assert "okx-usdt-swap.ndjson" not in workflow
