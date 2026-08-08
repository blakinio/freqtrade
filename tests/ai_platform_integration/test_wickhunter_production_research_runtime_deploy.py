from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
DEPLOY = ROOT / "deploy" / "synology" / "wickhunter-production-research-runtime"
WORKFLOW = (
    ROOT
    / ".github"
    / "workflows"
    / "ai-platform-wickhunter-wh09-production-research-runtime-deploy.yml"
)
RETRY_V2 = DEPLOY / "run-requests" / "retry-wh09-production-research-20260808-v2.json"
RETRY_V3 = DEPLOY / "run-requests" / "retry-wh09-production-research-20260808-v3.json"
DIAGNOSTIC_V4 = DEPLOY / "run-requests" / "diagnose-wh09-production-research-20260808-v4.json"
DIAGNOSTIC_PATH = (
    "deploy/synology/wickhunter-production-research-runtime/run-requests/"
    "diagnose-wh09-production-research-20260808-v4.json"
)
EXPECTED_DIAGNOSTIC_IMAGE_ID = (
    "sha256:c5a67281912e262a183dd7a5804609a2f69ca356d5eb98e4a5a8da169e07a749"
)


def test_compose_keeps_zero_authority_and_hardened_mounts() -> None:
    compose = (DEPLOY / "compose.yaml").read_text(encoding="utf-8")
    assert "--model-root" in compose
    assert "--activation-root" not in compose
    assert "--expected-model-hash" in compose
    assert "${POLL_SECONDS:-60}" in compose
    assert "read_only: true" in compose
    assert "cap_drop:" in compose and "- ALL" in compose
    assert "no-new-privileges:true" in compose
    assert "privileged: false" in compose
    assert 'user: "65532:65532"' in compose
    assert "LIQUID20_READER_GID" in compose
    assert 'HTTP_PROXY: ""' in compose
    assert 'HTTPS_PROXY: ""' in compose
    assert 'ALL_PROXY: ""' in compose
    assert "/runtime/model" in compose
    assert "/runtime/liquid20" in compose
    assert "/runtime/journal" in compose
    assert "/runtime/operator" in compose
    assert "pids_limit: 256" in compose
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


def test_image_runs_nonroot_exact_commit_operator() -> None:
    dockerfile = (DEPLOY / "Dockerfile").read_text(encoding="utf-8")
    assert "ARG OPERATOR_COMMIT" in dockerfile
    assert "org.opencontainers.image.revision" in dockerfile
    assert "lightgbm==4.6.0" in dockerfile
    assert "USER 65532:65532" in dockerfile
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


