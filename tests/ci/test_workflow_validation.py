from pathlib import Path
from typing import Any

import yaml

from tools.ci.validate_workflows import validate_repository


CENTRAL_WORKFLOWS = (
    Path(".github/workflows/ci.yml"),
    Path(".github/workflows/ci-components.yml"),
)


def _load_workflow(path: Path) -> dict[str, Any]:
    payload = yaml.safe_load(path.read_text(encoding="utf-8"))
    assert isinstance(payload, dict)
    return payload


def _uncancelable_job_level_always(payload: dict[str, Any]) -> list[str]:
    violations: list[str] = []
    jobs = payload.get("jobs", {})
    assert isinstance(jobs, dict)
    for job_name, job in jobs.items():
        if not isinstance(job, dict):
            continue
        condition = job.get("if")
        if (
            isinstance(condition, str)
            and "always()" in condition
            and "!cancelled()" not in condition.replace(" ", "")
        ):
            violations.append(str(job_name))
    return violations


def test_repository_workflows_satisfy_routing_and_security_contract() -> None:
    assert validate_repository(Path()) == []


def test_central_workflow_job_level_always_is_cancel_aware() -> None:
    failures = {
        path.as_posix(): _uncancelable_job_level_always(_load_workflow(path))
        for path in CENTRAL_WORKFLOWS
    }
    assert failures == {path.as_posix(): [] for path in CENTRAL_WORKFLOWS}


def test_bare_job_level_always_is_rejected_by_contract() -> None:
    payload = {"jobs": {"required-gate": {"if": "${{ always() }}"}}}
    assert _uncancelable_job_level_always(payload) == ["required-gate"]


def test_cancel_aware_always_still_supports_failure_evaluation() -> None:
    payload = {
        "jobs": {
            "required-gate": {
                "if": "${{ always() && !cancelled() }}",
                "needs": ["selected-job"],
            }
        }
    }
    assert _uncancelable_job_level_always(payload) == []
