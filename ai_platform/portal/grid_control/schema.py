from __future__ import annotations

from enum import StrEnum
from typing import Annotated, Self

from pydantic import Field, NonNegativeInt, PositiveInt, model_validator

from ai_platform.portal.contracts.bot_management.policies import (
    GridPolicyVersion,
    NonNegativeDecimal,
    PositiveDecimal,
)
from ai_platform.portal.contracts.bot_management.templates import MarginMode
from ai_platform.portal.contracts.common import (
    ContractModel,
    NonEmptyStr,
    Sha256Hex,
    UtcDateTime,
)
from ai_platform.portal.contracts.environment import ExecutionMode


class GridPreviewStatus(StrEnum):
    VALID = "VALID"
    REJECTED = "REJECTED"


class GridControlReasonCode(StrEnum):
    ALLOCATION_ZERO = "ALLOCATION_ZERO"
    CAPABILITY_EVIDENCE_STALE = "CAPABILITY_EVIDENCE_STALE"
    CAPABILITY_MISSING = "CAPABILITY_MISSING"
    CAPABILITY_REVISION_MISMATCH = "CAPABILITY_REVISION_MISMATCH"
    DIRECTION_UNSUPPORTED = "DIRECTION_UNSUPPORTED"
    DUPLICATE_LEVELS = "DUPLICATE_LEVELS"
    EXECUTION_MODE_UNSUPPORTED = "EXECUTION_MODE_UNSUPPORTED"
    LEVEL_COUNT_UNSUPPORTED = "LEVEL_COUNT_UNSUPPORTED"
    LEVERAGE_UNSUPPORTED = "LEVERAGE_UNSUPPORTED"
    MARGIN_MODE_UNSUPPORTED = "MARGIN_MODE_UNSUPPORTED"
    MINIMUM_AMOUNT_NOT_MET = "MINIMUM_AMOUNT_NOT_MET"
    MINIMUM_NOTIONAL_NOT_MET = "MINIMUM_NOTIONAL_NOT_MET"
    NON_MONOTONIC_LEVELS = "NON_MONOTONIC_LEVELS"
    OVER_ALLOCATION = "OVER_ALLOCATION"
    POLICY_ALREADY_EXISTS = "POLICY_ALREADY_EXISTS"
    POLICY_NOT_FOUND = "POLICY_NOT_FOUND"
    PRECISION_COLLAPSE = "PRECISION_COLLAPSE"
    PREVIEW_REJECTED = "PREVIEW_REJECTED"
    REVISION_CONFLICT = "REVISION_CONFLICT"
    SPACING_UNSUPPORTED = "SPACING_UNSUPPORTED"
    STOP_LOSS_UNSUPPORTED = "STOP_LOSS_UNSUPPORTED"
    TAKE_PROFIT_UNSUPPORTED = "TAKE_PROFIT_UNSUPPORTED"
    TEMPLATE_EVIDENCE_STALE = "TEMPLATE_EVIDENCE_STALE"
    TEMPLATE_REVISION_MISMATCH = "TEMPLATE_REVISION_MISMATCH"
    TENANT_MISMATCH = "TENANT_MISMATCH"
    TRAILING_GRID_UNSUPPORTED = "TRAILING_GRID_UNSUPPORTED"


class GridPreviewRequest(ContractModel):
    tenant_id: NonEmptyStr
    bot_id: NonEmptyStr
    bot_revision: PositiveInt
    config_revision: PositiveInt
    template_id: NonEmptyStr
    template_revision: PositiveInt
    exchange_profile_id: NonEmptyStr
    exchange_profile_revision: PositiveInt
    policy: GridPolicyVersion
    available_quote: PositiveDecimal
    execution_mode: ExecutionMode
    leverage: PositiveDecimal | None = None
    margin_mode: MarginMode | None = None


class GridLevel(ContractModel):
    level_number: PositiveInt
    raw_price: PositiveDecimal
    price: PositiveDecimal
    quote_allocation: PositiveDecimal
    quantity: NonNegativeDecimal
    notional: NonNegativeDecimal
    meets_minimum_amount: bool
    meets_minimum_notional: bool


class GridPreview(ContractModel):
    preview_id: Sha256Hex
    tenant_id: NonEmptyStr
    bot_id: NonEmptyStr
    bot_revision: PositiveInt
    config_revision: PositiveInt
    template_id: NonEmptyStr
    template_revision: PositiveInt
    exchange_profile_id: NonEmptyStr
    exchange_profile_revision: PositiveInt
    policy: GridPolicyVersion
    status: GridPreviewStatus
    reason_codes: tuple[GridControlReasonCode, ...] = ()
    levels: tuple[GridLevel, ...] = ()
    total_quote_allocation: NonNegativeDecimal
    unallocated_quote: NonNegativeDecimal
    generated_at: UtcDateTime
    preview_only: bool = True
    order_submission_performed: bool = False

    @model_validator(mode="after")
    def validate_preview(self) -> Self:
        reasons = [item.value for item in self.reason_codes]
        if len(reasons) != len(set(reasons)) or reasons != sorted(reasons):
            raise ValueError("grid preview reasons must be unique and sorted")
        if not self.preview_only or self.order_submission_performed:
            raise ValueError("grid preview must remain non-executing")
        if self.status == GridPreviewStatus.VALID:
            if self.reason_codes or not self.levels:
                raise ValueError("valid grid preview requires levels and no reasons")
        elif not self.reason_codes:
            raise ValueError("rejected grid preview requires reasons")
        numbers = [level.level_number for level in self.levels]
        if numbers and numbers != list(range(1, len(numbers) + 1)):
            raise ValueError("grid levels must be contiguous and ordered")
        return self


class PersistGridPolicyRequest(ContractModel):
    preview: GridPreview
    expected_revision: NonNegativeInt


class GridPolicyRevision(ContractModel):
    policy_revision_id: Sha256Hex
    tenant_id: NonEmptyStr
    bot_id: NonEmptyStr
    bot_revision: PositiveInt
    config_revision: PositiveInt
    revision: PositiveInt
    supersedes_revision: PositiveInt | None = None
    preview_id: Sha256Hex
    template_id: NonEmptyStr
    template_revision: PositiveInt
    exchange_profile_id: NonEmptyStr
    exchange_profile_revision: PositiveInt
    policy: GridPolicyVersion
    levels: Annotated[tuple[GridLevel, ...], Field(min_length=2)]
    total_quote_allocation: PositiveDecimal
    execution_mode: ExecutionMode
    created_by_actor_id: NonEmptyStr
    created_at: UtcDateTime
    immutable: bool = True
    order_submission_performed: bool = False

    @model_validator(mode="after")
    def validate_revision(self) -> Self:
        if self.revision == 1 and self.supersedes_revision is not None:
            raise ValueError("first grid revision must not supersede another revision")
        if self.revision > 1 and self.supersedes_revision != self.revision - 1:
            raise ValueError("grid revision must supersede the immediately prior revision")
        if self.execution_mode != ExecutionMode.DRY_RUN:
            raise ValueError("persisted grid policy must remain dry_run")
        if not self.immutable or self.order_submission_performed:
            raise ValueError("grid policy must remain immutable and non-executing")
        if len(self.levels) != self.policy.level_count:
            raise ValueError("persisted levels must match policy level count")
        return self
