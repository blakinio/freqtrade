import itertools
from decimal import Decimal

import pytest

from ai_platform.portal.contracts.bot_management.policies import GridSpacing
from ai_platform.portal.grid_control.level_generation import (
    apply_price_precision,
    arithmetic_levels,
    floor_to_step,
    generate_raw_levels,
    geometric_levels,
)


def test_floor_to_step_rounds_down_without_binary_float() -> None:
    assert floor_to_step(Decimal("1.239"), Decimal("0.01")) == Decimal("1.23")


def test_floor_to_step_can_produce_zero() -> None:
    assert floor_to_step(Decimal("0.001"), Decimal("0.01")) == Decimal("0.00")


def test_arithmetic_levels_include_exact_bounds() -> None:
    levels = arithmetic_levels(Decimal("90"), Decimal("110"), 5)
    assert levels == (
        Decimal("90"),
        Decimal("95"),
        Decimal("100"),
        Decimal("105"),
        Decimal("110"),
    )


def test_arithmetic_levels_are_deterministic() -> None:
    first = arithmetic_levels(Decimal("1"), Decimal("2"), 7)
    assert first == arithmetic_levels(Decimal("1"), Decimal("2"), 7)


def test_geometric_levels_include_exact_bounds_and_increase() -> None:
    levels = geometric_levels(Decimal("100"), Decimal("1600"), 5)
    assert levels[0] == Decimal("100")
    assert levels[-1] == Decimal("1600")
    assert all(current < following for current, following in itertools.pairwise(levels))


def test_geometric_levels_are_deterministic() -> None:
    first = geometric_levels(Decimal("90"), Decimal("110"), 11)
    assert first == geometric_levels(Decimal("90"), Decimal("110"), 11)


def test_generate_raw_levels_dispatches_arithmetic() -> None:
    assert generate_raw_levels(
        lower=Decimal("10"),
        upper=Decimal("20"),
        level_count=3,
        spacing=GridSpacing.ARITHMETIC,
    ) == (Decimal("10"), Decimal("15"), Decimal("20"))


def test_generate_raw_levels_dispatches_geometric() -> None:
    levels = generate_raw_levels(
        lower=Decimal("10"),
        upper=Decimal("40"),
        level_count=3,
        spacing=GridSpacing.GEOMETRIC,
    )
    assert levels[1].quantize(Decimal("0.0001")) == Decimal("20.0000")


def test_generate_raw_levels_rejects_unknown_spacing() -> None:
    with pytest.raises(ValueError, match="unsupported grid spacing"):
        generate_raw_levels(
            lower=Decimal("10"),
            upper=Decimal("20"),
            level_count=3,
            spacing="unknown",  # type: ignore[arg-type]
        )


def test_apply_price_precision_rounds_each_level_down() -> None:
    assert apply_price_precision(
        (Decimal("1.239"), Decimal("2.001")),
        Decimal("0.01"),
    ) == (Decimal("1.23"), Decimal("2.00"))
