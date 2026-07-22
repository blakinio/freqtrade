from __future__ import annotations

import pytest

from ai_platform.portal.contracts import (
    Environment,
    EnvironmentContext,
    ExecutionMode,
    Permission,
    RoleName,
    SecretKind,
    SecretRef,
    WorkloadPlane,
)
from ai_platform.portal.security import (
    PermissionDeniedError,
    SecretAccessDeniedError,
    builtin_role,
    can_access_secret,
    has_permission,
    permissions_for_roles,
    require_permission,
    require_secret_access,
)


def _secret(environment: Environment, tenant_id: str = "tenant-1") -> SecretRef:
    return SecretRef(
        provider="vault",
        reference_id="ref-1",
        version="1",
        environment=environment,
        tenant_id=tenant_id,
        kind=SecretKind.EXCHANGE_CREDENTIAL,
    )


def _context(
    environment: Environment,
    plane: WorkloadPlane,
    tenant_id: str = "tenant-1",
) -> EnvironmentContext:
    return EnvironmentContext(
        tenant_id=tenant_id,
        environment=environment,
        workload_plane=plane,
        execution_mode=ExecutionMode.DRY_RUN,
    )


def test_required_base_roles_are_defined() -> None:
    assert {role.value for role in RoleName} == {
        "user",
        "trader",
        "analyst",
        "model_reviewer",
        "admin",
        "service",
    }


def test_permission_model_contains_required_vocabulary() -> None:
    assert {permission.value for permission in Permission} == {
        "bot.read",
        "bot.create",
        "bot.start",
        "bot.pause",
        "bot.stop",
        "trade.manual_execute",
        "exchange.manage",
        "model.read",
        "model.train",
        "model.promote",
        "risk.manage",
        "audit.read",
        "admin.manage",
    }


def test_missing_and_unknown_permissions_fail_closed() -> None:
    assert not has_permission([], Permission.BOT_START)
    assert not has_permission([Permission.BOT_READ], "permission.unknown")
    assert not has_permission(["permission.unknown"], Permission.BOT_READ)

    with pytest.raises(PermissionDeniedError):
        require_permission([Permission.BOT_READ], Permission.BOT_START)


def test_role_resolution_ignores_unknown_roles_instead_of_granting_access() -> None:
    permissions = permissions_for_roles([RoleName.USER, "role.unknown"])

    assert Permission.BOT_READ in permissions
    assert Permission.BOT_START not in permissions


def test_builtin_admin_role_has_all_known_permissions() -> None:
    role = builtin_role("tenant-1", RoleName.ADMIN)

    assert set(role.permissions) == set(Permission)
    assert role.canonical_json() == role.canonical_json()


def test_research_plane_cannot_access_production_secret() -> None:
    context = _context(Environment.PRODUCTION, WorkloadPlane.RESEARCH)
    secret_ref = _secret(Environment.PRODUCTION)

    assert not can_access_secret(context, secret_ref)
    with pytest.raises(SecretAccessDeniedError):
        require_secret_access(context, secret_ref)


def test_training_plane_cannot_access_production_secret() -> None:
    context = _context(Environment.PRODUCTION, WorkloadPlane.MODEL_TRAINING)
    secret_ref = _secret(Environment.PRODUCTION)

    assert not can_access_secret(context, secret_ref)


def test_e2e_plane_cannot_access_production_secret() -> None:
    context = _context(Environment.PRODUCTION, WorkloadPlane.TEST_E2E)
    secret_ref = _secret(Environment.PRODUCTION)

    assert not can_access_secret(context, secret_ref)


def test_secret_access_requires_exact_tenant_and_environment() -> None:
    secret_ref = _secret(Environment.STAGING)

    assert not can_access_secret(
        _context(Environment.STAGING, WorkloadPlane.EXECUTION, tenant_id="tenant-2"),
        secret_ref,
    )
    assert not can_access_secret(
        _context(Environment.TEST, WorkloadPlane.EXECUTION),
        secret_ref,
    )
    assert can_access_secret(
        _context(Environment.STAGING, WorkloadPlane.EXECUTION),
        secret_ref,
    )


def test_execution_modes_do_not_contain_live_capital_mode() -> None:
    assert {mode.value for mode in ExecutionMode} == {"simulated", "dry_run"}


def test_environment_contract_is_explicit_and_closed() -> None:
    assert {environment.value for environment in Environment} == {
        "research",
        "test",
        "staging",
        "production",
    }
