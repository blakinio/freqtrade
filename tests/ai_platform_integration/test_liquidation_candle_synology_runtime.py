from __future__ import annotations

from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
WORKFLOW = REPO_ROOT / ".github/workflows/ai-platform-liquidation-candle-artifact.yml"
RUNTIME = REPO_ROOT / "deploy/synology/liquid20-candle-artifact/run.sh"
DOCKERFILE = REPO_ROOT / "deploy/synology/liquid20-candle-artifact/Dockerfile"
REQUEST_PATH = (
    "ai_platform/research/liquidations/datasets/run-requests/"
    "liquid20-candle-diagnostic-20260724-v1.json"
)


def test_workflow_uses_exact_one_file_synology_runner() -> None:
    workflow = WORKFLOW.read_text(encoding="utf-8")

    assert "runs-on: freqtrade-staging" in workflow
    assert "actions/setup-python@" not in workflow
    assert f"expected=$'A\\t{REQUEST_PATH}'" in workflow
    assert "github.event.pull_request.head.repo.full_name == github.repository" in workflow
    assert "bash deploy/synology/liquid20-candle-artifact/run.sh" in workflow


def test_runtime_is_bounded_and_exports_only_after_verification() -> None:
    runtime = RUNTIME.read_text(encoding="utf-8")

    for boundary in (
        "--read-only",
        "--cap-drop ALL",
        "--security-opt no-new-privileges:true",
        "--pids-limit 128",
        "--memory 512m",
        "type=volume,src=$volume,dst=/output",
    ):
        assert boundary in runtime

    assert runtime.index('phase="verify_artifact"') < runtime.index('phase="export_artifact"')
    assert 'docker cp "$exporter:/output/$evidence_root/." "$evidence_root/"' in runtime
    assert 'partial_artifact_published": false' in runtime
    assert 'orders_submitted": 0' in runtime
    assert 'trading_credentials_present": false' in runtime


def test_runtime_image_is_non_root_and_code_is_immutable() -> None:
    dockerfile = DOCKERFILE.read_text(encoding="utf-8")

    assert dockerfile.startswith("FROM python:3.13-slim-bookworm\n")
    assert "chown 65534:65534 /output" in dockerfile
    assert "chmod -R a-w /workspace" in dockerfile
    assert "USER 65534:65534" in dockerfile
