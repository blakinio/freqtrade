from __future__ import annotations

from pathlib import Path


WORKFLOW_PATH = Path(".github/workflows/ai-platform-okx-liquidation-shadow-acceptance.yml")
DOCUMENTATION_PATH = Path("docs/ai_platform/LIQUIDATION_OKX_SHADOW_ACCEPTANCE_EXECUTION.md")


def test_okx_acceptance_uses_verified_freqtrade_staging_mapping() -> None:
    workflow = WORKFLOW_PATH.read_text(encoding="utf-8")

    assert "runs-on: [freqtrade-staging]" in workflow
    assert "environment: synology-staging" in workflow
    assert "ACCEPTANCE_HOST_ID: freqtrade-synology-staging" in workflow
    assert "STATE_DIR: /var/lib/freqtrade-staging-state" in workflow
    assert "DURABLE_ROOT: /var/lib/freqtrade-staging-state/okx-liquidation-acceptance" in workflow
    assert (
        "DURABLE_URI: file:///var/lib/freqtrade-staging-state/okx-liquidation-acceptance"
        in workflow
    )
    assert "RUNNER_NAME_VALUE: ${{ runner.name }}" in workflow
    assert 'if [[ "$RUNNER_NAME_VALUE" != "$ACCEPTANCE_HOST_ID" ]]' in workflow
    assert 'if [[ "$RUNNER_OS_VALUE" != "Linux" ]]' in workflow


def test_okx_acceptance_prepares_and_probes_only_the_canonical_durable_root() -> None:
    workflow = WORKFLOW_PATH.read_text(encoding="utf-8")

    assert 'if [[ "$(dirname "$DURABLE_ROOT")" != "$STATE_DIR" ]]' in workflow
    assert 'if [[ ! -d "$STATE_DIR" ]]' in workflow
    assert 'if [[ ! -w "$STATE_DIR" ]]' in workflow
    assert 'mkdir -p "$DURABLE_ROOT"' in workflow
    assert 'if [[ ! -d "$DURABLE_ROOT" ]]' in workflow
    assert 'if [[ ! -w "$DURABLE_ROOT" ]]' in workflow
    assert 'tempfile.mkdtemp(prefix=".acceptance-preflight-", dir=durable_root)' in workflow
    assert "source.replace(target)" in workflow
    assert "os.fsync(handle.fileno())" in workflow
    assert "shutil.rmtree(probe_dir)" in workflow

    for marker in (
        "OKX_ACCEPTANCE_STATE_DIR_MISSING",
        "OKX_ACCEPTANCE_STATE_DIR_NOT_WRITABLE",
        "OKX_ACCEPTANCE_DURABLE_ROOT_CREATE_FAILED",
        "OKX_ACCEPTANCE_DURABLE_ROOT_NOT_WRITABLE",
        "OKX_ACCEPTANCE_DURABLE_ROOT_ATOMIC_IO_FAILED",
    ):
        assert marker in workflow


def test_okx_acceptance_uses_image_bootstrap_python_before_setup_python() -> None:
    workflow = WORKFLOW_PATH.read_text(encoding="utf-8")
    validation_step = workflow.split("- name: Refuse trading credential environment", 1)[0]

    assert "python3 - <<'PY'" in validation_step
    assert "python - <<'PY'" not in validation_step
    assert validation_step.index("python3 - <<'PY'") < workflow.index("- name: Set up Python")


def test_okx_acceptance_rejects_legacy_mapping_and_mutable_variables() -> None:
    workflow = WORKFLOW_PATH.read_text(encoding="utf-8")

    assert "okx-liquidation-staging" not in workflow
    assert "vars.OKX_ACCEPTANCE_HOST_ID" not in workflow
    assert "vars.OKX_ACCEPTANCE_DURABLE_ROOT" not in workflow
    assert "vars.OKX_ACCEPTANCE_DURABLE_URI" not in workflow
    assert "self-hosted" not in workflow


def test_okx_acceptance_documentation_matches_storage_repair() -> None:
    documentation = DOCUMENTATION_PATH.read_text(encoding="utf-8")

    for expected in (
        "freqtrade-synology-staging",
        "freqtrade-staging",
        "synology-staging",
        "/var/lib/freqtrade-staging-state/okx-liquidation-acceptance",
        "file:///var/lib/freqtrade-staging-state/okx-liquidation-acceptance",
        "30308573877",
        "30352834444",
        "90254107799",
        "OKX_ACCEPTANCE_DURABLE_ROOT_CREATE_FAILED",
    ):
        assert expected in documentation

    assert "OKX_ACCEPTANCE_*" in documentation
    assert "does not depend" in documentation
