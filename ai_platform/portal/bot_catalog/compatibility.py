from __future__ import annotations

from hashlib import sha256

from ai_platform.portal.bot_catalog.schema import (
    BotCatalogSnapshot,
    CatalogEntryState,
    CatalogTemplateEntry,
    ExchangeProfileCatalogEntry,
    ModelCatalogEntry,
    ModelRequirement,
    RiskPolicyCatalogEntry,
    RuntimeCatalogEntry,
    StrategyCatalogEntry,
)
from ai_platform.portal.contracts.bot_management.compatibility import (
    BotCompatibilityDecision,
    CompatibilityEvidenceRef,
    CompatibilityEvidenceType,
    CompatibilityReasonCode,
    CompatibilitySelection,
    CompatibilityStatus,
)
from ai_platform.portal.contracts.bot_management.templates import TradeDirection
from ai_platform.portal.contracts.common import UtcDateTime


class _CompatibilityAccumulator:
    def __init__(self, snapshot: BotCatalogSnapshot) -> None:
        self.snapshot = snapshot
        self.reasons: set[CompatibilityReasonCode] = set()
        self.evidence: dict[tuple[str, str, str, str], CompatibilityEvidenceRef] = {}

    def reject(self, reason: CompatibilityReasonCode) -> None:
        self.reasons.add(reason)

    def add_entry_evidence(
        self,
        evidence_type: CompatibilityEvidenceType,
        evidence_id: str,
        version: str,
        digest: str,
        state: CatalogEntryState,
    ) -> None:
        evidence = CompatibilityEvidenceRef(
            evidence_type=evidence_type,
            evidence_id=evidence_id,
            version=version,
            sha256=digest,
        )
        key = (evidence_type.value, evidence_id, version, digest)
        self.evidence[key] = evidence
        if state == CatalogEntryState.DEPRECATED:
            self.reject(CompatibilityReasonCode.EVIDENCE_STALE)
        elif state == CatalogEntryState.UNAVAILABLE:
            self.reject(CompatibilityReasonCode.EVIDENCE_MISSING)

    def add_missing_evidence(
        self,
        evidence_type: CompatibilityEvidenceType,
        evidence_id: str,
        version: str,
    ) -> None:
        proof = (
            f"{self.snapshot.catalog_id}:{self.snapshot.revision}:"
            f"{evidence_type.value}:{evidence_id}:{version}:missing"
        )
        self.add_entry_evidence(
            evidence_type,
            evidence_id,
            version,
            sha256(proof.encode("utf-8")).hexdigest(),
            CatalogEntryState.UNAVAILABLE,
        )

    def sorted_reasons(self) -> tuple[CompatibilityReasonCode, ...]:
        return tuple(sorted(self.reasons, key=lambda item: item.value))

    def sorted_evidence(self) -> tuple[CompatibilityEvidenceRef, ...]:
        return tuple(self.evidence[key] for key in sorted(self.evidence))


