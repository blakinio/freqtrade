from __future__ import annotations

from datetime import UTC, datetime, timedelta
from uuid import uuid4

from ai_platform.portal.contracts.bots import BotSpec
from ai_platform.portal.contracts.environment import ExecutionMode
from ai_platform.portal.contracts.identity import Permission
from ai_platform.portal.contracts.risk import ApprovedExecutionIntent
from ai_platform.portal.control_plane.context import RequestContext
from ai_platform.portal.control_plane.database import SessionFactory
from ai_platform.portal.control_plane.service import ControlPlaneService
from ai_platform.portal.intelligence.schema import DecisionSnapshot
from ai_platform.portal.intelligence.service import TradeIntelligenceService
from ai_platform.portal.learning.schema import AutonomyLevel, EvidenceWindow, ExperimentOutcome
from ai_platform.portal.learning.service import LearningService
from ai_platform.portal.risk.schema import RiskPolicyLimits
from ai_platform.portal.risk.service import RiskService
from ai_platform.portal.simulator.exchange import DeterministicExchangeSimulator
from ai_platform.portal.simulator.schema import ScenarioManifest, SimulatorEvidenceBundle


class ScenarioAssertionError(RuntimeError):
    pass


class UniversalScenarioRunner:
    def __init__(self, session_factory: SessionFactory) -> None:
        self._control = ControlPlaneService(session_factory)
        self._risk = RiskService(session_factory)
        self._intelligence = TradeIntelligenceService(session_factory)
        self._learning = LearningService(session_factory)

    def run(self, context: RequestContext, manifest: ScenarioManifest) -> SimulatorEvidenceBundle:
        required = {
            Permission.BOT_CREATE,
            Permission.BOT_READ,
            Permission.RISK_MANAGE,
            Permission.TRADE_MANUAL_EXECUTE,
        }
        if not required.issubset(set(context.permissions)):
            raise ScenarioAssertionError("scenario context lacks required portal permissions")
        if context.tenant_id != manifest.tenant_id:
            raise ScenarioAssertionError("scenario tenant does not match trusted request context")

        risk_policy_id = f"risk-{manifest.scenario_id}"
        model_version = f"model-active-{manifest.scenario_id}"
        bot = self._control.create_bot(
            context,
            manifest.bot_id,
            f"Scenario {manifest.scenario_id}",
            BotSpec(
                tenant_id=context.tenant_id,
                strategy_version="strategy-simulator-v1",
                model_version=model_version,
                risk_policy_version=risk_policy_id,
                exchange_connection_ref="exchange-simulator",
                pair_universe=(manifest.pair,),
                timeframe="5m",
                capital_allocation=manifest.initial_equity,
                capital_currency="USDT",
                runtime_version="simulator-v1",
                config_revision=1,
                environment=manifest.environment,
                execution_mode=ExecutionMode.DRY_RUN,
            ),
        )
        self._risk.register_policy(
            context,
            risk_policy_id,
            RiskPolicyLimits(
                max_order_notional=manifest.initial_equity,
                max_projected_gross_exposure=manifest.initial_equity,
                max_projected_open_positions=1,
                max_daily_loss=manifest.initial_equity,
                max_drawdown="0.50",
                require_healthy_runtime=True,
            ),
        )

        simulator = DeterministicExchangeSimulator(manifest)
        snapshot = simulator.build_snapshot(
            context,
            bot,
            pair=manifest.pair,
            side=manifest.side,
            amount=manifest.amount,
        )
        risk_result = self._risk.evaluate_manual_intent(
            context,
            bot_id=bot.bot_id,
            pair=manifest.pair,
            side=manifest.side,
            amount=manifest.amount,
            environment=manifest.environment,
            risk_policy_version_id=risk_policy_id,
            snapshot=snapshot,
        )
        if not isinstance(risk_result, ApprovedExecutionIntent):
            raise ScenarioAssertionError(
                f"scenario risk gate rejected intent: {risk_result.risk_decision.reason_codes}"
            )
        order = simulator.submit_approved_intent(risk_result, context.correlation_context())
        outcome = simulator.close_position()

        decision_snapshot = self._intelligence.record_decision_snapshot(
            context,
            DecisionSnapshot(
                snapshot_id=uuid4(),
                tenant_id=context.tenant_id,
                bot_id=bot.bot_id,
                trade_intent_id=risk_result.trade_intent.trade_intent_id,
                risk_decision_id=risk_result.risk_decision.risk_decision_id,
                config_revision=bot.spec.config_revision,
                strategy_version=bot.spec.strategy_version,
                model_version=bot.spec.model_version,
                risk_policy_version=bot.spec.risk_policy_version,
                source_runtime_id=simulator.runtime_id,
                pair=manifest.pair,
                side=manifest.side,
                amount=manifest.amount,
                decision_at=risk_result.risk_decision.occurred_at,
                evidence_ref=f"e2e-artifacts/{manifest.scenario_id}/decision-snapshot.json",
                evidence_sha256="a" * 64,
            ),
        )
        analysis = self._intelligence.analyze_outcome(
            context,
            snapshot_id=str(decision_snapshot.snapshot_id),
            outcome=outcome,
        )
        hypothesis = self._learning.create_hypothesis(
            context,
            analysis.insight,
            "Evaluate a reproducible candidate from the deterministic simulator outcome.",
        )
        experiment = self._learning.record_experiment(
            context,
            hypothesis_id=str(hypothesis.hypothesis_id),
            evidence_window=EvidenceWindow(
                start_at=datetime(2026, 5, 1, tzinfo=UTC),
                end_at=datetime(2026, 6, 1, tzinfo=UTC),
            ),
            autonomy_level=AutonomyLevel.L3_EXECUTE_RESEARCH,
            outcome=ExperimentOutcome.POSITIVE,
            result_summary="Deterministic simulator scenario produced a bounded candidate proposal.",
        )
        candidate = self._learning.register_candidate(
            context,
            experiment_id=str(experiment.experiment_id),
            model_family_id="simulator-family",
            candidate_model_version_id=f"candidate-{manifest.scenario_id}",
            dataset_version_id=f"dataset-{manifest.scenario_id}",
            feature_schema_version_id="features-simulator-v1",
        )

        active_after = self._control.get_bot(context, bot.bot_id).spec.model_version
        if active_after != model_version:
            raise ScenarioAssertionError("learning workflow mutated active model assignment")
        if outcome.closed_at <= outcome.opened_at:
            raise ScenarioAssertionError("simulated trade did not close after opening")

        return SimulatorEvidenceBundle(
            scenario_id=manifest.scenario_id,
            correlation_id=context.correlation_id,
            order_id=order.order_id,
            trade_id=outcome.trade_id,
            analysis_id=analysis.analysis_id,
            insight_id=analysis.insight.insight_id,
            hypothesis_id=hypothesis.hypothesis_id,
            experiment_id=experiment.experiment_id,
            candidate_id=candidate.candidate_id,
            active_model_before=model_version,
            active_model_after=active_after,
            candidate_model_version_id=candidate.candidate_model_version_id,
            realized_pnl=outcome.realized_pnl,
        )
