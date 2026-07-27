from __future__ import annotations

from hashlib import sha256
from typing import cast

from pydantic import ValidationError

from ai_platform.portal.bot_builder.repository import BotConfigurationRepository
from ai_platform.portal.bot_builder.schema import (
    BotBuilderAccessContext,
    BotBuilderReasonCode,
    BotConfigurationDraftPayload,
    BotConfigurationDraftPreview,
    BotConfigurationDraftRevision,
    CreateBotConfigurationDraft,
    DraftField,
    DraftReadinessStatus,
    DraftRevisionRef,
    FinalizeBotConfigurationDraft,
    FinalizedBotConfiguration,
    ReviseBotConfigurationDraft,
)
from ai_platform.portal.bot_catalog.schema import CatalogAccessContext
from ai_platform.portal.bot_catalog.service import BotCatalogService
from ai_platform.portal.contracts.bot_management.capabilities import BotManagementCapability
from ai_platform.portal.contracts.bot_management.compatibility import (
    BotCompatibilityDecision,
    CompatibilitySelection,
    CompatibilityStatus,
)
from ai_platform.portal.contracts.bot_management.configuration import BotManagementConfiguration
from ai_platform.portal.contracts.bot_management.policies import (
    EntryPolicyVersion,
    ExitPolicyVersion,
    MarketPolicyVersion,
    PositionSizingPolicyVersion,
    RuntimePolicyVersion,
)
from ai_platform.portal.contracts.bot_management.templates import (
    CatalogVersionRef,
    PolicyFamily,
)
from ai_platform.portal.contracts.common import UtcDateTime
from ai_platform.portal.contracts.environment import Environment, ExecutionMode


_REQUIRED_FIELDS: tuple[tuple[DraftField, str], ...] = (
    (DraftField.CATALOG_REF, "catalog_ref"),
    (DraftField.TEMPLATE_REF, "template_ref"),
    (DraftField.STRATEGY_VERSION, "strategy_version"),
    (DraftField.EXCHANGE_CONNECTION_REF, "exchange_connection_ref"),
    (DraftField.EXCHANGE_PROFILE_VERSION, "exchange_profile_version"),
    (DraftField.MARKET_POLICY, "market_policy"),
    (DraftField.ENTRY_POLICY, "entry_policy"),
    (DraftField.POSITION_SIZING_POLICY, "position_sizing_policy"),
    (DraftField.EXIT_POLICY, "exit_policy"),
    (DraftField.RISK_POLICY_VERSION, "risk_policy_version"),
    (DraftField.RUNTIME_POLICY, "runtime_policy"),
    (DraftField.ENVIRONMENT, "environment"),
    (DraftField.EXECUTION_MODE, "execution_mode"),
)


class BotBuilderServiceError(RuntimeError):
    def __init__(
        self,
        reason_code: BotBuilderReasonCode,
        message: str,
        details: tuple[str, ...] = (),
    ) -> None:
        super().__init__(message)
        self.reason_code = reason_code
        self.details = details


