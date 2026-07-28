from __future__ import annotations

import subprocess
from pathlib import Path


REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
DEPLOYMENT_ROOT = REPOSITORY_ROOT / "deploy" / "synology" / "liquid20"
WORKFLOW = REPOSITORY_ROOT / ".github" / "workflows" / "liquidations-live-synology.yml"


def test_bounded_deploy_renderer_produces_valid_wall_clock_limited_script(tmp_path: Path) -> None:
    source = DEPLOYMENT_ROOT / "deploy-live.sh"
    renderer = DEPLOYMENT_ROOT / "render-bounded-deploy.py"
    rendered = tmp_path / "deploy-live-bounded.sh"

    subprocess.run(
        ["python", str(renderer), str(source), str(rendered)],
        cwd=REPOSITORY_ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    subprocess.run(
        ["bash", "-n", str(rendered)],
        cwd=REPOSITORY_ROOT,
        check=True,
        capture_output=True,
        text=True,
    )

    script = rendered.read_text(encoding="utf-8")
    assert 'state_wait_seconds="${LIQUID20_STATE_WAIT_SECONDS:-180}"' in script
    assert 'local deadline=$((SECONDS + state_wait_seconds))' in script
    assert 'while (( SECONDS < deadline ))' in script
    assert 'timeout 10s docker exec --interactive "$selected_container" python -' in script
    assert 'timeout 10s docker inspect --format' in script
    assert 'timeout 10s docker logs --tail 200 "$selected_container"' in script
    assert 'candidate_first="$(wait_for_state "$candidate" "$candidate_started_ms")"' in script
    assert 'production_first="$(wait_for_state "$container_name" "$production_started_ms")"' in script
    assert 'root = Path("/data")' in script
    assert "for _ in $(seq 1 90)" not in script


def test_bounded_deploy_wrapper_and_workflow_are_exact_sha_entrypoint() -> None:
    wrapper = DEPLOYMENT_ROOT / "deploy-live-bounded.sh"
    subprocess.run(
        ["bash", "-n", str(wrapper)],
        cwd=REPOSITORY_ROOT,
        check=True,
        capture_output=True,
        text=True,
    )

    wrapper_text = wrapper.read_text(encoding="utf-8")
    workflow = WORKFLOW.read_text(encoding="utf-8")
    assert "render-bounded-deploy.py" in wrapper_text
    assert 'bash -n "$rendered"' in wrapper_text
    assert 'bash "$rendered"' in wrapper_text
    assert "bash deploy/synology/liquid20/deploy-live-bounded.sh" in workflow
    assert "bash deploy/synology/liquid20/deploy-live.sh" not in workflow
    assert "push:" in workflow
    assert "- develop" in workflow
    assert "pull_request:" not in workflow
