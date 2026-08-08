from __future__ import annotations

import argparse
import json
import time
from dataclasses import dataclass, field
from decimal import Decimal
from pathlib import Path

from ai_platform.wickhunter.candidate_paper_runtime_operator import (
    DEFAULT_MAX_SOURCE_AGE_MS,
    DEFAULT_PUBLIC_MARKET_BASE_URL,
    CandidatePaperRuntimeOperator,
    CandidatePaperRuntimeOperatorError,
    _assert_regular_absolute,
    _atomic_health,
    assert_closed_authority_environment,
    load_liquid20_snapshot,
)
from ai_platform.wickhunter.contracts import BotMode, DriftState
from ai_platform.wickhunter.production_research_runtime import (
    FROZEN_OUTCOME_HORIZON_MS,
    ZERO_AUTHORITY,
    ProductionResearchRuntimeService,
    build_production_research_runtime_binding,
)
from ai_platform.wickhunter.shadow_runtime_common import ShadowRuntimePolicy


HEALTH_SCHEMA_VERSION = "wickhunter-production-research-runtime-health-v1"
DEFAULT_POLL_SECONDS = 60


def _runtime_policy() -> ShadowRuntimePolicy:
    return ShadowRuntimePolicy(
        policy_version="wickhunter-production-research-runtime-v1",
        simulated_initial_equity_quote=Decimal("10000"),
        maximum_universe_age_ms=DEFAULT_MAX_SOURCE_AGE_MS,
        maximum_source_age_ms=DEFAULT_MAX_SOURCE_AGE_MS,
        minimum_healthy_sources=1,
        maximum_open_positions=4,
        maximum_drawdown_ratio=Decimal("0.20"),
        decision_history_limit=1000,
    )


