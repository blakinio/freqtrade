from __future__ import annotations

import hashlib
import json
import shutil
import tempfile
from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path
from typing import TypeAlias
from uuid import NAMESPACE_URL, UUID, uuid5

from pydantic import BaseModel

from ai_platform.portal.contracts.common import CorrelationContext
from ai_platform.portal.contracts.environment import Environment
from ai_platform.portal.contracts.execution import RuntimeHealthState
from ai_platform.portal.contracts.risk import (
    ApprovedExecutionIntent,
    RejectedExecutionIntent,
    RiskDecisionOutcome,
    TradeSide,
)
from ai_platform.portal.contracts.risk import (
    TradeIntent as PortalTradeIntent,
)
from ai_platform.portal.risk.schema import RiskEvaluationSnapshot
from ai_platform.wickhunter.contracts import (
    BotMode,
    RiskOutcome,
    TradeDirection,
    WickHunterTradeIntent,
)
from ai_platform.wickhunter.contracts import (
    RiskDecision as WickHunterRiskDecision,
)


PortalRiskEvaluationResult: TypeAlias = ApprovedExecutionIntent | RejectedExecutionIntent


class PortalRiskBridgeError(RuntimeError):
    """Base error for fail-closed portal risk integration."""


class PortalRiskBridgeBlockedError(PortalRiskBridgeError):
    """The WickHunter evidence is not eligible for portal risk evaluation."""


class PortalRiskEvidenceMismatchError(PortalRiskBridgeError):
    """Portal result evidence does not match the prepared request."""


def _require_positive(value: Decimal, *, field: str) -> None:
    if not value.is_finite() or value <= 0:
        raise ValueError(f"{field} must be finite and > 0")


def _require_non_negative(value: Decimal, *, field: str) -> None:
    if not value.is_finite() or value < 0:
        raise ValueError(f"{field} must be finite and >= 0")


def _utc_from_ms(value: int) -> datetime:
    if value <= 0:
        raise ValueError("timestamp milliseconds must be > 0")
    return datetime.fromtimestamp(value / 1000, tz=UTC)


def _deterministic_uuid(*parts: str) -> UUID:
    return uuid5(NAMESPACE_URL, "wickhunter:" + ":".join(parts))


def _canonical_json(payload: object) -> str:
    return json.dumps(payload, ensure_ascii=True, separators=(",", ":"), sort_keys=True)


def _sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _model_payload(model: BaseModel) -> object:
    return model.model_dump(mode="json")


@dataclass(frozen=True, slots=True)
class PortalRiskSnapshotSource:
    account_equity_quote: Decimal
    current_gross_exposure_quote: Decimal
    current_open_positions: int
    daily_loss_quote: Decimal
    current_drawdown: Decimal
    runtime_health: RuntimeHealthState
    observed_at_ms: int

    def __post_init__(self) -> None:
        _require_positive(self.account_equity_quote, field="account_equity_quote")
        _require_non_negative(
            self.current_gross_exposure_quote,
            field="current_gross_exposure_quote",
        )
        _require_non_negative(self.daily_loss_quote, field="daily_loss_quote")
        if self.current_open_positions < 0:
            raise ValueError("current_open_positions must be >= 0")
        if (
            not self.current_drawdown.is_finite()
            or self.current_drawdown < 0
            or self.current_drawdown > 1
        ):
            raise ValueError("current_drawdown must be within [0, 1]")
        if self.observed_at_ms <= 0:
            raise ValueError("observed_at_ms must be > 0")


@dataclass(frozen=True, slots=True)
class PortalRiskBinding:
    tenant_id: str
    source_actor_id: str
    environment: Environment
    portal_risk_policy_version: str

    def __post_init__(self) -> None:
        values = {
            "tenant_id": self.tenant_id,
            "source_actor_id": self.source_actor_id,
            "portal_risk_policy_version": self.portal_risk_policy_version,
        }
        for field_name, value in values.items():
            if not value.strip():
                raise ValueError(f"{field_name} must be non-empty")
        if self.environment is Environment.PRODUCTION:
            raise PortalRiskBridgeBlockedError(
                "WickHunter portal risk integration forbids production"
            )


