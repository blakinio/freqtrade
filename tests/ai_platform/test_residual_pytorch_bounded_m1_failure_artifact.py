from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
WORKFLOW_PATH = REPO_ROOT / ".github/workflows/residual-pytorch-bounded-m1-execution.yml"


def _workflow() -> str:
    return WORKFLOW_PATH.read_text(encoding="utf-8")


def test_matrix_audit_failure_evidence_is_durable() -> None:
    workflow = _workflow()
    runtime_copy = 'cp -R "$audit_run" "$audit_root/runtime"'

    assert "id: audit-matrix" in workflow
    assert "audit-stderr.log" in workflow
    assert "audit-exit-code.txt" in workflow
    assert "audit-run-path.txt" in workflow
    assert "run-request.json" in workflow
    assert "execution-contract.json" in workflow
    assert workflow.index("run-request.json") < workflow.index("set +e")
    assert workflow.index("execution-contract.json") < workflow.index("set +e")
    assert workflow.index(runtime_copy) < workflow.index("validate-summary")
    assert workflow.index(runtime_copy) < workflow.index("validate-audit")


def test_skipped_models_do_not_fail_artifact_uploads() -> None:
    workflow = _workflow()

    assert "id: execute-models" in workflow
    assert workflow.count("steps.execute-models.outcome") == 3
    assert workflow.count("if-no-files-found: warn") == 3
    assert "name: Upload matrix audit evidence" in workflow
    assert "if-no-files-found: error" in workflow
