from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from ai_platform.wickhunter.canonical import canonical_sha256
from ai_platform.wickhunter.contracts import (
    BotMode,
    DriftState,
    ShadowDecisionEvidence,
    ShadowStatus,
    TradeDirection,
)
from ai_platform.wickhunter.deterministic_replay import CandidateLabel, LabelOutcome
from ai_platform.wickhunter.shadow_runtime_common import (
    RUNTIME_PARITY_SCHEMA_VERSION,
    RUNTIME_SNAPSHOT_SCHEMA_VERSION,
    RuntimeHealth,
    RuntimeSourceStatus,
    ShadowRuntimeError,
    _require_finite,
    _require_git_sha,
    _require_positive,
    _require_sha256,
    _require_text,
)
from ai_platform.wickhunter.shadow_runtime_positions import (
    ClosedSimulatedPosition,
    RuntimeDecisionSummary,
    SimulatedPosition,
)
from ai_platform.wickhunter.shadow_runtime_state import ShadowRuntimeState


RUNTIME_REPLAY_PARITY_SCHEMA_VERSION = "wickhunter-runtime-replay-parity-v1"


@dataclass(frozen=True, slots=True)
class PortalObservabilitySnapshot:
    schema_version: str
    snapshot_id: str
    bot_instance: str
    mode: BotMode
    health: RuntimeHealth
    observed_at_ms: int
    universe_snapshot_hash: str
    dynamic_universe: tuple[str, ...]
    source_freshness: tuple[RuntimeSourceStatus, ...]
    model_version: str | None
    model_hash: str | None
    parameter_version: str | None
    parameter_hash: str | None
    dataset_hash: str | None
    code_sha: str | None
    decisions: tuple[RuntimeDecisionSummary, ...]
    positions: tuple[SimulatedPosition, ...]
    cumulative_realized_pnl_quote: Decimal
    unrealized_pnl_quote: Decimal
    simulated_equity_quote: Decimal
    drawdown_ratio: Decimal
    retraining_state: str
    validation_state: str
    model_drift: DriftState
    data_drift: DriftState
    circuit_breaker_active: bool
    circuit_breaker_reasons: tuple[str, ...]
    persistence_generation: int
    runtime_state_sha256: str
    read_only: bool = True
    trading_credentials_present: bool = False
    order_adapter_present: bool = False
    orders_submitted: int = 0
    live_capital_authorized: bool = False

    def __post_init__(self) -> None:
        if self.schema_version != RUNTIME_SNAPSHOT_SCHEMA_VERSION:
            raise ShadowRuntimeError("observability snapshot schema mismatch")
        _require_sha256(self.snapshot_id, field="snapshot_id")
        _require_text(self.bot_instance, field="bot_instance")
        if self.mode is BotMode.LIVE_BLOCKED:
            raise ShadowRuntimeError("live mode is forbidden")
        if self.observed_at_ms <= 0:
            raise ShadowRuntimeError("snapshot observed_at_ms must be > 0")
        _require_sha256(self.universe_snapshot_hash, field="universe_snapshot_hash")
        if self.dynamic_universe != tuple(sorted(set(self.dynamic_universe))):
            raise ShadowRuntimeError("dynamic universe must be unique and sorted")
        if self.source_freshness != tuple(
            sorted(self.source_freshness, key=lambda item: item.source)
        ):
            raise ShadowRuntimeError("source freshness must be sorted")
        _require_finite(
            self.cumulative_realized_pnl_quote,
            field="cumulative_realized_pnl_quote",
        )
        _require_finite(self.unrealized_pnl_quote, field="unrealized_pnl_quote")
        _require_positive(self.simulated_equity_quote, field="simulated_equity_quote")
        if not Decimal("0") <= self.drawdown_ratio <= Decimal("1"):
            raise ShadowRuntimeError("drawdown_ratio must be in [0, 1]")
        if self.circuit_breaker_reasons != tuple(sorted(set(self.circuit_breaker_reasons))):
            raise ShadowRuntimeError("circuit breaker reasons must be unique and sorted")
        _require_sha256(self.runtime_state_sha256, field="runtime_state_sha256")
        if (
            not self.read_only
            or self.trading_credentials_present
            or self.order_adapter_present
            or self.orders_submitted != 0
            or self.live_capital_authorized
        ):
            raise ShadowRuntimeError("observability snapshot contains forbidden authority")


