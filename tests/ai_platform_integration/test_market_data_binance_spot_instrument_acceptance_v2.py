from __future__ import annotations

import importlib.util
import json
from pathlib import Path
from types import ModuleType

import pytest


REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
WORKFLOW_PATH = (
    REPOSITORY_ROOT
    / ".github/workflows/ai-platform-binance-spot-instrument-shadow-acceptance-v2.yml"
)
PREFLIGHT_PATH = (
    REPOSITORY_ROOT
    / "tools/market_data/binance_spot_instrument_acceptance_v2_preflight.py"
)
TRIGGER_PATH = (
    "ai_platform/market_data/run-requests/"
    "binance-spot-instrument-shadow-acceptance-20260729-v2.json"
)
V1_TRIGGER_PATH = (
    "ai_platform/market_data/run-requests/"
    "binance-spot-instrument-shadow-acceptance-20260728-v1.json"
)


def _load_preflight() -> ModuleType:
    spec = importlib.util.spec_from_file_location("binance_acceptance_v2_preflight", PREFLIGHT_PATH)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_v2_workflow_is_exact_one_file_runner_gated_and_dependency_ready() -> None:
    workflow = WORKFLOW_PATH.read_text(encoding="utf-8")

    assert "types: [opened]" in workflow
    assert f'- "{TRIGGER_PATH}"' in workflow
    assert f"expected=$'A\\t{TRIGGER_PATH}'" in workflow
    assert V1_TRIGGER_PATH not in workflow
    assert "runs-on: [freqtrade-staging]" in workflow
    assert "environment: synology-staging" in workflow
    assert "jsonschema==4.26.0" in workflow
    assert workflow.index("Install pinned acceptance dependency") < workflow.index(
        "Validate frozen package without network"
    )
    assert "pull_request_target" not in workflow
    assert "workflow_dispatch" not in workflow
    assert "schedule:" not in workflow
    assert "curl " not in workflow
    assert "wget " not in workflow
    assert "api1.binance.com" not in workflow
    assert "data-api.binance.vision" not in workflow

    upload = workflow.split("- name: Upload bounded metadata evidence", 1)[1]
    upload = upload.split("- name: Remove isolated acceptance runtime", 1)[0]
    assert "sample-report.json" in upload
    assert "raw-response.json" not in upload
    assert "instrument-catalog-snapshot.json" not in upload


def test_v2_preflight_binds_new_request_identity(tmp_path: Path) -> None:
    preflight = _load_preflight()
    request_path = tmp_path / "request.json"
    request_path.write_text(json.dumps(preflight.EXPECTED_REQUEST), encoding="utf-8")
    preflight.REQUEST_PATH = request_path

    assert preflight._validate_request() == (
        "binance-spot-instrument-shadow-acceptance-20260729-v2-r1"
    )
    assert preflight.EXPECTED_REQUEST["request_id"] == (
        "binance-spot-instrument-shadow-acceptance-20260729-v2"
    )
    assert preflight.EXPECTED_REQUEST["production_source_enabled"] is False
    assert preflight.EXPECTED_REQUEST["orders_submitted"] == 0

    changed = dict(preflight.EXPECTED_REQUEST)
    changed["run_id"] = "reused-v1"
    request_path.write_text(json.dumps(changed), encoding="utf-8")
    with pytest.raises(SystemExit, match="REQUEST_CONTRACT_MISMATCH"):
        preflight._validate_request()


def test_v2_preflight_validates_runner_and_durable_root(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    preflight = _load_preflight()
    durable_root = tmp_path / "binance-spot-instrument-acceptance"
    runner_temp = tmp_path / "runner-temp"
    workspace = tmp_path / "workspace"
    runner_temp.mkdir()
    workspace.mkdir()

    environment = {
        "RUNNER_NAME_VALUE": "freqtrade-synology-staging",
        "RUNNER_OS_VALUE": "Linux",
        "RUNNER_ARCH_VALUE": "X64",
        "STATE_DIR": str(tmp_path),
        "DURABLE_ROOT": str(durable_root),
        "DURABLE_URI": f"file://{durable_root}",
        "RUNNER_TEMP_VALUE": str(runner_temp),
        "GITHUB_WORKSPACE_VALUE": str(workspace),
    }
    for name, value in environment.items():
        monkeypatch.setenv(name, value)

    preflight._validate_runner()
    run_id = "binance-spot-instrument-shadow-acceptance-20260729-v2-r1"
    preflight._prepare_durable_storage(run_id)

    assert durable_root.is_dir()
    assert not list(durable_root.glob(".acceptance-v2-preflight-*"))

    (durable_root / run_id).mkdir()
    with pytest.raises(SystemExit, match="RUN_ID_ALREADY_EXISTS"):
        preflight._prepare_durable_storage(run_id)

    monkeypatch.setenv("RUNNER_ARCH_VALUE", "ARM32")
    with pytest.raises(SystemExit, match="RUNNER_ARCH_MISMATCH"):
        preflight._validate_runner()
