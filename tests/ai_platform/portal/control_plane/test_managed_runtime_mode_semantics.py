from __future__ import annotations

from datetime import UTC, datetime
from types import SimpleNamespace
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import func, select

from ai_platform.portal.contracts.bots import (
    BotConfigRevision,
    BotConfigRevisionState,
    BotSpec,
)
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
from ai_platform.portal.control_plane.models import (
    BotRolloutRow,
    BotRow,
    RuntimeGenerationRow,
)
from ai_platform.portal.control_plane.repository import BotRepository
from ai_platform.portal.control_plane.service import (
    ControlPlaneConflictError,
    ControlPlaneService,
)
from ai_platform.wickhunter.contracts import BotMode
from ai_platform.wickhunter.runtime_mode import (
    ManagedRuntimeModeRequest,
    RuntimeModeRejectionReason,
    RuntimeModeResolutionError,
    resolve_managed_runtime_mode,
)


NOW = datetime(2026, 8, 9, 8, 30, tzinfo=UTC)


@pytest.fixture
def session_factory() -> SessionFactory:
    engine = build_engine("sqlite+pysqlite:///:memory:")
    create_schema(engine)
    return build_session_factory(engine)


def _context() -> RequestContext:
    return RequestContext(
        tenant_id="tenant-a",
        actor_id="actor-a",
        actor_type=ActorType.USER,
        permissions=(Permission.BOT_CREATE, Permission.BOT_READ, Permission.BOT_START),
        request_id=uuid4(),
        correlation_id=uuid4(),
        causation_id=uuid4(),
    )


def _spec(revision: int = 1, mode: BotMode = BotMode.SHADOW) -> BotSpec:
    return BotSpec(
        tenant_id="tenant-a",
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
        isolation_plan_digest="9" * 64,
        gateway_artifact_digest="a" * 64,
        gateway_contract_version="gateway-v1",
        gateway_contract_digest="b" * 64,
        market_data_egress_policy_version="market-egress-v1",
        market_data_egress_policy_digest="c" * 64,
    )


def _material_without_paper(*_args: object) -> RuntimeGenerationMaterial:
    return _base_material()


def _material_with_paper(
    _context: RequestContext,
    revision: BotConfigRevision,
) -> RuntimeGenerationMaterial:
    material = _base_material()
    if revision.managed_mode is not BotMode.PAPER:
        return material
    return material.model_copy(
        update={
            "paper_activation_authorized": True,
            "paper_authorization_id": "paper-auth-1",
            "paper_authorization_digest": "7" * 64,
            "paper_candidate_package_id": "candidate-package-1",
            "paper_candidate_manifest_sha256": "8" * 64,
        }
    )


