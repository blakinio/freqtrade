from __future__ import annotations

from datetime import UTC, datetime
from types import SimpleNamespace
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import func, select

from ai_platform.portal.contracts.bots import BotSpec
from ai_platform.portal.contracts.environment import Environment, ExecutionMode
from ai_platform.portal.contracts.identity import ActorType, Permission
from ai_platform.portal.contracts.runtime_generation import RuntimeGenerationMaterial
from ai_platform.portal.control_plane.api import create_app
from ai_platform.portal.control_plane.context import RequestContext
from ai_platform.portal.control_plane.database import (
    SessionFactory,
    build_engine,
    build_session_factory,
    create_schema,
)
from ai_platform.portal.control_plane.models import BotRolloutRow, BotRow, RuntimeGenerationRow
from ai_platform.portal.control_plane.repository import BotRepository
from ai_platform.portal.control_plane.service import ControlPlaneService
from ai_platform.wickhunter.contracts import BotMode
from ai_platform.wickhunter.runtime_mode import (
    RuntimeModeRejectionReason,
    RuntimeModeResolutionError,
)


NOW = datetime(2026, 8, 9, 8, 30, tzinfo=UTC)


@pytest.fixture
def session_factory() -> SessionFactory:
    engine = build_engine("sqlite+pysqlite:///:memory:")
    create_schema(engine)
    return build_session_factory(engine)


def _context(tenant_id: str = "tenant-a") -> RequestContext:
    return RequestContext(
        tenant_id=tenant_id,
        actor_id=f"actor-{tenant_id}",
        actor_type=ActorType.USER,
        permissions=(Permission.BOT_CREATE, Permission.BOT_READ, Permission.BOT_START),
        request_id=uuid4(),
        correlation_id=uuid4(),
        causation_id=uuid4(),
    )


def _spec(
    tenant_id: str,
    *,
    revision: int = 1,
    mode: BotMode = BotMode.SHADOW,
) -> BotSpec:
    return BotSpec(
        tenant_id=tenant_id,
        strategy_version="strategy-v1",
        model_version="model-v1",
        risk_policy_version="risk-v1",
        exchange_connection_ref="exchange-connection-1",
        pair_universe=("BTC/USDT",),
        timeframe="5m",
        capital_allocation="1000",
        capital_currency="USDT",
        runtime_version="freqtrade-2026.7",
        config_revision=revision,
        environment=Environment.TEST,
        execution_mode=ExecutionMode.DRY_RUN,
        managed_mode=mode,
    )


def _base_material() -> RuntimeGenerationMaterial:
    return RuntimeGenerationMaterial(
        normalized_runtime_config_digest="1" * 64,
        runtime_image_digest="2" * 64,
        strategy_artifact_digest="3" * 64,
        model_artifact_digest="4" * 64,
        feature_schema_version="features-v1",
        risk_policy_digest="5" * 64,
        exchange_mode="dry-run-public-market-data",
        exchange_connection_revision="exchange-revision-1",
        isolation_profile_version="isolation-v1",
        isolation_profile_digest="6" * 64,
        gateway_contract_version="gateway-v1",
    )


def _authorized_material(*_args: object) -> RuntimeGenerationMaterial:
    return _base_material().model_copy(
        update={
            "paper_activation_authorized": True,
            "paper_authorization_id": "paper-auth-1",
            "paper_authorization_digest": "7" * 64,
            "paper_candidate_package_id": "candidate-package-1",
            "paper_candidate_manifest_sha256": "8" * 64,
        }
    )


def _base_material_resolver(*_args: object) -> RuntimeGenerationMaterial:
    return _base_material()


def _service(
    session_factory: SessionFactory,
    resolver=_base_material_resolver,
) -> ControlPlaneService:
    return ControlPlaneService(
        session_factory,
        clock=lambda: NOW,
        generation_material_resolver=resolver,
    )


