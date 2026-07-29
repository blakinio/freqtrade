from __future__ import annotations

from collections.abc import Callable, Mapping, Sequence
from datetime import UTC, datetime
from enum import StrEnum
from pathlib import Path
from typing import Any, Literal, Protocol, Self

from pydantic import Field, field_validator, model_validator
from strategy_engine.domain.models import CanonicalModel, ShadowDecisionEvidence

from ai_platform.portal.contracts.bots import BotInstance, BotObservedState
from ai_platform.portal.contracts.common import CorrelationContext
from ai_platform.portal.contracts.environment import Environment, ExecutionMode
from ai_platform.portal.contracts.execution import ExecutionAdapter, RuntimeHealthState
from ai_platform.portal.execution.errors import ExecutionAdapterError
from ai_platform.portal.risk.schema import RiskEvaluationSnapshot, RiskPolicyLimits
from ai_platform.research.strategy_engine.ase00_adapter import AcceptedSyntheticEvent


Clock = Callable[[], datetime]


class Ase03Mode(StrEnum):
    SHADOW = "shadow"
    PAPER = "paper"


class Ase03Status(StrEnum):
    ADMITTED = "admitted"
    REJECTED = "rejected"
    ROLLED_BACK = "rolled_back"
    ROLLBACK_FAILED = "rollback_failed"


class Ase03IntegrationError(RuntimeError):
    def __init__(self, reason_code: str, message: str) -> None:
        super().__init__(message)
        self.reason_code = reason_code


class ShadowRunEngine(Protocol):
    def run(
        self,
        *,
        events: Sequence[AcceptedSyntheticEvent],
        strategy_document: Mapping[str, object],
        decision_time: datetime,
        risk_limits: RiskPolicyLimits,
        risk_snapshot: RiskEvaluationSnapshot,
        evidence_path: Path | None = None,
        generated_by_ai: bool = False,
        final_holdout_reused: bool = False,
    ) -> ShadowDecisionEvidence: ...


class SimulatorParityReport(CanonicalModel):
    schema_version: Literal["1.0.0"] = "1.0.0"
    simulator_evidence_hash: str = Field(pattern=r"^[0-9a-f]{64}$")
    shadow_evidence_hash: str = Field(pattern=r"^[0-9a-f]{64}$")
    passed: bool
    mismatch_codes: tuple[str, ...] = ()
    report_hash: str = Field(pattern=r"^[0-9a-f]{64}$")

    @model_validator(mode="after")
    def validate_consistency(self) -> Self:
        if self.passed and self.mismatch_codes:
            raise ValueError("a passing parity report cannot contain mismatch codes")
        if not self.passed and not self.mismatch_codes:
            raise ValueError("a failed parity report requires mismatch codes")
        expected = self.canonical_sha256(exclude={"report_hash"})
        if self.report_hash != expected:
            raise ValueError("report_hash does not match canonical parity report")
        return self

    @classmethod
    def create(cls, **values: Any) -> Self:
        payload = dict(values)
        payload.pop("report_hash", None)
        provisional = cls.model_construct(**payload, report_hash="0" * 64)
        digest = provisional.canonical_sha256(exclude={"report_hash"})
        return cls(**payload, report_hash=digest)


