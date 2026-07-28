from __future__ import annotations

from decimal import ROUND_DOWN, Decimal, localcontext

from ai_platform.portal.contracts.bot_management.policies import GridSpacing


CALCULATION_PRECISION = 50


def floor_to_step(value: Decimal, step: Decimal) -> Decimal:
    """Round a positive Decimal down to an explicit exchange step."""

    with localcontext() as context:
        context.prec = CALCULATION_PRECISION
        units = (value / step).to_integral_value(rounding=ROUND_DOWN)
        return units * step


def arithmetic_levels(
    lower: Decimal,
    upper: Decimal,
    level_count: int,
) -> tuple[Decimal, ...]:
    with localcontext() as context:
        context.prec = CALCULATION_PRECISION
        interval = (upper - lower) / Decimal(level_count - 1)
        values = [lower + interval * Decimal(index) for index in range(level_count)]
        values[0] = lower
        values[-1] = upper
        return tuple(values)


def geometric_levels(
    lower: Decimal,
    upper: Decimal,
    level_count: int,
) -> tuple[Decimal, ...]:
    with localcontext() as context:
        context.prec = CALCULATION_PRECISION
        logarithmic_step = (upper / lower).ln() / Decimal(level_count - 1)
        values = [lower * (logarithmic_step * Decimal(index)).exp() for index in range(level_count)]
        values[0] = lower
        values[-1] = upper
        return tuple(values)


def generate_raw_levels(
    *,
    lower: Decimal,
    upper: Decimal,
    level_count: int,
    spacing: GridSpacing,
) -> tuple[Decimal, ...]:
    if spacing == GridSpacing.ARITHMETIC:
        return arithmetic_levels(lower, upper, level_count)
    if spacing == GridSpacing.GEOMETRIC:
        return geometric_levels(lower, upper, level_count)
    raise ValueError("unsupported grid spacing")


def apply_price_precision(
    levels: tuple[Decimal, ...],
    price_step: Decimal,
) -> tuple[Decimal, ...]:
    return tuple(floor_to_step(level, price_step) for level in levels)
