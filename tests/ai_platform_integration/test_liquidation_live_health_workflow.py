from __future__ import annotations

from pathlib import Path


WORKFLOW = (
    Path(__file__).resolve().parents[2]
    / ".github"
    / "workflows"
    / "liquidations-live-operational-health.yml"
)


def test_runner_watchdog_uses_file_backed_github_payloads() -> None:
    workflow = WORKFLOW.read_text(encoding="utf-8")

    assert 'jobs_response="$RUNNER_TEMP/liquidations-live-run-jobs.json"' in workflow
    assert '--output "$jobs_response"' in workflow
    assert 'JOBS_JSON_PATH="$jobs_response" python' in workflow
    assert 'Path(os.environ["JOBS_JSON_PATH"]).read_text(encoding="utf-8")' in workflow

    assert 'ISSUES_JSON_PATH="$issues_response" python' in workflow
    assert 'Path(os.environ["ISSUES_JSON_PATH"]).read_text(encoding="utf-8")' in workflow

    assert 'JOBS_JSON="$jobs_json" python' not in workflow
    assert 'ISSUES_JSON="$issues_json" python' not in workflow
