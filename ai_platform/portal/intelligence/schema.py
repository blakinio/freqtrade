from __future__ import annotations

from decimal import Decimal
from enum import StrEnum
from uuid import UUID

from ai_platform.portal.contracts.common import ContractModel, NonEmptyStr, Sha256Hex, UtcDateTime
from ai_platform.portal.contracts.risk import TradeSide


class ReconciliationStatus(StrEnum):
    SYNCED = "SYNCED"
    PENDING = "PENDING"
    SOURCE_UNAVAILABLE = "SOURCE_UNAVAILABLE"
    MISMATCH = "MISMATCH"


class DiagnosisCode(StrEnum):
    PROFITABLE = "PROFITABLE"
    LOSS_WITHIN_EXPECTED_RISK = "LOSS_WITHIN_EXPECTED_RISK"
    LOSS_REQUIRES_REVIEW = "LOSS_REQUIRES_REVIEW"
    DATA_GAP = "DATA_GAP"


class InsightSeverity(StrEnum):
    INFO = "INFO"
    ATTENTION = "ATTENTION"
    SEVERE = "SEVERE"


class DecisionSnapshot(ContractModel):
    snapshot_id: UUID
    tenant_id: NonEmptyStr
    bot_id: NonEmptyStr
    trade_intent_id: UUID
    risk_decision_id: UUID
    config_revision: int
    strategy_version: NonEmptyStr
    model_version: NonEmptyStr
    risk_policy_version: NonEmptyStr
    source_runtime_id: NonEmptyStr
    pair: NonEmptyStr
    side: TradeSide
    amount: Decimal
    decision_at: UtcDateTime
    evidence_ref: NonEmptyStr
    evidence_sha256: Sha256Hex


class TradeOutcome(ContractModel):
    outcome_id: UUID
    tenant_id: NonEmptyStr
    trade_id: NonEmptyStr
    bot_id: NonEmptyStr
    source_runtime_id: NonEmptyStr
    pair: NonEmptyStr
    realized_pnl: Decimal
    fees: Decimal
    exit_reason: NonEmptyStr
    opened_at: UtcDateTime
    closed_at: UtcDateTime
    reconciliation_status: ReconciliationStatus
    loss_exceeded_risk_budget: bool = False


class DeterministicDiagnosis(ContractModel):
    diagnosis_id: UUID
    tenant_id: NonEmptyStr
    snapshot_id: UUID
    outcome_id: UUID
    code: DiagnosisCode
    reason_codes: tuple[NonEmptyStr, ...]
    evidence_links: tuple[NonEmptyStr, ...]
    created_at: UtcDateTime


class TradeInsight(ContractModel):
    insight_id: UUID
    tenant_id: NonEmptyStr
    diagnosis_id: UUID
    severity: InsightSeverity
    summary: NonEmptyStr
    synthesis_source: NonEmptyStr
    evidence_links: tuple[NonEmptyStr, ...]
    created_at: UtcDateTime


class TradeAnalysis(ContractModel):
    analysis_id: UUID
    tenant_id: NonEmptyStr
    snapshot: DecisionSnapshot
    outcome: TradeOutcome
    diagnosis: DeterministicDiagnosis
    insight: TradeInsight
    created_at: UtcDateTime