@dataclass(frozen=True, slots=True)
class PortalRiskRequestEvidence:
    schema_version: str
    source_trade_intent_id: str
    source_risk_decision_id: str
    portal_risk_policy_version: str
    portal_trade_intent: PortalTradeIntent
    portal_snapshot: RiskEvaluationSnapshot
    snapshot_observed_at_ms: int
    prepared_at_ms: int
    execution_adapter_authorized: bool = False
    live_capital_authorized: bool = False

    def __post_init__(self) -> None:
        if not self.schema_version.strip():
            raise ValueError("schema_version must be non-empty")
        if self.snapshot_observed_at_ms > self.prepared_at_ms:
            raise ValueError("portal snapshot cannot be observed after request preparation")
        if self.execution_adapter_authorized or self.live_capital_authorized:
            raise ValueError("WH-06 evidence cannot authorize execution or live capital")
        if self.portal_trade_intent.environment is Environment.PRODUCTION:
            raise ValueError("production portal trade intents are forbidden")

    def payload(self) -> dict[str, object]:
        return {
            "schema_version": self.schema_version,
            "source_trade_intent_id": self.source_trade_intent_id,
            "source_risk_decision_id": self.source_risk_decision_id,
            "portal_risk_policy_version": self.portal_risk_policy_version,
            "portal_trade_intent": _model_payload(self.portal_trade_intent),
            "portal_snapshot": _model_payload(self.portal_snapshot),
            "snapshot_observed_at_ms": self.snapshot_observed_at_ms,
            "prepared_at_ms": self.prepared_at_ms,
            "execution_adapter_authorized": self.execution_adapter_authorized,
            "live_capital_authorized": self.live_capital_authorized,
        }

    @property
    def request_sha256(self) -> str:
        return _sha256_text(_canonical_json(self.payload()))


@dataclass(frozen=True, slots=True)
class PortalRiskArtifactSet:
    root: Path
    request_path: Path
    result_path: Path | None
    manifest_path: Path
    request_sha256: str
    result_sha256: str | None
    manifest_sha256: str


def _validate_mode_environment(mode: BotMode, environment: Environment) -> None:
    allowed = {
        BotMode.RESEARCH: {Environment.RESEARCH, Environment.TEST},
        BotMode.SHADOW: {Environment.TEST, Environment.STAGING},
        BotMode.PAPER: {Environment.STAGING},
    }
    if environment not in allowed.get(mode, set()):
        raise PortalRiskBridgeBlockedError(
            f"mode {mode.value} is not authorized for environment {environment.value}"
        )


def build_portal_risk_request(
    *,
    intent: WickHunterTradeIntent,
    local_decision: WickHunterRiskDecision,
    binding: PortalRiskBinding,
    snapshot: PortalRiskSnapshotSource,
) -> PortalRiskRequestEvidence:
    if local_decision.trade_intent_id != intent.trade_intent_id:
        raise PortalRiskBridgeBlockedError("local risk decision references another intent")
    if local_decision.outcome is not RiskOutcome.ALLOW:
        raise PortalRiskBridgeBlockedError("local risk veto blocks portal risk submission")
    if local_decision.risk_policy_version != binding.portal_risk_policy_version:
        raise PortalRiskBridgeBlockedError("portal and local risk policy versions differ")
    if snapshot.observed_at_ms > local_decision.evaluated_at_ms:
        raise PortalRiskBridgeBlockedError("portal snapshot contains future evidence")
    _validate_mode_environment(intent.mode, binding.environment)

    planned_risk_ratio = max(
        intent.requested_base_risk_ratio,
        intent.dca_plan.maximum_total_risk_ratio,
    )
    intent_notional = (
        snapshot.account_equity_quote
        * planned_risk_ratio
        * intent.requested_leverage
    )
    _require_positive(intent_notional, field="intent_notional")
    amount = intent_notional / intent.decision_price
    _require_positive(amount, field="portal amount")

    correlation = CorrelationContext(
        request_id=_deterministic_uuid("request", intent.trade_intent_id),
        correlation_id=_deterministic_uuid("correlation", intent.trade_intent_id),
        causation_id=_deterministic_uuid("causation", intent.candidate_id),
    )
    prediction_id = (
        _deterministic_uuid("prediction", intent.score_id)
        if intent.model_version is not None
        else None
    )
    portal_intent = PortalTradeIntent(
        trade_intent_id=_deterministic_uuid("portal-intent", intent.trade_intent_id),
        tenant_id=binding.tenant_id,
        bot_id=intent.bot_instance,
        prediction_id=prediction_id,
        source_actor_id=binding.source_actor_id,
        pair=intent.symbol,
        side=TradeSide.BUY if intent.side is TradeDirection.LONG else TradeSide.SELL,
        amount=amount,
        environment=binding.environment,
        created_at=_utc_from_ms(intent.decision_timestamp_ms),
        context=correlation,
    )
    portal_snapshot = RiskEvaluationSnapshot(
        intent_notional=intent_notional,
        projected_gross_exposure=(
            snapshot.current_gross_exposure_quote + intent_notional
        ),
        projected_open_positions=snapshot.current_open_positions + 1,
        daily_loss=snapshot.daily_loss_quote,
        current_drawdown=snapshot.current_drawdown,
        runtime_health=snapshot.runtime_health,
    )
    return PortalRiskRequestEvidence(
        schema_version="wickhunter-portal-risk-request-v1",
        source_trade_intent_id=intent.trade_intent_id,
        source_risk_decision_id=local_decision.risk_decision_id,
        portal_risk_policy_version=binding.portal_risk_policy_version,
        portal_trade_intent=portal_intent,
        portal_snapshot=portal_snapshot,
        snapshot_observed_at_ms=snapshot.observed_at_ms,
        prepared_at_ms=local_decision.evaluated_at_ms,
    )


