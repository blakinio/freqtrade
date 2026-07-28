# ASE-00 E2E after squeeze alignment

- exit code: `1`

```text
============================= test session starts ==============================
platform linux -- Python 3.12.13, pytest-9.1.1, pluggy-1.6.0 -- /home/runner/work/freqtrade/freqtrade/ai_strategy_engine/.venv/bin/python
cachedir: .pytest_cache
rootdir: /home/runner/work/freqtrade/freqtrade
configfile: pyproject.toml
plugins: cov-7.1.0, anyio-4.14.2
collecting ... collected 12 items

tests/ai_platform_integration/test_ase00_vertical_slice.py::test_complete_synthetic_shadow_flow_uses_existing_risk_core FAILED [  8%]
tests/ai_platform_integration/test_ase00_vertical_slice.py::test_duplicate_event_is_idempotent FAILED [ 16%]
tests/ai_platform_integration/test_ase00_vertical_slice.py::test_delayed_event_is_accepted_when_available_before_decision FAILED [ 25%]
tests/ai_platform_integration/test_ase00_vertical_slice.py::test_out_of_order_event_input_is_normalized FAILED [ 33%]
tests/ai_platform_integration/test_ase00_vertical_slice.py::test_future_feature_is_rejected_fail_closed FAILED [ 41%]
tests/ai_platform_integration/test_ase00_vertical_slice.py::test_unconfirmed_pivot_is_rejected FAILED [ 50%]
tests/ai_platform_integration/test_ase00_vertical_slice.py::test_unconfirmed_htf_record_is_rejected PASSED [ 58%]
tests/ai_platform_integration/test_ase00_vertical_slice.py::test_existing_risk_core_rejection_is_preserved FAILED [ 66%]
tests/ai_platform_integration/test_ase00_vertical_slice.py::test_restart_and_replay_produces_identical_evidence FAILED [ 75%]
tests/ai_platform_integration/test_ase00_vertical_slice.py::test_missing_liquidation_data_fails_closed PASSED [ 83%]
tests/ai_platform_integration/test_ase00_vertical_slice.py::test_conflicting_duplicate_fails_closed_with_reason_code PASSED [ 91%]
tests/ai_platform_integration/test_ase00_vertical_slice.py::test_adapter_has_no_execution_or_freqtrade_dependency PASSED [100%]

=================================== FAILURES ===================================
_________ test_complete_synthetic_shadow_flow_uses_existing_risk_core __________

    def test_complete_synthetic_shadow_flow_uses_existing_risk_core() -> None:
>       evidence = _engine().run(
            events=_events(),
            strategy_document=_strategy(),
            decision_time=_decision_time(),
            risk_limits=_limits(),
            risk_snapshot=_snapshot(),
        )

tests/ai_platform_integration/test_ase00_vertical_slice.py:224: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 
ai_platform/research/strategy_engine/ase00_adapter.py:178: in run
    records, current_snapshot, previous_snapshot, event_snapshot = self._features(
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 

self = <ai_platform.research.strategy_engine.ase00_adapter.Ase00ShadowEngine object at 0x7fc9793e7ec0>
normalized = NormalizedEvents(events=(AcceptedSyntheticEvent(event_id='6e0e17a2b1d6dd1d9432e835a41c1b654f7a299b6f3099fee0c46b57e8dd...'notional': 250000.0})), reason_codes=(), data_hash='f293bc6e6c91b4ae02836068fb985ed135a0d35903b2264dbdfb0242be3bbf8b')
strategy = StrategyDefinition(schema_version='1.0.0', strategy_id='ase00-synthetic', version='1.0.0', universe=StrategyUniverse(s...='strategy:ase00-synthetic', lineage=(), details={'lineage_complete': True, 'future_shift': 0, 'research_mode': True}))
decision_time = datetime.datetime(2026, 7, 28, 4, 55, 2, 100000, tzinfo=datetime.timezone.utc)
config_hash = '1733266a431e538411c029e88b64723913f930717e09f0af098c595f181af677'

    def _features(
        self,
        normalized: NormalizedEvents,
        strategy: StrategyDefinition,
        decision_time: datetime,
        config_hash: str,
    ) -> tuple[
        tuple[FeatureRecord, ...],
        dict[str, JsonValue | Mapping[str, JsonValue]],
        dict[str, JsonValue | Mapping[str, JsonValue]],
        dict[str, JsonValue],
    ]:
        market_events = tuple(event for event in normalized.events if event.kind == "market_bar")
        frame = self._market_frame(market_events)
        latest_event = market_events[-1]
        records: list[FeatureRecord] = []
        current_snapshot: dict[str, JsonValue | Mapping[str, JsonValue]] = {}
        previous_snapshot: dict[str, JsonValue | Mapping[str, JsonValue]] = {}
    
        configured = {feature.id: feature for feature in strategy.features}
        squeeze_ref = configured.get("squeeze_ratio.v1")
        if squeeze_ref is not None:
            squeeze = squeeze_features(frame, **squeeze_ref.params)
            value = _row_mapping(
                squeeze,
                -1,
                (
                    "squeeze_ratio",
                    "squeeze_state",
                    "squeeze_duration",
                    "bars_since_release",
                    "linreg_momentum",
                    "momentum_slope",
                    "momentum_acceleration",
                ),
            )
>           record = make_feature_record(
                registry=self.registry,
                feature_id=squeeze_ref.id,
                symbol=latest_event.symbol,
                timeframe=squeeze_ref.timeframe,
                event_time=latest_event.event_time,
                detected_at=latest_event.detected_at,
                available_at=latest_event.available_at,
                value=value,
                is_confirmed=latest_event.is_confirmed,
                source=latest_event.source,
                data_version=normalized.data_hash,
                code_version=self.code_hash,
                configuration_hash=config_hash,
                source_event_id=latest_event.event_id,
                parameters=dict(squeeze_ref.params),
            )
E           TypeError: make_feature_record() got an unexpected keyword argument 'registry'

ai_platform/research/strategy_engine/ase00_adapter.py:401: TypeError
______________________ test_duplicate_event_is_idempotent ______________________

    def test_duplicate_event_is_idempotent() -> None:
        events = _events()
>       first = _engine().run(
            events=events,
            strategy_document=_strategy(),
            decision_time=_decision_time(),
            risk_limits=_limits(),
            risk_snapshot=_snapshot(),
        )

tests/ai_platform_integration/test_ase00_vertical_slice.py:247: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 
ai_platform/research/strategy_engine/ase00_adapter.py:178: in run
    records, current_snapshot, previous_snapshot, event_snapshot = self._features(
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 

self = <ai_platform.research.strategy_engine.ase00_adapter.Ase00ShadowEngine object at 0x7fc9792af740>
normalized = NormalizedEvents(events=(AcceptedSyntheticEvent(event_id='6e0e17a2b1d6dd1d9432e835a41c1b654f7a299b6f3099fee0c46b57e8dd...'notional': 250000.0})), reason_codes=(), data_hash='f293bc6e6c91b4ae02836068fb985ed135a0d35903b2264dbdfb0242be3bbf8b')
strategy = StrategyDefinition(schema_version='1.0.0', strategy_id='ase00-synthetic', version='1.0.0', universe=StrategyUniverse(s...='strategy:ase00-synthetic', lineage=(), details={'lineage_complete': True, 'future_shift': 0, 'research_mode': True}))
decision_time = datetime.datetime(2026, 7, 28, 4, 55, 2, 100000, tzinfo=datetime.timezone.utc)
config_hash = '1733266a431e538411c029e88b64723913f930717e09f0af098c595f181af677'

    def _features(
        self,
        normalized: NormalizedEvents,
        strategy: StrategyDefinition,
        decision_time: datetime,
        config_hash: str,
    ) -> tuple[
        tuple[FeatureRecord, ...],
        dict[str, JsonValue | Mapping[str, JsonValue]],
        dict[str, JsonValue | Mapping[str, JsonValue]],
        dict[str, JsonValue],
    ]:
        market_events = tuple(event for event in normalized.events if event.kind == "market_bar")
        frame = self._market_frame(market_events)
        latest_event = market_events[-1]
        records: list[FeatureRecord] = []
        current_snapshot: dict[str, JsonValue | Mapping[str, JsonValue]] = {}
        previous_snapshot: dict[str, JsonValue | Mapping[str, JsonValue]] = {}
    
        configured = {feature.id: feature for feature in strategy.features}
        squeeze_ref = configured.get("squeeze_ratio.v1")
        if squeeze_ref is not None:
            squeeze = squeeze_features(frame, **squeeze_ref.params)
            value = _row_mapping(
                squeeze,
                -1,
                (
                    "squeeze_ratio",
                    "squeeze_state",
                    "squeeze_duration",
                    "bars_since_release",
                    "linreg_momentum",
                    "momentum_slope",
                    "momentum_acceleration",
                ),
            )
>           record = make_feature_record(
                registry=self.registry,
                feature_id=squeeze_ref.id,
                symbol=latest_event.symbol,
                timeframe=squeeze_ref.timeframe,
                event_time=latest_event.event_time,
                detected_at=latest_event.detected_at,
                available_at=latest_event.available_at,
                value=value,
                is_confirmed=latest_event.is_confirmed,
                source=latest_event.source,
                data_version=normalized.data_hash,
                code_version=self.code_hash,
                configuration_hash=config_hash,
                source_event_id=latest_event.event_id,
                parameters=dict(squeeze_ref.params),
            )
E           TypeError: make_feature_record() got an unexpected keyword argument 'registry'

ai_platform/research/strategy_engine/ase00_adapter.py:401: TypeError
________ test_delayed_event_is_accepted_when_available_before_decision _________

    def test_delayed_event_is_accepted_when_available_before_decision() -> None:
        events = _events()
        events[-1] = replace(
            events[-1],
            available_at=events[-1].detected_at + timedelta(seconds=2),
        )
        decision_time = events[-1].available_at + timedelta(seconds=1)
>       evidence = _engine().run(
            events=events,
            strategy_document=_strategy(),
            decision_time=decision_time,
            risk_limits=_limits(),
            risk_snapshot=_snapshot(),
        )

tests/ai_platform_integration/test_ase00_vertical_slice.py:273: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 
ai_platform/research/strategy_engine/ase00_adapter.py:178: in run
    records, current_snapshot, previous_snapshot, event_snapshot = self._features(
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 

self = <ai_platform.research.strategy_engine.ase00_adapter.Ase00ShadowEngine object at 0x7fc9794323f0>
normalized = NormalizedEvents(events=(AcceptedSyntheticEvent(event_id='6e0e17a2b1d6dd1d9432e835a41c1b654f7a299b6f3099fee0c46b57e8dd...reason_codes=('DELAYED_EVENT_ACCEPTED',), data_hash='7d8c298e9c9e980661c75f26d6d6b29eececb684da022f4d44eda314fe4351e5')
strategy = StrategyDefinition(schema_version='1.0.0', strategy_id='ase00-synthetic', version='1.0.0', universe=StrategyUniverse(s...='strategy:ase00-synthetic', lineage=(), details={'lineage_complete': True, 'future_shift': 0, 'research_mode': True}))
decision_time = datetime.datetime(2026, 7, 28, 4, 55, 4, 50000, tzinfo=datetime.timezone.utc)
config_hash = '1733266a431e538411c029e88b64723913f930717e09f0af098c595f181af677'

    def _features(
        self,
        normalized: NormalizedEvents,
        strategy: StrategyDefinition,
        decision_time: datetime,
        config_hash: str,
    ) -> tuple[
        tuple[FeatureRecord, ...],
        dict[str, JsonValue | Mapping[str, JsonValue]],
        dict[str, JsonValue | Mapping[str, JsonValue]],
        dict[str, JsonValue],
    ]:
        market_events = tuple(event for event in normalized.events if event.kind == "market_bar")
        frame = self._market_frame(market_events)
        latest_event = market_events[-1]
        records: list[FeatureRecord] = []
        current_snapshot: dict[str, JsonValue | Mapping[str, JsonValue]] = {}
        previous_snapshot: dict[str, JsonValue | Mapping[str, JsonValue]] = {}
    
        configured = {feature.id: feature for feature in strategy.features}
        squeeze_ref = configured.get("squeeze_ratio.v1")
        if squeeze_ref is not None:
            squeeze = squeeze_features(frame, **squeeze_ref.params)
            value = _row_mapping(
                squeeze,
                -1,
                (
                    "squeeze_ratio",
                    "squeeze_state",
                    "squeeze_duration",
                    "bars_since_release",
                    "linreg_momentum",
                    "momentum_slope",
                    "momentum_acceleration",
                ),
            )
>           record = make_feature_record(
                registry=self.registry,
                feature_id=squeeze_ref.id,
                symbol=latest_event.symbol,
                timeframe=squeeze_ref.timeframe,
                event_time=latest_event.event_time,
                detected_at=latest_event.detected_at,
                available_at=latest_event.available_at,
                value=value,
                is_confirmed=latest_event.is_confirmed,
                source=latest_event.source,
                data_version=normalized.data_hash,
                code_version=self.code_hash,
                configuration_hash=config_hash,
                source_event_id=latest_event.event_id,
                parameters=dict(squeeze_ref.params),
            )
E           TypeError: make_feature_record() got an unexpected keyword argument 'registry'

ai_platform/research/strategy_engine/ase00_adapter.py:401: TypeError
_________________ test_out_of_order_event_input_is_normalized __________________

    def test_out_of_order_event_input_is_normalized() -> None:
>       ordered = _engine().run(
            events=_events(),
            strategy_document=_strategy(),
            decision_time=_decision_time(),
            risk_limits=_limits(),
            risk_snapshot=_snapshot(),
        )

tests/ai_platform_integration/test_ase00_vertical_slice.py:285: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 
ai_platform/research/strategy_engine/ase00_adapter.py:178: in run
    records, current_snapshot, previous_snapshot, event_snapshot = self._features(
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 

self = <ai_platform.research.strategy_engine.ase00_adapter.Ase00ShadowEngine object at 0x7fc979302000>
normalized = NormalizedEvents(events=(AcceptedSyntheticEvent(event_id='6e0e17a2b1d6dd1d9432e835a41c1b654f7a299b6f3099fee0c46b57e8dd...'notional': 250000.0})), reason_codes=(), data_hash='f293bc6e6c91b4ae02836068fb985ed135a0d35903b2264dbdfb0242be3bbf8b')
strategy = StrategyDefinition(schema_version='1.0.0', strategy_id='ase00-synthetic', version='1.0.0', universe=StrategyUniverse(s...='strategy:ase00-synthetic', lineage=(), details={'lineage_complete': True, 'future_shift': 0, 'research_mode': True}))
decision_time = datetime.datetime(2026, 7, 28, 4, 55, 2, 100000, tzinfo=datetime.timezone.utc)
config_hash = '1733266a431e538411c029e88b64723913f930717e09f0af098c595f181af677'

    def _features(
        self,
        normalized: NormalizedEvents,
        strategy: StrategyDefinition,
        decision_time: datetime,
        config_hash: str,
    ) -> tuple[
        tuple[FeatureRecord, ...],
        dict[str, JsonValue | Mapping[str, JsonValue]],
        dict[str, JsonValue | Mapping[str, JsonValue]],
        dict[str, JsonValue],
    ]:
        market_events = tuple(event for event in normalized.events if event.kind == "market_bar")
        frame = self._market_frame(market_events)
        latest_event = market_events[-1]
        records: list[FeatureRecord] = []
        current_snapshot: dict[str, JsonValue | Mapping[str, JsonValue]] = {}
        previous_snapshot: dict[str, JsonValue | Mapping[str, JsonValue]] = {}
    
        configured = {feature.id: feature for feature in strategy.features}
        squeeze_ref = configured.get("squeeze_ratio.v1")
        if squeeze_ref is not None:
            squeeze = squeeze_features(frame, **squeeze_ref.params)
            value = _row_mapping(
                squeeze,
                -1,
                (
                    "squeeze_ratio",
                    "squeeze_state",
                    "squeeze_duration",
                    "bars_since_release",
                    "linreg_momentum",
                    "momentum_slope",
                    "momentum_acceleration",
                ),
            )
>           record = make_feature_record(
                registry=self.registry,
                feature_id=squeeze_ref.id,
                symbol=latest_event.symbol,
                timeframe=squeeze_ref.timeframe,
                event_time=latest_event.event_time,
                detected_at=latest_event.detected_at,
                available_at=latest_event.available_at,
                value=value,
                is_confirmed=latest_event.is_confirmed,
                source=latest_event.source,
                data_version=normalized.data_hash,
                code_version=self.code_hash,
                configuration_hash=config_hash,
                source_event_id=latest_event.event_id,
                parameters=dict(squeeze_ref.params),
            )
E           TypeError: make_feature_record() got an unexpected keyword argument 'registry'

ai_platform/research/strategy_engine/ase00_adapter.py:401: TypeError
_________________ test_future_feature_is_rejected_fail_closed __________________

    def test_future_feature_is_rejected_fail_closed() -> None:
        events = _events()
        decision_time = _decision_time()
        events[-2] = replace(events[-2], available_at=decision_time + timedelta(seconds=1))
>       evidence = _engine().run(
            events=events,
            strategy_document=_strategy(),
            decision_time=decision_time,
            risk_limits=_limits(),
            risk_snapshot=_snapshot(),
        )

tests/ai_platform_integration/test_ase00_vertical_slice.py:308: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 
ai_platform/research/strategy_engine/ase00_adapter.py:178: in run
    records, current_snapshot, previous_snapshot, event_snapshot = self._features(
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 

self = <ai_platform.research.strategy_engine.ase00_adapter.Ase00ShadowEngine object at 0x7fc9792db6e0>
normalized = NormalizedEvents(events=(AcceptedSyntheticEvent(event_id='6e0e17a2b1d6dd1d9432e835a41c1b654f7a299b6f3099fee0c46b57e8dd...reason_codes=('DELAYED_EVENT_ACCEPTED',), data_hash='47defc3aa362709865dc2e239a0a6579919b2cfa47cc71157e9ee298269766b8')
strategy = StrategyDefinition(schema_version='1.0.0', strategy_id='ase00-synthetic', version='1.0.0', universe=StrategyUniverse(s...='strategy:ase00-synthetic', lineage=(), details={'lineage_complete': True, 'future_shift': 0, 'research_mode': True}))
decision_time = datetime.datetime(2026, 7, 28, 4, 55, 2, 100000, tzinfo=datetime.timezone.utc)
config_hash = '1733266a431e538411c029e88b64723913f930717e09f0af098c595f181af677'

    def _features(
        self,
        normalized: NormalizedEvents,
        strategy: StrategyDefinition,
        decision_time: datetime,
        config_hash: str,
    ) -> tuple[
        tuple[FeatureRecord, ...],
        dict[str, JsonValue | Mapping[str, JsonValue]],
        dict[str, JsonValue | Mapping[str, JsonValue]],
        dict[str, JsonValue],
    ]:
        market_events = tuple(event for event in normalized.events if event.kind == "market_bar")
        frame = self._market_frame(market_events)
        latest_event = market_events[-1]
        records: list[FeatureRecord] = []
        current_snapshot: dict[str, JsonValue | Mapping[str, JsonValue]] = {}
        previous_snapshot: dict[str, JsonValue | Mapping[str, JsonValue]] = {}
    
        configured = {feature.id: feature for feature in strategy.features}
        squeeze_ref = configured.get("squeeze_ratio.v1")
        if squeeze_ref is not None:
            squeeze = squeeze_features(frame, **squeeze_ref.params)
            value = _row_mapping(
                squeeze,
                -1,
                (
                    "squeeze_ratio",
                    "squeeze_state",
                    "squeeze_duration",
                    "bars_since_release",
                    "linreg_momentum",
                    "momentum_slope",
                    "momentum_acceleration",
                ),
            )
>           record = make_feature_record(
                registry=self.registry,
                feature_id=squeeze_ref.id,
                symbol=latest_event.symbol,
                timeframe=squeeze_ref.timeframe,
                event_time=latest_event.event_time,
                detected_at=latest_event.detected_at,
                available_at=latest_event.available_at,
                value=value,
                is_confirmed=latest_event.is_confirmed,
                source=latest_event.source,
                data_version=normalized.data_hash,
                code_version=self.code_hash,
                configuration_hash=config_hash,
                source_event_id=latest_event.event_id,
                parameters=dict(squeeze_ref.params),
            )
E           TypeError: make_feature_record() got an unexpected keyword argument 'registry'

ai_platform/research/strategy_engine/ase00_adapter.py:401: TypeError
______________________ test_unconfirmed_pivot_is_rejected ______________________

    def test_unconfirmed_pivot_is_rejected() -> None:
        events = _events()
>       baseline = _engine().run(
            events=events,
            strategy_document=_strategy(),
            decision_time=_decision_time(),
            risk_limits=_limits(),
            risk_snapshot=_snapshot(),
        )

tests/ai_platform_integration/test_ase00_vertical_slice.py:323: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 
ai_platform/research/strategy_engine/ase00_adapter.py:178: in run
    records, current_snapshot, previous_snapshot, event_snapshot = self._features(
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 

self = <ai_platform.research.strategy_engine.ase00_adapter.Ase00ShadowEngine object at 0x7fc9792e3170>
normalized = NormalizedEvents(events=(AcceptedSyntheticEvent(event_id='6e0e17a2b1d6dd1d9432e835a41c1b654f7a299b6f3099fee0c46b57e8dd...'notional': 250000.0})), reason_codes=(), data_hash='f293bc6e6c91b4ae02836068fb985ed135a0d35903b2264dbdfb0242be3bbf8b')
strategy = StrategyDefinition(schema_version='1.0.0', strategy_id='ase00-synthetic', version='1.0.0', universe=StrategyUniverse(s...='strategy:ase00-synthetic', lineage=(), details={'lineage_complete': True, 'future_shift': 0, 'research_mode': True}))
decision_time = datetime.datetime(2026, 7, 28, 4, 55, 2, 100000, tzinfo=datetime.timezone.utc)
config_hash = '1733266a431e538411c029e88b64723913f930717e09f0af098c595f181af677'

    def _features(
        self,
        normalized: NormalizedEvents,
        strategy: StrategyDefinition,
        decision_time: datetime,
        config_hash: str,
    ) -> tuple[
        tuple[FeatureRecord, ...],
        dict[str, JsonValue | Mapping[str, JsonValue]],
        dict[str, JsonValue | Mapping[str, JsonValue]],
        dict[str, JsonValue],
    ]:
        market_events = tuple(event for event in normalized.events if event.kind == "market_bar")
        frame = self._market_frame(market_events)
        latest_event = market_events[-1]
        records: list[FeatureRecord] = []
        current_snapshot: dict[str, JsonValue | Mapping[str, JsonValue]] = {}
        previous_snapshot: dict[str, JsonValue | Mapping[str, JsonValue]] = {}
    
        configured = {feature.id: feature for feature in strategy.features}
        squeeze_ref = configured.get("squeeze_ratio.v1")
        if squeeze_ref is not None:
            squeeze = squeeze_features(frame, **squeeze_ref.params)
            value = _row_mapping(
                squeeze,
                -1,
                (
                    "squeeze_ratio",
                    "squeeze_state",
                    "squeeze_duration",
                    "bars_since_release",
                    "linreg_momentum",
                    "momentum_slope",
                    "momentum_acceleration",
                ),
            )
>           record = make_feature_record(
                registry=self.registry,
                feature_id=squeeze_ref.id,
                symbol=latest_event.symbol,
                timeframe=squeeze_ref.timeframe,
                event_time=latest_event.event_time,
                detected_at=latest_event.detected_at,
                available_at=latest_event.available_at,
                value=value,
                is_confirmed=latest_event.is_confirmed,
                source=latest_event.source,
                data_version=normalized.data_hash,
                code_version=self.code_hash,
                configuration_hash=config_hash,
                source_event_id=latest_event.event_id,
                parameters=dict(squeeze_ref.params),
            )
E           TypeError: make_feature_record() got an unexpected keyword argument 'registry'

ai_platform/research/strategy_engine/ase00_adapter.py:401: TypeError
________________ test_existing_risk_core_rejection_is_preserved ________________

    def test_existing_risk_core_rejection_is_preserved() -> None:
>       evidence = _engine().run(
            events=_events(),
            strategy_document=_strategy(),
            decision_time=_decision_time(),
            risk_limits=_limits(),
            risk_snapshot=_snapshot(intent_notional="1001"),
        )

tests/ai_platform_integration/test_ase00_vertical_slice.py:381: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 
ai_platform/research/strategy_engine/ase00_adapter.py:178: in run
    records, current_snapshot, previous_snapshot, event_snapshot = self._features(
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 

self = <ai_platform.research.strategy_engine.ase00_adapter.Ase00ShadowEngine object at 0x7fc97942e1e0>
normalized = NormalizedEvents(events=(AcceptedSyntheticEvent(event_id='6e0e17a2b1d6dd1d9432e835a41c1b654f7a299b6f3099fee0c46b57e8dd...'notional': 250000.0})), reason_codes=(), data_hash='f293bc6e6c91b4ae02836068fb985ed135a0d35903b2264dbdfb0242be3bbf8b')
strategy = StrategyDefinition(schema_version='1.0.0', strategy_id='ase00-synthetic', version='1.0.0', universe=StrategyUniverse(s...='strategy:ase00-synthetic', lineage=(), details={'lineage_complete': True, 'future_shift': 0, 'research_mode': True}))
decision_time = datetime.datetime(2026, 7, 28, 4, 55, 2, 100000, tzinfo=datetime.timezone.utc)
config_hash = '1733266a431e538411c029e88b64723913f930717e09f0af098c595f181af677'

    def _features(
        self,
        normalized: NormalizedEvents,
        strategy: StrategyDefinition,
        decision_time: datetime,
        config_hash: str,
    ) -> tuple[
        tuple[FeatureRecord, ...],
        dict[str, JsonValue | Mapping[str, JsonValue]],
        dict[str, JsonValue | Mapping[str, JsonValue]],
        dict[str, JsonValue],
    ]:
        market_events = tuple(event for event in normalized.events if event.kind == "market_bar")
        frame = self._market_frame(market_events)
        latest_event = market_events[-1]
        records: list[FeatureRecord] = []
        current_snapshot: dict[str, JsonValue | Mapping[str, JsonValue]] = {}
        previous_snapshot: dict[str, JsonValue | Mapping[str, JsonValue]] = {}
    
        configured = {feature.id: feature for feature in strategy.features}
        squeeze_ref = configured.get("squeeze_ratio.v1")
        if squeeze_ref is not None:
            squeeze = squeeze_features(frame, **squeeze_ref.params)
            value = _row_mapping(
                squeeze,
                -1,
                (
                    "squeeze_ratio",
                    "squeeze_state",
                    "squeeze_duration",
                    "bars_since_release",
                    "linreg_momentum",
                    "momentum_slope",
                    "momentum_acceleration",
                ),
            )
>           record = make_feature_record(
                registry=self.registry,
                feature_id=squeeze_ref.id,
                symbol=latest_event.symbol,
                timeframe=squeeze_ref.timeframe,
                event_time=latest_event.event_time,
                detected_at=latest_event.detected_at,
                available_at=latest_event.available_at,
                value=value,
                is_confirmed=latest_event.is_confirmed,
                source=latest_event.source,
                data_version=normalized.data_hash,
                code_version=self.code_hash,
                configuration_hash=config_hash,
                source_event_id=latest_event.event_id,
                parameters=dict(squeeze_ref.params),
            )
E           TypeError: make_feature_record() got an unexpected keyword argument 'registry'

ai_platform/research/strategy_engine/ase00_adapter.py:401: TypeError
_____________ test_restart_and_replay_produces_identical_evidence ______________

tmp_path = PosixPath('/tmp/pytest-of-runner/pytest-0/test_restart_and_replay_produc0')

    def test_restart_and_replay_produces_identical_evidence(tmp_path: Path) -> None:
        path = tmp_path / "shadow-evidence.json"
>       first = _engine().run(
            events=_events(),
            strategy_document=_strategy(),
            decision_time=_decision_time(),
            risk_limits=_limits(),
            risk_snapshot=_snapshot(),
            evidence_path=path,
        )

tests/ai_platform_integration/test_ase00_vertical_slice.py:396: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 
ai_platform/research/strategy_engine/ase00_adapter.py:178: in run
    records, current_snapshot, previous_snapshot, event_snapshot = self._features(
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 

self = <ai_platform.research.strategy_engine.ase00_adapter.Ase00ShadowEngine object at 0x7fc97930c830>
normalized = NormalizedEvents(events=(AcceptedSyntheticEvent(event_id='6e0e17a2b1d6dd1d9432e835a41c1b654f7a299b6f3099fee0c46b57e8dd...'notional': 250000.0})), reason_codes=(), data_hash='f293bc6e6c91b4ae02836068fb985ed135a0d35903b2264dbdfb0242be3bbf8b')
strategy = StrategyDefinition(schema_version='1.0.0', strategy_id='ase00-synthetic', version='1.0.0', universe=StrategyUniverse(s...='strategy:ase00-synthetic', lineage=(), details={'lineage_complete': True, 'future_shift': 0, 'research_mode': True}))
decision_time = datetime.datetime(2026, 7, 28, 4, 55, 2, 100000, tzinfo=datetime.timezone.utc)
config_hash = '1733266a431e538411c029e88b64723913f930717e09f0af098c595f181af677'

    def _features(
        self,
        normalized: NormalizedEvents,
        strategy: StrategyDefinition,
        decision_time: datetime,
        config_hash: str,
    ) -> tuple[
        tuple[FeatureRecord, ...],
        dict[str, JsonValue | Mapping[str, JsonValue]],
        dict[str, JsonValue | Mapping[str, JsonValue]],
        dict[str, JsonValue],
    ]:
        market_events = tuple(event for event in normalized.events if event.kind == "market_bar")
        frame = self._market_frame(market_events)
        latest_event = market_events[-1]
        records: list[FeatureRecord] = []
        current_snapshot: dict[str, JsonValue | Mapping[str, JsonValue]] = {}
        previous_snapshot: dict[str, JsonValue | Mapping[str, JsonValue]] = {}
    
        configured = {feature.id: feature for feature in strategy.features}
        squeeze_ref = configured.get("squeeze_ratio.v1")
        if squeeze_ref is not None:
            squeeze = squeeze_features(frame, **squeeze_ref.params)
            value = _row_mapping(
                squeeze,
                -1,
                (
                    "squeeze_ratio",
                    "squeeze_state",
                    "squeeze_duration",
                    "bars_since_release",
                    "linreg_momentum",
                    "momentum_slope",
                    "momentum_acceleration",
                ),
            )
>           record = make_feature_record(
                registry=self.registry,
                feature_id=squeeze_ref.id,
                symbol=latest_event.symbol,
                timeframe=squeeze_ref.timeframe,
                event_time=latest_event.event_time,
                detected_at=latest_event.detected_at,
                available_at=latest_event.available_at,
                value=value,
                is_confirmed=latest_event.is_confirmed,
                source=latest_event.source,
                data_version=normalized.data_hash,
                code_version=self.code_hash,
                configuration_hash=config_hash,
                source_event_id=latest_event.event_id,
                parameters=dict(squeeze_ref.params),
            )
E           TypeError: make_feature_record() got an unexpected keyword argument 'registry'

ai_platform/research/strategy_engine/ase00_adapter.py:401: TypeError
=============================== warnings summary ===============================
ai_strategy_engine/.venv/lib/python3.12/site-packages/_pytest/config/__init__.py:1464
  /home/runner/work/freqtrade/freqtrade/ai_strategy_engine/.venv/lib/python3.12/site-packages/_pytest/config/__init__.py:1464: PytestConfigWarning: Unknown config option: asyncio_default_fixture_loop_scope
  
    self._warn_or_fail_if_strict(f"Unknown config option: {key}\n")

ai_strategy_engine/.venv/lib/python3.12/site-packages/_pytest/config/__init__.py:1464
  /home/runner/work/freqtrade/freqtrade/ai_strategy_engine/.venv/lib/python3.12/site-packages/_pytest/config/__init__.py:1464: PytestConfigWarning: Unknown config option: asyncio_mode
  
    self._warn_or_fail_if_strict(f"Unknown config option: {key}\n")

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
=========================== short test summary info ============================
FAILED tests/ai_platform_integration/test_ase00_vertical_slice.py::test_complete_synthetic_shadow_flow_uses_existing_risk_core - TypeError: make_feature_record() got an unexpected keyword argument 'registry'
FAILED tests/ai_platform_integration/test_ase00_vertical_slice.py::test_duplicate_event_is_idempotent - TypeError: make_feature_record() got an unexpected keyword argument 'registry'
FAILED tests/ai_platform_integration/test_ase00_vertical_slice.py::test_delayed_event_is_accepted_when_available_before_decision - TypeError: make_feature_record() got an unexpected keyword argument 'registry'
FAILED tests/ai_platform_integration/test_ase00_vertical_slice.py::test_out_of_order_event_input_is_normalized - TypeError: make_feature_record() got an unexpected keyword argument 'registry'
FAILED tests/ai_platform_integration/test_ase00_vertical_slice.py::test_future_feature_is_rejected_fail_closed - TypeError: make_feature_record() got an unexpected keyword argument 'registry'
FAILED tests/ai_platform_integration/test_ase00_vertical_slice.py::test_unconfirmed_pivot_is_rejected - TypeError: make_feature_record() got an unexpected keyword argument 'registry'
FAILED tests/ai_platform_integration/test_ase00_vertical_slice.py::test_existing_risk_core_rejection_is_preserved - TypeError: make_feature_record() got an unexpected keyword argument 'registry'
FAILED tests/ai_platform_integration/test_ase00_vertical_slice.py::test_restart_and_replay_produces_identical_evidence - TypeError: make_feature_record() got an unexpected keyword argument 'registry'
=================== 8 failed, 4 passed, 2 warnings in 1.85s ====================

```
