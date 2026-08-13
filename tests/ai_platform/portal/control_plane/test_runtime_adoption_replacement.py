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


NOW = datetime(2026, 8, 13, 7, 20, tzinfo=UTC)
BOT_ID = "wickhunter-wh09"


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
        actor_id="issue-1396-runtime-reconciler",
        actor_type=ActorType.SERVICE,
        permissions=tuple(permissions),
        request_id=uuid4(),
        correlation_id=uuid4(),
        causation_id=uuid4(),
    )


def _spec(revision: int, mode: BotMode) -> BotSpec:
    return BotSpec(
        tenant_id="tenant-a",
        strategy_version="WickHunter-WH09",
        model_version="H900",
        risk_policy_version=(
            "wh09-paper-zero-authority-v1"
            if mode is BotMode.PAPER
            else "wh09-shadow-zero-authority-v1"
        ),
        exchange_connection_ref="public-market-data-only",
        pair_universe=("BTC/USDT",),
        timeframe="5m",
        capital_allocation="1",
        capital_currency="USDT",
        runtime_version="0bc9fd995a63fac469fa4f014195f5cc83983dec",
        config_revision=revision,
        environment=Environment.PRODUCTION,
        execution_mode=ExecutionMode.DRY_RUN,
        managed_mode=mode,
    )


def _material(
    _context: RequestContext,
    revision: BotConfigRevision,
) -> RuntimeGenerationMaterial:
    paper = revision.managed_mode is BotMode.PAPER
    return RuntimeGenerationMaterial(
        normalized_runtime_config_digest=("d" if paper else "1") * 64,
        runtime_image_digest=("e" if paper else "2") * 64,
        strategy_artifact_digest="3" * 64,
        model_artifact_digest="0488eaea68a316e3659e3b9e2fcea667eb57de87a22888ce396d112a5c075d2e",
        feature_schema_version="WH09-H900",
        risk_policy_digest=("f" if paper else "5") * 64,
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
        paper_activation_authorized=paper,
        paper_authorization_id=("issue-1396-paper-owner-authorized" if paper else None),
        paper_authorization_digest=("b" * 64 if paper else None),
        paper_candidate_package_id=(
            "wickhunter-wh09-candidate-materialization-20260808-r1-h900s-7b23a958fd4d"
            if paper
            else None
        ),
        paper_candidate_manifest_sha256=(
            "9f5ba852e33915678ca085c2eeafbf526457a079ba8f6f2fb7c1097f1d20ab79" if paper else None
        ),
    )


def _observation(generation, *, runtime_instance_id: str) -> RuntimeGenerationObservation:
    return RuntimeGenerationObservation(
        observation_id=str(uuid4()),
        generation_id=generation.generation_id,
        runtime_instance_id=runtime_instance_id,
        reconciliation_epoch=1,
        reconciliation_attempt=1,
        observed_state="RUNNING",
        observed_generation_spec_digest=generation.generation_spec_digest,
        observed_image_digest=generation.runtime_image_digest,
        observed_config_digest=generation.normalized_runtime_config_digest,
        source_sequence=5,
        source_version="0bc9fd995a63fac469fa4f014195f5cc83983dec",
        source_observed_at=NOW,
        reconciled_at=NOW,
        identity_status=RuntimeIdentityStatus.MATCHED,
        freshness_status=ReconciliationFreshnessStatus.CURRENT,
        completeness_status=ReconciliationCompletenessStatus.COMPLETE,
        evidence_hash="c" * 64,
        reason_code=None,
    )


def _shadow_then_paper(session_factory: SessionFactory):
    context = _context()
    service = ControlPlaneService(
        session_factory,
        clock=lambda: NOW,
        generation_material_resolver=_material,
    )
    created = service.create_bot(context, BOT_ID, "WickHunter", _spec(1, BotMode.SHADOW))
    assert created.latest_authored_revision_id is not None
    shadow_revision = service.promote_revision(
        context,
        BOT_ID,
        created.latest_authored_revision_id,
        created.state_version,
    )
    current = service.get_bot(context, BOT_ID)
    _, shadow, _ = service.apply_revision(
        context,
        BOT_ID,
        shadow_revision.revision_id,
        current.state_version,
        "issue-1396-shadow",
    )
    reconcile_external_runtime_observation(
        session_factory,
        _context(admin=True),
        BOT_ID,
        _observation(shadow, runtime_instance_id="sha256:" + "1" * 64),
    )

    revised = service.revise_bot(context, BOT_ID, _spec(2, BotMode.PAPER))
    assert revised.latest_authored_revision_id is not None
    paper_revision = service.promote_revision(
        context,
        BOT_ID,
        revised.latest_authored_revision_id,
        revised.state_version,
    )
    current = service.get_bot(context, BOT_ID)
    pending, paper, rollout = service.apply_revision(
        context,
        BOT_ID,
        paper_revision.revision_id,
        current.state_version,
        "issue-1396-paper",
    )
    return context, service, shadow, paper, rollout, pending


def test_external_runtime_replacement_converges_shadow_to_eligible_paper(
    session_factory: SessionFactory,
) -> None:
    _, _, shadow, paper, rollout, pending = _shadow_then_paper(session_factory)

    assert paper.managed_mode is BotMode.PAPER
    assert paper.paper_authorization_digest == "b" * 64
    assert pending.desired_runtime_generation_id == paper.generation_id
    assert pending.observed_runtime_generation_id == shadow.generation_id
    assert rollout.from_generation_id == shadow.generation_id

    paper_observation = _observation(
        paper,
        runtime_instance_id="sha256:" + "2" * 64,
    )
    result = reconcile_external_runtime_observation(
        session_factory,
        _context(admin=True),
        BOT_ID,
        paper_observation,
    )

    assert result.bot.desired_runtime_generation_id == paper.generation_id
    assert result.bot.observed_runtime_generation_id == paper.generation_id
    assert result.bot.spec.managed_mode is BotMode.PAPER
    assert result.generation.managed_mode is BotMode.PAPER
    assert result.observation == paper_observation

    with session_factory() as session:
        rollout_row = session.get(BotRolloutRow, rollout.rollout_id)
        assert rollout_row is not None
        assert rollout_row.status == "SUCCEEDED"
        assert rollout_row.reason_code == "EXTERNAL_RUNTIME_ADOPTED"

    assert (
        latest_runtime_observation(
            session_factory,
            _context(admin=True),
            BOT_ID,
        )
        == paper_observation
    )


def test_external_runtime_replacement_fails_closed_on_wrong_rollout_lineage(
    session_factory: SessionFactory,
) -> None:
    context, _, shadow, paper, rollout, _ = _shadow_then_paper(session_factory)

    with session_factory() as session, session.begin():
        rollout_row = session.get(BotRolloutRow, rollout.rollout_id)
        assert rollout_row is not None
        rollout_row.from_generation_id = None

    with pytest.raises(ControlPlaneConflictError, match="does not start from"):
        reconcile_external_runtime_observation(
            session_factory,
            _context(admin=True),
            BOT_ID,
            _observation(paper, runtime_instance_id="sha256:" + "2" * 64),
        )

    with session_factory() as session:
        row = session.get(BotRow, (context.tenant_id, BOT_ID))
        assert row is not None
        assert row.observed_runtime_generation_id == shadow.generation_id