def validate_portal_risk_result(
    *,
    request: PortalRiskRequestEvidence,
    result: PortalRiskEvaluationResult,
) -> None:
    if result.tenant_id != request.portal_trade_intent.tenant_id:
        raise PortalRiskEvidenceMismatchError("portal result tenant mismatch")
    if result.trade_intent != request.portal_trade_intent:
        raise PortalRiskEvidenceMismatchError("portal result trade intent mismatch")
    if (
        result.risk_decision.trade_intent_id
        != request.portal_trade_intent.trade_intent_id
    ):
        raise PortalRiskEvidenceMismatchError("portal decision intent identity mismatch")
    if (
        result.risk_decision.risk_policy_version
        != request.portal_risk_policy_version
    ):
        raise PortalRiskEvidenceMismatchError("portal risk policy version mismatch")
    if (
        result.context.correlation_id
        != request.portal_trade_intent.context.correlation_id
    ):
        raise PortalRiskEvidenceMismatchError("portal result correlation mismatch")
    expected = (
        RiskDecisionOutcome.APPROVED
        if isinstance(result, ApprovedExecutionIntent)
        else RiskDecisionOutcome.REJECTED
    )
    if result.risk_decision.decision is not expected:
        raise PortalRiskEvidenceMismatchError("portal result wrapper/outcome mismatch")


def _result_payload(result: PortalRiskEvaluationResult) -> dict[str, object]:
    return {
        "result_kind": (
            "approved"
            if isinstance(result, ApprovedExecutionIntent)
            else "rejected"
        ),
        "result": _model_payload(result),
        "order_submission_performed": False,
        "execution_adapter_called": False,
        "live_capital_authorized": False,
    }


def _write_json(path: Path, payload: object) -> None:
    path.write_text(_canonical_json(payload) + "\n", encoding="utf-8")


def persist_portal_risk_evidence(
    *,
    output_root: Path,
    request: PortalRiskRequestEvidence,
    result: PortalRiskEvaluationResult | None = None,
) -> PortalRiskArtifactSet:
    if result is not None:
        validate_portal_risk_result(request=request, result=result)

    final_root = output_root / request.request_sha256
    if final_root.exists():
        raise FileExistsError(f"portal risk evidence already exists: {final_root}")
    output_root.mkdir(parents=True, exist_ok=True)
    temp_root = Path(
        tempfile.mkdtemp(
            prefix=f".{request.request_sha256}.tmp-",
            dir=output_root,
        )
    )
    try:
        request_path = temp_root / "request.json"
        _write_json(request_path, request.payload())
        request_file_sha = _sha256_file(request_path)

        result_path: Path | None = None
        result_file_sha: str | None = None
        if result is not None:
            result_path = temp_root / "result.json"
            _write_json(result_path, _result_payload(result))
            result_file_sha = _sha256_file(result_path)

        manifest_without_hash: dict[str, object] = {
            "schema_version": "wickhunter-portal-risk-bundle-v1",
            "request_sha256": request.request_sha256,
            "status": (
                "prepared"
                if result is None
                else (
                    "approved"
                    if isinstance(result, ApprovedExecutionIntent)
                    else "rejected"
                )
            ),
            "files": {
                "request.json": request_file_sha,
                **(
                    {"result.json": result_file_sha}
                    if result_file_sha is not None
                    else {}
                ),
            },
            "order_submission_performed": False,
            "execution_adapter_called": False,
            "live_capital_authorized": False,
        }
        manifest_sha = _sha256_text(_canonical_json(manifest_without_hash))
        manifest_payload = {
            **manifest_without_hash,
            "manifest_sha256": manifest_sha,
        }
        manifest_path = temp_root / "manifest.json"
        _write_json(manifest_path, manifest_payload)

        temp_root.rename(final_root)
        return PortalRiskArtifactSet(
            root=final_root,
            request_path=final_root / request_path.name,
            result_path=(
                final_root / result_path.name if result_path is not None else None
            ),
            manifest_path=final_root / manifest_path.name,
            request_sha256=request.request_sha256,
            result_sha256=result_file_sha,
            manifest_sha256=manifest_sha,
        )
    except Exception:
        shutil.rmtree(temp_root, ignore_errors=True)
        raise