@dataclass(frozen=True, slots=True)
class ReplayShadowParityEvidence:
    schema_version: str
    parity_id: str
    shadow_decision_id: str
    label_id: str
    symbol: str
    side: TradeDirection
    decision_timestamp_ms: int
    dataset_hash: str
    code_sha: str
    take_profit_ratio: Decimal
    stop_loss_ratio: Decimal
    label_outcome: LabelOutcome
    identities_match: bool
    policy_match: bool
    execution_authority_absent: bool

    def __post_init__(self) -> None:
        if self.schema_version != RUNTIME_PARITY_SCHEMA_VERSION:
            raise ShadowRuntimeError("parity schema mismatch")
        for digest, field_name in (
            (self.parity_id, "parity_id"),
            (self.shadow_decision_id, "shadow_decision_id"),
            (self.label_id, "label_id"),
            (self.dataset_hash, "dataset_hash"),
        ):
            _require_sha256(digest, field=field_name)
        _require_text(self.symbol, field="symbol")
        _require_git_sha(self.code_sha, field="code_sha")
        if self.decision_timestamp_ms <= 0:
            raise ShadowRuntimeError("parity decision timestamp must be > 0")
        for ratio, field_name in (
            (self.take_profit_ratio, "take_profit_ratio"),
            (self.stop_loss_ratio, "stop_loss_ratio"),
        ):
            _require_positive(ratio, field=field_name)
        if not (self.identities_match and self.policy_match and self.execution_authority_absent):
            raise ShadowRuntimeError("replay/shadow parity evidence is not accepted")


@dataclass(frozen=True, slots=True)
class RuntimeReplayParityEvidence:
    schema_version: str
    parity_id: str
    shadow_decision_id: str
    original_evidence_sha256: str
    replayed_evidence_sha256: str
    symbol: str
    side: TradeDirection
    decision_timestamp_ms: int
    dataset_hash: str
    code_sha: str
    take_profit_ratio: Decimal
    stop_loss_ratio: Decimal
    identities_match: bool
    policy_match: bool
    replay_match: bool
    execution_authority_absent: bool

    def __post_init__(self) -> None:
        if self.schema_version != RUNTIME_REPLAY_PARITY_SCHEMA_VERSION:
            raise ShadowRuntimeError("runtime replay parity schema mismatch")
        for digest, field_name in (
            (self.parity_id, "parity_id"),
            (self.shadow_decision_id, "shadow_decision_id"),
            (self.original_evidence_sha256, "original_evidence_sha256"),
            (self.replayed_evidence_sha256, "replayed_evidence_sha256"),
            (self.dataset_hash, "dataset_hash"),
        ):
            _require_sha256(digest, field=field_name)
        _require_text(self.symbol, field="symbol")
        _require_git_sha(self.code_sha, field="code_sha")
        if self.decision_timestamp_ms <= 0:
            raise ShadowRuntimeError("runtime replay decision timestamp must be > 0")
        for ratio, field_name in (
            (self.take_profit_ratio, "take_profit_ratio"),
            (self.stop_loss_ratio, "stop_loss_ratio"),
        ):
            _require_positive(ratio, field=field_name)
        if not (
            self.identities_match
            and self.policy_match
            and self.replay_match
            and self.execution_authority_absent
        ):
            raise ShadowRuntimeError("runtime replay parity evidence is not accepted")


PaperParityEvidence = ReplayShadowParityEvidence | RuntimeReplayParityEvidence


@dataclass(frozen=True, slots=True)
class ShadowRuntimeStepResult:
    state: ShadowRuntimeState
    snapshot: PortalObservabilitySnapshot
    decisions: tuple[ShadowDecisionEvidence, ...]
    closed_positions: tuple[ClosedSimulatedPosition, ...]


def verify_replay_shadow_parity(
    *,
    shadow_decision: ShadowDecisionEvidence,
    label: CandidateLabel,
) -> ReplayShadowParityEvidence:
    intent = shadow_decision.trade_intent
    candidate = shadow_decision.candidate
    if intent is None or candidate is None:
        raise ShadowRuntimeError("parity requires a directional shadow decision")
    if label.outcome is LabelOutcome.MISSING_ENTRY:
        raise ShadowRuntimeError("missing-entry label cannot prove runtime parity")
    identities_match = (
        candidate.symbol == label.symbol
        and candidate.side is label.side
        and candidate.decision_timestamp_ms == label.decision_timestamp_ms
        and intent.dataset_hash == label.dataset_manifest_sha256
        and intent.code_sha == label.source_commit_sha
    )
    policy_match = (
        intent.take_profit_ratio == label.take_profit_ratio
        and intent.stop_loss_ratio == label.stop_loss_ratio
    )
    execution_authority_absent = (
        not label.execution_enabled
        and not label.live_capital_authorized
        and not label.trading_credentials_present
        and label.orders_submitted == 0
    )
    payload = {
        "shadow_decision_id": shadow_decision.shadow_decision_id,
        "label_id": label.label_id,
        "symbol": label.symbol,
        "side": label.side.value,
        "decision_timestamp_ms": label.decision_timestamp_ms,
        "dataset_hash": intent.dataset_hash,
        "code_sha": intent.code_sha,
        "take_profit_ratio": intent.take_profit_ratio,
        "stop_loss_ratio": intent.stop_loss_ratio,
        "label_outcome": label.outcome.value,
        "identities_match": identities_match,
        "policy_match": policy_match,
        "execution_authority_absent": execution_authority_absent,
    }
    return ReplayShadowParityEvidence(
        schema_version=RUNTIME_PARITY_SCHEMA_VERSION,
        parity_id=canonical_sha256(
            {"schema_version": RUNTIME_PARITY_SCHEMA_VERSION, "payload": payload}
        ),
        shadow_decision_id=shadow_decision.shadow_decision_id,
        label_id=label.label_id,
        symbol=label.symbol,
        side=label.side,
        decision_timestamp_ms=label.decision_timestamp_ms,
        dataset_hash=intent.dataset_hash,
        code_sha=intent.code_sha,
        take_profit_ratio=intent.take_profit_ratio,
        stop_loss_ratio=intent.stop_loss_ratio,
        label_outcome=label.outcome,
        identities_match=identities_match,
        policy_match=policy_match,
        execution_authority_absent=execution_authority_absent,
    )


