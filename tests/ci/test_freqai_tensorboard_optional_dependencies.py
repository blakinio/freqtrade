from __future__ import annotations

import subprocess
import sys
from pathlib import Path


REPOSITORY_ROOT = Path(__file__).resolve().parents[2]


def test_tensorboard_fallback_does_not_require_xgboost() -> None:
    script = r'''
import builtins
from pathlib import Path

original_import = builtins.__import__


def import_without_xgboost(name, globals=None, locals=None, fromlist=(), level=0):
    if name == "xgboost" or name.startswith("xgboost."):
        raise ModuleNotFoundError("No module named 'xgboost'", name="xgboost")
    return original_import(name, globals, locals, fromlist, level)


builtins.__import__ = import_without_xgboost

from freqtrade.freqai.tensorboard import TBCallback

callback = TBCallback(Path("."))
assert callback.after_iteration(None, 0, {}) is False
assert callback.after_training("model") == "model"
'''
    result = subprocess.run(
        [sys.executable, "-c", script],
        cwd=REPOSITORY_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
