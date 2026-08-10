from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

import pytest

from ai_platform.portal.contracts.bots import BotConfigRevision, BotSpec
from ai_platform.portal.contracts.environment import Environment, ExecutionMode
from ai_platform.portal.contracts.identity import ActorType, Permission
from ai_platform.portal.contracts.runtime_generation import (
    ReconciliationCompletenessStatus,
    ReconciliationFreshnessStatus,
    RuntimeGenerationMaterial,
    RuntimeGenerationObservation,
    RuntimeIdentityStatus,
)
from ai_platform.portal.control_plane._service_core import ControlPlaneConflictError
from ai_platform.portal.control_plane.context import RequestContext
from ai_platform.portal.control_plane.database import (
    SessionFactory,
    build_engine,
    build_session_factory,
    create_schema,
)
from ai_platform.portal.control_plane.models import BotRolloutRow, BotRow
from ai_platform.portal.control_plane.runtime_adoption import (
    latest_runtime_observation,
    reconcile_external_runtime_observation,
)
from ai_platform.portal.control_plane.service import ControlPlaneService
from ai_platform.wickhunter.contracts import BotMode


NOW = datetime(2026, 8, 10, 6, 30, tzinfo=UTC)


@pytest.fixture
def session_factory() -> SessionFactory:
    engine = build_engine("sqlite+pysqlite:///:memory:")
    create_schema(engine)
    return build_session_factory(engine)


def _context(*, admin: bool = False) -> RequestContext:
    permissions = [Permission.BOT_CREATE, Permission.BOT_READ, Permission.BOT_START]
    if admin:
        permissions.append(Permission.ADMIN_MANAGE)
    return RequestContext(
        tenant_id="tenant-a",
        actor_id="portal-runtime-reconciler",
        actor_type=ActorType.SERVICE,
        permissions=tuple(permissions),
        request_id=uuid4(),
        correlation_id=uuid4(),
        causation_id=uuid4(),
    )


def _spec() -> BotSpec:
    return BotSpec(
        tenant_id="tenant-a",
        strategy_version="WickHunter-WH09",
        model_version="H900",
        risk_policy_version="wh09-shadow-zero-authority-v1",
        exchange_connection_ref="public-market-data-only",
        pair_universe=("BTC/USDT",),
        timeframe="5m",
        capital_allocation="1",
        capital_currency="USDT",
        runtime_version="90cfc5ded10b0c6cb6406d00042817aca611e900",
        config_revision=1,
        environment=Environment.PRODUCTION,
        execution_mode=ExecutionMode.DRY_RUN,
        managed_mode=BotMode.SHADOW,
    )


def _material(
    _context: RequestContext,
    _revision: BotConfigRevision,
) -> RuntimeGenerationMaterial:
    return RuntimeGenerationMaterial(
        normalized_runtime_config_digest="1" * 64,
        runtime_image_digest="2" * 64,
        strategy_artifact_digest="3" * 64,
        model_artifact_digest="0488eaea68a316e3659e3b9e2fcea667eb57de87a22888ce396d112a5c075d2e",
        feature_schema_version="WH09-H900",
        risk_policy_digest="5" * 64,
        exchange_mode="public-market-data-only",
        exchange_connection_revision=None,
        isolation_profile_version="synology-wh09-zero-authority-v1",
        isolation_profile_digest="6" * 64,
        isolation_plan_digest="7" * 64,
        gateway_artifact_digest="8" * 64,
        gateway_contract_version="no-order-gateway-v1",
        gateway_contract_digest="9" * 64,
        market_data_egress_policy_version="binance-public-market-only-v1",
        market_data_egress_policy_digest="a" * 64,
    )


def _desired_generation(session_factory: SessionFactory):
    context = _context()
    service = ControlPlaneService(
        session_factory,
        clock=lambda: NOW,
        generation_material_resolver=_material,
    )
    created = service.create_bot(context, "wickhunter-wh09", "WickHunter", _spec())
    assert created.latest_authored_revision_id is not None
    revision = service.promote_revision(
        context,
        created.bot_id,
        created.latest_authored_revision_id,
        created.state_version,
    )
    bot, generation, rollout = service.apply_revision(
        context,
        created.bot_id,
        revision.revision_id,
        2,
        "adopt-existing-wh09",
    )
    assert bot.observed_runtime_generation_id is None
    return bot, generation, rollout


