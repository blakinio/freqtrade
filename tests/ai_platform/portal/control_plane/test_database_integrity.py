from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal
from uuid import uuid4

import pytest
from sqlalchemy.exc import IntegrityError

from ai_platform.portal.contracts.common import CorrelationContext
from ai_platform.portal.contracts.environment import Environment
from ai_platform.portal.contracts.risk import (
    RiskDecision,
    RiskDecisionOutcome,
    RiskLimitEvaluation,
    TradeIntent,
    TradeSide,
)
from ai_platform.portal.control_plane.database import (
    build_engine,
    build_session_factory,
    create_schema,
)
from ai_platform.portal.risk.repository import RiskRepository


def test_sqlite_enables_foreign_keys_for_every_connection() -> None:
    engine = build_engine("sqlite+pysqlite:///:memory:")
    try:
        with engine.connect() as connection:
            assert connection.exec_driver_sql("PRAGMA foreign_keys").scalar_one() == 1
            connection.exec_driver_sql(
                "CREATE TABLE parent (tenant_id TEXT NOT NULL, id TEXT NOT NULL, "
                "PRIMARY KEY (tenant_id, id))"
            )
            connection.exec_driver_sql(
                "CREATE TABLE child (tenant_id TEXT NOT NULL, parent_id TEXT NOT NULL, "
                "FOREIGN KEY (tenant_id, parent_id) "
                "REFERENCES parent (tenant_id, id) ON DELETE RESTRICT)"
            )
            with pytest.raises(IntegrityError):
                connection.exec_driver_sql(
                    "INSERT INTO child (tenant_id, parent_id) VALUES ('tenant-a', 'missing')"
                )
    finally:
        engine.dispose()


def test_risk_repository_persists_trade_intent_before_dependent_decision() -> None:
    engine = build_engine("sqlite+pysqlite:///:memory:")
    create_schema(engine)
    session_factory = build_session_factory(engine)
    repository = RiskRepository()
    now = datetime.now(UTC)
    correlation = CorrelationContext(request_id=uuid4(), correlation_id=uuid4())
    intent = TradeIntent(
        trade_intent_id=uuid4(),
        tenant_id="tenant-a",
        bot_id="bot-a",
        source_actor_id="actor-a",
        pair="BTC/USDT",
        side=TradeSide.BUY,
        amount=Decimal("1"),
        environment=Environment.TEST,
        created_at=now,
        context=correlation,
    )
    decision = RiskDecision(
        risk_decision_id=uuid4(),
        tenant_id=intent.tenant_id,
        trade_intent_id=intent.trade_intent_id,
        risk_policy_version="policy-v1",
        decision=RiskDecisionOutcome.APPROVED,
        reason_codes=("within_limits",),
        evaluated_limits=(
            RiskLimitEvaluation(
                limit_name="notional",
                configured_value="1000",
                observed_value="1",
                passed=True,
            ),
        ),
        occurred_at=now,
        context=correlation,
    )

    try:
        with session_factory.begin() as session:
            repository.add_trade_intent(session, intent)
            repository.add_risk_decision(session, decision)
        with session_factory() as session:
            assert repository.get_trade_intent(
                session,
                intent.tenant_id,
                intent.trade_intent_id,
            ) == intent
            assert repository.get_risk_decision(
                session,
                decision.tenant_id,
                decision.risk_decision_id,
            ) == decision
    finally:
        engine.dispose()
