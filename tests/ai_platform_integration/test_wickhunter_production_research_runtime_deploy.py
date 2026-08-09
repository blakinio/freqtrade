from __future__ import annotations

import json
import subprocess
from pathlib import Path

from tools.ci.classify_wickhunter_wh09_deploy_request import diagnostic_request_changed


ROOT = Path(__file__).resolve().parents[2]
DEPLOY = ROOT / "deploy" / "synology" / "wickhunter-production-research-runtime"
WORKFLOW = (
    ROOT
    / ".github"
    / "workflows"
    / "ai-platform-wickhunter-wh09-production-research-runtime-deploy.yml"
)
RETRY_V6 = DEPLOY / "run-requests" / "retry-wh09-production-research-20260809-v6.json"
DIAGNOSTIC_PATH = (
    "deploy/synology/wickhunter-production-research-runtime/run-requests/"
    "diagnose-wh09-production-research-20260808-v4.json"
)


def _workflow_shell_step(workflow: str, step_name: str) -> str:
    lines = workflow.splitlines()
    marker = f"      - name: {step_name}"
    start = lines.index(marker)
    run_index = next(
        index
        for index in range(start + 1, len(lines))
        if lines[index] == "        run: |"
    )
    body: list[str] = []
    for line in lines[run_index + 1 :]:
        if line.startswith("      - name: "):
            break
        if line.startswith("          "):
            body.append(line[10:])
        elif not line:
            body.append("")
        else:
            raise AssertionError(f"unexpected workflow shell indentation: {line!r}")
    return "\n".join(body) + "\n"


def test_compose_keeps_zero_authority_and_synology_compatible_hardening() -> None:
    compose = (DEPLOY / "compose.yaml").read_text(encoding="utf-8")
    assert "--model-root" in compose
    assert "--activation-root" not in compose
    assert "--expected-model-hash" in compose
    assert "${POLL_SECONDS:-60}" in compose
    assert "read_only: true" in compose
    assert "cap_drop:" in compose and "- ALL" in compose
    assert "no-new-privileges:true" in compose
    assert "privileged: false" in compose
    assert 'user: "65531:65531"' in compose
    assert "LIQUID20_READER_GID" in compose
    assert 'HTTP_PROXY: ""' in compose
    assert 'HTTPS_PROXY: ""' in compose
    assert 'ALL_PROXY: ""' in compose
    assert "/runtime/model" in compose
    assert "/runtime/liquid20" in compose
    assert "/runtime/journal" in compose
    assert "/runtime/operator" in compose
    assert "ulimits:" in compose
    assert "nproc:" in compose
    assert "soft: 256" in compose
    assert "hard: 256" in compose
    assert "pids_limit:" not in compose
    assert "mem_limit: 2g" in compose
    assert "restart: unless-stopped" in compose
    assert "cpus:" not in compose
    assert "cpu_quota:" not in compose
    assert "cpu_period:" not in compose
    assert "ports:" not in compose
    assert "/var/run/docker.sock" not in compose
    assert "BINANCE_API_KEY" not in compose
    assert "BINANCE_API_SECRET" not in compose


def test_deployment_is_pinned_to_h900_identity() -> None:
    compose = (DEPLOY / "compose.yaml").read_text(encoding="utf-8")
    readme = (DEPLOY / "README.md").read_text(encoding="utf-8")
    expected = (
        "wickhunter-wh09-candidate-materialization-20260808-r1-h900s-7b23a958fd4d",
        "9f5ba852e33915678ca085c2eeafbf526457a079ba8f6f2fb7c1097f1d20ab79",
        "0488eaea68a316e3659e3b9e2fcea667eb57de87a22888ce396d112a5c075d2e",
        "eddd12e3d0c5922547df89d9fa3d8556b8131a62c3cb8057c5a20c66747a240b",
        "014b471b9ccc663c3551a151353ae7cd932bd43ed48b9fbf239baad3483e2c11",
    )
    for value in expected:
        assert value in compose
        assert value in readme
    assert "no_trade_confidence=0.60" in readme
    assert "candidate_paper_validation_authorized=false" in readme
    assert "execution_enabled=false" in readme
    assert "orders_submitted=0" in readme
    assert "live_capital_authorized=false" in readme