def _observation(generation, **updates: object) -> RuntimeGenerationObservation:
    payload = dict(
        observation_id=str(uuid4()),
        generation_id=generation.generation_id,
        runtime_instance_id="sha256:" + "b" * 64,
        reconciliation_epoch=1,
        reconciliation_attempt=1,
        observed_state="RUNNING",
        observed_generation_spec_digest=generation.generation_spec_digest,
        observed_image_digest=generation.runtime_image_digest,
        observed_config_digest=generation.normalized_runtime_config_digest,
        source_sequence=2,
        source_version="wickhunter-wh09-candidate-materialization-20260808-r1-h900s-7b23a958fd4d",
        source_observed_at=NOW,
        reconciled_at=NOW,
        identity_status=RuntimeIdentityStatus.MATCHED,
        freshness_status=ReconciliationFreshnessStatus.CURRENT,
        completeness_status=ReconciliationCompletenessStatus.COMPLETE,
        evidence_hash="c" * 64,
        reason_code=None,
    )
    payload.update(updates)
    return RuntimeGenerationObservation(**payload)


def test_external_runtime_adoption_converges_without_creating_second_generation(
    session_factory: SessionFactory,
) -> None:
    _, generation, rollout = _desired_generation(session_factory)
    observation = _observation(generation)

    result = reconcile_external_runtime_observation(
        session_factory,
        _context(admin=True),
        "wickhunter-wh09",
        observation,
    )

    assert result.adopted_external_runtime is True
    assert result.bot.name == "WickHunter"
    assert result.bot.spec.managed_mode is BotMode.SHADOW
    assert result.bot.spec.model_version == "H900"
    assert result.bot.desired_runtime_generation_id == generation.generation_id
    assert result.bot.observed_runtime_generation_id == generation.generation_id
    assert result.bot.observed_state.value == "RUNNING"
    assert result.generation.managed_mode is BotMode.SHADOW
    assert result.observation.runtime_instance_id.startswith("sha256:")

    with session_factory() as session:
        rows = session.query(BotRow).all()
        assert len(rows) == 1
        rollout_row = session.get(BotRolloutRow, rollout.rollout_id)
        assert rollout_row is not None
        assert rollout_row.status == "SUCCEEDED"
        assert rollout_row.reason_code == "EXTERNAL_RUNTIME_ADOPTED"

    persisted = latest_runtime_observation(
        session_factory,
        _context(admin=True),
        "wickhunter-wh09",
    )
    assert persisted == observation


def test_external_runtime_adoption_is_idempotent_for_same_observation(
    session_factory: SessionFactory,
) -> None:
    _, generation, _ = _desired_generation(session_factory)
    observation = _observation(generation)
    context = _context(admin=True)

    first = reconcile_external_runtime_observation(
        session_factory, context, "wickhunter-wh09", observation
    )
    second = reconcile_external_runtime_observation(
        session_factory, context, "wickhunter-wh09", observation
    )

    assert second.observation == first.observation
    assert second.bot.observed_runtime_generation_id == generation.generation_id


def test_external_runtime_adoption_fails_closed_on_identity_or_digest_mismatch(
    session_factory: SessionFactory,
) -> None:
    _, generation, _ = _desired_generation(session_factory)
    context = _context(admin=True)

    for observation in (
        _observation(generation, observed_image_digest="d" * 64),
        _observation(generation, identity_status=RuntimeIdentityStatus.MISMATCH),
        _observation(
            generation,
            freshness_status=ReconciliationFreshnessStatus.STALE,
        ),
        _observation(
            generation,
            completeness_status=ReconciliationCompletenessStatus.INCOMPLETE,
        ),
    ):
        with pytest.raises(ControlPlaneConflictError):
            reconcile_external_runtime_observation(
                session_factory,
                context,
                "wickhunter-wh09",
                observation,
            )

    with session_factory() as session:
        row = session.get(BotRow, (context.tenant_id, "wickhunter-wh09"))
        assert row is not None
        assert row.observed_runtime_generation_id is None
