from __future__ import annotations

from datetime import UTC, datetime
from typing import cast
from uuid import UUID, uuid4

import pytest
from fastapi import Request
from fastapi.testclient import TestClient

from ai_platform.portal.contracts.common import CorrelationContext
from ai_platform.portal.contracts.environment import Environment, ExecutionMode
from ai_platform.portal.contracts.identity import ActorType, Permission
from ai_platform.portal.contracts.strategy_closure import (
    CapabilityRequirement,
    ClosureRequestContext,
    PublicContractProvenance,
    SignalWizardFeatureSelection,
    SignalWizardPreviewCommand,
    SignalWizardSubmitCommand,
    StrategyCapability,
)
from ai_platform.portal.control_plane.api import create_app
from ai_platform.portal.control_plane.context import RequestContext
from ai_platform.portal.control_plane.database import (
    build_engine,
    build_session_factory,
    create_schema,
)
from ai_platform.portal.identity.http import create_identity_enabled_app
from ai_platform.portal.identity.service import IdentityService
from ai_platform.portal.signal_wizard.service import (
    SignalWizardConflictError,
    SignalWizardNotFoundError,
    SignalWizardService,
    SignalWizardValidationError,
)


REQUEST_ID = UUID("00000000-0000-0000-0000-000000000101")
CORRELATION_ID = UUID("00000000-0000-0000-0000-000000000102")
NOW = datetime(2026, 7, 30, 20, 0, tzinfo=UTC)


class _RotatingIdentityBoundary:
    """Minimal identity boundary that creates trusted per-request identifiers."""

    def __init__(self) -> None:
        self.last_context: RequestContext | None = None

    def resolve_request(self, _request: Request) -> RequestContext:
        self.last_context = RequestContext(
            tenant_id="tenant-a",
            actor_id="analyst-1",
            actor_type=ActorType.USER,
            permissions=(Permission.MODEL_READ, Permission.MODEL_TRAIN),
            request_id=uuid4(),
            correlation_id=uuid4(),
        )
        return self.last_context

    def enforce_csrf(self, _request: Request) -> None:
        return None


def _context(tenant_id: str = "tenant-a", *, train: bool = True) -> RequestContext:
    permissions = [Permission.MODEL_READ]
    if train:
        permissions.append(Permission.MODEL_TRAIN)
    return RequestContext(
        tenant_id=tenant_id,
        actor_id="analyst-1",
        actor_type=ActorType.USER,
        permissions=tuple(permissions),
        request_id=REQUEST_ID,
        correlation_id=CORRELATION_ID,
    )


def _closure_context(tenant_id: str = "tenant-a") -> ClosureRequestContext:
    return ClosureRequestContext(
        tenant_id=tenant_id,
        actor_id="analyst-1",
        actor_type=ActorType.USER,
        resource_type="strategy",
        resource_id="strategy-1",
        environment=Environment.RESEARCH,
        execution_mode=ExecutionMode.SIMULATED,
        correlation=CorrelationContext(
            request_id=REQUEST_ID,
            correlation_id=CORRELATION_ID,
        ),
        provenance=PublicContractProvenance(
            producer="signal-wizard-test",
            artifact_id="wizard-artifact-1",
            created_at=NOW,
            source_refs=("feature-registry:1.0.0",),
        ),
    )


def _capability(value: StrategyCapability) -> CapabilityRequirement:
    return CapabilityRequirement(
        capability=value,
        authorization_decision_ref=f"decision:{value.value}",
    )


def _preview_command(
    *,
    tenant_id: str = "tenant-a",
    idempotency_key: str = "preview-1",
    feature_id: str = "atr.v1",
) -> SignalWizardPreviewCommand:
    parameters = {"period": 14} if feature_id == "atr.v1" else {}
    return SignalWizardPreviewCommand(
        context=_closure_context(tenant_id),
        idempotency_key=idempotency_key,
        strategy_id="strategy-1",
        feature_selections=(
            SignalWizardFeatureSelection(
                feature_id=feature_id,
                timeframe="5m",
                parameters=parameters,
            ),
        ),
        condition_ast={"all": [{"feature": feature_id, "op": "gt", "value": 0}]},
        capability=_capability(StrategyCapability.STRATEGY_RESEARCH),
    )


def _service() -> SignalWizardService:
    engine = build_engine("sqlite+pysqlite:///:memory:")
    create_schema(engine)
    return SignalWizardService(build_session_factory(engine))


def test_preview_is_durable_canonical_and_idempotent() -> None:
    service = _service()
    context = _context()
    command = _preview_command()

    first = service.preview(context, command)
    second = service.preview(context, command)

    assert second == first
    assert first.strategy_definition["schema_version"] == "2.0.0"
    assert first.strategy_definition["features"][0]["id"] == "atr.v1"
    assert first.strategy_definition["features"][0]["params"] == {
        "period": 14,
        "ma_type": "rma",
    }
    assert first.strategy_definition["execution"]["execution_authority"] is False
    assert first.execution_authority is False
    assert first.promotion_authority is False
    assert len(first.preview_hash) == 64


