import ast
import hashlib
from datetime import UTC, datetime
from pathlib import Path
from unittest.mock import MagicMock

import pytest


REPO_ROOT = Path(__file__).resolve().parents[2]
STRATEGY_PATH = (
    REPO_ROOT
    / "ai_platform"
    / "strategies"
    / "AiDesiredPositionRLLifecycleAlignedResearchStrategy.py"
)
EXPECTED_STRATEGY_SHA256 = "366785129798d1332ce593f919c54aa23eefb2b15b2d850ab32d5c5cbdf0d5b7"


class _TradeStub:
    pair = "BTC/USDT"
    is_short = False

    def __init__(self, open_rate: float = 100_000.0) -> None:
        self.open_rate = open_rate
        self.max_rate = open_rate
        self.min_rate = open_rate

    def calc_profit_ratio(self, rate: float) -> float:
        return (rate / self.open_rate) - 1.0

    def adjust_min_max_rates(self, high: float, low: float) -> None:
        self.max_rate = max(self.max_rate, high)
        self.min_rate = min(self.min_rate, low)


def _strategy_class_node() -> ast.ClassDef:
    tree = ast.parse(STRATEGY_PATH.read_text(encoding="utf-8"))
    classes = [node for node in tree.body if isinstance(node, ast.ClassDef)]
    assert len(classes) == 1
    return classes[0]


def _runtime_strategy():
    pytest.importorskip("humanize", reason="full Freqtrade runtime dependency is not installed")
    pytest.importorskip("talib", reason="full Freqtrade runtime dependency is not installed")

    from ai_platform.strategies.AiDesiredPositionRLLifecycleAlignedResearchStrategy import (
        AiDesiredPositionRLLifecycleAlignedResearchStrategy,
    )
    from ai_platform.strategies.AiDesiredPositionRLResearchStrategy import (
        AiDesiredPositionRLResearchStrategy,
    )
    from freqtrade.enums import ExitCheckTuple, ExitType

    strategy = AiDesiredPositionRLLifecycleAlignedResearchStrategy(config={})
    strategy.exit_profit_only = False
    strategy.exit_profit_offset = 0.0
    strategy.custom_exit = MagicMock(return_value=False)
    return strategy, AiDesiredPositionRLResearchStrategy, ExitCheckTuple, ExitType


def test_lifecycle_aligned_strategy_source_has_exact_single_override() -> None:
    class_node = _strategy_class_node()

    assert class_node.name == "AiDesiredPositionRLLifecycleAlignedResearchStrategy"
    assert len(class_node.bases) == 1
    assert isinstance(class_node.bases[0], ast.Name)
    assert class_node.bases[0].id == "AiDesiredPositionRLResearchStrategy"

    assignments = [node for node in class_node.body if isinstance(node, ast.Assign)]
    assert len(assignments) == 1
    assignment = assignments[0]
    assert len(assignment.targets) == 1
    assert isinstance(assignment.targets[0], ast.Name)
    assert assignment.targets[0].id == "ignore_roi_if_entry_signal"
    assert isinstance(assignment.value, ast.Constant)
    assert assignment.value.value is True

    forbidden_nodes = (
        ast.AnnAssign,
        ast.AugAssign,
        ast.FunctionDef,
        ast.AsyncFunctionDef,
    )
    assert not any(isinstance(node, forbidden_nodes) for node in class_node.body)


def test_lifecycle_aligned_strategy_source_hash_is_frozen() -> None:
    digest = hashlib.sha256(STRATEGY_PATH.read_bytes()).hexdigest()
    assert digest == EXPECTED_STRATEGY_SHA256


def test_runtime_inheritance_preserves_baseline_lifecycle() -> None:
    strategy, baseline_class, _, _ = _runtime_strategy()
    strategy_class = type(strategy)

    assert strategy_class.__bases__ == (baseline_class,)
    assert {name for name in strategy_class.__dict__ if not name.startswith("_")} == {
        "ignore_roi_if_entry_signal"
    }
    assert strategy_class.ignore_roi_if_entry_signal is True
    assert strategy_class.minimal_roi == baseline_class.minimal_roi
    assert strategy_class.stoploss == baseline_class.stoploss
    assert strategy_class.timeframe == baseline_class.timeframe
    assert strategy_class.can_short == baseline_class.can_short
    assert strategy_class.use_exit_signal == baseline_class.use_exit_signal


def test_active_target_long_suppresses_roi_only() -> None:
    strategy, _, ExitCheckTuple, ExitType = _runtime_strategy()
    strategy.min_roi_reached = MagicMock(return_value=True)
    strategy.ft_stoploss_reached = MagicMock(
        return_value=ExitCheckTuple(exit_type=ExitType.NONE),
    )

    result = strategy.should_exit(
        _TradeStub(),
        rate=100_000.0,
        current_time=datetime.now(UTC),
        enter=True,
        exit_=False,
    )

    assert result == []
    strategy.min_roi_reached.assert_not_called()


def test_roi_remains_available_without_active_target_long() -> None:
    strategy, _, ExitCheckTuple, ExitType = _runtime_strategy()
    strategy.min_roi_reached = MagicMock(return_value=True)
    strategy.ft_stoploss_reached = MagicMock(
        return_value=ExitCheckTuple(exit_type=ExitType.NONE),
    )

    result = strategy.should_exit(
        _TradeStub(),
        rate=100_000.0,
        current_time=datetime.now(UTC),
        enter=False,
        exit_=False,
    )

    assert [item.exit_type for item in result] == [ExitType.ROI]
    strategy.min_roi_reached.assert_called_once()


def test_hard_stoploss_remains_active_with_target_long() -> None:
    strategy, _, ExitCheckTuple, ExitType = _runtime_strategy()
    strategy.min_roi_reached = MagicMock(return_value=True)
    strategy.ft_stoploss_reached = MagicMock(
        return_value=ExitCheckTuple(exit_type=ExitType.STOP_LOSS),
    )

    result = strategy.should_exit(
        _TradeStub(),
        rate=95_000.0,
        current_time=datetime.now(UTC),
        enter=True,
        exit_=False,
    )

    assert [item.exit_type for item in result] == [ExitType.STOP_LOSS]
    strategy.min_roi_reached.assert_not_called()


def test_target_flat_exit_signal_remains_active() -> None:
    strategy, _, ExitCheckTuple, ExitType = _runtime_strategy()
    strategy.min_roi_reached = MagicMock(return_value=False)
    strategy.ft_stoploss_reached = MagicMock(
        return_value=ExitCheckTuple(exit_type=ExitType.NONE),
    )

    result = strategy.should_exit(
        _TradeStub(),
        rate=100_000.0,
        current_time=datetime.now(UTC),
        enter=False,
        exit_=True,
    )

    assert [item.exit_type for item in result] == [ExitType.EXIT_SIGNAL]
