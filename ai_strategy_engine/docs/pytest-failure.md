# ASE-00 pytest diagnostic

- exit code: `2`

```text
============================= test session starts ==============================
platform linux -- Python 3.12.13, pytest-9.1.1, pluggy-1.6.0 -- /home/runner/work/freqtrade/freqtrade/ai_strategy_engine/.venv/bin/python
cachedir: .pytest_cache
rootdir: /home/runner/work/freqtrade/freqtrade/ai_strategy_engine
configfile: pyproject.toml
testpaths: tests
plugins: cov-7.1.0
collecting ... collected 54 items / 1 error

==================================== ERRORS ====================================
___________ ERROR collecting tests/unit/test_materialize_starter.py ____________
ImportError while importing test module '/home/runner/work/freqtrade/freqtrade/ai_strategy_engine/tests/unit/test_materialize_starter.py'.
Hint: make sure your test modules/packages have valid Python names.
Traceback:
/opt/hostedtoolcache/Python/3.12.13/x64/lib/python3.12/importlib/__init__.py:90: in import_module
    return _bootstrap._gcd_import(name[level:], package, level)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
tests/unit/test_materialize_starter.py:8: in <module>
    from materialize_starter import _safe_extract
E   ModuleNotFoundError: No module named 'materialize_starter'
=========================== short test summary info ============================
ERROR tests/unit/test_materialize_starter.py
!!!!!!!!!!!!!!!!!!!! Interrupted: 1 error during collection !!!!!!!!!!!!!!!!!!!!
=============================== 1 error in 0.72s ===============================

```