@dataclass(slots=True)
class ProductionResearchRuntimeOperator(CandidatePaperRuntimeOperator):
    service: ProductionResearchRuntimeService
    last_success_at_ms: int | None = field(default=None, init=False)

    def __post_init__(self) -> None:
        if self.service.binding.request.mode is not BotMode.SHADOW:
            raise CandidatePaperRuntimeOperatorError("research runtime binding mode must be SHADOW")
        _assert_regular_absolute(self.liquid20_root_path, field="Liquid20 input")
        if not self.health_path.is_absolute():
            raise CandidatePaperRuntimeOperatorError("health path must be absolute")
        if self.health_path.parent.is_symlink():
            raise CandidatePaperRuntimeOperatorError("health root cannot be a symlink")
        if self.maximum_source_age_ms < 1:
            raise CandidatePaperRuntimeOperatorError("maximum source age must be positive")
        if self.service.operator_commit != self.operator_commit:
            raise CandidatePaperRuntimeOperatorError("service and operator commit differ")
        assert_closed_authority_environment()

    def _health_payload(
        self,
        *,
        status: str,
        checked_at_ms: int,
        liquid20_snapshot_id: str | None,
        runtime_health: str,
        circuit_breaker_reasons: tuple[str, ...],
        error_code: str | None,
        error_message: str | None,
    ) -> dict[str, object]:
        if runtime_health not in {"healthy", "degraded", "fail_closed"}:
            raise CandidatePaperRuntimeOperatorError("runtime health is invalid")
        canonical_breaker_reasons = tuple(sorted(set(circuit_breaker_reasons)))
        state = self.service.runtime.state
        identity = self.service.binding.identity
        telemetry_sha256 = None
        telemetry_path = self.service.journal.telemetry_path
        if telemetry_path.is_file() and not telemetry_path.is_symlink():
            payload = json.loads(telemetry_path.read_text(encoding="utf-8"))
            if isinstance(payload, dict):
                value = payload.get("telemetry_sha256")
                if isinstance(value, str):
                    telemetry_sha256 = value
        payload = {
            "schema_version": HEALTH_SCHEMA_VERSION,
            "status": status,
            "checked_at_ms": checked_at_ms,
            "last_success_at_ms": self.last_success_at_ms,
            "operator_commit": self.operator_commit,
            "binding_id": self.service.binding.binding_id,
            "run_id": identity.run_id,
            "mode": identity.mode.value,
            "generation": state.generation,
            "last_observed_at_ms": state.last_observed_at_ms,
            "liquid20_snapshot_id": liquid20_snapshot_id,
            "runtime_health": runtime_health,
            "model_drift": self.model_drift.value,
            "data_drift": self.data_drift.value,
            "circuit_breaker_active": bool(canonical_breaker_reasons),
            "circuit_breaker_reasons": list(canonical_breaker_reasons),
            "error_code": error_code,
            "error_message": None if error_message is None else error_message[:240],
            "model_version": identity.model_version,
            "model_hash": identity.model_hash,
            "model_artifact_sha256": identity.model_artifact_sha256,
            "parameter_version": identity.parameter_version,
            "parameter_hash": identity.parameter_hash,
            "dataset_hash": identity.dataset_hash,
            "no_trade_confidence": str(identity.no_trade_confidence),
            "outcome_horizon_ms": FROZEN_OUTCOME_HORIZON_MS,
            "telemetry_sha256": telemetry_sha256,
            **ZERO_AUTHORITY,
        }
        from ai_platform.wickhunter.canonical import canonical_sha256

        payload["health_sha256"] = canonical_sha256(payload)
        return payload

    def run_once(self, *, observed_at_ms: int | None = None) -> int:
        now_ms = time.time_ns() // 1_000_000 if observed_at_ms is None else observed_at_ms
        liquid20 = load_liquid20_snapshot(
            self.liquid20_root_path,
            now_ms=now_ms,
            maximum_age_ms=self.maximum_source_age_ms,
        )
        open_position_symbols = tuple(
            sorted({position.symbol.upper() for position in self.service.runtime.state.positions})
        )
        pending_outcome_symbols = self.service.journal.pending_outcome_symbols(
            observed_at_ms=now_ms
        )
        decision_market_symbols = tuple(
            sorted({*liquid20.universe.selected_symbols, *open_position_symbols})
        )
        market_symbols = tuple(sorted({*decision_market_symbols, *pending_outcome_symbols}))
        markets, unavailable_symbols = self._fetch_public_market_snapshots(
            symbols=market_symbols,
            observed_at_ms=now_ms,
        )
        unavailable_open_positions = tuple(
            sorted(set(open_position_symbols) & set(unavailable_symbols))
        )
        if unavailable_open_positions:
            raise CandidatePaperRuntimeOperatorError(
                "simulated SHADOW position lacks Binance USD-M public market context: "
                + ",".join(unavailable_open_positions)
            )
        market_by_symbol = {market.symbol: market for market in markets}
        decision_markets = tuple(
            market_by_symbol[symbol]
            for symbol in decision_market_symbols
            if symbol in market_by_symbol
        )
        tick = self._compose_tick(
            liquid20=liquid20,
            markets=decision_markets,
            observed_at_ms=now_ms,
            unavailable_symbols=unavailable_symbols,
        )
        result = self.service.step(tick)
        self.service.journal.materialize_due_outcomes(
            observed_at_ms=now_ms,
            mark_prices={market.symbol: market.decision_price for market in markets},
            operator_commit=self.operator_commit,
        )
        self.service.journal.publish_telemetry(
            checked_at_ms=now_ms,
            operator_commit=self.operator_commit,
            runtime_state=result.state,
        )
        breaker_reasons = set(result.snapshot.circuit_breaker_reasons)
        if self.circuit_breaker_active:
            breaker_reasons.add("operator_circuit_breaker_active")
        canonical_breaker_reasons = tuple(sorted(breaker_reasons))
        runtime_health = (
            "fail_closed" if canonical_breaker_reasons else result.snapshot.health.value
        )
        self.last_success_at_ms = now_ms
        _atomic_health(
            self.health_path,
            self._health_payload(
                status="healthy",
                checked_at_ms=now_ms,
                liquid20_snapshot_id=liquid20.snapshot_id,
                runtime_health=runtime_health,
                circuit_breaker_reasons=canonical_breaker_reasons,
                error_code=None,
                error_message=None,
            ),
        )
        return result.state.generation