def verify_runtime_replay_parity(
    *,
    shadow_decision: ShadowDecisionEvidence,
    replayed_decision: ShadowDecisionEvidence,
) -> RuntimeReplayParityEvidence:
    if shadow_decision.status is not ShadowStatus.SIMULATED_ALLOWED:
        raise ShadowRuntimeError("runtime replay parity requires an allowed decision")
    if replayed_decision.status is not ShadowStatus.SIMULATED_ALLOWED:
        raise ShadowRuntimeError("runtime replay changed the allowed decision status")
    intent = shadow_decision.trade_intent
    replay_intent = replayed_decision.trade_intent
    candidate = shadow_decision.candidate
    replay_candidate = replayed_decision.candidate
    if intent is None or replay_intent is None or candidate is None or replay_candidate is None:
        raise ShadowRuntimeError("runtime replay parity requires directional decisions")
    original_sha256 = canonical_sha256(shadow_decision)
    replayed_sha256 = canonical_sha256(replayed_decision)
    identities_match = (
        shadow_decision.shadow_decision_id == replayed_decision.shadow_decision_id
        and candidate.candidate_id == replay_candidate.candidate_id
        and candidate.symbol == replay_candidate.symbol
        and candidate.side is replay_candidate.side
        and candidate.decision_timestamp_ms == replay_candidate.decision_timestamp_ms
        and intent.trade_intent_id == replay_intent.trade_intent_id
        and intent.dataset_hash == replay_intent.dataset_hash
        and intent.code_sha == replay_intent.code_sha
    )
    policy_match = (
        intent.take_profit_ratio == replay_intent.take_profit_ratio
        and intent.stop_loss_ratio == replay_intent.stop_loss_ratio
        and intent.requested_base_risk_ratio == replay_intent.requested_base_risk_ratio
        and intent.requested_leverage == replay_intent.requested_leverage
        and intent.dca_plan == replay_intent.dca_plan
        and shadow_decision.risk_decision == replayed_decision.risk_decision
    )
    replay_match = original_sha256 == replayed_sha256
    execution_authority_absent = True
    payload = {
        "shadow_decision_id": shadow_decision.shadow_decision_id,
        "original_evidence_sha256": original_sha256,
        "replayed_evidence_sha256": replayed_sha256,
        "symbol": candidate.symbol,
        "side": candidate.side.value,
        "decision_timestamp_ms": candidate.decision_timestamp_ms,
        "dataset_hash": intent.dataset_hash,
        "code_sha": intent.code_sha,
        "take_profit_ratio": intent.take_profit_ratio,
        "stop_loss_ratio": intent.stop_loss_ratio,
        "identities_match": identities_match,
        "policy_match": policy_match,
        "replay_match": replay_match,
        "execution_authority_absent": execution_authority_absent,
    }
    return RuntimeReplayParityEvidence(
        schema_version=RUNTIME_REPLAY_PARITY_SCHEMA_VERSION,
        parity_id=canonical_sha256(
            {"schema_version": RUNTIME_REPLAY_PARITY_SCHEMA_VERSION, "payload": payload}
        ),
        shadow_decision_id=shadow_decision.shadow_decision_id,
        original_evidence_sha256=original_sha256,
        replayed_evidence_sha256=replayed_sha256,
        symbol=candidate.symbol,
        side=candidate.side,
        decision_timestamp_ms=candidate.decision_timestamp_ms,
        dataset_hash=intent.dataset_hash,
        code_sha=intent.code_sha,
        take_profit_ratio=intent.take_profit_ratio,
        stop_loss_ratio=intent.stop_loss_ratio,
        identities_match=identities_match,
        policy_match=policy_match,
        replay_match=replay_match,
        execution_authority_absent=execution_authority_absent,
    )