class Ase03AuditRecord(CanonicalModel):
    schema_version: Literal["1.0.0"] = "1.0.0"
    record_type: Literal["admission", "rollback"]
    idempotency_key: str = Field(min_length=1)
    occurred_at: datetime
    mode: Ase03Mode
    status: Ase03Status
    tenant_id: str = Field(min_length=1)
    bot_id: str = Field(min_length=1)
    strategy_id: str = Field(min_length=1)
    strategy_version: str = Field(min_length=1)
    simulator_evidence_hash: str = Field(pattern=r"^[0-9a-f]{64}$")
    shadow_evidence_hash: str = Field(pattern=r"^[0-9a-f]{64}$")
    parity_report_hash: str = Field(pattern=r"^[0-9a-f]{64}$")
    risk_outcome: Literal["approved", "rejected", "no_signal"]
    runtime_id: str | None = None
    runtime_observed_state: str | None = None
    runtime_health: str | None = None
    source_admission_hash: str | None = Field(
        default=None,
        pattern=r"^[0-9a-f]{64}$",
    )
    evidence_refs: dict[str, str]
    reason_codes: tuple[str, ...]
    execution_submission_performed: Literal[False] = False
    no_order_submitted: Literal[True] = True
    record_hash: str = Field(pattern=r"^[0-9a-f]{64}$")

    @field_validator("occurred_at")
    @classmethod
    def require_utc(cls, value: datetime) -> datetime:
        if value.tzinfo is None or value.utcoffset() != UTC.utcoffset(value):
            raise ValueError("occurred_at must be timezone-aware UTC")
        return value

    @model_validator(mode="after")
    def verify_hash_and_shape(self) -> Self:
        if self.record_type == "rollback" and self.source_admission_hash is None:
            raise ValueError("rollback record requires source_admission_hash")
        if self.record_type == "admission" and self.source_admission_hash is not None:
            raise ValueError("admission record cannot contain source_admission_hash")
        expected = self.canonical_sha256(exclude={"record_hash"})
        if self.record_hash != expected:
            raise ValueError("record_hash does not match canonical audit record")
        return self

    @classmethod
    def create(cls, **values: Any) -> Self:
        payload = dict(values)
        payload.pop("record_hash", None)
        provisional = cls.model_construct(**payload, record_hash="0" * 64)
        digest = provisional.canonical_sha256(exclude={"record_hash"})
        return cls(**payload, record_hash=digest)


class Ase03AuditStore:
    """Append-only evidence and admission/rollback records."""

    def __init__(self, root: Path) -> None:
        self.root = root
        self.evidence_root = root / "evidence"
        self.audit_path = root / "audit.jsonl"

    def find(self, idempotency_key: str) -> Ase03AuditRecord | None:
        for record in self.records():
            if record.idempotency_key == idempotency_key:
                return record
        return None

    def persist_evidence(self, channel: str, evidence: ShadowDecisionEvidence) -> str:
        if channel not in {"simulator", "shadow"}:
            raise Ase03IntegrationError(
                "EVIDENCE_CHANNEL_INVALID",
                f"unsupported channel: {channel}",
            )
        relative = Path("evidence") / f"{channel}-{evidence.evidence_hash}.json"
        self._persist(relative, evidence.canonical_json() + "\n", "EVIDENCE_CONFLICT")
        return relative.as_posix()

    def persist_parity(self, report: SimulatorParityReport) -> str:
        relative = Path("evidence") / f"parity-{report.report_hash}.json"
        self._persist(relative, report.canonical_json() + "\n", "PARITY_EVIDENCE_CONFLICT")
        return relative.as_posix()

    def append(self, record: Ase03AuditRecord) -> Ase03AuditRecord:
        existing = self.find(record.idempotency_key)
        if existing is not None:
            if existing.record_hash != record.record_hash:
                raise Ase03IntegrationError(
                    "AUDIT_IDEMPOTENCY_CONFLICT",
                    "idempotency key maps to a different ASE-03 audit record",
                )
            return existing
        self.root.mkdir(parents=True, exist_ok=True)
        with self.audit_path.open("a", encoding="utf-8") as handle:
            handle.write(record.canonical_json() + "\n")
        return record

    def records(self) -> tuple[Ase03AuditRecord, ...]:
        if not self.audit_path.exists():
            return ()
        return tuple(
            Ase03AuditRecord.model_validate_json(line)
            for line in self.audit_path.read_text(encoding="utf-8").splitlines()
            if line.strip()
        )

    def _persist(self, relative: Path, encoded: str, reason_code: str) -> None:
        path = self.root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        if path.exists():
            if path.read_text(encoding="utf-8") != encoded:
                raise Ase03IntegrationError(
                    reason_code,
                    f"immutable evidence path contains conflicting payload: {relative}",
                )
            return
        path.write_text(encoded, encoding="utf-8")


