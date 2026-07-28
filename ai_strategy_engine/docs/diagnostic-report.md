# ASE-00 current diagnostic report

## package_pytest

- exit code: `1`

```text
...............................F............F.........                   [100%]
=================================== FAILURES ===================================
___________ test_miyagi_name_is_absent_from_runtime_provider_source ____________

    def test_miyagi_name_is_absent_from_runtime_provider_source() -> None:
        runtime_source = ROOT / "src/strategy_engine"
        offending = [
            str(path.relative_to(ROOT))
            for path in runtime_source.rglob("*.py")
            if "miyagi" in path.read_text(encoding="utf-8").lower()
        ]
>       assert offending == []
E       AssertionError: assert ['src/strateg...ge_filter.py'] == []
E         
E         Left contains 3 more items, first extra item: 'src/strategy_engine/features/trend.py'
E         
E         Full diff:
E         - []
E         + [
E         +     'src/strategy_engine/features/trend.py',
E         +     'src/strategy_engine/features/momentum.py',
E         +     'src/strategy_engine/features/range_filter.py',
E         + ]

tests/unit/test_miyagi_provenance.py:91: AssertionError
_________________ test_cooldown_blocks_rapid_direction_change __________________

    def test_cooldown_blocks_rapid_direction_change() -> None:
        raw = pd.Series([1, 0, -1, 0, 0, -1, 0, 1])
        result = no_repeat_signals(raw, cooldown_bars=3)
>       assert result.tolist() == [1, 0, 0, 0, 0, -1, 0, 0]
E       assert [1, 0, 0, 0, 0, 0, ...] == [1, 0, 0, 0, 0, -1, ...]
E         
E         At index 5 diff: 0 != -1
E         
E         Full diff:
E           [
E               1,
E               0,
E               0,
E               0,
E               0,
E         -     -1,
E               0,
E               0,
E         +     1,
E           ]

tests/unit/test_signal_policies.py:17: AssertionError
=========================== short test summary info ============================
FAILED tests/unit/test_miyagi_provenance.py::test_miyagi_name_is_absent_from_runtime_provider_source - AssertionError: assert ['src/strateg...ge_filter.py'] == []
  
  Left contains 3 more items, first extra item: 'src/strategy_engine/features/trend.py'
  
  Full diff:
  - []
  + [
  +     'src/strategy_engine/features/trend.py',
  +     'src/strategy_engine/features/momentum.py',
  +     'src/strategy_engine/features/range_filter.py',
  + ]
FAILED tests/unit/test_signal_policies.py::test_cooldown_blocks_rapid_direction_change - assert [1, 0, 0, 0, 0, 0, ...] == [1, 0, 0, 0, 0, -1, ...]
  
  At index 5 diff: 0 != -1
  
  Full diff:
    [
        1,
        0,
        0,
        0,
        0,
  -     -1,
        0,
        0,
  +     1,
    ]
2 failed, 52 passed in 1.28s
```

## package_ruff

- exit code: `1`