def _create_promoted(
    service: ControlPlaneService,
    context: RequestContext,
    spec: BotSpec,
):
    created = service.create_bot(context, "bot-1", "Managed bot", spec)
    assert created.latest_authored_revision_id is not None
    promoted = service.promote_revision(
        context,
        "bot-1",
        created.latest_authored_revision_id,
        created.state_version,
    )
    return created, promoted


def _assert_no_activation_rows(session_factory: SessionFactory) -> None:
    with session_factory() as session:
        generations = session.scalar(select(func.count()).select_from(RuntimeGenerationRow))
        rollouts = session.scalar(select(func.count()).select_from(BotRolloutRow))
    assert generations == 0
    assert rollouts == 0


def test_shadow_generation_binds_canonical_mode_identity(
    session_factory: SessionFactory,
) -> None:
    context = _context()
    service = _service(session_factory)
    _, promoted = _create_promoted(service, context, _spec(context.tenant_id))

    bot, generation, _ = service.apply_revision(
        context,
        "bot-1",
        promoted.revision_id,
        2,
        "apply-shadow",
    )

    assert generation.managed_mode is BotMode.SHADOW
    assert generation.paper_authorization_digest is None
    assert len(generation.managed_mode_request_digest) == 64
    assert len(generation.managed_mode_resolution_digest) == 64
    assert bot.desired_runtime_generation_id == generation.generation_id
    assert bot.observed_runtime_generation_id is None

    persisted = BotRepository()
    with session_factory() as session:
        stored = persisted.get_runtime_generation(
            session,
            context.tenant_id,
            generation.generation_id,
        )
    assert stored == generation


def test_saving_paper_revision_does_not_roll_out_or_change_observed_generation(
    session_factory: SessionFactory,
) -> None:
    context = _context()
    service = _service(session_factory, _authorized_material)
    _, promoted = _create_promoted(service, context, _spec(context.tenant_id))
    _, shadow_generation, _ = service.apply_revision(
        context,
        "bot-1",
        promoted.revision_id,
        2,
        "apply-shadow",
    )

    # Represent an earlier authoritative reconciliation of the SHADOW generation.
    with session_factory() as session, session.begin():
        row = session.get(BotRow, (context.tenant_id, "bot-1"))
        assert row is not None
        row.observed_runtime_generation_id = shadow_generation.generation_id

    revised = service.revise_bot(
        context,
        "bot-1",
        _spec(context.tenant_id, revision=2, mode=BotMode.PAPER),
    )

    assert revised.spec.managed_mode is BotMode.PAPER
    assert revised.desired_runtime_generation_id == shadow_generation.generation_id
    assert revised.observed_runtime_generation_id == shadow_generation.generation_id

    with session_factory() as session:
        active = BotRepository().get_runtime_generation(
            session,
            context.tenant_id,
            shadow_generation.generation_id,
        )
    assert active is not None
    assert active.managed_mode is BotMode.SHADOW


def test_authorized_paper_apply_changes_desired_mode_but_not_observed_until_reconciliation(
    session_factory: SessionFactory,
) -> None:
    context = _context()
    service = _service(session_factory, _authorized_material)
    _, r1 = _create_promoted(service, context, _spec(context.tenant_id))
    _, shadow_generation, _ = service.apply_revision(
        context,
        "bot-1",
        r1.revision_id,
        2,
        "apply-shadow",
    )

    with session_factory() as session, session.begin():
        row = session.get(BotRow, (context.tenant_id, "bot-1"))
        assert row is not None
        row.observed_runtime_generation_id = shadow_generation.generation_id

    revised = service.revise_bot(
        context,
        "bot-1",
        _spec(context.tenant_id, revision=2, mode=BotMode.PAPER),
    )
    assert revised.latest_authored_revision_id is not None
    r2 = service.promote_revision(
        context,
        "bot-1",
        revised.latest_authored_revision_id,
        revised.state_version,
    )
    updated, paper_generation, _ = service.apply_revision(
        context,
        "bot-1",
        r2.revision_id,
        5,
        "apply-paper",
    )

    assert paper_generation.managed_mode is BotMode.PAPER
    assert paper_generation.paper_authorization_digest == "7" * 64
    assert paper_generation.managed_mode_request_digest != shadow_generation.managed_mode_request_digest
    assert (
        paper_generation.managed_mode_resolution_digest
        != shadow_generation.managed_mode_resolution_digest
    )
    assert paper_generation.generation_spec_digest != shadow_generation.generation_spec_digest
    assert updated.desired_runtime_generation_id == paper_generation.generation_id
    assert updated.observed_runtime_generation_id == shadow_generation.generation_id

    repository = BotRepository()
    with session_factory() as session:
        desired = repository.get_runtime_generation(
            session,
            context.tenant_id,
            updated.desired_runtime_generation_id,
        )
        observed = repository.get_runtime_generation(
            session,
            context.tenant_id,
            updated.observed_runtime_generation_id,
        )
    assert desired is not None and desired.managed_mode is BotMode.PAPER
    assert observed is not None and observed.managed_mode is BotMode.SHADOW


