from __future__ import annotations

import json
from pathlib import Path

from tools.ci.change_classifier import classify, load_config


CONFIG = load_config(Path("tools/ci/change-routing.json"))


def route(
    *paths: str,
    event: str = "pull_request",
    action: str = "synchronize",
    labels=(),
):
    return classify(paths, event=event, action=action, labels=labels, config=CONFIG)["outputs"]


def test_documentation_only_skips_heavy_runtime_gates() -> None:
    result = route("docs/agents/PROMPTING_STANDARD.md")
    assert result["docs"] and result["docs_only"] and result["lightweight"]
    for gate in (
        "core_light",
        "core_matrix",
        "online",
        "portal_backend_tests",
        "portal_web_validation",
        "portal_browser_e2e",
        "postgres_recovery",
        "exact_image",
        "closure_e2e",
    ):
        assert not result[gate], gate


def test_portal_backend_selects_backend_and_exact_image_not_browser() -> None:
    result = route("ai_platform/portal/control_plane/api.py")
    assert result["portal_backend_tests"]
    assert result["portal_contract"]
    assert result["exact_image"]
    assert not result["portal_web_validation"]
    assert not result["portal_browser_e2e"]


def test_portal_web_runtime_selects_web_and_browser_without_database() -> None:
    result = route("ai_platform/portal/web/app/bots/page.tsx")
    assert not result["ai_platform"]
    assert result["portal_web_validation"]
    assert result["portal_browser_e2e"]
    assert not result["postgres_recovery"]
    assert not result["exact_image"]


def test_contract_change_crosses_backend_and_browser_boundaries() -> None:
    result = route("ai_platform/portal/contracts/bot_management/commands.py")
    assert result["portal_backend_tests"]
    assert result["portal_browser_e2e"]
    assert result["closure_e2e"]


def test_portal_e2e_scenarios_and_tests_select_closure_validation() -> None:
    for path in (
        "ai_platform/portal/e2e/scenarios/bot_management_closure.json",
        "tests/ai_platform/portal/e2e/test_bm09_closure_manifest.py",
    ):
        result = route(path)
        assert result["portal_backend_tests"], path
        assert result["closure_e2e"], path


def test_migration_selects_schema_postgresql_and_exact_image() -> None:
    result = route("ai_platform/portal/risk/migrations/0002_limits.py")
    assert result["schema_database"]
    assert result["portal_schema_light"]
    assert result["postgres_recovery"]
    assert result["exact_image"]
    assert result["high_risk"]
    assert not result["full"]


def test_identity_change_is_high_risk_and_fail_closed() -> None:
    result = route("ai_platform/portal/identity/repository.py")
    assert result["identity_oidc"]
    assert result["postgres_recovery"]
    assert result["exact_image"]
    assert result["security_analysis"]
    assert not result["full"]


def test_dependency_change_selects_matrix_distribution_online_and_image() -> None:
    result = route("deploy/synology/portal-oidc/requirements.txt")
    assert result["dependencies_packaging"]
    assert result["core_matrix"]
    assert result["compatibility_sweep"]
    assert result["build_distribution"]
    assert result["online"]
    assert result["exact_image"]


def test_core_change_gets_light_validation_without_exhaustive_matrix() -> None:
    result = route("freqtrade/configuration/configuration.py")
    assert result["core_light"]
    assert not result["core_matrix"]
    assert not result["portal_backend_tests"]


def test_critical_core_change_selects_compatibility_and_online() -> None:
    result = route("freqtrade/exchange/exchange.py")
    assert result["core_light"]
    assert result["core_matrix"]
    assert result["compatibility_sweep"]
    assert result["online"]
    assert result["high_risk"]
    assert not result["full"]
    assert not result["portal_backend_tests"]
    assert not result["exact_image"]


def test_strategy_engine_change_selects_strategy_and_closure() -> None:
    result = route("ai_strategy_engine/service.py")
    assert result["strategy_engine"]
    assert result["closure_e2e"]


def test_docker_runtime_change_selects_deployment_and_exact_image() -> None:
    result = route("deploy/synology/portal-oidc/Dockerfile.control-plane")
    assert result["deployment"]
    assert result["docker_runtime"]
    assert result["exact_image"]
    assert result["high_risk"]
    assert not result["full"]


def test_explicit_full_label_selects_all_heavy_acceptance_gates() -> None:
    result = route("docs/README.md", labels=("ci:full",))
    assert result["full"]
    assert result["core_matrix"]
    assert result["closure_e2e"]
    assert result["portal_completeness_audit"]
    assert result["security_analysis"]
    assert result["exact_image"]
    assert result["portal_full_browser_e2e"]
    assert result["portal_backend_tests"]
    assert result["portal_web_validation"]


def test_ready_for_review_preserves_changed_path_routing() -> None:
    result = route("docs/agents/PROMPTING_STANDARD.md", action="ready_for_review")
    assert result["docs_only"]
    assert not result["full"]
    assert not result["core_matrix"]
    assert not result["portal_full_browser_e2e"]


def test_develop_push_preserves_path_routing_but_release_is_full() -> None:
    push = classify(
        ["docs/agents/PROMPTING_STANDARD.md"],
        event="push",
        ref_name="develop",
        config=CONFIG,
    )["outputs"]
    release = classify([], event="release", config=CONFIG)["outputs"]
    assert push["docs_only"] and not push["full"]
    assert release["full"]


def test_ci_architecture_change_runs_every_routing_acceptance_tier() -> None:
    result = route("tools/ci/change_classifier.py")
    assert result["ci_architecture"]
    assert result["full"]
    assert result["core_matrix"]
    assert result["exact_image"]
    assert result["portal_full_browser_e2e"]
    assert result["portal_completeness_audit"]


def test_unknown_path_falls_back_to_core_validation() -> None:
    result = route("novel_component/file.xyz")
    assert result["core"] and result["core_light"]


def test_machine_readable_result_is_json_serializable() -> None:
    result = classify(
        ["ai_platform/portal/web/app/page.tsx", "ai_platform/portal/contracts/api.py"],
        config=CONFIG,
    )
    encoded = json.dumps(result, sort_keys=True)
    assert '"portal_browser_e2e": true' in encoded


def test_empty_unexpected_diff_fails_closed() -> None:
    result = classify([], event="pull_request", config=CONFIG)["outputs"]
    assert result["full"] and result["core_matrix"] and result["closure_e2e"]
    assert result["exact_image"] and result["portal_full_browser_e2e"]
    assert result["portal_backend_tests"] and result["portal_web_validation"]


def test_null_label_payload_is_accepted_by_cli_parser() -> None:
    from tools.ci.change_classifier import _labels

    assert _labels("null") == set()
