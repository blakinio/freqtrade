from unittest.mock import MagicMock

from freqtrade.enums import ExitCheckTuple, ExitType
from freqtrade.persistence import Trade
from freqtrade.util import dt_now

from ai_platform.strategies.AiDesiredPositionRLLifecycleAlignedResearchStrategy import (
    AiDesiredPositionRLLifecycleAlignedResearchStrategy,
)
from ai_platform.strategies.AiDesiredPositionRLResearchStrategy import (
    AiDesiredPositionRLResearchStrategy,
)


def _strategy() -> AiDesiredPositionRLLifecycleAlignedResearchStrategy:
    strategy = AiDesiredPositionRLLifecycleAlignedResearchStrategy(config={})
    strategy.exit_profit_only = False
    strategy.exit_profit_offset = 0.0
    strategy.custom_exit = MagicMock(return_value=False)
    return strategy


def _trade() -> Trade:
    return Trade(
        pair="BTC/USDT",
        stake_amount=100.0,
        amount=0.001,
        open_date=dt_now(),
        fee_open=0.002,
        fee_close=0.002,
        exchange="kraken",
        open_rate=100_000.0,
        leverage=1.0,
    )


def _exit_types(result: list[ExitCheckTuple]) -> list[ExitType]:
    return [item.exit_type for item in result]


def test_lifecycle_aligned_strategy_has_exact_single_override() -> None:
    strategy_class = AiDesiredPositionRLLifecycleAlignedResearchStrategy

    assert strategy_class.__bases__ == (AiDesiredPositionRLResearchStrategy,)
    assert {
        name for name in strategy_class.__dict__ if not name.startswith("_")
    } == {"ignore_roi_if_entry_signal"}
    assert strategy_class.ignore_roi_if_entry_signal is True

    assert strategy_class.minimal_roi == AiDesiredPositionRLResearchStrategy.minimal_roi
    assert strategy_class.stoploss == AiDesiredPositionRLResearchStrategy.stoploss
    assert strategy_class.timeframe == AiDesiredPositionRLResearchStrategy.timeframe
    assert strategy_class.can_short == AiDesiredPositionRLResearchStrategy.can_short
    assert strategy_class.use_exit_signal == AiDesiredPositionRLResearchStrategy.use_exit_signal


def test_active_target_long_suppresses_roi_only() -> None:
    strategy = _strategy()
    strategy.min_roi_reached = MagicMock(return_value=True)
    strategy.ft_stoploss_reached = MagicMock(
        return_value=ExitCheckTuple(exit_type=ExitType.NONE),
    )

    result = strategy.should_exit(
        _trade(),
        rate=100_000.0,
        current_time=dt_now(),
        enter=True,
        exit_=False,
    )

    assert result == []
    strategy.min_roi_reached.assert_not_called()


def test_roi_remains_available_without_active_target_long() -> None:
    strategy = _strategy()
    strategy.min_roi_reached = MagicMock(return_value=True)
    strategy.ft_stoploss_reached = MagicMock(
        return_value=ExitCheckTuple(exit_type=ExitType.NONE),
    )

    result = strategy.should_exit(
        _trade(),
        rate=100_000.0,
        current_time=dt_now(),
        enter=False,
        exit_=False,
    )

    assert _exit_types(result) == [ExitType.ROI]
    strategy.min_roi_reached.assert_called_once()


def test_hard_stoploss_remains_active_with_target_long() -> None:
    strategy = _strategy()
    strategy.min_roi_reached = MagicMock(return_value=True)
    strategy.ft_stoploss_reached = MagicMock(
        return_value=ExitCheckTuple(exit_type=ExitType.STOP_LOSS),
    )

    result = strategy.should_exit(
        _trade(),
        rate=95_000.0,
        current_time=dt_now(),
        enter=True,
        exit_=False,
    )

    assert _exit_types(result) == [ExitType.STOP_LOSS]
    strategy.min_roi_reached.assert_not_called()


def test_target_flat_exit_signal_remains_active() -> None:
    strategy = _strategy()
    strategy.min_roi_reached = MagicMock(return_value=False)
    strategy.ft_stoploss_reached = MagicMock(
        return_value=ExitCheckTuple(exit_type=ExitType.NONE),
    )

    result = strategy.should_exit(
        _trade(),
        rate=100_000.0,
        current_time=dt_now(),
        enter=False,
        exit_=True,
    )

    assert _exit_types(result) == [ExitType.EXIT_SIGNAL]
