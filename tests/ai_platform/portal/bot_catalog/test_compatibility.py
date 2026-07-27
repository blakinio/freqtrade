from __future__ import annotations

import pytest

from ai_platform.portal.bot_catalog.repository import InMemoryBotCatalogRepository
from ai_platform.portal.bot_catalog.schema import (
    CatalogAccessContext,
    CatalogAccessReasonCode,
    CatalogEntryState,
    ModelRequirement,
)
from ai_platform.portal.bot_catalog.service import (
    BotCatalogService,
    BotCatalogServiceError,
)
from ai_platform.portal.contracts.bot_management.capabilities import (
    BotManagementCapability,
)
from ai_platform.portal.contracts.bot_management.compatibility import (
    CompatibilityReasonCode,
    CompatibilitySelection,
    CompatibilityStatus,
)
from ai_platform.portal.contracts.bot_management.templates import (
    CatalogVersionRef,
    MarketType,
    PolicyFamily,
    TradeDirection,
)
from ai_platform.portal.contracts.environment import ExecutionMode
from tests.ai_platform.portal.bot_catalog.conftest import (
    NOW,
    snapshot_with_templates,
    template_entry,
)


def test_compatible_selection_produces_deterministic_authoritative_evidence(
    service: BotCatalogService,
    access: CatalogAccessContext,
    selection: CompatibilitySelection,
) -> None:
    catalog_ref = CatalogVersionRef(catalog_id="approved-bots", version="1")

    first = service.decide_compatibility(access, catalog_ref, selection, NOW)
    second = service.decide_compatibility(access, catalog_ref, selection, NOW)

    assert first.status == CompatibilityStatus.COMPATIBLE
    assert first.reason_codes == ()
    assert len(first.evidence_refs) == 6
    assert first == second
    assert first.canonical_json() == second.canonical_json()
    assert first.decision_id.startswith("compat_")


def test_tenant_mismatch_fails_before_compatibility_evaluation(
    service: BotCatalogService,
    access: CatalogAccessContext,
    selection: CompatibilitySelection,
) -> None:
    mismatched = selection.model_copy(update={"tenant_id": "tenant-b"})

    with pytest.raises(BotCatalogServiceError) as exc_info:
        service.decide_compatibility(
            access,
            CatalogVersionRef(catalog_id="approved-bots", version="1"),
            mismatched,
            NOW,
        )

    assert exc_info.value.reason_code == CatalogAccessReasonCode.TENANT_MISMATCH


def test_compatibility_requires_catalog_read_capability(
    service: BotCatalogService,
    selection: CompatibilitySelection,
) -> None:
    access = CatalogAccessContext(
        tenant_id="tenant-a",
        capabilities=(BotManagementCapability.TEMPLATE_READ,),
    )

    with pytest.raises(BotCatalogServiceError) as exc_info:
        service.decide_compatibility(
            access,
            CatalogVersionRef(catalog_id="approved-bots", version="1"),
            selection,
            NOW,
        )

    assert exc_info.value.reason_code == CatalogAccessReasonCode.CAPABILITY_MISSING


def test_stale_template_revision_has_stable_reason_and_missing_proof(
    service: BotCatalogService,
    access: CatalogAccessContext,
    selection: CompatibilitySelection,
) -> None:
    stale = selection.model_copy(
        update={"template_ref": CatalogVersionRef(catalog_id="directional-v1", version="2")}
    )

    decision = service.decide_compatibility(
        access,
        CatalogVersionRef(catalog_id="approved-bots", version="1"),
        stale,
        NOW,
    )

    assert decision.status == CompatibilityStatus.REJECTED
    assert CompatibilityReasonCode.TEMPLATE_REVISION_STALE in decision.reason_codes
    assert CompatibilityReasonCode.EVIDENCE_MISSING in decision.reason_codes


