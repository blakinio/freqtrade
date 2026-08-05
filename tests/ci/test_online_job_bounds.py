from pathlib import Path

import yaml


WORKFLOW_PATH = Path(".github/workflows/ci.yml")


def _workflow_jobs() -> dict:
    workflow = yaml.safe_load(WORKFLOW_PATH.read_text(encoding="utf-8"))
    jobs = workflow.get("jobs")
    assert isinstance(jobs, dict)
    return jobs


def test_online_compatibility_job_is_bounded_and_fail_closed() -> None:
    jobs = _workflow_jobs()
    online_job = jobs["online-tests"]

    assert online_job["timeout-minutes"] == 30
    assert online_job.get("continue-on-error") is not True

    test_step = next(
        step
        for step in online_job["steps"]
        if step.get("name") == "Tests incl. ccxt compatibility tests"
    )
    command = test_step["run"]
    assert "--timeout=300" in command

    ci_gate = jobs["ci-gate"]
    assert "online-tests" in ci_gate["needs"]
    gate_step = next(
        step
        for step in ci_gate["steps"]
        if step.get("name") == "Validate selected and skipped job outcomes"
    )
    assert 'require_success "$ONLINE_SCOPE" "$ONLINE_RESULT"' in gate_step["run"]