def _boolean(value: str) -> bool:
    normalized = value.strip().lower()
    if normalized == "true":
        return True
    if normalized == "false":
        return False
    raise argparse.ArgumentTypeError("boolean value must be true or false")


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Persistent fail-closed WickHunter WH09 production research/shadow operator"
    )
    parser.add_argument("--model-root", type=Path, required=True)
    parser.add_argument("--journal-root", type=Path, required=True)
    parser.add_argument("--liquid20-root", type=Path, required=True)
    parser.add_argument("--health-root", type=Path, required=True)
    parser.add_argument("--operator-commit", required=True)
    parser.add_argument("--expected-package-id", required=True)
    parser.add_argument("--expected-manifest-sha256", required=True)
    parser.add_argument("--expected-model-artifact-sha256", required=True)
    parser.add_argument("--expected-model-hash", required=True)
    parser.add_argument("--expected-parameter-hash", required=True)
    parser.add_argument(
        "--bot-instance",
        default="wickhunter-wh09-production-research",
    )
    parser.add_argument(
        "--public-market-base-url",
        default=DEFAULT_PUBLIC_MARKET_BASE_URL,
    )
    parser.add_argument("--poll-seconds", type=int, default=DEFAULT_POLL_SECONDS)
    parser.add_argument(
        "--maximum-source-age-ms",
        type=int,
        default=DEFAULT_MAX_SOURCE_AGE_MS,
    )
    parser.add_argument(
        "--model-drift",
        choices=tuple(item.value for item in DriftState),
        default=DriftState.HEALTHY.value,
    )
    parser.add_argument(
        "--data-drift",
        choices=tuple(item.value for item in DriftState),
        default=DriftState.HEALTHY.value,
    )
    parser.add_argument("--circuit-breaker-active", type=_boolean, default=False)
    parser.add_argument("--cycles", type=int, default=0)
    return parser


def build_operator(arguments: argparse.Namespace) -> ProductionResearchRuntimeOperator:
    assert_closed_authority_environment()
    _assert_regular_absolute(arguments.model_root, field="model root")
    _assert_regular_absolute(arguments.liquid20_root, field="Liquid20 input")
    _assert_regular_absolute(arguments.journal_root, field="journal root", must_exist=False)
    _assert_regular_absolute(arguments.health_root, field="health root", must_exist=False)
    arguments.journal_root.mkdir(parents=True, exist_ok=True)
    arguments.health_root.mkdir(parents=True, exist_ok=True)
    binding = build_production_research_runtime_binding(
        model_root=arguments.model_root,
        expected_package_id=arguments.expected_package_id,
        expected_manifest_sha256=arguments.expected_manifest_sha256,
        expected_model_artifact_sha256=arguments.expected_model_artifact_sha256,
        expected_model_hash=arguments.expected_model_hash,
        expected_parameter_hash=arguments.expected_parameter_hash,
        bot_instance=arguments.bot_instance,
    )
    service = ProductionResearchRuntimeService.create(
        binding=binding,
        journal_root=arguments.journal_root,
        operator_commit=arguments.operator_commit,
        policy=_runtime_policy(),
    )
    return ProductionResearchRuntimeOperator(
        service=service,
        liquid20_root_path=arguments.liquid20_root,
        health_path=arguments.health_root / "health.json",
        operator_commit=arguments.operator_commit,
        public_market_base_url=arguments.public_market_base_url,
        maximum_source_age_ms=arguments.maximum_source_age_ms,
        model_drift=DriftState(arguments.model_drift),
        data_drift=DriftState(arguments.data_drift),
        circuit_breaker_active=arguments.circuit_breaker_active,
    )


def main() -> int:
    arguments = _parser().parse_args()
    if arguments.cycles < 0:
        raise CandidatePaperRuntimeOperatorError("cycles must be >= 0")
    operator = build_operator(arguments)
    if arguments.cycles == 0:
        operator.run_forever(poll_seconds=arguments.poll_seconds)
        return 0
    if not 60 <= arguments.poll_seconds <= 900:
        raise CandidatePaperRuntimeOperatorError("poll cadence must be within 60..900 seconds")
    for index in range(arguments.cycles):
        checked_at_ms = time.time_ns() // 1_000_000
        try:
            operator.run_once(observed_at_ms=checked_at_ms)
        except Exception as exc:
            operator.publish_failure(exc, checked_at_ms=checked_at_ms)
            raise
        if index + 1 < arguments.cycles:
            time.sleep(arguments.poll_seconds)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
