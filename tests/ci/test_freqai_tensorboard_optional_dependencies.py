from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest


REPOSITORY_ROOT = Path(__file__).resolve().parents[2]


def _run_script(script: str) -> None:
    result = subprocess.run(
        [sys.executable, "-c", script],
        cwd=REPOSITORY_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr


def test_tensorboard_fallback_does_not_require_xgboost() -> None:
    _run_script(
        r"""
import builtins
from pathlib import Path

original_import = builtins.__import__


def import_without_xgboost(
    name,
    globals=None,
    locals=None,
    fromlist=(),
    level=0,
):
    if name == "xgboost" or name.startswith("xgboost."):
        raise ModuleNotFoundError("No module named 'xgboost'", name="xgboost")
    return original_import(name, globals, locals, fromlist, level)


builtins.__import__ = import_without_xgboost

from freqtrade.freqai.tensorboard import TBCallback

callback = TBCallback(Path("."))
assert callback.after_iteration(None, 0, {}) is False
assert callback.after_training("model") == "model"
"""
    )


def test_tensorboard_fallback_does_not_hide_broken_xgboost_imports() -> None:
    _run_script(
        r"""
import builtins

original_import = builtins.__import__


def import_with_broken_xgboost(
    name,
    globals=None,
    locals=None,
    fromlist=(),
    level=0,
):
    if name == "xgboost" or name.startswith("xgboost."):
        raise ModuleNotFoundError("No module named 'numpy'", name="numpy")
    return original_import(name, globals, locals, fromlist, level)


builtins.__import__ = import_with_broken_xgboost

try:
    from freqtrade.freqai.tensorboard.base_tensorboard import BaseTensorBoardCallback
except ModuleNotFoundError as exc:
    assert exc.name == "numpy"
else:
    raise AssertionError(BaseTensorBoardCallback)
"""
    )


def test_tensorboard_fallback_preserves_xgboost_callback_contract() -> None:
    callback_module = pytest.importorskip("xgboost.callback")

    from freqtrade.freqai.tensorboard.base_tensorboard import BaseTensorBoardCallback

    assert issubclass(BaseTensorBoardCallback, callback_module.TrainingCallback)
