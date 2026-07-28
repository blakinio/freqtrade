# ASE-00 E2E diagnostic

- exit code: `2`

```text
============================= test session starts ==============================
platform linux -- Python 3.12.13, pytest-9.1.1, pluggy-1.6.0 -- /home/runner/work/freqtrade/freqtrade/ai_strategy_engine/.venv/bin/python
cachedir: .pytest_cache
rootdir: /home/runner/work/freqtrade/freqtrade
configfile: pyproject.toml
plugins: cov-7.1.0
collecting ... collected 0 items / 1 error

==================================== ERRORS ====================================
_ ERROR collecting tests/ai_platform_integration/test_ase00_vertical_slice.py __
ImportError while importing test module '/home/runner/work/freqtrade/freqtrade/tests/ai_platform_integration/test_ase00_vertical_slice.py'.
Hint: make sure your test modules/packages have valid Python names.
Traceback:
ai_strategy_engine/.venv/lib/python3.12/site-packages/_pytest/python.py:508: in importtestmodule
    mod = import_path(
ai_strategy_engine/.venv/lib/python3.12/site-packages/_pytest/pathlib.py:596: in import_path
    importlib.import_module(module_name)
/opt/hostedtoolcache/Python/3.12.13/x64/lib/python3.12/importlib/__init__.py:90: in import_module
    return _bootstrap._gcd_import(name[level:], package, level)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
<frozen importlib._bootstrap>:1387: in _gcd_import
    ???
<frozen importlib._bootstrap>:1360: in _find_and_load
    ???
<frozen importlib._bootstrap>:1331: in _find_and_load_unlocked
    ???
<frozen importlib._bootstrap>:935: in _load_unlocked
    ???
ai_strategy_engine/.venv/lib/python3.12/site-packages/_pytest/assertion/rewrite.py:188: in exec_module
    exec(co, module.__dict__)
tests/ai_platform_integration/test_ase00_vertical_slice.py:19: in <module>
    from ai_platform.portal.risk.schema import RiskEvaluationSnapshot, RiskPolicyLimits
ai_platform/portal/risk/__init__.py:7: in <module>
    from ai_platform.portal.risk.service import (
ai_platform/portal/risk/service.py:29: in <module>
    from ai_platform.portal.control_plane.context import RequestContext
ai_platform/portal/control_plane/__init__.py:1: in <module>
    from ai_platform.portal.control_plane.api import create_app
ai_platform/portal/control_plane/api.py:7: in <module>
    from fastapi import Depends, FastAPI, status
E   ModuleNotFoundError: No module named 'fastapi'
=============================== warnings summary ===============================
ai_strategy_engine/.venv/lib/python3.12/site-packages/_pytest/config/__init__.py:1464
  /home/runner/work/freqtrade/freqtrade/ai_strategy_engine/.venv/lib/python3.12/site-packages/_pytest/config/__init__.py:1464: PytestConfigWarning: Unknown config option: asyncio_default_fixture_loop_scope
  
    self._warn_or_fail_if_strict(f"Unknown config option: {key}\n")

ai_strategy_engine/.venv/lib/python3.12/site-packages/_pytest/config/__init__.py:1464
  /home/runner/work/freqtrade/freqtrade/ai_strategy_engine/.venv/lib/python3.12/site-packages/_pytest/config/__init__.py:1464: PytestConfigWarning: Unknown config option: asyncio_mode
  
    self._warn_or_fail_if_strict(f"Unknown config option: {key}\n")

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
=========================== short test summary info ============================
ERROR tests/ai_platform_integration/test_ase00_vertical_slice.py
!!!!!!!!!!!!!!!!!!!! Interrupted: 1 error during collection !!!!!!!!!!!!!!!!!!!!
========================= 2 warnings, 1 error in 1.01s =========================

```
