
import pytest

from strategy_engine.risk.position_management import DcaLevel, TakeProfitLevel, validate_dca_plan, validate_take_profit_plan


def test_valid_partial_take_profit_plan() -> None:
    validate_take_profit_plan((TakeProfitLevel(1.0, 0.5), TakeProfitLevel(2.0, 0.5)))


def test_dca_cannot_exceed_max_exposure() -> None:
    with pytest.raises(ValueError):
        validate_dca_plan(
            (DcaLevel(1.0, 0.3), DcaLevel(2.0, 0.3)),
            initial_fraction=0.5,
            max_exposure=0.8,
            max_levels=2,
        )
