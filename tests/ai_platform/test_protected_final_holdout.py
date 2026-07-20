import json
from pathlib import Path

import pytest

from ai_platform.scripts import run_optimization, run_validation
from ai_platform.scripts.protected_final_holdout import (
    FINAL_HOLDOUT_WORKFLOW,
    protected_timerange,
)
from ai_platform.scripts.run_experiment import ExperimentError, load_manifest


ROOT = Path(__file__).resolve().parents[2]
BASELINE_MANIFEST = ROOT / "ai_platform/experiments/baseline-v1.json"
FINAL_HOLDOUT_MANIFEST = ROOT / "ai_platform/experiments/final-holdout-v2.json"


def _write_manifest(tmp_path: Path, **updates: object) -> Path:
    manifest = json.loads(BASELINE_MANIFEST.read_text(encoding="utf-8"))
    manifest.update(updates)
    path = tmp_path / "experiment.json"
    path.write_text(json.dumps(manifest), encoding="utf-8")
    return path


def test_protected_final_holdout_matches_prospective_declaration() -> None:
    assert protected_timerange() == "20260801-20260930"


def test_generic_manifest_outside_protected_holdout_remains_allowed() -> None:
    manifest = load_manifest(BASELINE_MANIFEST)
    assert manifest["experiment_id"] == "freqai-baseline-v1"


def test_generic_manifest_rejects_protected_evaluation_window(tmp_path: Path) -> None:
    path = _write_manifest(tmp_path, timerange="20260815-20260915")

    with pytest.raises(ExperimentError, match="overlaps protected final holdout 20260801-20260930"):
        load_manifest(path)


def test_generic_manifest_rejects_protected_download_coverage(tmp_path: Path) -> None:
    path = _write_manifest(tmp_path, download_timerange="20250701-20260815")

    with pytest.raises(ExperimentError, match="via download_timerange"):
        load_manifest(path)


def test_final_holdout_manifest_is_blocked_outside_dedicated_workflow(monkeypatch) -> None:
    monkeypatch.delenv("GITHUB_ACTIONS", raising=False)
    monkeypatch.delenv("GITHUB_WORKFLOW", raising=False)
    monkeypatch.delenv("GITHUB_EVENT_NAME", raising=False)

    with pytest.raises(ExperimentError, match="dedicated final-holdout-v2 workflow"):
        load_manifest(FINAL_HOLDOUT_MANIFEST)


def test_exact_final_holdout_manifest_is_allowed_only_in_dedicated_workflow(monkeypatch) -> None:
    monkeypatch.setenv("GITHUB_ACTIONS", "true")
    monkeypatch.setenv("GITHUB_WORKFLOW", FINAL_HOLDOUT_WORKFLOW)
    monkeypatch.setenv("GITHUB_EVENT_NAME", "pull_request")

    manifest = load_manifest(FINAL_HOLDOUT_MANIFEST)
    assert manifest["timerange"] == "20260801-20260930"


def test_workflow_environment_cannot_authorize_a_different_manifest(
    tmp_path: Path,
    monkeypatch,
) -> None:
    monkeypatch.setenv("GITHUB_ACTIONS", "true")
    monkeypatch.setenv("GITHUB_WORKFLOW", FINAL_HOLDOUT_WORKFLOW)
    monkeypatch.setenv("GITHUB_EVENT_NAME", "pull_request")
    path = _write_manifest(
        tmp_path,
        experiment_id="freqai-baseline-final-holdout-v2",
        timerange="20260801-20260930",
        download_timerange="20250801-20260930",
    )

    with pytest.raises(ExperimentError, match="dedicated final-holdout-v2 workflow"):
        load_manifest(path)


def test_validation_and_optimization_use_the_guarded_shared_manifest_loader() -> None:
    assert run_validation.load_manifest is load_manifest
    assert run_optimization.load_manifest is load_manifest