def test_image_runs_as_dedicated_nonroot_exact_commit_operator() -> None:
    dockerfile = (DEPLOY / "Dockerfile").read_text(encoding="utf-8")
    assert "ARG OPERATOR_COMMIT" in dockerfile
    assert "org.opencontainers.image.revision" in dockerfile
    assert "lightgbm==4.6.0" in dockerfile
    assert "groupadd --gid 65531 wickhunter" in dockerfile
    assert "useradd --uid 65531 --gid 65531" in dockerfile
    assert "USER 65531:65531" in dockerfile
    assert "65532" not in dockerfile
    assert (
        'ENTRYPOINT ["python", "-m", "ai_platform.wickhunter.production_research_runtime_operator"]'
    ) in dockerfile


def test_healthcheck_rejects_nested_fail_closed_runtime() -> None:
    healthcheck = (DEPLOY / "research_runtime_healthcheck.py").read_text(encoding="utf-8")
    assert 'health.get("runtime_health") not in {"healthy", "degraded"}' in healthcheck
    assert 'health.get("circuit_breaker_active") is True' in healthcheck
    operator = (
        ROOT / "ai_platform" / "wickhunter" / "production_research_runtime_operator.py"
    ).read_text(encoding="utf-8")
    assert 'status = "fail_closed" if runtime_health == "fail_closed" else "healthy"' in operator
    assert 'error_code = None if status == "healthy" else "runtime_fail_closed"' in operator