def compare_simulator_shadow(
    simulator: ShadowDecisionEvidence,
    shadow: ShadowDecisionEvidence,
) -> SimulatorParityReport:
    mismatch_codes: list[str] = []
    simulator_identity = (
        simulator.decision_time,
        simulator.symbol,
        simulator.timeframe,
        simulator.strategy_id,
        simulator.strategy_version,
    )
    shadow_identity = (
        shadow.decision_time,
        shadow.symbol,
        shadow.timeframe,
        shadow.strategy_id,
        shadow.strategy_version,
    )
    if simulator_identity != shadow_identity:
        mismatch_codes.append("PARITY_IDENTITY_MISMATCH")
    if (simulator.data_hash, simulator.config_hash, simulator.code_hash) != (
        shadow.data_hash,
        shadow.config_hash,
        shadow.code_hash,
    ):
        mismatch_codes.append("PARITY_INPUT_HASH_MISMATCH")
    if tuple(record.canonical_sha256() for record in simulator.feature_records) != tuple(
        record.canonical_sha256() for record in shadow.feature_records
    ):
        mismatch_codes.append("PARITY_FEATURE_MISMATCH")
    simulator_signal = None if simulator.signal is None else simulator.signal.canonical_sha256()
    shadow_signal = None if shadow.signal is None else shadow.signal.canonical_sha256()
    if simulator_signal != shadow_signal:
        mismatch_codes.append("PARITY_SIGNAL_MISMATCH")
    if simulator.risk_outcome != shadow.risk_outcome:
        mismatch_codes.append("PARITY_RISK_MISMATCH")
    if not simulator.no_order_submitted or not shadow.no_order_submitted:
        mismatch_codes.append("PARITY_ORDER_BOUNDARY_BROKEN")
    return SimulatorParityReport.create(
        simulator_evidence_hash=simulator.evidence_hash,
        shadow_evidence_hash=shadow.evidence_hash,
        passed=not mismatch_codes,
        mismatch_codes=tuple(mismatch_codes),
    )


