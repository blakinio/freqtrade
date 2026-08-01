from __future__ import annotations

import argparse
import hashlib
import json
import os
from datetime import UTC, datetime
from uuid import NAMESPACE_URL, uuid4, uuid5

from ai_platform.portal.contracts.identity import RoleName
from ai_platform.portal.control_plane.database import (
    Base,
    build_engine,
    build_session_factory,
)
from ai_platform.portal.identity.repository import IdentityRepository
from ai_platform.portal.identity.schema import IdentityAuditEvent, MembershipStatus, PrincipalStatus


def _required_environment(name: str) -> str:
    value = os.environ.get(name, "").strip()
    if not value:
        raise RuntimeError(f"required bootstrap setting is missing: {name}")
    return value


def bootstrap(args: argparse.Namespace) -> dict[str, object]:
    if not args.confirm_exact_principal:
        raise RuntimeError("exact-principal bootstrap confirmation is required")
    issuer = _required_environment("PORTAL_IDENTITY_ISSUER")
    database_url = _required_environment("PORTAL_DATABASE_URL")
    subject = args.subject.strip()
    display_name = args.display_name.strip()
    tenant_id = args.tenant_id.strip()
    if not subject or not display_name or not tenant_id:
        raise RuntimeError("subject, display name and tenant ID must be non-empty")

    engine = build_engine(database_url)
    Base.metadata.create_all(engine)
    session_factory = build_session_factory(engine)
    now = datetime.now(UTC)
    principal_id = str(uuid5(NAMESPACE_URL, f"{issuer}|{subject}"))
    membership_id = str(uuid5(NAMESPACE_URL, f"{issuer}|{subject}|{tenant_id}|membership"))

    with session_factory() as session:
        repository = IdentityRepository(session)
        principal = repository.get_principal_by_external_identity(issuer, subject)
        if principal is None:
            principal = repository.create_principal(
                principal_id=principal_id,
                issuer=issuer,
                subject=subject,
                display_name=display_name,
                email=args.email,
                now=now,
            )
        elif principal.status != PrincipalStatus.ACTIVE.value:
            raise RuntimeError("exact principal exists but is disabled")
        elif principal.principal_id != principal_id:
            raise RuntimeError("exact external identity is mapped to an unexpected principal")

        memberships = repository.list_memberships_for_principal(principal.principal_id, now)
        matching = tuple(item for item in memberships if item.tenant_id == tenant_id)
        if matching:
            membership = matching[0]
            if membership.status != MembershipStatus.ACTIVE.value:
                raise RuntimeError("exact membership exists but is disabled")
            if json.loads(membership.roles_json) != [RoleName.ADMIN.value]:
                raise RuntimeError("exact membership roles differ from the bootstrap contract")
            created = False
        else:
            membership = repository.create_membership(
                membership_id=membership_id,
                principal_id=principal.principal_id,
                tenant_id=tenant_id,
                roles=(RoleName.ADMIN,),
                valid_from=now,
                valid_until=None,
                now=now,
            )
            repository.add_audit_event(
                IdentityAuditEvent(
                    event_id=str(uuid4()),
                    action="identity.membership_bootstrapped",
                    actor_id="target-owner-bootstrap",
                    principal_id=principal.principal_id,
                    tenant_id=tenant_id,
                    membership_id=membership.membership_id,
                    result="success",
                    reason="explicit_exact_principal_bootstrap",
                    occurred_at=now,
                    correlation_id=None,
                )
            )
            created = True
        session.commit()

    return {
        "status": "success",
        "created": created,
        "principal_id": principal_id,
        "membership_id": membership_id,
        "tenant_id": tenant_id,
        "role": RoleName.ADMIN.value,
        "issuer": issuer,
        "subject_sha256": hashlib.sha256(subject.encode("utf-8")).hexdigest(),
        "secret_values_recorded": False,
        "live_capital_authorized": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--subject", required=True)
    parser.add_argument("--display-name", required=True)
    parser.add_argument("--email")
    parser.add_argument("--tenant-id", default="tenant-local")
    parser.add_argument("--confirm-exact-principal", action="store_true")
    result = bootstrap(parser.parse_args())
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
