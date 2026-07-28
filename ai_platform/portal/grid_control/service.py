from __future__ import annotations

import itertools
from collections.abc import Callable
from datetime import UTC, datetime
from decimal import Decimal, localcontext
from hashlib import sha256

from ai_platform.portal.contracts.bot_management.capabilities import BotManagementCapability
from ai_platform.portal.contracts.bot_management.policies import GridAllocationMode
from ai_platform.portal.contracts.bot_management.templates import TradeDirection
from ai_platform.portal.contracts.environment import ExecutionMode
from ai_platform.portal.grid_control.evidence import (
    EvidenceFreshness,
    GridControlContext,
    GridExchangeCapabilityEvidence,
    GridTemplateCapabilityEvidence,
)
from ai_platform.portal.grid_control.level_generation import (
    CALCULATION_PRECISION,
    apply_price_precision,
    floor_to_step,
    generate_raw_levels,
)
from ai_platform.portal.grid_control.repository import GridControlRepository
from ai_platform.portal.grid_control.schema import (
    GridControlReasonCode,
    GridLevel,
    GridPolicyRevision,
    GridPreview,
    GridPreviewRequest,
    GridPreviewStatus,
    PersistGridPolicyRequest,
)


Clock = Callable[[], datetime]


class GridControlServiceError(RuntimeError):
    def __init__(self, reason_codes: tuple[GridControlReasonCode, ...]) -> None:
        self.reason_codes = _sorted_reasons(reason_codes)
        super().__init__(",".join(item.value for item in self.reason_codes))


def _sorted_reasons(
    reasons: tuple[GridControlReasonCode, ...] | set[GridControlReasonCode],
) -> tuple[GridControlReasonCode, ...]:
    return tuple(sorted(set(reasons), key=lambda item: item.value))


