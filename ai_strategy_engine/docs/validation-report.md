# ASE-00 validation report

## package_pytest

- exit code: `1`

```text
............................................F.........                   [100%]
=================================== FAILURES ===================================
_______ test_cooldown_blocks_rapid_direction_change_without_replaying_it _______

    def test_cooldown_blocks_rapid_direction_change_without_replaying_it() -> None:
        raw = pd.Series([1, 0, -1, 0, 0, -1, 0, 1])
        result = no_repeat_signals(raw, cooldown_bars=3)
>       assert result.tolist() == [1, 0, 0, 0, 0, 0, 0, 1]
E       assert [1, 0, 0, 0, 0, -1, ...] == [1, 0, 0, 0, 0, 0, ...]
E         
E         At index 5 diff: -1 != 0
E         
E         Full diff:
E           [
E               1,
E               0,
E               0,
E               0,
E               0,
E         +     -1,
E               0,
E               0,
E         -     1,
E           ]

tests/unit/test_signal_policies.py:17: AssertionError
=========================== short test summary info ============================
FAILED tests/unit/test_signal_policies.py::test_cooldown_blocks_rapid_direction_change_without_replaying_it - assert [1, 0, 0, 0, 0, -1, ...] == [1, 0, 0, 0, 0, 0, ...]
  
  At index 5 diff: -1 != 0
  
  Full diff:
    [
        1,
        0,
        0,
        0,
        0,
  +     -1,
        0,
        0,
  -     1,
    ]
1 failed, 53 passed in 1.31s
```

## package_ruff

- exit code: `0`

```text
All checks passed!
```

## package_mypy

- exit code: `0`

```text
Success: no issues found in 29 source files
```

## package_compile

- exit code: `0`

```text
```

## platform_ruff

- exit code: `0`

```text
All checks passed!
```

## platform_compile

- exit code: `0`

```text
```

## platform_pytest

- exit code: `2`

```text

==================================== ERRORS ====================================
_ ERROR collecting tests/ai_platform_integration/test_ase00_vertical_slice.py __
ImportError while importing test module '/home/runner/work/freqtrade/freqtrade/tests/ai_platform_integration/test_ase00_vertical_slice.py'.
Hint: make sure your test modules/packages have valid Python names.
Traceback:
/opt/hostedtoolcache/Python/3.12.13/x64/lib/python3.12/importlib/__init__.py:90: in import_module
    return _bootstrap._gcd_import(name[level:], package, level)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
tests/ai_platform_integration/test_ase00_vertical_slice.py:18: in <module>
    from ai_platform.portal.contracts.execution import RuntimeHealthState
E   ModuleNotFoundError: No module named 'ai_platform'
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
2 warnings, 1 error in 0.53s
```

