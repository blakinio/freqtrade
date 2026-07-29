from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class TakeProfitLevel:
    target_r: float
    reduce_fraction: float


@dataclass(frozen=True)
class DcaLevel:
    adverse_move_r: float
    add_fraction: float


def validate_take_profit_plan(levels: tuple[TakeProfitLevel, ...]) -> None:
    if not levels:
        raise ValueError("at least one take-profit level is required")
    targets = [level.target_r for level in levels]
    if any(target <= 0 for target in targets) or targets != sorted(targets):
        raise ValueError("take-profit targets must be positive and ascending")
    total = sum(level.reduce_fraction for level in levels)
    if any(level.reduce_fraction <= 0 for level in levels) or total > 1.0 + 1e-12:
        raise ValueError("take-profit fractions must be positive and total <= 1")


def validate_dca_plan(
    levels: tuple[DcaLevel, ...],
    *,
    initial_fraction: float,
    max_exposure: float,
    max_levels: int,
) -> None:
    if not 0 < initial_fraction <= max_exposure <= 1:
        raise ValueError("require 0 < initial_fraction <= max_exposure <= 1")
    if len(levels) > max_levels:
        raise ValueError("DCA level count exceeds max_levels")
    moves = [level.adverse_move_r for level in levels]
    if any(move <= 0 for move in moves) or moves != sorted(moves):
        raise ValueError("DCA adverse moves must be positive and ascending")
    if any(level.add_fraction <= 0 for level in levels):
        raise ValueError("DCA add fractions must be positive")
    total = initial_fraction + sum(level.add_fraction for level in levels)
    if total > max_exposure + 1e-12:
        raise ValueError("DCA plan exceeds max_exposure")