@pytest.mark.parametrize(
    ("mode", "reason"),
    [
        (BotMode.PAPER, RuntimeModeRejectionReason.PAPER_ELIGIBILITY_REQUIRED),
        (BotMode.LIVE_BLOCKED, RuntimeModeRejectionReason.LIVE_CAPITAL_NOT_AUTHORIZED),
        (BotMode.RESEARCH, RuntimeModeRejectionReason.RESEARCH_MODE_NOT_MANAGED_RUNTIME),
    ],
)
def test_unresolved_managed_modes_fail_closed_without_generation_or_rollout(
    session_factory: SessionFactory,
    mode: BotMode,
    reason: RuntimeModeRejectionReason,
) -> None:
    context = _context()
    service = _service(session_factory)
    _, promoted = _create_promoted(
        service,
        context,
        _spec(context.tenant_id, mode=mode),
    )

    with pytest.raises(RuntimeModeResolutionError) as caught:
        service.apply_revision(
            context,
            "bot-1",
            promoted.revision_id,
            2,
            f"apply-{mode.value}",
        )

    assert caught.value.reason is reason
    assert service.get_bot(context, "bot-1").desired_runtime_generation_id is None
    _assert_no_activation_rows(session_factory)


def test_paper_false_authorization_and_malformed_evidence_have_stable_reasons(
    session_factory: SessionFactory,
) -> None:
    context = _context()

    def denied_material(*_args: object) -> RuntimeGenerationMaterial:
        return _base_material().model_copy(
            update={
                "paper_activation_authorized": False,
                "paper_authorization_id": "paper-auth-1",
                "paper_authorization_digest": "7" * 64,
                "paper_candidate_package_id": "candidate-package-1",
                "paper_candidate_manifest_sha256": "8" * 64,
            }
        )

    denied_service = _service(session_factory, denied_material)
    _, promoted = _create_promoted(
        denied_service,
        context,
        _spec(context.tenant_id, mode=BotMode.PAPER),
    )
    with pytest.raises(RuntimeModeResolutionError) as denied:
        denied_service.apply_revision(
            context,
            "bot-1",
            promoted.revision_id,
            2,
            "paper-denied",
        )
    assert denied.value.reason is RuntimeModeRejectionReason.PAPER_NOT_AUTHORIZED
    _assert_no_activation_rows(session_factory)

    # Use a fresh database and a deliberately malformed trusted-resolver object so the
    # producer, rather than Pydantic input validation, proves its stable fail-closed reason.
    malformed_engine = build_engine("sqlite+pysqlite:///:memory:")
    create_schema(malformed_engine)
    malformed_factory = build_session_factory(malformed_engine)

    def malformed_material(*_args: object):
        payload = _base_material().model_dump(mode="python")
        payload.update(
            paper_activation_authorized=True,
            paper_authorization_id="paper-auth-1",
            paper_authorization_digest="not-a-sha256",
            paper_candidate_package_id="candidate-package-1",
            paper_candidate_manifest_sha256="8" * 64,
        )
        return SimpleNamespace(**payload)

    malformed_service = _service(malformed_factory, malformed_material)
    _, malformed_revision = _create_promoted(
        malformed_service,
        context,
        _spec(context.tenant_id, mode=BotMode.PAPER),
    )
    with pytest.raises(RuntimeModeResolutionError) as malformed:
        malformed_service.apply_revision(
            context,
            "bot-1",
            malformed_revision.revision_id,
            2,
            "paper-malformed",
        )
    assert malformed.value.reason is RuntimeModeRejectionReason.PAPER_ELIGIBILITY_INVALID
    _assert_no_activation_rows(malformed_factory)