class GridControlService:
    """Generate and persist dry-run grid evidence without submitting orders."""

    def __init__(
        self,
        repository: GridControlRepository,
        clock: Clock | None = None,
    ) -> None:
        self._repository = repository
        self._clock = clock or (lambda: datetime.now(UTC))

    def preview(
        self,
        context: GridControlContext,
        request: GridPreviewRequest,
        template: GridTemplateCapabilityEvidence,
        exchange: GridExchangeCapabilityEvidence,
    ) -> GridPreview:
        generated_at = self._clock()
        preview_id = self._preview_id(request, template, exchange)
        reasons = self._capability_reasons(context, request, template, exchange)

        requested_total, per_level = self._allocation(request)
        if requested_total > request.available_quote:
            reasons.add(GridControlReasonCode.OVER_ALLOCATION)

        levels: tuple[GridLevel, ...] = ()
        blocking_reasons = {
            GridControlReasonCode.TENANT_MISMATCH,
            GridControlReasonCode.TEMPLATE_REVISION_MISMATCH,
            GridControlReasonCode.CAPABILITY_REVISION_MISMATCH,
            GridControlReasonCode.SPACING_UNSUPPORTED,
            GridControlReasonCode.LEVEL_COUNT_UNSUPPORTED,
        }
        if not reasons.intersection(blocking_reasons):
            raw_levels = generate_raw_levels(
                lower=request.policy.lower_price,
                upper=request.policy.upper_price,
                level_count=request.policy.level_count,
                spacing=request.policy.spacing,
            )
            prices = apply_price_precision(raw_levels, exchange.price_step)
            if any(price <= 0 for price in prices):
                reasons.add(GridControlReasonCode.PRECISION_COLLAPSE)
            else:
                if len(set(prices)) != len(prices):
                    reasons.add(GridControlReasonCode.PRECISION_COLLAPSE)
                    reasons.add(GridControlReasonCode.DUPLICATE_LEVELS)
                if any(current >= following for current, following in itertools.pairwise(prices)):
                    reasons.add(GridControlReasonCode.NON_MONOTONIC_LEVELS)
                levels = self._levels(raw_levels, prices, per_level, exchange)
                if any(level.quantity == 0 for level in levels):
                    reasons.add(GridControlReasonCode.ALLOCATION_ZERO)
                if any(not level.meets_minimum_amount for level in levels):
                    reasons.add(GridControlReasonCode.MINIMUM_AMOUNT_NOT_MET)
                if any(not level.meets_minimum_notional for level in levels):
                    reasons.add(GridControlReasonCode.MINIMUM_NOTIONAL_NOT_MET)

        unallocated = max(request.available_quote - requested_total, Decimal("0"))
        reason_codes = _sorted_reasons(reasons)
        return GridPreview(
            preview_id=preview_id,
            tenant_id=request.tenant_id,
            bot_id=request.bot_id,
            bot_revision=request.bot_revision,
            config_revision=request.config_revision,
            template_id=request.template_id,
            template_revision=request.template_revision,
            exchange_profile_id=request.exchange_profile_id,
            exchange_profile_revision=request.exchange_profile_revision,
            policy=request.policy,
            status=(GridPreviewStatus.REJECTED if reason_codes else GridPreviewStatus.VALID),
            reason_codes=reason_codes,
            levels=levels,
            total_quote_allocation=requested_total,
            unallocated_quote=unallocated,
            generated_at=generated_at,
        )

    def persist(
        self,
        context: GridControlContext,
        request: PersistGridPolicyRequest,
    ) -> GridPolicyRevision:
        preview = request.preview
        reasons: set[GridControlReasonCode] = set()
        if preview.tenant_id != context.tenant_id:
            reasons.add(GridControlReasonCode.TENANT_MISMATCH)
        if BotManagementCapability.GRID_CONFIGURE not in context.capabilities:
            reasons.add(GridControlReasonCode.CAPABILITY_MISSING)
        if preview.status != GridPreviewStatus.VALID:
            reasons.add(GridControlReasonCode.PREVIEW_REJECTED)
        if reasons:
            raise GridControlServiceError(tuple(reasons))

        latest = self._repository.get_latest(context.tenant_id, preview.bot_id)
        observed_revision = latest.revision if latest is not None else 0
        if request.expected_revision != observed_revision:
            raise GridControlServiceError((GridControlReasonCode.REVISION_CONFLICT,))

        revision_number = observed_revision + 1
        revision_id = sha256(
            "|".join(
                (
                    preview.preview_id,
                    context.tenant_id,
                    preview.bot_id,
                    str(revision_number),
                    context.actor.actor_id,
                )
            ).encode("utf-8")
        ).hexdigest()
        revision = GridPolicyRevision(
            policy_revision_id=revision_id,
            tenant_id=context.tenant_id,
            bot_id=preview.bot_id,
            bot_revision=preview.bot_revision,
            config_revision=preview.config_revision,
            revision=revision_number,
            supersedes_revision=(observed_revision or None),
            preview_id=preview.preview_id,
            template_id=preview.template_id,
            template_revision=preview.template_revision,
            exchange_profile_id=preview.exchange_profile_id,
            exchange_profile_revision=preview.exchange_profile_revision,
            policy=preview.policy,
            levels=preview.levels,
            total_quote_allocation=preview.total_quote_allocation,
            execution_mode=ExecutionMode.DRY_RUN,
            created_by_actor_id=context.actor.actor_id,
            created_at=self._clock(),
        )
        try:
            self._repository.save_revision(revision)
        except ValueError as exc:
            raise GridControlServiceError((GridControlReasonCode.POLICY_ALREADY_EXISTS,)) from exc
        return revision

    @staticmethod
    def _allocation(request: GridPreviewRequest) -> tuple[Decimal, Decimal]:
        policy = request.policy
        with localcontext() as context:
            context.prec = CALCULATION_PRECISION
            if policy.allocation_mode == GridAllocationMode.TOTAL_QUOTE:
                assert policy.total_quote_allocation is not None
                total = policy.total_quote_allocation
                return total, total / Decimal(policy.level_count)
            assert policy.per_level_quote_amount is not None
            per_level = policy.per_level_quote_amount
            return per_level * Decimal(policy.level_count), per_level

    @staticmethod
    def _levels(
        raw_levels: tuple[Decimal, ...],
        prices: tuple[Decimal, ...],
        per_level: Decimal,
        exchange: GridExchangeCapabilityEvidence,
    ) -> tuple[GridLevel, ...]:
        result: list[GridLevel] = []
        for index, (raw_price, price) in enumerate(zip(raw_levels, prices, strict=False), start=1):
            quantity = floor_to_step(per_level / price, exchange.quantity_step)
            notional = quantity * price
            result.append(
                GridLevel(
                    level_number=index,
                    raw_price=raw_price,
                    price=price,
                    quote_allocation=per_level,
                    quantity=quantity,
                    notional=notional,
                    meets_minimum_amount=quantity >= exchange.minimum_amount,
                    meets_minimum_notional=notional >= exchange.minimum_notional,
                )
            )
        return tuple(result)

    @staticmethod
    def _preview_id(
        request: GridPreviewRequest,
        template: GridTemplateCapabilityEvidence,
        exchange: GridExchangeCapabilityEvidence,
    ) -> str:
        material = "|".join(
            (request.canonical_json(), template.canonical_json(), exchange.canonical_json())
        )
        return sha256(material.encode("utf-8")).hexdigest()

    @staticmethod
    def _capability_reasons(
        context: GridControlContext,
        request: GridPreviewRequest,
        template: GridTemplateCapabilityEvidence,
        exchange: GridExchangeCapabilityEvidence,
    ) -> set[GridControlReasonCode]:
        reasons: set[GridControlReasonCode] = set()
        if any(
            tenant_id != context.tenant_id
            for tenant_id in (request.tenant_id, template.tenant_id, exchange.tenant_id)
        ):
            reasons.add(GridControlReasonCode.TENANT_MISMATCH)
        if BotManagementCapability.GRID_CONFIGURE not in context.capabilities:
            reasons.add(GridControlReasonCode.CAPABILITY_MISSING)
        if request.execution_mode != ExecutionMode.DRY_RUN:
            reasons.add(GridControlReasonCode.EXECUTION_MODE_UNSUPPORTED)
        if template.freshness != EvidenceFreshness.CURRENT:
            reasons.add(GridControlReasonCode.TEMPLATE_EVIDENCE_STALE)
        if exchange.freshness != EvidenceFreshness.CURRENT:
            reasons.add(GridControlReasonCode.CAPABILITY_EVIDENCE_STALE)
        if (
            template.template_id != request.template_id
            or template.template_revision != request.template_revision
        ):
            reasons.add(GridControlReasonCode.TEMPLATE_REVISION_MISMATCH)
        if (
            exchange.profile_id != request.exchange_profile_id
            or exchange.profile_revision != request.exchange_profile_revision
        ):
            reasons.add(GridControlReasonCode.CAPABILITY_REVISION_MISMATCH)
        if request.policy.spacing not in template.supported_spacings:
            reasons.add(GridControlReasonCode.SPACING_UNSUPPORTED)
        if request.policy.direction not in template.supported_directions:
            reasons.add(GridControlReasonCode.DIRECTION_UNSUPPORTED)
        if request.policy.level_count > template.maximum_level_count:
            reasons.add(GridControlReasonCode.LEVEL_COUNT_UNSUPPORTED)
        if request.policy.direction == TradeDirection.SHORT and not exchange.supports_short:
            reasons.add(GridControlReasonCode.DIRECTION_UNSUPPORTED)
        if request.policy.trailing_range_percent is not None and not (
            template.supports_trailing_grid and exchange.supports_trailing_grid
        ):
            reasons.add(GridControlReasonCode.TRAILING_GRID_UNSUPPORTED)
        if request.policy.take_profit_price is not None and not (
            template.supports_take_profit and exchange.supports_take_profit
        ):
            reasons.add(GridControlReasonCode.TAKE_PROFIT_UNSUPPORTED)
        if request.policy.stop_loss_price is not None and not (
            template.supports_stop_loss and exchange.supports_stop_loss
        ):
            reasons.add(GridControlReasonCode.STOP_LOSS_UNSUPPORTED)
        if request.leverage is not None and (
            not template.supports_leverage
            or exchange.maximum_leverage is None
            or request.leverage > exchange.maximum_leverage
        ):
            reasons.add(GridControlReasonCode.LEVERAGE_UNSUPPORTED)
        if request.margin_mode is not None and (
            not template.supports_margin
            or request.margin_mode not in exchange.supported_margin_modes
        ):
            reasons.add(GridControlReasonCode.MARGIN_MODE_UNSUPPORTED)
        return reasons
