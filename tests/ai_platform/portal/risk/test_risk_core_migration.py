from __future__ import annotations

from sqlalchemy import inspect

from ai_platform.portal.control_plane.database import build_engine
from ai_platform.portal.risk.database import create_risk_schema


def test_risk_schema_creates_expected_tables_and_decision_foreign_key() -> None:
    engine = build_engine("sqlite+pysqlite:///:memory:")
    create_risk_schema(engine)
    inspector = inspect(engine)

    assert {
        "portal_risk_policies",
        "portal_risk_kill_switches",
        "portal_trade_intents",
        "portal_risk_decisions",
        "portal_audit_events",
        "portal_outbox_events",
    }.issubset(set(inspector.get_table_names()))

    foreign_keys = inspector.get_foreign_keys("portal_risk_decisions")
    assert any(
        key["referred_table"] == "portal_trade_intents"
        and key["constrained_columns"] == ["tenant_id", "trade_intent_id"]
        for key in foreign_keys
    )
