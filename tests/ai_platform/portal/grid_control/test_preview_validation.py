from decimal import Decimal

from ai_platform.portal.contracts.bot_management.capabilities import BotManagementCapability
from ai_platform.portal.contracts.bot_management.policies import GridSpacing
from ai_platform.portal.contracts.bot_management.templates import MarginMode, TradeDirection
from ai_platform.portal.contracts.environment import ExecutionMode
from ai_platform.portal.grid_control.evidence import EvidenceFreshness
from ai_platform.portal.grid_control.schema import GridControlReasonCode, GridPreviewStatus
from tests.ai_platform.portal.grid_control.support import (
    context,
    exchange,
    request,
    service,
    template,
)


def test_valid_arithmetic_preview_is_dry_run_only() -> None:
    preview = service().preview(context(), request(), template(), exchange())
    assert preview.status == GridPreviewStatus.VALID
    assert preview.reason_codes == ()
    assert len(preview.levels) == 5
    assert preview.preview_only is True
    assert preview.order_submission_performed is False
    assert preview.total_quote_allocation == Decimal("300")
    assert preview.unallocated_quote == Decimal("200")


def test_valid_preview_levels_are_strictly_increasing() -> None:
    preview = service().preview(context(), request(), template(), exchange())
    prices = [level.price for level in preview.levels]
    assert prices == sorted(prices)
    assert len(prices) == len(set(prices))


def test_preview_identity_is_deterministic() -> None:
    grid_service = service()
    first = grid_service.preview(context(), request(), template(), exchange())
    second = grid_service.preview(context(), request(), template(), exchange())
    assert first.preview_id == second.preview_id
    assert first.levels == second.levels


def test_geometric_preview_is_supported() -> None:
    grid_request = request().model_copy(
        update={"policy": request().policy.model_copy(update={"spacing": GridSpacing.GEOMETRIC})}
    )
    preview = service().preview(context(), grid_request, template(), exchange())
    assert preview.status == GridPreviewStatus.VALID
    assert preview.levels[0].price == Decimal("90")
    assert preview.levels[-1].price == Decimal("110")


def test_per_level_allocation_is_accumulated() -> None:
    grid_request = request().model_copy(
        update={
            "policy": request().policy.model_copy(
                update={
                    "allocation_mode": "per_level_quote",
                    "total_quote_allocation": None,
                    "per_level_quote_amount": Decimal("40"),
                }
            )
        }
    )
    preview = service().preview(context(), grid_request, template(), exchange())
    assert preview.total_quote_allocation == Decimal("200")
    assert all(level.quote_allocation == Decimal("40") for level in preview.levels)


def test_over_allocation_is_rejected() -> None:
    grid_request = request().model_copy(update={"available_quote": Decimal("100")})
    preview = service().preview(context(), grid_request, template(), exchange())
    assert preview.status == GridPreviewStatus.REJECTED
    assert GridControlReasonCode.OVER_ALLOCATION in preview.reason_codes


def test_missing_grid_capability_is_rejected() -> None:
    denied = context().model_copy(update={"capabilities": ()})
    preview = service().preview(denied, request(), template(), exchange())
    assert preview.reason_codes == (GridControlReasonCode.CAPABILITY_MISSING,)


def test_tenant_mismatch_is_rejected_without_levels() -> None:
    foreign = request().model_copy(update={"tenant_id": "tenant-b"})
    preview = service().preview(context(), foreign, template(), exchange())
    assert GridControlReasonCode.TENANT_MISMATCH in preview.reason_codes
    assert preview.levels == ()


def test_simulated_mode_is_rejected() -> None:
    grid_request = request().model_copy(update={"execution_mode": ExecutionMode.SIMULATED})
    preview = service().preview(context(), grid_request, template(), exchange())
    assert GridControlReasonCode.EXECUTION_MODE_UNSUPPORTED in preview.reason_codes


def test_stale_template_evidence_is_rejected() -> None:
    stale = template().model_copy(update={"freshness": EvidenceFreshness.STALE})
    preview = service().preview(context(), request(), stale, exchange())
    assert GridControlReasonCode.TEMPLATE_EVIDENCE_STALE in preview.reason_codes


def test_stale_exchange_evidence_is_rejected() -> None:
    stale = exchange().model_copy(update={"freshness": EvidenceFreshness.STALE})
    preview = service().preview(context(), request(), template(), stale)
    assert GridControlReasonCode.CAPABILITY_EVIDENCE_STALE in preview.reason_codes


def test_template_revision_mismatch_is_rejected_without_levels() -> None:
    mismatched = template().model_copy(update={"template_revision": 9})
    preview = service().preview(context(), request(), mismatched, exchange())
    assert GridControlReasonCode.TEMPLATE_REVISION_MISMATCH in preview.reason_codes
    assert preview.levels == ()


def test_exchange_revision_mismatch_is_rejected_without_levels() -> None:
    mismatched = exchange().model_copy(update={"profile_revision": 9})
    preview = service().preview(context(), request(), template(), mismatched)
    assert GridControlReasonCode.CAPABILITY_REVISION_MISMATCH in preview.reason_codes
    assert preview.levels == ()


