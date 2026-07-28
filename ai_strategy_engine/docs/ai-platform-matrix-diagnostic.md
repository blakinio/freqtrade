# AI Platform post-format matrix diagnostic

- Ruff check: `0`
- Ruff format: `0`
- compileall: `0`
- pytest: `1`

## check
```text
All checks passed!
```

## format
```text
427 files already formatted
```

## compile
```text
```

## pytest
```text
........................................................................ [  7%]
........................................................................ [ 14%]
........................................................................ [ 22%]
........................................................................ [ 29%]
........................................................................ [ 37%]
........................................................................ [ 44%]
........................................................................ [ 51%]
.....................................................................F.. [ 59%]
........................................................................ [ 66%]
F..........................ss.............................F............. [ 74%]
........................................................................ [ 81%]
.............sssss.................................................sssss [ 88%]
ssssssssssssssssss..sssssssssssssssssssssssss........................... [ 96%]
....................................                                     [100%]
=================================== FAILURES ===================================
_ test_extractor_default_drawdown_matches_freqtrade_implementation_when_available _

trades = [ParsedTrade(source_index=0, open_date_original='2026-05-01T00:00:00Z', close_date_original='2026-05-02T00:00:00Z', op...c), close_date=datetime.datetime(2026, 5, 6, 0, 0, tzinfo=datetime.timezone.utc), profit_abs=-25.0, exit_reason='roi')]
starting_balance = 1000.0

    def _freqtrade_drawdown(
        trades: list[ParsedTrade],
        starting_balance: float,
    ) -> float:
        if not trades:
            return 0.0
        try:
            import pandas as pd
    
>           from freqtrade.data.metrics import calculate_max_drawdown

ai_platform/scripts/model_comparison_oos_result_extractor.py:318: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 
freqtrade/data/__init__.py:5: in <module>
    from freqtrade.data import converter
freqtrade/data/converter/__init__.py:12: in <module>
    from freqtrade.data.converter.trade_converter import (
freqtrade/data/converter/trade_converter.py:11: in <module>
    from freqtrade.configuration import TimeRange
freqtrade/configuration/__init__.py:4: in <module>
    from freqtrade.configuration.config_setup import setup_utils_configuration
freqtrade/configuration/config_setup.py:7: in <module>
    from .configuration import Configuration
freqtrade/configuration/configuration.py:15: in <module>
    from freqtrade.configuration.environment_vars import environment_vars_to_dict
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 

    import logging
    import os
    from typing import Any
    
>   import rapidjson
E   ModuleNotFoundError: No module named 'rapidjson'

freqtrade/configuration/environment_vars.py:5: ModuleNotFoundError

The above exception was the direct cause of the following exception:

tmp_path = PosixPath('/tmp/pytest-of-runner/pytest-0/test_extractor_default_drawdow0')

    def test_extractor_default_drawdown_matches_freqtrade_implementation_when_available(
        tmp_path: Path,
    ) -> None:
        pytest.importorskip("pandas")
        manifest = _canonical_manifest()
        manifest_path = _write_manifest(tmp_path, manifest)
        trades = [
            _trade("2026-05-01T00:00:00Z", "2026-05-02T00:00:00Z", 100.0),
            _trade("2026-05-03T00:00:00Z", "2026-05-04T00:00:00Z", -50.0),
            _trade("2026-05-05T00:00:00Z", "2026-05-06T00:00:00Z", -25.0),
        ]
        archive_path = _write_archive(tmp_path, manifest, trades)
    
>       result = extract_oos_result(archive_path, manifest_path)
                 ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

tests/ai_platform/test_model_comparison_oos_result_extractor.py:278: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 
ai_platform/scripts/model_comparison_oos_result_extractor.py:407: in extract_oos_result
    drawdown = float(calculator(included, starting_balance))
                     ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 

trades = [ParsedTrade(source_index=0, open_date_original='2026-05-01T00:00:00Z', close_date_original='2026-05-02T00:00:00Z', op...c), close_date=datetime.datetime(2026, 5, 6, 0, 0, tzinfo=datetime.timezone.utc), profit_abs=-25.0, exit_reason='roi')]
starting_balance = 1000.0

    def _freqtrade_drawdown(
        trades: list[ParsedTrade],
        starting_balance: float,
    ) -> float:
        if not trades:
            return 0.0
        try:
            import pandas as pd
    
            from freqtrade.data.metrics import calculate_max_drawdown
        except ImportError as exc:
>           raise ModelComparisonOosExtractorError(
                "Non-empty OOS drawdown extraction requires the full Freqtrade runtime dependencies"
            ) from exc
E           ai_platform.scripts.model_comparison_oos_result_extractor.ModelComparisonOosExtractorError: Non-empty OOS drawdown extraction requires the full Freqtrade runtime dependencies

ai_platform/scripts/model_comparison_oos_result_extractor.py:320: ModelComparisonOosExtractorError
_ ResidualPyTorchBoundedM1ExecutionTests.test_encoded_timeranges_stop_before_consumed_oos _

self = <tests.ai_platform.test_residual_pytorch_bounded_m1_execution.ResidualPyTorchBoundedM1ExecutionTests testMethod=test_encoded_timeranges_stop_before_consumed_oos>

    @unittest.skipUnless(NUMERIC_RUNTIME_AVAILABLE, "requires NumPy and Pandas")
    def test_encoded_timeranges_stop_before_consumed_oos(self) -> None:
>       from freqtrade.configuration import TimeRange

tests/ai_platform/test_residual_pytorch_bounded_m1_execution.py:59: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 
freqtrade/configuration/__init__.py:4: in <module>
    from freqtrade.configuration.config_setup import setup_utils_configuration
freqtrade/configuration/config_setup.py:7: in <module>
    from .configuration import Configuration
freqtrade/configuration/configuration.py:15: in <module>
    from freqtrade.configuration.environment_vars import environment_vars_to_dict
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 

    import logging
    import os
    from typing import Any
    
>   import rapidjson
E   ModuleNotFoundError: No module named 'rapidjson'

freqtrade/configuration/environment_vars.py:5: ModuleNotFoundError
________________ test_observable_strategy_disabled_and_enabled _________________

monkeypatch = <_pytest.monkeypatch.MonkeyPatch object at 0x7fef148ea3c0>
tmp_path = PosixPath('/tmp/pytest-of-runner/pytest-0/test_observable_strategy_disab0')

    def test_observable_strategy_disabled_and_enabled(
        monkeypatch: pytest.MonkeyPatch,
        tmp_path: Path,
    ) -> None:
        pandas = pytest.importorskip("pandas")
>       observable_module = importlib.import_module(
            "ai_platform.strategies.AiDesiredPositionRLLifecycleAlignedObservableResearchStrategy"
        )

tests/ai_platform/test_rl_v2_action_observability_execution.py:217: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 
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
<frozen importlib._bootstrap_external>:999: in exec_module
    ???
<frozen importlib._bootstrap>:488: in _call_with_frames_removed
    ???
ai_platform/strategies/AiDesiredPositionRLLifecycleAlignedObservableResearchStrategy.py:13: in <module>
    from ai_platform.strategies.AiDesiredPositionRLLifecycleAlignedResearchStrategy import (
ai_platform/strategies/AiDesiredPositionRLLifecycleAlignedResearchStrategy.py:1: in <module>
    from ai_platform.strategies.AiDesiredPositionRLResearchStrategy import (
ai_platform/strategies/AiDesiredPositionRLResearchStrategy.py:12: in <module>
    from ai_platform.strategies.AiLongOnlyRLResearchStrategy import AiLongOnlyRLResearchStrategy
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 

>   import talib.abstract as ta
E   ModuleNotFoundError: No module named 'talib'

ai_platform/strategies/AiLongOnlyRLResearchStrategy.py:1: ModuleNotFoundError
=============================== warnings summary ===============================
../../../../../opt/hostedtoolcache/Python/3.12.13/x64/lib/python3.12/site-packages/_pytest/config/__init__.py:1464
  /opt/hostedtoolcache/Python/3.12.13/x64/lib/python3.12/site-packages/_pytest/config/__init__.py:1464: PytestConfigWarning: Unknown config option: asyncio_default_fixture_loop_scope
  
    self._warn_or_fail_if_strict(f"Unknown config option: {key}\n")

../../../../../opt/hostedtoolcache/Python/3.12.13/x64/lib/python3.12/site-packages/_pytest/config/__init__.py:1464
  /opt/hostedtoolcache/Python/3.12.13/x64/lib/python3.12/site-packages/_pytest/config/__init__.py:1464: PytestConfigWarning: Unknown config option: asyncio_mode
  
    self._warn_or_fail_if_strict(f"Unknown config option: {key}\n")

../../../../../opt/hostedtoolcache/Python/3.12.13/x64/lib/python3.12/site-packages/fastapi/testclient.py:1
  /opt/hostedtoolcache/Python/3.12.13/x64/lib/python3.12/site-packages/fastapi/testclient.py:1: StarletteDeprecationWarning: Using `httpx` with `starlette.testclient` is deprecated; install `httpx2` instead.
    from starlette.testclient import TestClient as TestClient  # noqa

tests/ai_platform/portal/grid_control/test_preview_validation.py::test_per_level_allocation_is_accumulated
  /opt/hostedtoolcache/Python/3.12.13/x64/lib/python3.12/site-packages/pydantic/main.py:475: UserWarning: Pydantic serializer warnings:
    PydanticSerializationUnexpectedValue(Expected `enum` - serialized value may not be as expected [field_name='allocation_mode', input_value='per_level_quote', input_type=str])
    return self.__pydantic_serializer__.to_python(

tests/ai_platform/portal/identity/test_identity_lifecycle.py::test_open_redirect_is_rejected
tests/ai_platform/portal/product/test_product_capabilities.py::test_signal_validation_rejects_pair_outside_immutable_bot_config
  /opt/hostedtoolcache/Python/3.12.13/x64/lib/python3.12/site-packages/starlette/_exception_handler.py:59: StarletteDeprecationWarning: 'HTTP_422_UNPROCESSABLE_ENTITY' is deprecated. Use 'HTTP_422_UNPROCESSABLE_CONTENT' instead.
    response = await handler(conn, exc)  # type: ignore[arg-type]

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
=========================== short test summary info ============================
FAILED tests/ai_platform/test_model_comparison_oos_result_extractor.py::test_extractor_default_drawdown_matches_freqtrade_implementation_when_available - ai_platform.scripts.model_comparison_oos_result_extractor.ModelComparisonOosExtractorError: Non-empty OOS drawdown extraction requires the full Freqtrade runtime dependencies
FAILED tests/ai_platform/test_residual_pytorch_bounded_m1_execution.py::ResidualPyTorchBoundedM1ExecutionTests::test_encoded_timeranges_stop_before_consumed_oos - ModuleNotFoundError: No module named 'rapidjson'
FAILED tests/ai_platform/test_rl_v2_action_observability_execution.py::test_observable_strategy_disabled_and_enabled - ModuleNotFoundError: No module named 'talib'
3 failed, 914 passed, 55 skipped, 6 warnings in 14.26s
```