class Ase03PaperShadowController:
    def __init__(
        self,
        *,
        simulator_engine: ShadowRunEngine,
        shadow_engine: ShadowRunEngine,
        execution_adapter: ExecutionAdapter,
        audit_store: Ase03AuditStore,
        clock: Clock | None = None,
    ) -> None:
        self.simulator_engine = simulator_engine
        self.shadow_engine = shadow_engine
        self.execution_adapter = execution_adapter
        self.audit_store = audit_store
        self.clock = clock or (lambda: datetime.now(UTC))

    def admit(
        self,
        *,
        idempotency_key: str,
        mode: Ase03Mode,
        tenant_id: str,
        bot_id: str,
        events: Sequence[AcceptedSyntheticEvent],
        strategy_document: Mapping[str, object],
        decision_time: datetime,
        risk_limits: RiskPolicyLimits,
        risk_snapshot: RiskEvaluationSnapshot,
        context: CorrelationContext,
        bot: BotInstance | None = None,
        generated_by_ai: bool = False,
        final_holdout_reused: bool = False,
    ) -> Ase03AuditRecord:
        existing = self.audit_store.find(idempotency_key)
        if existing is not None:
            if existing.record_type != "admission":
                raise Ase03IntegrationError(
                    "AUDIT_IDEMPOTENCY_CONFLICT",
                    "admission key is already used by another record type",
                )
            return existing

        simulator = self._run_engine(
            self.simulator_engine,
            events=events,
            strategy_document=strategy_document,
            decision_time=decision_time,
            risk_limits=risk_limits,
            risk_snapshot=risk_snapshot,
            generated_by_ai=generated_by_ai,
            final_holdout_reused=final_holdout_reused,
        )
        shadow = self._run_engine(
            self.shadow_engine,
            events=events,
            strategy_document=strategy_document,
            decision_time=decision_time,
            risk_limits=risk_limits,
            risk_snapshot=risk_snapshot,
            generated_by_ai=generated_by_ai,
            final_holdout_reused=final_holdout_reused,
        )
        parity = compare_simulator_shadow(simulator, shadow)
        evidence_refs = {
            "simulator": self.audit_store.persist_evidence("simulator", simulator),
            "shadow": self.audit_store.persist_evidence("shadow", shadow),
            "parity": self.audit_store.persist_parity(parity),
        }
        reason_codes = list(parity.mismatch_codes)
        status = Ase03Status.REJECTED
        runtime_id: str | None = None
        runtime_state: str | None = None
        runtime_health: str | None = None

        if not parity.passed:
            reason_codes.append("SIMULATOR_PARITY_REJECTED")
        elif shadow.risk_outcome != "approved" or shadow.signal is None:
            reason_codes.append("RISK_APPROVAL_REQUIRED")
        elif mode is Ase03Mode.SHADOW:
            status = Ase03Status.ADMITTED
            reason_codes.append("SHADOW_ADMITTED_NO_RUNTIME")
        else:
            (
                status,
                runtime_id,
                runtime_state,
                runtime_health,
                paper_reasons,
            ) = self._admit_paper(
                tenant_id=tenant_id,
                bot_id=bot_id,
                bot=bot,
                context=context,
            )
            reason_codes.extend(paper_reasons)

        record = Ase03AuditRecord.create(
            record_type="admission",
            idempotency_key=idempotency_key,
            occurred_at=self.clock(),
            mode=mode,
            status=status,
            tenant_id=tenant_id,
            bot_id=bot_id,
            strategy_id=shadow.strategy_id,
            strategy_version=shadow.strategy_version,
            simulator_evidence_hash=simulator.evidence_hash,
            shadow_evidence_hash=shadow.evidence_hash,
            parity_report_hash=parity.report_hash,
            risk_outcome=shadow.risk_outcome,
            runtime_id=runtime_id,
            runtime_observed_state=runtime_state,
            runtime_health=runtime_health,
            source_admission_hash=None,
            evidence_refs=evidence_refs,
            reason_codes=tuple(dict.fromkeys(reason_codes)),
        )
        return self.audit_store.append(record)

    def rollback(
        self,
        *,
        idempotency_key: str,
        admission: Ase03AuditRecord,
        context: CorrelationContext,
    ) -> Ase03AuditRecord:
        existing = self.audit_store.find(idempotency_key)
        if existing is not None:
            if existing.record_type != "rollback":
                raise Ase03IntegrationError(
                    "AUDIT_IDEMPOTENCY_CONFLICT",
                    "rollback key is already used by another record type",
                )
            return existing
        if admission.record_type != "admission" or admission.status is not Ase03Status.ADMITTED:
            raise Ase03IntegrationError(
                "ROLLBACK_SOURCE_INVALID",
                "rollback requires an admitted ASE-03 record",
            )

        status = Ase03Status.ROLLED_BACK
        runtime_state = admission.runtime_observed_state
        runtime_health = admission.runtime_health
        reason_codes: list[str] = []
        if admission.mode is Ase03Mode.SHADOW:
            reason_codes.append("SHADOW_ROLLBACK_NO_RUNTIME")
        else:
            try:
                stopped = self.execution_adapter.stop_bot(
                    admission.tenant_id,
                    admission.bot_id,
                    context,
                )
                runtime_state = stopped.observed_state.value
                if stopped.observed_state is BotObservedState.STOPPED:
                    reason_codes.append("PAPER_RUNTIME_STOPPED")
                else:
                    status = Ase03Status.ROLLBACK_FAILED
                    reason_codes.append("PAPER_RUNTIME_STOP_NOT_CONFIRMED")
                health = self.execution_adapter.get_health(
                    admission.tenant_id,
                    admission.bot_id,
                    context,
                )
                runtime_health = health.health.value
            except ExecutionAdapterError as exc:
                status = Ase03Status.ROLLBACK_FAILED
                reason_codes.append(exc.reason_code)

        record = Ase03AuditRecord.create(
            record_type="rollback",
            idempotency_key=idempotency_key,
            occurred_at=self.clock(),
            mode=admission.mode,
            status=status,
            tenant_id=admission.tenant_id,
            bot_id=admission.bot_id,
            strategy_id=admission.strategy_id,
            strategy_version=admission.strategy_version,
            simulator_evidence_hash=admission.simulator_evidence_hash,
            shadow_evidence_hash=admission.shadow_evidence_hash,
            parity_report_hash=admission.parity_report_hash,
            risk_outcome=admission.risk_outcome,
            runtime_id=admission.runtime_id,
            runtime_observed_state=runtime_state,
            runtime_health=runtime_health,
            source_admission_hash=admission.record_hash,
            evidence_refs=admission.evidence_refs,
            reason_codes=tuple(reason_codes),
        )
        return self.audit_store.append(record)

    @staticmethod
    def _run_engine(
        engine: ShadowRunEngine,
        *,
        events: Sequence[AcceptedSyntheticEvent],
        strategy_document: Mapping[str, object],
        decision_time: datetime,
        risk_limits: RiskPolicyLimits,
        risk_snapshot: RiskEvaluationSnapshot,
        generated_by_ai: bool,
        final_holdout_reused: bool,
    ) -> ShadowDecisionEvidence:
        return engine.run(
            events=events,
            strategy_document=strategy_document,
            decision_time=decision_time,
            risk_limits=risk_limits,
            risk_snapshot=risk_snapshot,
            generated_by_ai=generated_by_ai,
            final_holdout_reused=final_holdout_reused,
        )

    def _admit_paper(
        self,
        *,
        tenant_id: str,
        bot_id: str,
        bot: BotInstance | None,
        context: CorrelationContext,
    ) -> tuple[Ase03Status, str | None, str | None, str | None, tuple[str, ...]]:
        if bot is None:
            return Ase03Status.REJECTED, None, None, None, ("PAPER_BOT_REQUIRED",)
        if bot.tenant_id != tenant_id or bot.bot_id != bot_id:
            return Ase03Status.REJECTED, None, None, None, ("PAPER_BOT_SCOPE_MISMATCH",)
        if bot.spec.execution_mode is not ExecutionMode.DRY_RUN:
            return Ase03Status.REJECTED, None, None, None, ("PAPER_REQUIRES_DRY_RUN",)
        if bot.spec.environment not in {Environment.TEST, Environment.STAGING}:
            return Ase03Status.REJECTED, None, None, None, ("PAPER_ENVIRONMENT_FORBIDDEN",)

        runtime_id: str | None = None
        runtime_state: str | None = None
        runtime_health: str | None = None
        try:
            provisioned = self.execution_adapter.provision_bot(bot, context)
            runtime_id = provisioned.runtime_id
            runtime_state = provisioned.observed_state.value
            if provisioned.observed_state is BotObservedState.ERROR:
                return (
                    Ase03Status.REJECTED,
                    runtime_id,
                    runtime_state,
                    runtime_health,
                    ("PAPER_PROVISION_FAILED",),
                )
            started = self.execution_adapter.start_bot(bot, context)
            runtime_state = started.observed_state.value
            health = self.execution_adapter.get_health(tenant_id, bot_id, context)
            runtime_health = health.health.value
            if (
                started.observed_state is not BotObservedState.RUNNING
                or health.health is not RuntimeHealthState.HEALTHY
            ):
                self._stop_best_effort(tenant_id, bot_id, context)
                return (
                    Ase03Status.REJECTED,
                    runtime_id,
                    runtime_state,
                    runtime_health,
                    ("PAPER_RUNTIME_UNHEALTHY",),
                )
        except ExecutionAdapterError as exc:
            return (
                Ase03Status.REJECTED,
                runtime_id,
                runtime_state,
                runtime_health,
                (exc.reason_code,),
            )
        return (
            Ase03Status.ADMITTED,
            runtime_id,
            runtime_state,
            runtime_health,
            ("PAPER_DRY_RUN_ADMITTED", "ORDER_SUBMISSION_NOT_INVOKED"),
        )

    def _stop_best_effort(
        self,
        tenant_id: str,
        bot_id: str,
        context: CorrelationContext,
    ) -> None:
        try:
            self.execution_adapter.stop_bot(tenant_id, bot_id, context)
        except ExecutionAdapterError:
            return