def test_bounded_deploy_retries_preserve_exact_image_and_authorized_compose() -> None:
    workflow = WORKFLOW.read_text(encoding="utf-8")
    retry_v2 = json.loads(RETRY_V2.read_text(encoding="utf-8"))
    retry_v3 = json.loads(RETRY_V3.read_text(encoding="utf-8"))

    assert "environment: synology-staging" in workflow
    assert "timeout-minutes: 45" in workflow
    assert "freqtrade-staging" in workflow
    assert "retry-wh09-production-research-20260808-v2.json" in workflow
    assert "retry-wh09-production-research-20260808-v3.json" in workflow
    assert "docker image inspect" in workflow
    assert "org.opencontainers.image.revision" in workflow
    assert 'revision=""' in workflow
    assert 'if [[ "$revision" != "$DEPLOY_COMMIT" ]]; then' in workflow
    assert '[[ "$revision" == "$DEPLOY_COMMIT" ]]' not in workflow
    assert "--no-build" in workflow
    assert "two advancing cycles" in workflow
    assert "docker exec" in workflow
    assert "research_runtime_healthcheck.py" in workflow
    assert '"mode": "shadow"' in workflow
    assert '"no_trade_confidence": "0.60"' in workflow
    assert '"execution_enabled": False' in workflow
    assert '"orders_submitted": 0' in workflow
    assert '"live_capital_authorized": False' in workflow
    assert "AUTHORIZED_COMPOSE_SNAPSHOT" in workflow
    assert 'cp -- "$COMPOSE_FILE" "$AUTHORIZED_COMPOSE_SNAPSHOT"' in workflow
    assert 'cp -- "$AUTHORIZED_COMPOSE_SNAPSHOT" "$COMPOSE_FILE"' in workflow
    assert "CPU-CFS/NanoCPUs fields" in workflow

    snapshot_index = workflow.index('cp -- "$COMPOSE_FILE" "$AUTHORIZED_COMPOSE_SNAPSHOT"')
    checkout_index = workflow.index("Checkout exact merged runtime implementation")
    build_index = workflow.index("docker build")
    restore_index = workflow.index('cp -- "$AUTHORIZED_COMPOSE_SNAPSHOT" "$COMPOSE_FILE"')
    assert snapshot_index < checkout_index < build_index < restore_index

    assert retry_v2 == {
        "schema_version": 1,
        "request_id": "wickhunter-wh09-production-research-deploy-retry-20260808-v2",
        "deploy_commit": "ec0f53cc4df7dfcf008f5f7a4e6ab3733a2cefe5",
        "previous_run_id": 31268955706,
        "previous_job_id": 93139010419,
        "failure_class": "docker_compose_build_deadline_exceeded_after_exact_image_export",
        "reuse_exact_image_if_present": True,
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
    assert retry_v3 == {
        "schema_version": 1,
        "request_id": "wickhunter-wh09-production-research-deploy-retry-20260808-v3",
        "deploy_commit": "ec0f53cc4df7dfcf008f5f7a4e6ab3733a2cefe5",
        "previous_run_id": 31273808566,
        "previous_job_id": 93144045334,
        "failure_class": "synology_kernel_rejects_nanocpus_without_cpu_cfs",
        "reuse_exact_image_if_present": True,
        "synology_cpu_cfs_limit_disabled": True,
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


def test_diagnostic_v4_is_read_only_and_bound_to_failed_deployment() -> None:
    workflow = WORKFLOW.read_text(encoding="utf-8")
    diagnostic = json.loads(DIAGNOSTIC_V4.read_text(encoding="utf-8"))

    assert DIAGNOSTIC_PATH in workflow
    assert "Inspect existing WH09 SHADOW runtime without recreation" in workflow
    assert "EXPECTED_DIAGNOSTIC_CONTAINER_ID" in workflow
    assert "EXPECTED_DIAGNOSTIC_IMAGE_ID" in workflow
    assert "6724290d3078f09fc82c434e239d2d8afd3686ddedd27ff7d400834538cfbfe0" in workflow
    assert EXPECTED_DIAGNOSTIC_IMAGE_ID in workflow
    assert "docker logs --tail 300" in workflow
    assert 'docker compose -f "$COMPOSE_FILE" up' in workflow
    assert "if: always()" in workflow
    assert "toJSON(github.event.commits)" in workflow
    assert "!contains(toJSON(github.event.commits)" in workflow
    assert "contains(toJSON(github.event.commits)" in workflow

    diagnose_index = workflow.index("  diagnose:")
    diagnostic_section = workflow[diagnose_index:]
    assert 'docker compose -f "$COMPOSE_FILE" up' not in diagnostic_section
    assert "docker ps -aq --no-trunc" in diagnostic_section
    assert "docker restart" not in diagnostic_section
    assert "docker start" not in diagnostic_section
    assert "docker stop" not in diagnostic_section
    assert "docker rm" not in diagnostic_section
    assert "docker kill" not in diagnostic_section

    assert diagnostic == {
        "schema_version": 1,
        "request_id": "wickhunter-wh09-production-research-diagnostic-20260808-v4",
        "deploy_commit": "ec0f53cc4df7dfcf008f5f7a4e6ab3733a2cefe5",
        "deployment_authorization_commit": "c64df386a4fa3ba739b6eaa1a223ca798a7bcae2",
        "previous_run_id": 31275253098,
        "previous_job_id": 93147659559,
        "expected_container_id": "6724290d3078f09fc82c434e239d2d8afd3686ddedd27ff7d400834538cfbfe0",
        "expected_image_id": EXPECTED_DIAGNOSTIC_IMAGE_ID,
        "failure_class": "runtime_health_file_absent_after_container_start",
        "diagnostic_only": True,
        "container_recreate_authorized": False,
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