def test_unsupported_spacing_is_rejected_without_levels() -> None:
    limited = template().model_copy(update={"supported_spacings": (GridSpacing.ARITHMETIC,)})
    grid_request = request().model_copy(
        update={"policy": request().policy.model_copy(update={"spacing": GridSpacing.GEOMETRIC})}
    )
    preview = service().preview(context(), grid_request, limited, exchange())
    assert GridControlReasonCode.SPACING_UNSUPPORTED in preview.reason_codes
    assert preview.levels == ()


def test_level_count_above_template_limit_is_rejected() -> None:
    limited = template().model_copy(update={"maximum_level_count": 4})
    preview = service().preview(context(), request(), limited, exchange())
    assert GridControlReasonCode.LEVEL_COUNT_UNSUPPORTED in preview.reason_codes


def test_short_direction_requires_exchange_support() -> None:
    grid_request = request().model_copy(
        update={"policy": request().policy.model_copy(update={"direction": TradeDirection.SHORT})}
    )
    limited = exchange().model_copy(update={"supports_short": False})
    preview = service().preview(context(), grid_request, template(), limited)
    assert GridControlReasonCode.DIRECTION_UNSUPPORTED in preview.reason_codes


def test_trailing_grid_requires_both_evidence_sources() -> None:
    grid_request = request().model_copy(
        update={
            "policy": request().policy.model_copy(update={"trailing_range_percent": Decimal("2")})
        }
    )
    limited = template().model_copy(update={"supports_trailing_grid": False})
    preview = service().preview(context(), grid_request, limited, exchange())
    assert GridControlReasonCode.TRAILING_GRID_UNSUPPORTED in preview.reason_codes


def test_take_profit_requires_both_evidence_sources() -> None:
    grid_request = request().model_copy(
        update={"policy": request().policy.model_copy(update={"take_profit_price": Decimal("120")})}
    )
    limited = exchange().model_copy(update={"supports_take_profit": False})
    preview = service().preview(context(), grid_request, template(), limited)
    assert GridControlReasonCode.TAKE_PROFIT_UNSUPPORTED in preview.reason_codes


def test_stop_loss_requires_both_evidence_sources() -> None:
    grid_request = request().model_copy(
        update={"policy": request().policy.model_copy(update={"stop_loss_price": Decimal("80")})}
    )
    limited = exchange().model_copy(update={"supports_stop_loss": False})
    preview = service().preview(context(), grid_request, template(), limited)
    assert GridControlReasonCode.STOP_LOSS_UNSUPPORTED in preview.reason_codes


def test_leverage_above_exchange_maximum_is_rejected() -> None:
    grid_request = request().model_copy(update={"leverage": Decimal("25")})
    preview = service().preview(context(), grid_request, template(), exchange())
    assert GridControlReasonCode.LEVERAGE_UNSUPPORTED in preview.reason_codes


def test_margin_mode_must_be_explicitly_supported() -> None:
    grid_request = request().model_copy(update={"margin_mode": MarginMode.CROSS})
    limited = exchange().model_copy(update={"supported_margin_modes": (MarginMode.ISOLATED,)})
    preview = service().preview(context(), grid_request, template(), limited)
    assert GridControlReasonCode.MARGIN_MODE_UNSUPPORTED in preview.reason_codes


def test_minimum_amount_failure_is_explicit() -> None:
    limited = exchange().model_copy(update={"minimum_amount": Decimal("10")})
    preview = service().preview(context(), request(), template(), limited)
    assert GridControlReasonCode.MINIMUM_AMOUNT_NOT_MET in preview.reason_codes
    assert all(not level.meets_minimum_amount for level in preview.levels)


def test_minimum_notional_failure_is_explicit() -> None:
    limited = exchange().model_copy(update={"minimum_notional": Decimal("100")})
    preview = service().preview(context(), request(), template(), limited)
    assert GridControlReasonCode.MINIMUM_NOTIONAL_NOT_MET in preview.reason_codes


def test_precision_collapse_is_rejected() -> None:
    coarse = exchange().model_copy(update={"price_step": Decimal("100")})
    preview = service().preview(context(), request(), template(), coarse)
    assert GridControlReasonCode.PRECISION_COLLAPSE in preview.reason_codes


def test_reason_codes_are_sorted() -> None:
    denied = context().model_copy(update={"capabilities": ()})
    stale = template().model_copy(update={"freshness": EvidenceFreshness.STALE})
    grid_request = request().model_copy(update={"execution_mode": ExecutionMode.SIMULATED})
    preview = service().preview(denied, grid_request, stale, exchange())
    values = [item.value for item in preview.reason_codes]
    assert values == sorted(values)


def test_unrelated_capability_does_not_authorize_grid() -> None:
    denied = context().model_copy(update={"capabilities": (BotManagementCapability.BOT_CREATE,)})
    preview = service().preview(denied, request(), template(), exchange())
    assert GridControlReasonCode.CAPABILITY_MISSING in preview.reason_codes
