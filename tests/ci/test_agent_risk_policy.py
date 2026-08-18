from __future__ import annotations

import json
from pathlib import Path

from tools.agents.risk_policy import derive_policy, load_policy, main


POLICY_PATH = Path("docs/agents/RISK_BASED_EXECUTION_POLICY.json")
POLICY = load_policy(POLICY_PATH)
REQUIRED_RISKS = {
    "persistent_data",
    "research_integrity",
    "model_activation",
    "auth_or_secrets",
    "shared_synology_mutation",
    "deployment",
    "user_workflow_change",
    "destructive_operation",
    "real_capital",
}


def test_policy_contains_required_risk_dimensions() -> None:
    assert REQUIRED_RISKS <= set(POLICY["risk_dimensions"])


def test_low_risk_task_uses_only_baseline_gates() -> None:
    result = derive_policy([], policy=POLICY)
    assert not result["stopped"]
    assert result["escalation_gates"] == []
    assert result["required_gates"] == POLICY["baseline_gates"]
    assert "real_applicable_e2e" not in result["required_gates"]
    assert "independent_audit" not in result["required_gates"]


def test_user_workflow_change_adds_real_e2e_only_from_that_dimension() -> None:
    result = derive_policy(["user_workflow_change"], policy=POLICY)
    assert result["escalation_gates"] == ["real_applicable_e2e"]


def test_persistent_and_shared_state_risks_compose_recovery_controls() -> None:
    result = derive_policy(
        ["persistent_data", "shared_synology_mutation"],
        policy=POLICY,
    )
    gates = set(result["required_gates"])
    assert "restart_and_recovery_validation" in gates
    assert "pre_and_post_health_validation" in gates
    assert "durable_state_and_recovery_validation" in gates
    assert "independent_audit" in gates


def test_research_and_model_activation_keep_integrity_and_rollback_controls() -> None:
    result = derive_policy(["research_integrity", "model_activation"], policy=POLICY)
    gates = set(result["required_gates"])
    assert "data_provenance_validation" in gates
    assert "leakage_and_lookahead_validation" in gates
    assert "evaluation_integrity_validation" in gates
    assert "immutable_model_identity" in gates
    assert "deliberate_activation" in gates
    assert "rollback_or_reversibility" in gates


def test_security_deployment_and_governance_risks_compose_targeted_gates() -> None:
    result = derive_policy(
        ["auth_or_secrets", "deployment", "governance_or_ci"],
        policy=POLICY,
    )
    gates = set(result["required_gates"])
    assert "targeted_security_and_secret_boundary_validation" in gates
    assert "artifact_or_image_provenance" in gates
    assert "target_specific_acceptance" in gates
    assert "policy_regression" in gates
    assert "trusted_base_self_validation" in gates


def test_real_capital_is_fail_closed() -> None:
    result = derive_policy(["real_capital"], policy=POLICY)
    assert result["stopped"]
    assert result["stop_reasons"]


def test_unknown_risk_is_rejected() -> None:
    try:
        derive_policy(["imaginary_risk"], policy=POLICY)
    except ValueError as exc:
        assert "imaginary_risk" in str(exc)
    else:
        raise AssertionError("unknown risk was accepted")


def test_cli_is_machine_readable_and_real_capital_exits_nonzero(capsys) -> None:
    assert main(["--risk", "user_workflow_change"]) == 0
    normal = json.loads(capsys.readouterr().out)
    assert normal["escalation_gates"] == ["real_applicable_e2e"]

    assert main(["--risk", "real_capital"]) == 2
    stopped = json.loads(capsys.readouterr().out)
    assert stopped["stopped"] is True