def test_final_retry_v6_is_one_shot_exact_source_and_zero_authority() -> None:
    workflow = WORKFLOW.read_text(encoding="utf-8")
    retry = json.loads(RETRY_V6.read_text(encoding="utf-8"))

    assert "environment: synology-staging" in workflow
    assert "timeout-minutes: 45" in workflow
    assert "freqtrade-staging" in workflow
    assert "retry-wh09-production-research-20260809-v6.json" in workflow
    assert "EXPECTED_COMPOSE_BLOB_SHA" in workflow
    assert "git diff --name-status" in workflow
    assert "$'A\\t'\"$REQUEST_PATH\"" in workflow
    assert 'git rev-parse "$GITHUB_SHA:$COMPOSE_FILE"' in workflow
    assert "docker build --no-cache" in workflow
    assert "org.opencontainers.image.revision" in workflow
    assert "COMPOSE_PROJECT_NAME: wickhunter-production-research-runtime" in workflow
    assert "COMPOSE_SERVICE: wickhunter-production-research-runtime" in workflow
    assert "label=com.docker.compose.project=$COMPOSE_PROJECT_NAME" in workflow
    assert "label=com.docker.compose.service=$COMPOSE_SERVICE" in workflow
    assert "WH09 compose service identity is not unique" in workflow
    assert "PREVIOUS_RUNTIME_CONTAINER_ID" in workflow
    assert 'docker stop --time 30 "$PREVIOUS_RUNTIME_CONTAINER_ID"' in workflow
    assert '[[ "$existing" == "${PREVIOUS_RUNTIME_CONTAINER_ID:-}" ]] && continue' in workflow
    assert workflow.count('"$RUNTIME_UID"|"$RUNTIME_UID":*|*:"$RUNTIME_GID")') == 2
    assert '"$RUNTIME_UID:"*' not in workflow
    assert '*":"$RUNTIME_GID"' not in workflow
    assert "--pid=host" in workflow
    assert "--network none" in workflow
    assert "--read-only" in workflow
    assert "--cap-drop ALL" in workflow
    assert "--security-opt no-new-privileges:true" in workflow
    assert "hidepid=" in workflow
    assert "restrictive proc visibility is not allowed" in workflow
    assert "snapshot =" in workflow
    assert "host PID namespace probe has incomplete PID visibility" in workflow
    assert "cannot read stable host PID" in workflow
    assert "if not pid_dir.exists():" in workflow
    assert "HOST_PID_UID_ISOLATION_PASS" in workflow
    assert "ps -eo uid=" not in workflow
    assert 'export WICKHUNTER_RESEARCH_RUNTIME_IMAGE="$image_id"' in workflow
    assert '"$image_id" - "$RUNTIME_UID"' in workflow
    assert "--no-build --force-recreate" in workflow
    assert "deployed_image_id=\"$(docker inspect --format '{{.Image}}'" in workflow
    assert '[[ "$deployed_image_id" == "$image_id" ]]' in workflow
    assert "runtime immutable image identity mismatch" in workflow
    assert "'image_id': runtime_image_id" in workflow
    assert "two advancing cycles" in workflow
    assert "docker exec" in workflow
    assert "research_runtime_healthcheck.py" in workflow
    assert '"mode": "shadow"' in workflow
    assert '"no_trade_confidence": "0.60"' in workflow
    assert '"execution_enabled": False' in workflow
    assert '"orders_submitted": 0' in workflow
    assert '"live_capital_authorized": False' in workflow
    assert 'RUNTIME_UID: "65531"' in workflow
    assert 'RUNTIME_GID: "65531"' in workflow
    assert "RLIMIT_NPROC_DEDICATED_HOST_UID_FALLBACK" in workflow
    assert "pids_limit" in workflow  # forbidden-field guard documents the unsupported setting
    assert "PidsLimit" not in workflow

    assert retry == {
        "schema_version": 1,
        "request_id": "wickhunter-wh09-production-research-deploy-retry-20260809-v6",
        "deploy_commit": "90cfc5ded10b0c6cb6406d00042817aca611e900",
        "previous_run_id": 31326580829,
        "previous_job_id": 93277819212,
        "failure_class": "bash_case_pattern_parse_error_before_host_validation",
        "runtime_repair_authorized": True,
        "container_recreate_authorized": True,
        "replace_unsupported_pids_cgroup_with_nproc_rlimit": True,
        "persistent_internal_demo_production_authorized": True,
        "mode": "shadow",
        "no_trade_confidence": "0.60",
        "paper_activation_authorized": False,
        "automatic_promotion_enabled": False,
        "trading_credentials_present": False,
        "order_adapter_present": False,
        "execution_enabled": False,
        "orders_submitted": 0,
        "live_capital_authorized": False,
    }


def test_wh09_deployment_shell_steps_are_bash_parseable() -> None:
    workflow = WORKFLOW.read_text(encoding="utf-8")
    for step_name in (
        "Validate runner zero authority and host inputs",
        "Build exact image verify host UID isolation and force-recreate SHADOW runtime",
    ):
        script = _workflow_shell_step(workflow, step_name)
        subprocess.run(
            ["bash", "-n"],
            input=script,
            text=True,
            check=True,
            capture_output=True,
        )


def test_diagnostic_classifier_matches_only_exact_changed_file_elements() -> None:
    lookalike_event = {
        "commits": [
            {
                "added": [f"{DIAGNOSTIC_PATH}.bak"],
                "modified": [f"prefix-{DIAGNOSTIC_PATH}"],
                "removed": [],
                "message": DIAGNOSTIC_PATH,
            }
        ]
    }
    assert diagnostic_request_changed(lookalike_event, DIAGNOSTIC_PATH) is False

    multi_commit_event = {
        "commits": [
            {"added": ["unrelated.txt"], "modified": [], "removed": []},
            {"added": [], "modified": [DIAGNOSTIC_PATH], "removed": []},
            {"added": [f"{DIAGNOSTIC_PATH}.bak"], "modified": [], "removed": []},
        ]
    }
    assert diagnostic_request_changed(multi_commit_event, DIAGNOSTIC_PATH) is True
