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
RETRY = DEPLOY / "run-requests" / "retry-wh09-production-research-20260808-v2.json"


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


def test_bounded_deploy_retry_reuses_exact_image_and_keeps_zero_authority() -> None:
    workflow = WORKFLOW.read_text(encoding="utf-8")
    retry = json.loads(RETRY.read_text(encoding="utf-8"))

    assert "environment: synology-staging" in workflow
    assert "timeout-minutes: 45" in workflow
    assert "freqtrade-staging" in workflow
    assert "retry-wh09-production-research-20260808-v2.json" in workflow
    assert "docker image inspect" in workflow
    assert "org.opencontainers.image.revision" in workflow
    assert "--no-build" in workflow
    assert "two advancing cycles" in workflow
    assert "docker exec" in workflow
    assert "research_runtime_healthcheck.py" in workflow
    assert '"mode": "shadow"' in workflow
    assert '"no_trade_confidence": "0.60"' in workflow
    assert '"execution_enabled": False' in workflow
    assert '"orders_submitted": 0' in workflow
    assert '"live_capital_authorized": False' in workflow

    assert retry == {
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