class BotCatalogCompatibilityEvaluator:
    def evaluate(
        self,
        snapshot: BotCatalogSnapshot,
        selection: CompatibilitySelection,
        decided_at: UtcDateTime,
    ) -> BotCompatibilityDecision:
        accumulator = _CompatibilityAccumulator(snapshot)
        template_entry = self._evaluate_template(snapshot, selection, accumulator)
        strategy_entry = self._evaluate_strategy(snapshot, selection, accumulator)
        model_entry = self._evaluate_model(snapshot, selection, template_entry, accumulator)
        exchange_entry = self._evaluate_exchange(snapshot, selection, accumulator)
        runtime_entry = self._evaluate_runtime(snapshot, selection, accumulator)
        risk_entry = self._evaluate_risk(snapshot, selection, accumulator)

        if template_entry is not None:
            self._evaluate_template_selection(template_entry, selection, accumulator)
        if strategy_entry is not None:
            self._evaluate_strategy_selection(strategy_entry, selection, accumulator)
        if model_entry is not None:
            self._evaluate_model_selection(model_entry, selection, accumulator)
        if exchange_entry is not None:
            self._evaluate_exchange_selection(exchange_entry, selection, accumulator)
        if runtime_entry is not None:
            self._evaluate_runtime_selection(runtime_entry, selection, accumulator)
        if risk_entry is not None:
            self._evaluate_risk_selection(risk_entry, selection, accumulator)

        reasons = accumulator.sorted_reasons()
        evidence = accumulator.sorted_evidence()
        decision_id = self._decision_id(snapshot, selection, reasons, evidence)
        status = CompatibilityStatus.COMPATIBLE if not reasons else CompatibilityStatus.REJECTED
        return BotCompatibilityDecision(
            decision_id=decision_id,
            tenant_id=selection.tenant_id,
            selection=selection,
            status=status,
            reason_codes=reasons,
            evidence_refs=evidence,
            decided_at=decided_at,
        )

    @staticmethod
    def _evaluate_template(
        snapshot: BotCatalogSnapshot,
        selection: CompatibilitySelection,
        accumulator: _CompatibilityAccumulator,
    ) -> CatalogTemplateEntry | None:
        exact = next(
            (
                entry
                for entry in snapshot.templates
                if entry.template.template_id == selection.template_ref.catalog_id
                and str(entry.template.revision) == selection.template_ref.version
            ),
            None,
        )
        if exact is None:
            same_template = any(
                entry.template.template_id == selection.template_ref.catalog_id
                for entry in snapshot.templates
            )
            accumulator.reject(
                CompatibilityReasonCode.TEMPLATE_REVISION_STALE
                if same_template
                else CompatibilityReasonCode.TEMPLATE_NOT_FOUND
            )
            accumulator.add_missing_evidence(
                CompatibilityEvidenceType.TEMPLATE,
                selection.template_ref.catalog_id,
                selection.template_ref.version,
            )
            return None
        accumulator.add_entry_evidence(
            CompatibilityEvidenceType.TEMPLATE,
            exact.template.template_id,
            str(exact.template.revision),
            exact.sha256,
            exact.state,
        )
        return exact

    @staticmethod
    def _evaluate_strategy(
        snapshot: BotCatalogSnapshot,
        selection: CompatibilitySelection,
        accumulator: _CompatibilityAccumulator,
    ) -> StrategyCatalogEntry | None:
        entry = next(
            (item for item in snapshot.strategies if item.version == selection.strategy_version),
            None,
        )
        if entry is None:
            accumulator.reject(CompatibilityReasonCode.STRATEGY_UNSUPPORTED)
            accumulator.add_missing_evidence(
                CompatibilityEvidenceType.STRATEGY,
                selection.strategy_version,
                selection.strategy_version,
            )
            return None
        accumulator.add_entry_evidence(
            CompatibilityEvidenceType.STRATEGY,
            entry.strategy_id,
            entry.version,
            entry.sha256,
            entry.state,
        )
        return entry

    @staticmethod
    def _evaluate_model(
        snapshot: BotCatalogSnapshot,
        selection: CompatibilitySelection,
        template_entry: CatalogTemplateEntry | None,
        accumulator: _CompatibilityAccumulator,
    ) -> ModelCatalogEntry | None:
        if selection.model_version is None:
            if (
                template_entry is not None
                and template_entry.model_requirement == ModelRequirement.REQUIRED
            ):
                accumulator.reject(CompatibilityReasonCode.MODEL_REQUIRED)
            return None
        entry = next(
            (item for item in snapshot.models if item.version == selection.model_version),
            None,
        )
        if entry is None:
            accumulator.reject(CompatibilityReasonCode.MODEL_UNSUPPORTED)
            accumulator.add_missing_evidence(
                CompatibilityEvidenceType.MODEL,
                selection.model_version,
                selection.model_version,
            )
            return None
        accumulator.add_entry_evidence(
            CompatibilityEvidenceType.MODEL,
            entry.model_id,
            entry.version,
            entry.sha256,
            entry.state,
        )
        return entry

    @staticmethod
    def _evaluate_exchange(
        snapshot: BotCatalogSnapshot,
        selection: CompatibilitySelection,
        accumulator: _CompatibilityAccumulator,
    ) -> ExchangeProfileCatalogEntry | None:
        entry = next(
            (
                item
                for item in snapshot.exchange_profiles
                if item.version == selection.exchange_profile_version
            ),
            None,
        )
        if entry is None:
            accumulator.reject(CompatibilityReasonCode.EXCHANGE_PROFILE_UNSUPPORTED)
            accumulator.add_missing_evidence(
                CompatibilityEvidenceType.EXCHANGE_PROFILE,
                selection.exchange_profile_version,
                selection.exchange_profile_version,
            )
            return None
        accumulator.add_entry_evidence(
            CompatibilityEvidenceType.EXCHANGE_PROFILE,
            entry.profile.profile_id,
            entry.version,
            entry.sha256,
            entry.state,
        )
        return entry

    @staticmethod
    def _evaluate_runtime(
        snapshot: BotCatalogSnapshot,
        selection: CompatibilitySelection,
        accumulator: _CompatibilityAccumulator,
    ) -> RuntimeCatalogEntry | None:
        entry = next(
            (item for item in snapshot.runtimes if item.version == selection.runtime_version),
            None,
        )
        if entry is None:
            accumulator.reject(CompatibilityReasonCode.RUNTIME_VERSION_UNSUPPORTED)
            accumulator.add_missing_evidence(
                CompatibilityEvidenceType.RUNTIME,
                selection.runtime_version,
                selection.runtime_version,
            )
            return None
        accumulator.add_entry_evidence(
            CompatibilityEvidenceType.RUNTIME,
            entry.runtime_id,
            entry.version,
            entry.sha256,
            entry.state,
        )
        return entry

    @staticmethod
    def _evaluate_risk(
        snapshot: BotCatalogSnapshot,
        selection: CompatibilitySelection,
        accumulator: _CompatibilityAccumulator,
    ) -> RiskPolicyCatalogEntry | None:
        entry = next(
            (
                item
                for item in snapshot.risk_policies
                if item.version == selection.risk_policy_version
            ),
            None,
        )
        if entry is None:
            accumulator.reject(CompatibilityReasonCode.RISK_POLICY_UNSUPPORTED)
            accumulator.add_missing_evidence(
                CompatibilityEvidenceType.RISK_POLICY,
                selection.risk_policy_version,
                selection.risk_policy_version,
            )
            return None
        accumulator.add_entry_evidence(
            CompatibilityEvidenceType.RISK_POLICY,
            entry.risk_policy_id,
            entry.version,
            entry.sha256,
            entry.state,
        )
        return entry

    @staticmethod
    def _evaluate_template_selection(
        entry: CatalogTemplateEntry,
        selection: CompatibilitySelection,
        accumulator: _CompatibilityAccumulator,
    ) -> None:
        template = entry.template
        if selection.strategy_version not in template.supported_strategy_versions:
            accumulator.reject(CompatibilityReasonCode.STRATEGY_UNSUPPORTED)
        if selection.model_version is not None:
            if entry.model_requirement == ModelRequirement.FORBIDDEN:
                accumulator.reject(CompatibilityReasonCode.MODEL_UNSUPPORTED)
            elif selection.model_version not in template.supported_model_versions:
                accumulator.reject(CompatibilityReasonCode.MODEL_UNSUPPORTED)
        if selection.exchange_profile_version not in template.supported_exchange_profile_versions:
            accumulator.reject(CompatibilityReasonCode.EXCHANGE_PROFILE_UNSUPPORTED)
        if selection.market_type not in template.supported_market_types:
            accumulator.reject(CompatibilityReasonCode.MARKET_TYPE_UNSUPPORTED)
        if selection.direction not in template.supported_directions:
            accumulator.reject(CompatibilityReasonCode.DIRECTION_UNSUPPORTED)
        if selection.execution_mode not in template.supported_execution_modes:
            accumulator.reject(CompatibilityReasonCode.EXECUTION_MODE_UNSUPPORTED)
        selected = set(selection.policy_families)
        required = set(template.required_policy_families)
        allowed = required | set(template.optional_policy_families)
        if not required.issubset(selected):
            accumulator.reject(CompatibilityReasonCode.POLICY_FAMILY_MISSING)
        if not selected.issubset(allowed):
            accumulator.reject(CompatibilityReasonCode.POLICY_FAMILY_UNSUPPORTED)

    @staticmethod
    def _evaluate_strategy_selection(
        entry: StrategyCatalogEntry,
        selection: CompatibilitySelection,
        accumulator: _CompatibilityAccumulator,
    ) -> None:
        if selection.market_type not in entry.supported_market_types:
            accumulator.reject(CompatibilityReasonCode.MARKET_TYPE_UNSUPPORTED)
        if selection.direction not in entry.supported_directions:
            accumulator.reject(CompatibilityReasonCode.DIRECTION_UNSUPPORTED)
        if selection.execution_mode not in entry.supported_execution_modes:
            accumulator.reject(CompatibilityReasonCode.EXECUTION_MODE_UNSUPPORTED)
        if selection.model_version is not None:
            if selection.model_version not in entry.supported_model_versions:
                accumulator.reject(CompatibilityReasonCode.MODEL_UNSUPPORTED)
        if selection.runtime_version not in entry.supported_runtime_versions:
            accumulator.reject(CompatibilityReasonCode.RUNTIME_VERSION_UNSUPPORTED)
        if selection.risk_policy_version not in entry.supported_risk_policy_versions:
            accumulator.reject(CompatibilityReasonCode.RISK_POLICY_UNSUPPORTED)
        if not set(selection.policy_families).issubset(entry.supported_policy_families):
            accumulator.reject(CompatibilityReasonCode.POLICY_FAMILY_UNSUPPORTED)

    @staticmethod
    def _evaluate_model_selection(
        entry: ModelCatalogEntry,
        selection: CompatibilitySelection,
        accumulator: _CompatibilityAccumulator,
    ) -> None:
        if selection.strategy_version not in entry.compatible_strategy_versions:
            accumulator.reject(CompatibilityReasonCode.MODEL_UNSUPPORTED)
        if selection.runtime_version not in entry.supported_runtime_versions:
            accumulator.reject(CompatibilityReasonCode.RUNTIME_VERSION_UNSUPPORTED)

    @staticmethod
    def _evaluate_exchange_selection(
        entry: ExchangeProfileCatalogEntry,
        selection: CompatibilitySelection,
        accumulator: _CompatibilityAccumulator,
    ) -> None:
        if selection.market_type not in entry.profile.market_types:
            accumulator.reject(CompatibilityReasonCode.MARKET_TYPE_UNSUPPORTED)
        if selection.direction in (TradeDirection.SHORT, TradeDirection.BOTH):
            if not entry.profile.supports_short:
                accumulator.reject(CompatibilityReasonCode.DIRECTION_UNSUPPORTED)

    @staticmethod
    def _evaluate_runtime_selection(
        entry: RuntimeCatalogEntry,
        selection: CompatibilitySelection,
        accumulator: _CompatibilityAccumulator,
    ) -> None:
        if selection.market_type not in entry.supported_market_types:
            accumulator.reject(CompatibilityReasonCode.MARKET_TYPE_UNSUPPORTED)
        if selection.execution_mode not in entry.supported_execution_modes:
            accumulator.reject(CompatibilityReasonCode.EXECUTION_MODE_UNSUPPORTED)

    @staticmethod
    def _evaluate_risk_selection(
        entry: RiskPolicyCatalogEntry,
        selection: CompatibilitySelection,
        accumulator: _CompatibilityAccumulator,
    ) -> None:
        if selection.market_type not in entry.supported_market_types:
            accumulator.reject(CompatibilityReasonCode.MARKET_TYPE_UNSUPPORTED)
        if selection.execution_mode not in entry.supported_execution_modes:
            accumulator.reject(CompatibilityReasonCode.EXECUTION_MODE_UNSUPPORTED)
        if not set(selection.policy_families).issubset(entry.supported_policy_families):
            accumulator.reject(CompatibilityReasonCode.RISK_POLICY_UNSUPPORTED)

    @staticmethod
    def _decision_id(
        snapshot: BotCatalogSnapshot,
        selection: CompatibilitySelection,
        reasons: tuple[CompatibilityReasonCode, ...],
        evidence: tuple[CompatibilityEvidenceRef, ...],
    ) -> str:
        material = "|".join(
            (
                snapshot.catalog_id,
                str(snapshot.revision),
                selection.canonical_json(),
                ",".join(reason.value for reason in reasons),
                ",".join(item.canonical_json() for item in evidence),
            )
        )
        return f"compat_{sha256(material.encode('utf-8')).hexdigest()[:32]}"
