from __future__ import annotations

import subprocess
import sys
from pathlib import Path


def test_conversion_runtime_import_does_not_require_unrelated_dependencies() -> None:
    repository_root = Path(__file__).resolve().parents[2]
    probe = r'''
import builtins

real_import = builtins.__import__


def guarded_import(name, globals=None, locals=None, fromlist=(), level=0):
    blocked = ("jsonschema", "pydantic")
    if any(name == item or name.startswith(f"{item}.") for item in blocked):
        raise ModuleNotFoundError(f"blocked unrelated dependency: {name}")
    return real_import(name, globals, locals, fromlist, level)


builtins.__import__ = guarded_import

from ai_platform.scripts.wickhunter_live_archive_conversion import (
    convert_production_archive,
    verify_operation,
)
from ai_platform.wickhunter import load_accepted_import as exported_loader
from ai_platform.wickhunter.dataset import load_accepted_import as direct_loader

assert callable(convert_production_archive)
assert callable(verify_operation)
assert exported_loader is direct_loader
'''
    completed = subprocess.run(
        [sys.executable, "-c", probe],
        cwd=repository_root,
        check=False,
        capture_output=True,
        text=True,
    )

    assert completed.returncode == 0, completed.stderr
