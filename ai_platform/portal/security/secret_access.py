from __future__ import annotations

from ai_platform.portal.contracts.environment import Environment, EnvironmentContext, WorkloadPlane
from ai_platform.portal.contracts.secret_refs import SecretRef


class SecretAccessDeniedError(PermissionError):
    pass


_PRODUCTION_SECRET_DENIED_PLANES = frozenset(
    {
        WorkloadPlane.RESEARCH,
        WorkloadPlane.MODEL_TRAINING,
        WorkloadPlane.TEST_E2E,
    }
)


def can_access_secret(context: EnvironmentContext, secret_ref: SecretRef) -> bool:
    if context.tenant_id != secret_ref.tenant_id:
        return False
    if context.environment != secret_ref.environment:
        return False
    if (
        secret_ref.environment is Environment.PRODUCTION
        and context.workload_plane in _PRODUCTION_SECRET_DENIED_PLANES
    ):
        return False
    return True


def require_secret_access(context: EnvironmentContext, secret_ref: SecretRef) -> None:
    if not can_access_secret(context, secret_ref):
        raise SecretAccessDeniedError(
            "secret access denied by tenant, environment, or workload-plane boundary"
        )