def _service(
    session_factory: SessionFactory,
    resolver=_material_without_paper,
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


def _activation_counts(session_factory: SessionFactory) -> tuple[int, int]:
    with session_factory() as session:
        generations = session.scalar(select(func.count()).select_from(RuntimeGenerationRow))
        rollouts = session.scalar(select(func.count()).select_from(BotRolloutRow))
    return int(generations or 0), int(rollouts or 0)


def test_shadow_generation_binds_mode_identity_and_persists(
    session_factory: SessionFactory,
) -> None:
    context = _context()
    service = _service(session_factory)
    _, revision = _create_promoted(service, context, _spec())

    bot, generation, _ = service.apply_revision(
        context,
        "bot-1",
        revision.revision_id,
        2,
        "apply-shadow",
    )

    assert generation.managed_mode is BotMode.SHADOW
    assert generation.paper_authorization_digest is None
    assert len(generation.managed_mode_request_digest) == 64
    assert len(generation.managed_mode_resolution_digest) == 64
    assert generation.isolation_plan_digest == "9" * 64
    assert generation.gateway_artifact_digest == "a" * 64
    assert generation.gateway_contract_digest == "b" * 64
    assert generation.market_data_egress_policy_version == "market-egress-v1"
    assert generation.market_data_egress_policy_digest == "c" * 64
    assert bot.desired_runtime_generation_id == generation.generation_id
    assert bot.observed_runtime_generation_id is None
    with session_factory() as session:
        stored = BotRepository().get_runtime_generation(
            session,
            context.tenant_id,
            generation.generation_id,
        )
    assert stored == generation


def test_save_paper_does_not_roll_out_and_apply_preserves_observed_until_reconciliation(
    session_factory: SessionFactory,
) -> None:
    context = _context()
    service = _service(session_factory, _material_with_paper)
    _, r1 = _create_promoted(service, context, _spec())
    _, shadow, _ = service.apply_revision(
        context,
        "bot-1",
        r1.revision_id,
        2,
        "apply-r1",
    )

    # Simulate an earlier authoritative reconciliation of the SHADOW generation.
    with session_factory() as session, session.begin():
        row = session.get(BotRow, (context.tenant_id, "bot-1"))
        assert row is not None
        row.observed_runtime_generation_id = shadow.generation_id

    revised = service.revise_bot(context, "bot-1", _spec(2, BotMode.PAPER))
    assert revised.spec.managed_mode is BotMode.PAPER
    assert revised.desired_runtime_generation_id == shadow.generation_id
    assert revised.observed_runtime_generation_id == shadow.generation_id
    assert revised.latest_authored_revision_id is not None

    r2 = service.promote_revision(
        context,
        "bot-1",
        revised.latest_authored_revision_id,
        revised.state_version,
    )
    updated, paper, _ = service.apply_revision(
        context,
        "bot-1",
        r2.revision_id,
        5,
        "apply-r2",
    )

    assert paper.managed_mode is BotMode.PAPER
    assert paper.paper_authorization_digest == "7" * 64
    assert paper.managed_mode_request_digest != shadow.managed_mode_request_digest
    assert paper.managed_mode_resolution_digest != shadow.managed_mode_resolution_digest
    assert paper.generation_spec_digest != shadow.generation_spec_digest
    assert updated.desired_runtime_generation_id == paper.generation_id
    assert updated.observed_runtime_generation_id == shadow.generation_id

    repository = BotRepository()
    with session_factory() as session:
        desired = repository.get_runtime_generation(
            session,
            context.tenant_id,
            paper.generation_id,
        )
        observed = repository.get_runtime_generation(
            session,
            context.tenant_id,
            shadow.generation_id,
        )
    assert desired is not None and desired.managed_mode is BotMode.PAPER
    assert observed is not None and observed.managed_mode is BotMode.SHADOW


def test_live_mode_is_rejected_before_authored_persistence(
    session_factory: SessionFactory,
) -> None:
    context = _context()
    service = _service(session_factory)

    with pytest.raises(ValueError, match="LIVE managed mode is reserved"):
        service.create_bot(
            context,
            "bot-1",
            "Blocked LIVE bot",
            _spec(mode=BotMode.LIVE_BLOCKED),
        )

    assert service.list_bots(context) == ()
    assert _activation_counts(session_factory) == (0, 0)

    client = TestClient(create_app(session_factory, lambda: context))
    payload = _spec().model_dump(mode="json")
    payload["managed_mode"] = BotMode.LIVE_BLOCKED.value
    response = client.post(
        "/v1/bots",
        json={"bot_id": "bot-1", "name": "Blocked LIVE bot", "spec": payload},
    )

    assert response.status_code == 422
    assert "LIVE managed mode is reserved" in str(response.json()["detail"])
    assert service.list_bots(context) == ()


def test_live_mode_is_rejected_on_revision_and_legacy_promotion(
    session_factory: SessionFactory,
) -> None:
    context = _context()
    service = _service(session_factory)
    created = service.create_bot(context, "bot-1", "Managed bot", _spec())

    with pytest.raises(ValueError, match="LIVE managed mode is reserved"):
        service.revise_bot(context, "bot-1", _spec(2, BotMode.LIVE_BLOCKED))
    assert service.get_bot(context, "bot-1").state_version == created.state_version

    repository = BotRepository()
    with session_factory() as session, session.begin():
        initial = repository.get_revision_by_id(
            session,
            context.tenant_id,
            "bot-1",
            created.latest_authored_revision_id or "",
        )
        assert initial is not None
        legacy_live = initial.model_copy(
            update={
                "revision_id": "legacy-live-revision",
                "revision": 2,
                "managed_mode": BotMode.LIVE_BLOCKED,
                "state": BotConfigRevisionState.DRAFT,
                "revision_content_digest": None,
            }
        )
        repository.add_revision(session, legacy_live)

    with pytest.raises(ControlPlaneConflictError, match="LIVE managed mode is reserved"):
        service.promote_revision(
            context,
            "bot-1",
            "legacy-live-revision",
            created.state_version,
        )

    with session_factory() as session:
        stored = repository.get_revision_by_id(
            session,
            context.tenant_id,
            "bot-1",
            "legacy-live-revision",
        )
    assert stored is not None and stored.state is BotConfigRevisionState.DRAFT
    assert service.get_bot(context, "bot-1").state_version == created.state_version
    assert _activation_counts(session_factory) == (0, 0)


def test_runtime_resolver_keeps_reserved_live_mode_fail_closed() -> None:
    with pytest.raises(RuntimeModeResolutionError) as caught:
        resolve_managed_runtime_mode(ManagedRuntimeModeRequest(mode=BotMode.LIVE_BLOCKED))

    assert caught.value.reason is RuntimeModeRejectionReason.LIVE_CAPITAL_NOT_AUTHORIZED


@pytest.mark.parametrize(
    ("mode", "reason"),
    [
        (BotMode.PAPER, RuntimeModeRejectionReason.PAPER_ELIGIBILITY_REQUIRED),
        (BotMode.RESEARCH, RuntimeModeRejectionReason.RESEARCH_MODE_NOT_MANAGED_RUNTIME),
    ],
)
def test_unresolved_modes_fail_closed_without_durable_activation(
    session_factory: SessionFactory,
    mode: BotMode,
    reason: RuntimeModeRejectionReason,
) -> None:
    context = _context()
    service = _service(session_factory)
    _, revision = _create_promoted(service, context, _spec(mode=mode))

    with pytest.raises(RuntimeModeResolutionError) as caught:
        service.apply_revision(
            context,
            "bot-1",
            revision.revision_id,
            2,
            f"apply-{mode.value}",
        )

    assert caught.value.reason is reason
    assert service.get_bot(context, "bot-1").desired_runtime_generation_id is None
    assert _activation_counts(session_factory) == (0, 0)


def test_denied_and_malformed_paper_evidence_have_stable_fail_closed_reasons(
    session_factory: SessionFactory,
) -> None:
    context = _context()

    def denied(
        _context: RequestContext,
        _revision: BotConfigRevision,
    ) -> RuntimeGenerationMaterial:
        return _base_material().model_copy(
            update={
                "paper_activation_authorized": False,
                "paper_authorization_id": "paper-auth-1",
                "paper_authorization_digest": "7" * 64,
                "paper_candidate_package_id": "candidate-package-1",
                "paper_candidate_manifest_sha256": "8" * 64,
            }
        )

    denied_service = _service(session_factory, denied)
    _, revision = _create_promoted(
        denied_service,
        context,
        _spec(mode=BotMode.PAPER),
    )
    with pytest.raises(RuntimeModeResolutionError) as denied_error:
        denied_service.apply_revision(
            context,
            "bot-1",
            revision.revision_id,
            2,
            "paper-denied",
        )
    assert denied_error.value.reason is RuntimeModeRejectionReason.PAPER_NOT_AUTHORIZED
    assert _activation_counts(session_factory) == (0, 0)

    engine = build_engine("sqlite+pysqlite:///:memory:")
    create_schema(engine)
    malformed_factory = build_session_factory(engine)

    def malformed(_context: RequestContext, _revision: BotConfigRevision):
        payload = _base_material().model_dump(mode="python")
        payload.update(
            paper_activation_authorized=True,
            paper_authorization_id="paper-auth-1",
            paper_authorization_digest="not-a-sha256",
            paper_candidate_package_id="candidate-package-1",
            paper_candidate_manifest_sha256="8" * 64,
        )
        return SimpleNamespace(**payload)

    malformed_service = _service(malformed_factory, malformed)
    _, malformed_revision = _create_promoted(
        malformed_service,
        context,
        _spec(mode=BotMode.PAPER),
    )
    with pytest.raises(RuntimeModeResolutionError) as malformed_error:
        malformed_service.apply_revision(
            context,
            "bot-1",
            malformed_revision.revision_id,
            2,
            "paper-malformed",
        )
    assert malformed_error.value.reason is RuntimeModeRejectionReason.PAPER_ELIGIBILITY_INVALID
    assert _activation_counts(malformed_factory) == (0, 0)


def test_rollback_and_restart_resolve_mode_from_target_revision(
    session_factory: SessionFactory,
) -> None:
    context = _context()
    service = _service(session_factory, _material_with_paper)
    _, r1 = _create_promoted(service, context, _spec())
    _, g1, _ = service.apply_revision(
        context,
        "bot-1",
        r1.revision_id,
        2,
        "apply-r1",
    )

    revised = service.revise_bot(context, "bot-1", _spec(2, BotMode.PAPER))
    assert revised.latest_authored_revision_id is not None
    r2 = service.promote_revision(
        context,
        "bot-1",
        revised.latest_authored_revision_id,
        revised.state_version,
    )
    _, g2, _ = service.apply_revision(
        context,
        "bot-1",
        r2.revision_id,
        5,
        "apply-r2",
    )
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

    assert [generation.managed_mode for generation in (g1, g2, g3, g4)] == [
        BotMode.SHADOW,
        BotMode.PAPER,
        BotMode.SHADOW,
        BotMode.PAPER,
    ]
    assert [generation.generation_ordinal for generation in (g1, g2, g3, g4)] == [
        1,
        2,
        3,
        4,
    ]
    assert restarted.desired_runtime_generation_id == g4.generation_id


def test_api_rejects_client_paper_authorization_and_reports_server_reason(
    session_factory: SessionFactory,
) -> None:
    context = _context()
    client = TestClient(
        create_app(
            session_factory,
            lambda: context,
            generation_material_resolver=_material_without_paper,
        )
    )
    created = client.post(
        "/v1/bots",
        json={
            "bot_id": "bot-1",
            "name": "Paper bot",
            "spec": _spec(mode=BotMode.PAPER).model_dump(mode="json"),
        },
    )
    assert created.status_code == 201
    revision_id = created.json()["latest_authored_revision_id"]
    promoted = client.post(
        f"/v1/bots/bot-1/revisions/{revision_id}/promote",
        json={"expected_state_version": 1},
    )
    assert promoted.status_code == 200

    client_claim = client.post(
        "/v1/bots/bot-1/apply",
        json={
            "revision_id": revision_id,
            "expected_state_version": 2,
            "idempotency_key": "client-claim",
            "paper_activation_authorized": True,
            "paper_authorization_digest": "7" * 64,
        },
    )
    assert client_claim.status_code == 422

    server_check = client.post(
        "/v1/bots/bot-1/apply",
        json={
            "revision_id": revision_id,
            "expected_state_version": 2,
            "idempotency_key": "server-check",
        },
    )
    assert server_check.status_code == 409
    assert (
        server_check.json()["detail"] == RuntimeModeRejectionReason.PAPER_ELIGIBILITY_REQUIRED.value
    )
    assert _activation_counts(session_factory) == (0, 0)
