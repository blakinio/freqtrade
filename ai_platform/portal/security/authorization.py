from __future__ import annotations

from collections.abc import Iterable

from ai_platform.portal.contracts.common import NonEmptyStr
from ai_platform.portal.contracts.identity import Permission, Role, RoleName


class PermissionDeniedError(PermissionError):
    pass


_BUILTIN_ROLE_PERMISSIONS: dict[RoleName, frozenset[Permission]] = {
    RoleName.USER: frozenset({Permission.BOT_READ, Permission.MODEL_READ}),
    RoleName.TRADER: frozenset(
        {
            Permission.BOT_READ,
            Permission.BOT_CREATE,
            Permission.BOT_START,
            Permission.BOT_PAUSE,
            Permission.BOT_STOP,
            Permission.TRADE_MANUAL_EXECUTE,
            Permission.MODEL_READ,
        }
    ),
    RoleName.ANALYST: frozenset(
        {
            Permission.BOT_READ,
            Permission.MODEL_READ,
            Permission.MODEL_TRAIN,
            Permission.AUDIT_READ,
        }
    ),
    RoleName.MODEL_REVIEWER: frozenset(
        {
            Permission.BOT_READ,
            Permission.MODEL_READ,
            Permission.MODEL_PROMOTE,
            Permission.AUDIT_READ,
        }
    ),
    RoleName.ADMIN: frozenset(Permission),
    RoleName.SERVICE: frozenset({Permission.BOT_READ}),
}


def builtin_role(tenant_id: NonEmptyStr, role_name: RoleName) -> Role:
    return Role(
        role_id=f"builtin:{role_name.value}",
        tenant_id=tenant_id,
        name=role_name,
        permissions=_BUILTIN_ROLE_PERMISSIONS[role_name],
    )


def permissions_for_roles(role_names: Iterable[RoleName | str]) -> frozenset[Permission]:
    granted: set[Permission] = set()
    for role_name in role_names:
        try:
            parsed = role_name if isinstance(role_name, RoleName) else RoleName(role_name)
        except ValueError:
            continue
        granted.update(_BUILTIN_ROLE_PERMISSIONS.get(parsed, frozenset()))
    return frozenset(granted)


def has_permission(granted: Iterable[Permission | str], required: Permission | str) -> bool:
    try:
        required_permission = required if isinstance(required, Permission) else Permission(required)
    except ValueError:
        return False

    parsed_grants: set[Permission] = set()
    for item in granted:
        try:
            parsed_grants.add(item if isinstance(item, Permission) else Permission(item))
        except ValueError:
            continue
    return required_permission in parsed_grants


def require_permission(granted: Iterable[Permission | str], required: Permission | str) -> None:
    if not has_permission(granted, required):
        raise PermissionDeniedError(f"permission denied: {required}")
