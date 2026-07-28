from __future__ import annotations

from pathlib import Path


REPOSITORY_ROOT = Path(__file__).resolve().parents[4]
WORKFLOW_PATH = (
    REPOSITORY_ROOT / ".github/workflows/liquidations-live-portal-synology-proof.yml"
)
SOURCE_PATH = REPOSITORY_ROOT / "deploy/synology/portal/prove-liquidations-live.sh"
WRAPPER_PATH = (
    REPOSITORY_ROOT / "deploy/synology/portal/run-liquidations-live-portal-proof.sh"
)


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def test_wrapper_replaces_only_the_legacy_health_wait() -> None:
    source = _read(SOURCE_PATH)
    wrapper = _read(WRAPPER_PATH)

    legacy_marker = (
        "docker inspect --format "
        "'{{if .State.Health}}{{.State.Health.Status}}{{else}}{{.State.Status}}{{end}}'"
    )
    assert source.count(legacy_marker) == 2
    assert "text.count(old) != 1" in wrapper
    assert "text.replace(old, new)" in wrapper
    assert "text.count(needle) != 1" in wrapper
    assert "text.replace(needle, diagnostic, 1)" in wrapper


def test_readiness_is_bounded_and_uses_the_candidate_http_surface() -> None:
    wrapper = _read(WRAPPER_PATH)

    assert "for _ in $(seq 1 60)" in wrapper
    assert 'fetch("http://127.0.0.1:3000/login"' in wrapper
    assert "response.status === 200" in wrapper
    assert "candidate_ready=true" in wrapper
    assert "Candidate did not pass explicit HTTP readiness probe" in wrapper
    assert "image_healthcheck_present=${candidate_healthcheck_present}" in wrapper


def test_failure_evidence_remains_fail_closed() -> None:
    wrapper = _read(WRAPPER_PATH)

    assert '"result": "failure"' in wrapper
    assert '"completed": False' in wrapper
    assert '"research_preview": True' in wrapper
    assert '"trading_authorized": False' in wrapper
    assert (
        "See the paired workflow log for the exact ERR trap line and command." in wrapper
    )
    assert "--privileged" not in wrapper
    assert "docker restart" not in wrapper
    assert "docker update" not in wrapper


def test_workflow_executes_and_retriggers_on_the_wrapper() -> None:
    workflow = _read(WORKFLOW_PATH)

    wrapper_path = "deploy/synology/portal/run-liquidations-live-portal-proof.sh"
    assert workflow.count(wrapper_path) == 2
    assert "runs-on: freqtrade-staging" in workflow
    assert "environment: synology-staging" in workflow
    assert (
        "PORTAL_LIQUIDATIONS_HOST_ROOT: /volume1/docker/freqtrade-liquidations/data"
        in workflow
    )
    assert "if: always()" in workflow
    assert "retention-days: 30" in workflow
