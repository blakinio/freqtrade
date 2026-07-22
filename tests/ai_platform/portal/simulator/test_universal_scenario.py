from __future__ import annotations

from pathlib import Path
from uuid import uuid4

import pytest

from ai_platform.portal.contracts.identity import ActorType, Permission
from ai_platform.portal.control_plane.context import RequestContext
from ai_platform.portal.control_plane.database import build_engine, build_session_factory, create_schema
from ai_platform.portal.intelligence.database import create_intelligence_schema
from ai_platform.portal.learning.database import create_learning_schema
from ai_platform.portal.risk.database import create_risk_schema
from ai_platform.portal.simulator.runner import ScenarioAssertionError, UniversalScenarioRunner
from ai_platform.portal.simulator.schema import ScenarioManifest


SCENARIO = Path("tests/ai_platform/portal/simulator/scenarios/profitable.json")


def _context(*permissions: Permission) -> RequestContext:
    return RequestContext(
        tenant_id="tenant-e2e",
        actor_id="agent-e2e",
        actor_type=ActorType.AGENT,
        permissions=permissions,
        request_id=uuid4(),
        correlation_id=uuid4(),
    )


def _session_factory():
    engine = build_engine("sqlite+pysqlite:///:memory:")
    create_schema(engine)
    create_risk_schema(engine)
    create_intelligence_schema(engine)
    create_learning_schema(engine)
    return build_session_factory(engine)


def test_universal_scenario_executes_simulated_trade_and_learning_candidate_without_model_mutation() -> None:
    manifest = ScenarioManifest.model_validate_json(SCENARIO.read_text(encoding="utf-8"))
    context = _context(
        Permission.BOT_CREATE,
        Permission.BOT_READ,
        Permission.RISK_MANAGE,
        Permission.TRADE_MANUAL_EXECUTE,
    )

    evidence = UniversalScenarioRunner(_session_factory()).run(context, manifest)

    assert evidence.realized_pnl == 10
    assert evidence.order_id.startswith("sim-order-")
    assert evidence.trade_id.startswith("sim-trade-")
    assert evidence.active_model_before == evidence.active_model_after
    assert evidence.candidate_model_version_id != evidence.active_model_after


def test_universal_scenario_requires_explicit_portal_permissions() -> None:
    manifest = ScenarioManifest.model_validate_json(SCENARIO.read_text(encoding="utf-8"))

    with pytest.raises(ScenarioAssertionError, match="required portal permissions"):
        UniversalScenarioRunner(_session_factory()).run(_context(Permission.BOT_READ), manifest)


def test_first_failure_evidence_is_preserved_without_retry_or_sleep() -> None:
    manifest = ScenarioManifest.model_validate_json(SCENARIO.read_text(encoding="utf-8"))
    context = _context(Permission.BOT_READ)

    report = UniversalScenarioRunner(_session_factory()).run_captured(context, manifest)

    assert report.passed is False
    assert report.evidence is None
    assert report.failure is not None
    assert report.failure.correlation_id == context.correlation_id
    assert report.failure.stage == "scenario_assertion"
    assert report.failure.reason_code == "scenario context lacks required portal permissions"


def test_scenario_manifest_is_deterministic_and_uses_explicit_readiness_not_sleep() -> None:
    manifest = ScenarioManifest.model_validate_json(SCENARIO.read_text(encoding="utf-8"))

    assert manifest.entry_tick.occurred_at < manifest.exit_tick.occurred_at
    assert manifest.entry_tick.pair == manifest.exit_tick.pair == manifest.pair
    runner_source = Path("ai_platform/portal/simulator/runner.py").read_text(encoding="utf-8")
    exchange_source = Path("ai_platform/portal/simulator/exchange.py").read_text(encoding="utf-8")
    assert "sleep(" not in runner_source
    assert "sleep(" not in exchange_source