class BotConfigurationBuilderService:
    def __init__(
        self,
        repository: BotConfigurationRepository,
        catalog_service: BotCatalogService,
    ) -> None:
        self._repository = repository
        self._catalog_service = catalog_service

    def create_draft(
        self,
        access: BotBuilderAccessContext,
        request: CreateBotConfigurationDraft,
        created_at: UtcDateTime,
    ) -> BotConfigurationDraftRevision:
        self._require_capability(access, BotManagementCapability.BOT_CREATE)
        if self._repository.get_latest_draft(access.tenant_id, request.draft_id) is not None:
            raise BotBuilderServiceError(
                BotBuilderReasonCode.DRAFT_ALREADY_EXISTS,
                "draft already exists for this tenant",
            )
        draft = BotConfigurationDraftRevision(
            draft_id=request.draft_id,
            tenant_id=access.tenant_id,
            bot_id=request.bot_id,
            revision=1,
            payload=request.payload,
            created_by_actor_id=access.actor_id,
            created_at=created_at,
        )
        self._repository.save_draft(draft)
        return draft

    def revise_draft(
        self,
        access: BotBuilderAccessContext,
        request: ReviseBotConfigurationDraft,
        created_at: UtcDateTime,
    ) -> BotConfigurationDraftRevision:
        self._require_any_capability(
            access,
            (BotManagementCapability.BOT_CREATE, BotManagementCapability.BOT_REVISE),
        )
        latest = self._repository.get_latest_draft(access.tenant_id, request.draft_id)
        if latest is None:
            raise BotBuilderServiceError(
                BotBuilderReasonCode.DRAFT_NOT_FOUND,
                "draft does not exist for this tenant",
            )
        if latest.revision != request.expected_revision:
            raise BotBuilderServiceError(
                BotBuilderReasonCode.DRAFT_REVISION_CONFLICT,
                "draft revision does not match the expected revision",
            )
        revised = BotConfigurationDraftRevision(
            draft_id=latest.draft_id,
            tenant_id=latest.tenant_id,
            bot_id=latest.bot_id,
            revision=latest.revision + 1,
            supersedes_revision=latest.revision,
            payload=request.payload,
            created_by_actor_id=access.actor_id,
            created_at=created_at,
        )
        self._repository.save_draft(revised)
        return revised

    def preview_draft(
        self,
        access: BotBuilderAccessContext,
        draft_ref: DraftRevisionRef,
        decided_at: UtcDateTime,
    ) -> BotConfigurationDraftPreview:
        draft = self._require_draft(access, draft_ref)
        self._require_any_capability(
            access,
            (BotManagementCapability.BOT_CREATE, BotManagementCapability.BOT_REVISE),
        )
        missing_fields = self._missing_fields(draft.payload)
        if missing_fields:
            return BotConfigurationDraftPreview(
                draft_ref=draft_ref,
                status=DraftReadinessStatus.INCOMPLETE,
                missing_fields=missing_fields,
            )
        decision = self._decide_compatibility(access, draft.payload, decided_at)
        if decision.status == CompatibilityStatus.REJECTED:
            return BotConfigurationDraftPreview(
                draft_ref=draft_ref,
                status=DraftReadinessStatus.INCOMPATIBLE,
                compatibility_decision=decision,
            )
        revision = self._next_configuration_revision(draft.tenant_id, draft.bot_id)
        try:
            self._compose_configuration(draft, decision, revision, access.actor_id, decided_at)
        except ValidationError as exc:
            return BotConfigurationDraftPreview(
                draft_ref=draft_ref,
                status=DraftReadinessStatus.INVALID,
                validation_errors=self._validation_errors(exc),
                compatibility_decision=decision,
            )
        return BotConfigurationDraftPreview(
            draft_ref=draft_ref,
            status=DraftReadinessStatus.READY,
            compatibility_decision=decision,
        )

    def finalize_draft(
        self,
        access: BotBuilderAccessContext,
        request: FinalizeBotConfigurationDraft,
        decided_at: UtcDateTime,
    ) -> FinalizedBotConfiguration:
        draft = self._require_draft(access, request.draft_ref)
        self._require_any_capability(
            access,
            (BotManagementCapability.BOT_CREATE, BotManagementCapability.BOT_REVISE),
        )
        existing = self._repository.get_finalization(request.draft_ref)
        if existing is not None:
            return existing
        latest_draft = self._repository.get_latest_draft(draft.tenant_id, draft.draft_id)
        if latest_draft is None or latest_draft.revision != draft.revision:
            raise BotBuilderServiceError(
                BotBuilderReasonCode.DRAFT_REVISION_CONFLICT,
                "only the latest draft revision may be finalized",
            )
        latest_configuration = self._repository.get_latest_configuration(
            draft.tenant_id,
            draft.bot_id,
        )
        if latest_configuration is None:
            self._require_capability(access, BotManagementCapability.BOT_CREATE)
            if request.expected_configuration_revision is not None:
                raise BotBuilderServiceError(
                    BotBuilderReasonCode.CONFIGURATION_REVISION_CONFLICT,
                    "first configuration requires a null expected revision",
                )
            configuration_revision = 1
        else:
            self._require_capability(access, BotManagementCapability.BOT_REVISE)
            if request.expected_configuration_revision != latest_configuration.revision:
                raise BotBuilderServiceError(
                    BotBuilderReasonCode.CONFIGURATION_REVISION_CONFLICT,
                    "configuration revision does not match the expected revision",
                )
            configuration_revision = latest_configuration.revision + 1
        missing_fields = self._missing_fields(draft.payload)
        if missing_fields:
            raise BotBuilderServiceError(
                BotBuilderReasonCode.CONFIGURATION_INVALID,
                "draft is incomplete",
                tuple(item.value for item in missing_fields),
            )
        decision = self._decide_compatibility(access, draft.payload, decided_at)
        if decision.status == CompatibilityStatus.REJECTED:
            raise BotBuilderServiceError(
                BotBuilderReasonCode.COMPATIBILITY_REJECTED,
                "catalog compatibility rejected the draft",
                tuple(item.value for item in decision.reason_codes),
            )
        try:
            configuration = self._compose_configuration(
                draft,
                decision,
                configuration_revision,
                access.actor_id,
                decided_at,
            )
        except ValidationError as exc:
            raise BotBuilderServiceError(
                BotBuilderReasonCode.CONFIGURATION_INVALID,
                "configuration composition failed validation",
                self._validation_errors(exc),
            ) from exc
        digest = sha256(configuration.canonical_json().encode()).hexdigest()
        finalization = FinalizedBotConfiguration(
            draft_ref=request.draft_ref,
            configuration=configuration,
            compatibility_decision=decision,
            configuration_sha256=digest,
        )
        self._repository.save_finalization(finalization)
        return finalization

    def _require_draft(
        self,
        access: BotBuilderAccessContext,
        draft_ref: DraftRevisionRef,
    ) -> BotConfigurationDraftRevision:
        if access.tenant_id != draft_ref.tenant_id:
            raise BotBuilderServiceError(
                BotBuilderReasonCode.TENANT_MISMATCH,
                "draft tenant does not match access context",
            )
        draft = self._repository.get_draft(
            draft_ref.tenant_id,
            draft_ref.draft_id,
            draft_ref.revision,
        )
        if draft is None:
            raise BotBuilderServiceError(
                BotBuilderReasonCode.DRAFT_NOT_FOUND,
                "draft revision does not exist",
            )
        return draft

    def _decide_compatibility(
        self,
        access: BotBuilderAccessContext,
        payload: BotConfigurationDraftPayload,
        decided_at: UtcDateTime,
    ) -> BotCompatibilityDecision:
        self._require_capability(access, BotManagementCapability.CATALOG_READ)
        catalog_ref = cast(CatalogVersionRef, payload.catalog_ref)
        selection = self._compatibility_selection(access.tenant_id, payload)
        return self._catalog_service.decide_compatibility(
            CatalogAccessContext(
                tenant_id=access.tenant_id,
                capabilities=access.capabilities,
            ),
            catalog_ref,
            selection,
            decided_at,
        )

    @staticmethod
    def _compatibility_selection(
        tenant_id: str,
        payload: BotConfigurationDraftPayload,
    ) -> CompatibilitySelection:
        market = cast(MarketPolicyVersion, payload.market_policy)
        runtime = cast(RuntimePolicyVersion, payload.runtime_policy)
        return CompatibilitySelection(
            tenant_id=tenant_id,
            template_ref=cast(CatalogVersionRef, payload.template_ref),
            strategy_version=cast(str, payload.strategy_version),
            model_version=payload.model_version,
            exchange_profile_version=cast(str, payload.exchange_profile_version),
            market_type=market.market_type,
            direction=market.direction,
            execution_mode=cast(ExecutionMode, payload.execution_mode),
            runtime_version=runtime.runtime_version,
            risk_policy_version=cast(str, payload.risk_policy_version),
            policy_families=BotConfigurationBuilderService._policy_families(payload),
        )

    @staticmethod
    def _policy_families(payload: BotConfigurationDraftPayload) -> tuple[PolicyFamily, ...]:
        families: set[PolicyFamily] = set()
        if payload.market_policy is not None:
            families.add(PolicyFamily.MARKET)
        if payload.entry_policy is not None:
            families.add(PolicyFamily.ENTRY)
        if payload.position_sizing_policy is not None:
            families.add(PolicyFamily.POSITION_SIZING)
        if payload.dca_policy is not None:
            families.add(PolicyFamily.DCA)
        if payload.exit_policy is not None:
            families.add(PolicyFamily.EXIT)
        if payload.risk_policy_version is not None:
            families.add(PolicyFamily.RISK_REFERENCE)
        if payload.signal_policy is not None:
            families.add(PolicyFamily.SIGNAL)
        if payload.grid_policy is not None:
            families.add(PolicyFamily.GRID)
        if payload.runtime_policy is not None:
            families.add(PolicyFamily.RUNTIME)
        return tuple(sorted(families, key=lambda item: item.value))

    @staticmethod
    def _missing_fields(payload: BotConfigurationDraftPayload) -> tuple[DraftField, ...]:
        missing = [
            field for field, attribute in _REQUIRED_FIELDS if getattr(payload, attribute) is None
        ]
        return tuple(sorted(missing, key=lambda item: item.value))

    def _next_configuration_revision(self, tenant_id: str, bot_id: str) -> int:
        latest = self._repository.get_latest_configuration(tenant_id, bot_id)
        return 1 if latest is None else latest.revision + 1

    @staticmethod
    def _compose_configuration(
        draft: BotConfigurationDraftRevision,
        decision: BotCompatibilityDecision,
        revision: int,
        actor_id: str,
        created_at: UtcDateTime,
    ) -> BotManagementConfiguration:
        payload = draft.payload
        configuration_id = (
            "cfg_" + sha256(f"{draft.tenant_id}:{draft.bot_id}".encode()).hexdigest()[:24]
        )
        return BotManagementConfiguration(
            configuration_id=configuration_id,
            tenant_id=draft.tenant_id,
            bot_id=draft.bot_id,
            revision=revision,
            template_ref=cast(CatalogVersionRef, payload.template_ref),
            compatibility_decision_ref=decision.decision_id,
            strategy_version=cast(str, payload.strategy_version),
            model_version=payload.model_version,
            exchange_connection_ref=cast(str, payload.exchange_connection_ref),
            market_policy=cast(MarketPolicyVersion, payload.market_policy),
            entry_policy=cast(EntryPolicyVersion, payload.entry_policy),
            position_sizing_policy=cast(
                PositionSizingPolicyVersion,
                payload.position_sizing_policy,
            ),
            dca_policy=payload.dca_policy,
            exit_policy=cast(ExitPolicyVersion, payload.exit_policy),
            risk_policy_version=cast(str, payload.risk_policy_version),
            signal_policy=payload.signal_policy,
            grid_policy=payload.grid_policy,
            runtime_policy=cast(RuntimePolicyVersion, payload.runtime_policy),
            environment=cast(Environment, payload.environment),
            execution_mode=cast(ExecutionMode, payload.execution_mode),
            created_by_actor_id=actor_id,
            created_at=created_at,
        )

    @staticmethod
    def _validation_errors(exc: ValidationError) -> tuple[str, ...]:
        messages: set[str] = set()
        for error in exc.errors(include_input=False, include_url=False):
            location = ".".join(str(item) for item in error["loc"]) or "configuration"
            messages.add(f"{location}: {error['msg']}")
        return tuple(sorted(messages))

    @staticmethod
    def _require_capability(
        access: BotBuilderAccessContext,
        capability: BotManagementCapability,
    ) -> None:
        if capability not in access.capabilities:
            raise BotBuilderServiceError(
                BotBuilderReasonCode.CAPABILITY_MISSING,
                f"missing required capability: {capability.value}",
            )

    @staticmethod
    def _require_any_capability(
        access: BotBuilderAccessContext,
        capabilities: tuple[BotManagementCapability, ...],
    ) -> None:
        if not any(item in access.capabilities for item in capabilities):
            names = ",".join(sorted(item.value for item in capabilities))
            raise BotBuilderServiceError(
                BotBuilderReasonCode.CAPABILITY_MISSING,
                f"missing one of required capabilities: {names}",
            )
