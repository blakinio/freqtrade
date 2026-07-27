from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
WORKFLOW_PATH = REPO_ROOT / ".github/workflows/residual-pytorch-bounded-m1-execution.yml"


def test_matrix_audit_failure_evidence_is_durable_and_bounded() -> None:
    workflow = WORKFLOW_PATH.read_text(encoding="utf-8")

    assert "id: audit-matrix" in workflow
    assert '2> >(tee "$audit_root/audit-stderr.log" >&2)' in workflow
    assert 'printf \'%s\\n\' "$audit_status" > "$audit_root/audit-exit-code.txt"' in workflow
    assert 'cp audit-run-path.txt "$audit_root/audit-run-path.txt"' in workflow
    assert workflow.index('cp "$REQUEST_PATH" "$audit_root/run-request.json"') < workflow.index(
        "set +e"
    )
    assert workflow.index('cp "$CONTRACT_PATH" "$audit_root/execution-contract.json"') < workflow.index(
        "set +e"
    )


def test_skipped_models_do_not_create_false_upload_failures() -> None:
    workflow = WORKFLOW_PATH.read_text(encoding="utf-8")

    assert "id: execute-models" in workflow
    assert workflow.count("if: always() && steps.execute-models.outcome != 'skipped'") == 3
    assert workflow.count("if-no-files-found: warn") == 3
    assert "name: Upload matrix audit evidence\n        if: always()" in workflow
    assert "path: ${{ env.EVIDENCE_ROOT }}/audit/\n          if-no-files-found: error" in workflow
