from __future__ import annotations

import argparse
import json
from pathlib import Path

from pydantic import ValidationError

from ai_platform.portal.deploy.cloudflare.schema import (
    AccessSurface,
    RateLimitFamily,
    StagingIngressPolicy,
)


REQUIRED_ACCESS_SURFACES = frozenset(AccessSurface)
REQUIRED_RATE_LIMIT_FAMILIES = frozenset(RateLimitFamily)


def load_policy(path: Path) -> StagingIngressPolicy:
    return StagingIngressPolicy.model_validate_json(path.read_text(encoding="utf-8"))


def policy_violations(policy: StagingIngressPolicy) -> tuple[str, ...]:
    violations: list[str] = []
    missing_access = REQUIRED_ACCESS_SURFACES.difference(policy.privileged_surfaces)
    if missing_access:
        violations.append(
            "missing Access protection surfaces: "
            + ", ".join(sorted(surface.value for surface in missing_access))
        )
    missing_limits = REQUIRED_RATE_LIMIT_FAMILIES.difference(policy.rate_limit_families)
    if missing_limits:
        violations.append(
            "missing WAF/rate-limit families: "
            + ", ".join(sorted(family.value for family in missing_limits))
        )
    env_refs = (
        policy.public_base_url_env,
        policy.privileged_path_env,
        policy.origin_probe_url_env,
        policy.freqtrade_probe_url_env,
        policy.access_client_id_env,
        policy.access_client_secret_env,
    )
    if len(set(env_refs)) != len(env_refs):
        violations.append("staging environment references must be distinct")
    return tuple(violations)


def validate_policy(path: Path) -> tuple[str, ...]:
    try:
        policy = load_policy(path)
    except (OSError, ValidationError) as exc:
        return (str(exc),)
    return policy_violations(policy)


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate fail-closed Cloudflare staging policy")
    parser.add_argument("policy", type=Path)
    args = parser.parse_args()
    violations = validate_policy(args.policy)
    if violations:
        print(json.dumps({"valid": False, "violations": violations}, indent=2))
        return 1
    print(json.dumps({"valid": True, "violations": []}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
