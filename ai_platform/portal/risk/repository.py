from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from ai_platform.portal.contracts.audit import AuditEvent
from ai_platform.portal.contracts.environment import Environment
from ai_platform.portal.contracts.events import EventEnvelope
from ai_platform.portal.contracts.risk import RiskDecision, TradeIntent
from ai_platform.portal.control_plane.models import AuditEventRow, OutboxEventRow
from ai_platform.portal.risk.models import (
    RiskDecisionRow,
    RiskKillSwitchRow,
    RiskPolicyRow,
    TradeIntentRow,
)
from ai_platform.portal.risk.schema import KillSwitchState, RiskPolicyDefinition


def _utc_from_database(value: datetime) -> datetime:
    if value.tzinfo is None or value.utcoffset() is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)


class RiskRepository:
    def add_policy(self, session: Session, definition: RiskPolicyDefinition) -> None:
        version = definition.version
        session.add(
            RiskPolicyRow(
                tenant_id=version.tenant_id,
                risk_policy_version_id=version.risk_policy_version_id,
                policy_hash=version.policy_hash,
                definition_json=definition.canonical_json(),
                created_by_actor_id=version.created_by_actor_id,
                created_at=version.created_at,
            )
        )

    def get_policy(
        self,
        session: Session,
        tenant_id: str,
        risk_policy_version_id: str,
    ) -> RiskPolicyDefinition | None:
        row = session.get(RiskPolicyRow, (tenant_id, risk_policy_version_id))
        if row is None:
            return None
        return RiskPolicyDefinition.model_validate_json(row.definition_json)

    def list_policies(self, session: Session, tenant_id: str) -> tuple[RiskPolicyDefinition, ...]:
        rows = session.scalars(
            select(RiskPolicyRow)
            .where(RiskPolicyRow.tenant_id == tenant_id)
            .order_by(RiskPolicyRow.risk_policy_version_id)
        ).all()
        return tuple(RiskPolicyDefinition.model_validate_json(row.definition_json) for row in rows)

    def get_kill_switch(
        self,
        session: Session,
        tenant_id: str,
        environment: Environment,
    ) -> KillSwitchState | None:
        row = session.get(RiskKillSwitchRow, (tenant_id, environment.value))
        if row is None:
            return None
        return KillSwitchState(
            tenant_id=row.tenant_id,
            environment=Environment(row.environment),
            active=row.active,
            reason_code=row.reason_code,
            updated_by_actor_id=row.updated_by_actor_id,
            updated_at=_utc_from_database(row.updated_at),
        )

    def set_kill_switch(self, session: Session, state: KillSwitchState) -> KillSwitchState:
        row = session.get(RiskKillSwitchRow, (state.tenant_id, state.environment.value))
        if row is None:
            row = RiskKillSwitchRow(
                tenant_id=state.tenant_id,
                environment=state.environment.value,
                active=state.active,
                reason_code=state.reason_code,
                updated_by_actor_id=state.updated_by_actor_id,
                updated_at=state.updated_at,
            )
            session.add(row)
        else:
            row.active = state.active
            row.reason_code = state.reason_code
            row.updated_by_actor_id = state.updated_by_actor_id
            row.updated_at = state.updated_at
        session.flush()
        return state

    def add_trade_intent(self, session: Session, intent: TradeIntent) -> None:
        session.add(
            TradeIntentRow(
                tenant_id=intent.tenant_id,
                trade_intent_id=str(intent.trade_intent_id),
                bot_id=intent.bot_id,
                intent_json=intent.canonical_json(),
                created_at=intent.created_at,
            )
        )

    def get_trade_intent(
        self,
        session: Session,
        tenant_id: str,
        trade_intent_id: UUID,
    ) -> TradeIntent | None:
        row = session.get(TradeIntentRow, (tenant_id, str(trade_intent_id)))
        if row is None:
            return None
        return TradeIntent.model_validate_json(row.intent_json)

    def list_trade_intents(self, session: Session, tenant_id: str) -> tuple[TradeIntent, ...]:
        rows = session.scalars(
            select(TradeIntentRow)
            .where(TradeIntentRow.tenant_id == tenant_id)
            .order_by(TradeIntentRow.created_at, TradeIntentRow.trade_intent_id)
        ).all()
        return tuple(TradeIntent.model_validate_json(row.intent_json) for row in rows)

    def add_risk_decision(self, session: Session, decision: RiskDecision) -> None:
        session.add(
            RiskDecisionRow(
                tenant_id=decision.tenant_id,
                risk_decision_id=str(decision.risk_decision_id),
                trade_intent_id=str(decision.trade_intent_id),
                decision_json=decision.canonical_json(),
                occurred_at=decision.occurred_at,
            )
        )

    def get_risk_decision(
        self,
        session: Session,
        tenant_id: str,
        risk_decision_id: UUID,
    ) -> RiskDecision | None:
        row = session.get(RiskDecisionRow, (tenant_id, str(risk_decision_id)))
        if row is None:
            return None
        return RiskDecision.model_validate_json(row.decision_json)

    def list_risk_decisions(
        self,
        session: Session,
        tenant_id: str,
    ) -> tuple[RiskDecision, ...]:
        rows = session.scalars(
            select(RiskDecisionRow)
            .where(RiskDecisionRow.tenant_id == tenant_id)
            .order_by(RiskDecisionRow.occurred_at, RiskDecisionRow.risk_decision_id)
        ).all()
        return tuple(RiskDecision.model_validate_json(row.decision_json) for row in rows)

    def add_audit_event(self, session: Session, event: AuditEvent) -> None:
        session.add(
            AuditEventRow(
                audit_id=str(event.audit_id),
                tenant_id=event.tenant_id,
                actor_id=event.actor_id,
                resource_type=event.resource_type,
                resource_id=event.resource_id,
                action=event.action.value,
                result=event.result.value,
                occurred_at=event.occurred_at,
                event_json=event.canonical_json(),
            )
        )

    def add_outbox_event(self, session: Session, event: EventEnvelope) -> None:
        session.add(
            OutboxEventRow(
                event_id=str(event.event_id),
                tenant_id=event.tenant_id,
                event_type=event.event_type.value,
                aggregate_type=event.aggregate_type,
                aggregate_id=event.aggregate_id,
                occurred_at=event.occurred_at,
                event_json=event.canonical_json(),
                published_at=None,
            )
        )