def test_preview_rejects_idempotency_conflict_and_unapproved_feature() -> None:
    service = _service()
    context = _context()
    service.preview(context, _preview_command())

    changed = SignalWizardPreviewCommand.model_validate(
        {
            **_preview_command().model_dump(mode="python"),
            "strategy_id": "strategy-2",
        }
    )
    with pytest.raises(SignalWizardConflictError, match="idempotency"):
        service.preview(context, changed)

    with pytest.raises(SignalWizardValidationError) as rejected:
        service.preview(
            context,
            _preview_command(idempotency_key="preview-2", feature_id="squeeze_ratio.v1"),
        )
    assert rejected.value.reason_code == "FEATURE_NOT_APPROVED_FOR_AI"


def test_submit_persists_preview_derived_experiment_intent() -> None:
    service = _service()
    context = _context()
    preview = service.preview(context, _preview_command())
    strategy_version = str(preview.strategy_definition["version"])
    command = SignalWizardSubmitCommand(
        context=_closure_context(),
        idempotency_key="submit-1",
        preview_hash=preview.preview_hash,
        experiment_name="ATR research candidate",
        expected_strategy_version=strategy_version,
        capability=_capability(StrategyCapability.EXPERIMENT_SUBMIT),
    )

    first = service.submit(context, command)
    second = service.submit(context, command)

    assert second == first
    assert first.accepted is True
    assert "SIGNAL_WIZARD_CANDIDATE_PERSISTED" in first.reason_codes
    assert first.execution_authority is False
    assert first.promotion_authority is False


def test_submit_is_tenant_scoped_and_version_bound() -> None:
    service = _service()
    preview = service.preview(_context(), _preview_command())
    wrong_tenant = SignalWizardSubmitCommand(
        context=_closure_context("tenant-b"),
        idempotency_key="submit-other",
        preview_hash=preview.preview_hash,
        experiment_name="cross tenant",
        expected_strategy_version=str(preview.strategy_definition["version"]),
        capability=_capability(StrategyCapability.EXPERIMENT_SUBMIT),
    )
    with pytest.raises(SignalWizardNotFoundError):
        service.submit(_context("tenant-b"), wrong_tenant)

    wrong_version = SignalWizardSubmitCommand(
        context=_closure_context(),
        idempotency_key="submit-wrong-version",
        preview_hash=preview.preview_hash,
        experiment_name="wrong version",
        expected_strategy_version="strategy-1:other",
        capability=_capability(StrategyCapability.EXPERIMENT_SUBMIT),
    )
    with pytest.raises(SignalWizardConflictError, match="expected strategy version"):
        service.submit(_context(), wrong_version)


def test_control_plane_registers_preview_and_submit_routes() -> None:
    engine = build_engine("sqlite+pysqlite:///:memory:")
    create_schema(engine)
    factory = build_session_factory(engine)
    context = _context()
    client = TestClient(create_app(factory, lambda: context))

    preview_response = client.post(
        "/v1/signal-wizard/preview",
        json=_preview_command().model_dump(mode="json"),
    )
    assert preview_response.status_code == 200
    preview_payload = preview_response.json()

    submit = SignalWizardSubmitCommand(
        context=_closure_context(),
        idempotency_key="submit-api-1",
        preview_hash=preview_payload["preview_hash"],
        experiment_name="API candidate",
        expected_strategy_version=preview_payload["strategy_definition"]["version"],
        capability=_capability(StrategyCapability.EXPERIMENT_SUBMIT),
    )
    submit_response = client.post(
        "/v1/signal-wizard/submit",
        json=submit.model_dump(mode="json"),
    )
    assert submit_response.status_code == 201
    assert submit_response.json()["accepted"] is True


def test_identity_enabled_routes_bind_trusted_per_request_correlation() -> None:
    engine = build_engine("sqlite+pysqlite:///:memory:")
    create_schema(engine)
    factory = build_session_factory(engine)
    identity = _RotatingIdentityBoundary()
    client = TestClient(create_identity_enabled_app(factory, cast(IdentityService, identity)))

    preview_response = client.post(
        "/v1/signal-wizard/preview",
        json=_preview_command(idempotency_key="preview-identity").model_dump(mode="json"),
    )
    assert preview_response.status_code == 200
    assert identity.last_context is not None
    preview_context = identity.last_context
    preview_payload = preview_response.json()
    assert preview_payload["context"]["correlation"] == (
        preview_context.correlation_context().model_dump(mode="json")
    )
    assert preview_payload["context"]["correlation"]["request_id"] != str(REQUEST_ID)

    submit = SignalWizardSubmitCommand(
        context=_closure_context(),
        idempotency_key="submit-identity",
        preview_hash=preview_payload["preview_hash"],
        experiment_name="Identity-enabled candidate",
        expected_strategy_version=preview_payload["strategy_definition"]["version"],
        capability=_capability(StrategyCapability.EXPERIMENT_SUBMIT),
    )
    submit_response = client.post(
        "/v1/signal-wizard/submit",
        json=submit.model_dump(mode="json"),
    )
    assert submit_response.status_code == 201
    assert identity.last_context is not None
    submit_context = identity.last_context
    assert submit_context.request_id != preview_context.request_id
    assert submit_response.json()["context"]["correlation"] == (
        submit_context.correlation_context().model_dump(mode="json")
    )