```text
UP040 Type alias `SnapshotValue` uses `TypeAlias` annotation instead of the `type` keyword
  --> src/strategy_engine/dsl/evaluator.py:12:1
   |
10 | from strategy_engine.domain.models import Action, Side, StrategyDefinition
11 |
12 | SnapshotValue: TypeAlias = JsonValue | Mapping[str, JsonValue]
   | ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
   |
help: Use the `type` keyword

SIM102 Use a single `if` statement instead of nested `if` statements
   --> src/strategy_engine/dsl/validator.py:158:9
    |
156 |       def _validate_dca(risk: Mapping[str, object]) -> None:
157 |           position_size = risk.get("position_size")
158 | /         if isinstance(position_size, Mapping) and position_size.get("type") == "dca":
159 | |             if risk.get("max_exposure") is None:
    | |________________________________________________^
160 |                   raise StrategyValidationError(
161 |                       "DCA_REQUIRES_MAX_EXPOSURE", "DCA requires max_exposure"
    |
help: Combine `if` statements using `and`

SIM102 Use a single `if` statement instead of nested `if` statements
   --> src/strategy_engine/dsl/validator.py:226:9
    |
224 |               )
225 |           feature = condition.get("feature")
226 | /         if feature is not None:
227 | |             if not isinstance(feature, str) or feature not in declared_features:
    | |________________________________________________________________________________^
228 |                   raise StrategyValidationError(
229 |                       "FEATURE_NOT_DECLARED", f"{label} references an undeclared feature: {feature}"
    |
help: Combine `if` statements using `and`

SIM401 Use `parameters.get(name, spec.default)` instead of an `if` block
   --> src/strategy_engine/registry.py:229:21
    |
227 |         resolved: dict[str, object] = {}
228 |         for name, spec in definition.parameters.items():
229 |             value = parameters[name] if name in parameters else spec.default
    |                     ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
230 |             resolved[name] = spec.validate(value)
231 |         _validate_constraints(definition.constraints, resolved, feature_id)
    |
help: Replace with `parameters.get(name, spec.default)`

FURB162 Unnecessary timezone replacement with zero offset
   --> src/strategy_engine/validation/leakage.py:205:41
    |
203 |         )
204 |     try:
205 |         parsed = datetime.fromisoformat(raw_value.replace("Z", "+00:00"))
    |                                         ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
206 |     except ValueError as exc:
207 |         raise LeakageError(
    |
help: Remove `.replace()` call

RUF034 Useless `if`-`else` condition
  --> tests/unit/test_miyagi_provenance.py:32:13
   |
30 |           for classification in ALLOWED_CLASSIFICATIONS
31 |           for key in (
32 | /             document["miyagi_10_in_1"][classification]
33 | |             if isinstance(document["miyagi_10_in_1"][classification], dict)
34 | |             else document["miyagi_10_in_1"][classification]
   | |___________________________________________________________^
35 |           )
36 |       }
   |

RUF034 Useless `if`-`else` condition
  --> tests/unit/test_miyagi_provenance.py:60:13
   |
58 |           for classification in ALLOWED_CLASSIFICATIONS
59 |           for key in (
60 | /             document["miyagi_bonsai"][classification]
61 | |             if isinstance(document["miyagi_bonsai"][classification], dict)
62 | |             else document["miyagi_bonsai"][classification]
   | |__________________________________________________________^
63 |           )
64 |       }
   |

DTZ001 `datetime.datetime()` called without a `tzinfo` argument
  --> tests/unit/test_models.py:50:13
   |
49 | def test_timezone_must_be_utc() -> None:
50 |     naive = datetime(2026, 1, 1)
   |             ^^^^^^^^^^^^^^^^^^^^
51 |     with pytest.raises(ValidationError):
52 |         _feature(event_time=naive, detected_at=naive, available_at=naive)
   |
help: Pass a `datetime.timezone` object to the `tzinfo` parameter

Found 8 errors.
No fixes available (3 hidden fixes can be enabled with the `--unsafe-fixes` option).
```

## package_mypy

- exit code: `1`

```text
src/strategy_engine/registry.py:9: error: Library stubs not installed for "yaml"  [import-untyped]
src/strategy_engine/registry.py:9: note: Hint: "python3 -m pip install types-PyYAML"
src/strategy_engine/policies/signals.py:3: error: Library stubs not installed for "pandas"  [import-untyped]
src/strategy_engine/features/macd.py:3: error: Library stubs not installed for "pandas"  [import-untyped]
src/strategy_engine/features/base.py:6: error: Library stubs not installed for "pandas"  [import-untyped]
src/strategy_engine/features/base.py:6: note: Hint: "python3 -m pip install pandas-stubs"
src/strategy_engine/features/base.py:6: note: (or run "mypy --install-types" to install all missing stub packages)
src/strategy_engine/features/base.py:6: note: See https://mypy.readthedocs.io/en/stable/running_mypy.html#missing-imports
src/strategy_engine/features/pivots.py:6: error: Library stubs not installed for "pandas"  [import-untyped]
src/strategy_engine/api/contracts.py:9: error: Missing type arguments for generic type "dict"  [type-arg]
src/strategy_engine/api/contracts.py:24: error: Missing type arguments for generic type "dict"  [type-arg]
src/strategy_engine/api/contracts.py:25: error: Missing type arguments for generic type "dict"  [type-arg]
src/strategy_engine/dsl/evaluator.py:112: error: Redundant cast to "list[JsonValue]"  [redundant-cast]
src/strategy_engine/dsl/evaluator.py:135: error: Redundant cast to "dict[str, JsonValue]"  [redundant-cast]
src/strategy_engine/features/common.py:4: error: Library stubs not installed for "pandas"  [import-untyped]
src/strategy_engine/features/candles.py:4: error: Library stubs not installed for "pandas"  [import-untyped]
src/strategy_engine/features/volume.py:4: error: Library stubs not installed for "pandas"  [import-untyped]
src/strategy_engine/features/trend.py:6: error: Library stubs not installed for "pandas"  [import-untyped]
src/strategy_engine/features/supertrend.py:4: error: Library stubs not installed for "pandas"  [import-untyped]
src/strategy_engine/features/squeeze.py:4: error: Library stubs not installed for "pandas"  [import-untyped]
src/strategy_engine/features/range_filter.py:4: error: Library stubs not installed for "pandas"  [import-untyped]
src/strategy_engine/features/momentum.py:3: error: Library stubs not installed for "pandas"  [import-untyped]
Found 18 errors in 15 files (checked 29 source files)
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

## platform_pytest

- exit code: `4`

```text
ImportError while loading conftest '/home/runner/work/freqtrade/freqtrade/tests/conftest.py'.
tests/conftest.py:14: in <module>
    from xdist.scheduler.loadscope import LoadScopeScheduling
E   ModuleNotFoundError: No module named 'xdist'
```