def test_required_model_is_rejected_when_selection_omits_it(
    access: CatalogAccessContext,
    selection: CompatibilitySelection,
) -> None:
    required = template_entry(model_requirement=ModelRequirement.REQUIRED)
    snapshot = snapshot_with_templates((required,))
    service = BotCatalogService(InMemoryBotCatalogRepository((snapshot,)))
    without_model = selection.model_copy(update={"model_version": None})

    decision = service.decide_compatibility(
        access,
        snapshot.catalog_ref,
        without_model,
        NOW,
    )

    assert decision.reason_codes == (CompatibilityReasonCode.MODEL_REQUIRED,)


def test_deprecated_model_rejects_with_stale_evidence(
    access: CatalogAccessContext,
    selection: CompatibilitySelection,
) -> None:
    snapshot = snapshot_with_templates(
        (template_entry(),),
        model_state=CatalogEntryState.DEPRECATED,
    )
    service = BotCatalogService(InMemoryBotCatalogRepository((snapshot,)))

    decision = service.decide_compatibility(access, snapshot.catalog_ref, selection, NOW)

    assert decision.status == CompatibilityStatus.REJECTED
    assert decision.reason_codes == (CompatibilityReasonCode.EVIDENCE_STALE,)


def test_missing_model_has_model_and_evidence_reasons(
    access: CatalogAccessContext,
    selection: CompatibilitySelection,
) -> None:
    snapshot = snapshot_with_templates((template_entry(),))
    snapshot = type(snapshot).model_validate({**snapshot.model_dump(), "models": ()})
    service = BotCatalogService(InMemoryBotCatalogRepository((snapshot,)))

    decision = service.decide_compatibility(access, snapshot.catalog_ref, selection, NOW)

    assert CompatibilityReasonCode.MODEL_UNSUPPORTED in decision.reason_codes
    assert CompatibilityReasonCode.EVIDENCE_MISSING in decision.reason_codes


def test_cross_capability_conflicts_return_sorted_reason_codes(
    access: CatalogAccessContext,
    selection: CompatibilitySelection,
) -> None:
    snapshot = snapshot_with_templates((template_entry(),))
    service = BotCatalogService(InMemoryBotCatalogRepository((snapshot,)))
    incompatible = selection.model_copy(
        update={
            "direction": TradeDirection.SHORT,
            "execution_mode": ExecutionMode.SIMULATED,
            "market_type": MarketType.FUTURES,
            "policy_families": (
                PolicyFamily.GRID,
                PolicyFamily.MARKET,
                PolicyFamily.RUNTIME,
            ),
            "runtime_version": "runtime-missing",
            "risk_policy_version": "risk-missing",
        }
    )

    decision = service.decide_compatibility(access, snapshot.catalog_ref, incompatible, NOW)
    values = [reason.value for reason in decision.reason_codes]

    assert decision.status == CompatibilityStatus.REJECTED
    assert values == sorted(values)
    assert CompatibilityReasonCode.DIRECTION_UNSUPPORTED in decision.reason_codes
    assert CompatibilityReasonCode.EXECUTION_MODE_UNSUPPORTED in decision.reason_codes
    assert CompatibilityReasonCode.MARKET_TYPE_UNSUPPORTED in decision.reason_codes
    assert CompatibilityReasonCode.POLICY_FAMILY_MISSING in decision.reason_codes
    assert CompatibilityReasonCode.POLICY_FAMILY_UNSUPPORTED in decision.reason_codes
    assert CompatibilityReasonCode.RUNTIME_VERSION_UNSUPPORTED in decision.reason_codes
    assert CompatibilityReasonCode.RISK_POLICY_UNSUPPORTED in decision.reason_codes


def test_latest_catalog_ref_is_capability_gated(
    service: BotCatalogService,
    access: CatalogAccessContext,
) -> None:
    assert service.latest_catalog_ref(access, "approved-bots") == CatalogVersionRef(
        catalog_id="approved-bots",
        version="1",
    )
