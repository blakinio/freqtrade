from pathlib import Path

import pytest
from pydantic import ValidationError

from ai_platform.portal.deploy.cloudflare.policy import load_policy, policy_violations
from ai_platform.portal.deploy.cloudflare.schema import StagingIngressPolicy


POLICY = Path("ai_platform/portal/deploy/cloudflare/staging-policy.example.json")


def test_example_policy_is_fail_closed_and_complete() -> None:
    policy = load_policy(POLICY)

    assert policy.tunnel_required is True
    assert policy.origin_public_ingress_allowed is False
    assert policy.freqtrade_public_ingress_allowed is False
    assert policy.execution_mode == "simulated"
    assert policy.managed_waf_enabled is True
    assert policy_violations(policy) == ()


def test_policy_cannot_enable_public_origin_or_live_execution() -> None:
    payload = load_policy(POLICY).model_dump(mode="json")
    payload["origin_public_ingress_allowed"] = True

    with pytest.raises(ValidationError):
        StagingIngressPolicy.model_validate(payload)

    payload = load_policy(POLICY).model_dump(mode="json")
    payload["execution_mode"] = "live"
    with pytest.raises(ValidationError):
        StagingIngressPolicy.model_validate(payload)


def test_policy_rejects_secret_values_instead_of_env_references() -> None:
    payload = load_policy(POLICY).model_dump(mode="json")
    payload["access_client_secret_env"] = "actual-secret-value"

    with pytest.raises(ValidationError):
        StagingIngressPolicy.model_validate(payload)


def test_policy_requires_all_access_and_rate_limit_families() -> None:
    policy = load_policy(POLICY)
    payload = policy.model_dump(mode="json")
    payload["privileged_surfaces"] = ["admin"]
    payload["rate_limit_families"] = ["authentication"]

    violations = policy_violations(StagingIngressPolicy.model_validate(payload))

    assert any(item.startswith("missing Access protection surfaces:") for item in violations)
    assert any(item.startswith("missing WAF/rate-limit families:") for item in violations)