def test_rollback_and_restart_resolve_mode_from_target_revision(
    session_factory: SessionFactory,
) -> None:
    context = _context()
    service = _service(session_factory, _authorized_material)
    _, r1 = _create_promoted(service, context, _spec(context.tenant_id))
    _, g1, _ = service.apply_revision(context, "bot-1", r1.revision_id, 2, "apply-r1")

    revised = service.revise_bot(
        context,
        "bot-1",
        _spec(context.tenant_id, revision=2, mode=BotMode.PAPER),
    )
    assert revised.latest_authored_revision_id is not None
    r2 = service.promote_revision(
        context,
        "bot-1",
        revised.latest_authored_revision_id,
        revised.state_version,
    )
    _, g2, _ = service.apply_revision(context, "bot-1", r2.revision_id, 5, "apply-r2")

    rolled_back, g3, _ = service.rollback_to_revision(
        context,
        "bot-1",
        r1.revision_id,
        6,
        "rollback-r1",
    )
    restarted, g4, _ = service.restart_with_revision(
        context,
        "bot-1",
        r2.revision_id,
        rolled_back.state_version,
        "restart-r2",
    )

    assert [g1.managed_mode, g2.managed_mode, g3.managed_mode, g4.managed_mode] == [
        BotMode.SHADOW,
        BotMode.PAPER,
        BotMode.SHADOW,
        BotMode.PAPER,
    ]
    assert [g1.generation_ordinal, g2.generation_ordinal, g3.generation_ordinal, g4.generation_ordinal] == [
        1,
        2,
        3,
        4,
    ]
    assert restarted.desired_runtime_generation_id == g4.generation_id


def test_api_reports_stable_paper_rejection_and_never_accepts_client_authorization(
    session_factory: SessionFactory,
) -> None:
    context = _context()
    client = TestClient(
        create_app(
            session_factory,
            lambda: context,
            generation_material_resolver=_base_material_resolver,
        )
    )
    payload = {
        "bot_id": "bot-1",
        "name": "Paper bot",
        "spec": _spec(context.tenant_id, mode=BotMode.PAPER).model_dump(mode="json"),
    }
    created = client.post("/v1/bots", json=payload)
    assert created.status_code == 201
    revision_id = created.json()["latest_authored_revision_id"]
    promoted = client.post(
        f"/v1/bots/bot-1/revisions/{revision_id}/promote",
        json={"expected_state_version": 1},
    )
    assert promoted.status_code == 200

    response = client.post(
        "/v1/bots/bot-1/apply",
        json={
            "revision_id": revision_id,
            "expected_state_version": 2,
            "idempotency_key": "paper-api-rejected",
            "paper_activation_authorized": True,
            "paper_authorization_digest": "7" * 64,
        },
    )
    assert response.status_code == 422

    response = client.post(
        "/v1/bots/bot-1/apply",
        json={
            "revision_id": revision_id,
            "expected_state_version": 2,
            "idempotency_key": "paper-api-server-check",
        },
    )
    assert response.status_code == 409
    assert response.json()["detail"] == RuntimeModeRejectionReason.PAPER_ELIGIBILITY_REQUIRED.value
    _assert_no_activation_rows(session_factory)
