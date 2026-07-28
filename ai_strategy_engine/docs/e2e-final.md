# ASE-00 E2E current diagnostic

- exit code: `1`

```text
============================= test session starts ==============================
platform linux -- Python 3.12.13, pytest-9.1.1, pluggy-1.6.0 -- /home/runner/work/freqtrade/freqtrade/ai_strategy_engine/.venv/bin/python
cachedir: .pytest_cache
rootdir: /home/runner/work/freqtrade/freqtrade
configfile: pyproject.toml
plugins: cov-7.1.0, anyio-4.14.2
collecting ... collected 12 items

tests/ai_platform_integration/test_ase00_vertical_slice.py::test_complete_synthetic_shadow_flow_uses_existing_risk_core PASSED [  8%]
tests/ai_platform_integration/test_ase00_vertical_slice.py::test_duplicate_event_is_idempotent PASSED [ 16%]
tests/ai_platform_integration/test_ase00_vertical_slice.py::test_delayed_event_is_accepted_when_available_before_decision PASSED [ 25%]
tests/ai_platform_integration/test_ase00_vertical_slice.py::test_out_of_order_event_input_is_normalized PASSED [ 33%]
tests/ai_platform_integration/test_ase00_vertical_slice.py::test_future_feature_is_rejected_fail_closed PASSED [ 41%]
tests/ai_platform_integration/test_ase00_vertical_slice.py::test_unconfirmed_pivot_is_rejected PASSED [ 50%]
tests/ai_platform_integration/test_ase00_vertical_slice.py::test_unconfirmed_htf_record_is_rejected PASSED [ 58%]
tests/ai_platform_integration/test_ase00_vertical_slice.py::test_existing_risk_core_rejection_is_preserved PASSED [ 66%]
tests/ai_platform_integration/test_ase00_vertical_slice.py::test_restart_and_replay_produces_identical_evidence PASSED [ 75%]
tests/ai_platform_integration/test_ase00_vertical_slice.py::test_missing_liquidation_data_fails_closed PASSED [ 83%]
tests/ai_platform_integration/test_ase00_vertical_slice.py::test_conflicting_duplicate_fails_closed_with_reason_code PASSED [ 91%]
tests/ai_platform_integration/test_ase00_vertical_slice.py::test_adapter_has_no_execution_or_freqtrade_dependency FAILED [100%]

=================================== FAILURES ===================================
____________ test_adapter_has_no_execution_or_freqtrade_dependency _____________

    def test_adapter_has_no_execution_or_freqtrade_dependency() -> None:
        source = inspect.getsource(ase00_adapter)
        assert "ai_platform.portal.execution" not in source
>       assert "ExecutionAdapter" not in source
E       assert 'ExecutionAdapter' not in 'from __future__ import annotations\n\nimport math\nimport os\nfrom collections.abc import Mapping, Sequence\nfrom dataclasses import dataclass, replace\nfrom datetime import UTC, datetime, timedelta\nfrom pathlib import Path\nfrom typing import Literal, cast\n\nimport pandas as pd\nfrom pydantic import JsonValue\n\nfrom ai_platform.portal.contracts.risk import RiskDecisionOutcome\nfrom ai_platform.portal.risk.schema import RiskEvaluationSnapshot, RiskPolicyLimits\nfrom ai_platform.portal.risk.service import RiskService\nfrom strategy_engine.domain.models import (\n    Action,\n    FeatureRecord,\n    Provenance,\n    ShadowDecisionEvidence,\n    Side,\n    SignalEvent,\n    StrategyDefinition,\n    canonical_sha256,\n)\nfrom strategy_engine.dsl.evaluator import EvaluationSnapshot, StrategyEvaluator\nfrom strategy_engine.dsl.validator import StrategyValidationError, StrategyValidator\nfrom strategy_engine.features.pivots import PivotEvent, confirmed_pivots\nfrom strategy_engine.features.records import make_confirmed_pivot_record, make_feature_record\nfrom strategy_engine.features.squeeze import squeeze_features\nfrom strategy_engine.features.supertrend import supertrend_features\nfrom strategy_engine.registry import FeatureRegistry, SearchSpaceRegistry\nfrom strategy_engine.validation.leakage import (\n    LeakageContext,\n    LeakageError,\n    assert_features_available,\n)\n\n\nEventKind = Literal["market_bar", "liquidation"]\n\n\nclass Ase00Reason:\n    DUPLICATE_EVENT_IGNORED = "DUPLICATE_EVENT_IGNORED"\n    CONFLICTING_DUPLICATE_EVENT = "CONFLICTING_DUPLICATE_EVENT"\n    OUT_OF_ORDER_EVENT_NORMALIZED = "OUT_OF_ORDER_EVENT_NORMALIZED"\n    DELAYED_EVENT_ACCEPTED = "DELAYED_EVENT_ACCEPTED"\n    MISSING_REQUIRED_DATA = "MISSING_REQUIRED_DATA"\n    MARKET_BAR_INVALID = "MARKET_BAR_INVALID"\n    DUPLICATE_MARKET_TIMESTAMP = "DUPLICATE_MARKET_TIMESTAMP"\n    STRATEGY_REJECTED = "STRATEGY_REJECTED"\n    LEAKAGE_GUARD_REJECTED = "LEAKAGE_GUARD_REJECTED"\n    SHADOW_ONLY = "SHADOW_ONLY"\n\n\n@dataclass(frozen=True)\nclass AcceptedSyntheticEvent:\n    event_id: str\n    idempotency_key: str\n    kind: EventKind\n    symbol: str\n    timeframe: str\n    event_time: datetime\n    detected_at: datetime\n    available_at: datetime\n    source: str\n    is_confirmed: bool\n    source_data_version: str\n    payload: Mapping[str, JsonValue]\n\n    def __post_init__(self) -> None:\n        for name in ("event_id", "idempotency_key", "symbol", "timeframe", "source"):\n            if not getattr(self, name):\n                raise ValueError(f"{name} cannot be empty")\n        _require_utc(self.event_time, "event_time")\n        _require_utc(self.detected_at, "detected_at")\n        _require_utc(self.available_at, "available_at")\n        if self.detected_at < self.event_time:\n            raise ValueError("detected_at cannot precede event_time")\n        if self.available_at < self.detected_at:\n            raise ValueError("available_at cannot precede detected_at")\n        if len(self.source_data_version) != 64 or any(\n            char not in "0123456789abcdef" for char in self.source_data_version\n        ):\n            raise ValueError("source_data_version must be a lowercase SHA-256")\n\n    def canonical_payload(self) -> dict[str, JsonValue]:\n        return {\n            "event_id": self.event_id,\n            "idempotency_key": self.idempotency_key,\n            "kind": self.kind,\n            "symbol": self.symbol,\n            "timeframe": self.timeframe,\n            "event_time": self.event_time.isoformat(),\n            "detected_at": self.detected_at.isoformat(),\n            "available_at": self.available_at.isoformat(),\n            "source": self.source,\n            "is_confirmed": self.is_confirmed,\n            "source_data_version": self.source_data_version,\n            "payload": dict(self.payload),\n        }\n\n\n@dataclass(frozen=True)\nclass NormalizedEvents:\n    events: tuple[AcceptedSyntheticEvent, ...]\n    reason_codes: tuple[str, ...]\n    data_hash: str\n\n\nclass Ase00FailClosed(RuntimeError):\n    def __init__(self, reason_code: str, message: str) -> None:\n        super().__init__(message)\n        self.reason_code = reason_code\n\n\nclass Ase00ShadowEngine:\n    """Synthetic ASE-00 vertical slice.\n\n    The class intentionally imports only Portal Risk Core models/service. It does not import or\n    construct an ExecutionAdapter and never creates an execution intent or order.\n    """\n\n    def __init__(\n        self,\n        *,\n        code_hash: str,\n        repository_root: Path | None = None,\n        processing_delay_threshold: timedelta = timedelta(seconds=1),\n    ) -> None:\n        _require_sha256(code_hash, "code_hash")\n        if processing_delay_threshold < timedelta(0):\n            raise ValueError("processing_delay_threshold cannot be negative")\n        self.code_hash = code_hash\n        self.processing_delay_threshold = processing_delay_threshold\n        self.repository_root = repository_root or Path(__file__).resolve().parents[3]\n        strategy_root = self.repository_root / "ai_strategy_engine"\n        self.registry = FeatureRegistry.load(strategy_root / "configs/feature_registry.v1.yaml")\n        self.search_spaces = SearchSpaceRegistry.load(\n            strategy_root / "configs/search_spaces.v1.yaml"\n        )\n        self.validator = StrategyValidator(self.registry, self.search_spaces)\n        self.evaluator = StrategyEvaluator()\n\n    def run(\n        self,\n        *,\n        events: Sequence[AcceptedSyntheticEvent],\n        strategy_document: Mapping[str, object],\n        decision_time: datetime,\n        risk_limits: RiskPolicyLimits,\n        risk_snapshot: RiskEvaluationSnapshot,\n        evidence_path: Path | None = None,\n        generated_by_ai: bool = False,\n        final_holdout_reused: bool = False,\n    ) -> ShadowDecisionEvidence:\n        _require_utc(decision_time, "decision_time")\n        raw_data_hash = canonical_sha256([event.canonical_payload() for event in events])\n        strategy_id = _document_string(strategy_document, "strategy_id", "unknown-strategy")\n        strategy_version = _document_string(strategy_document, "version", "0.0.0")\n        symbol = events[0].symbol if events else "UNKNOWN"\n        timeframe = events[0].timeframe if events else "UNKNOWN"\n\n        try:\n            strategy = self.validator.validate(\n                strategy_document,\n                generated_by_ai=generated_by_ai,\n            )\n            normalized = self._normalize_events(events)\n            symbol, timeframe = self._require_single_market(normalized.events)\n            config_hash = canonical_sha256(\n                {\n                    "strategy": strategy.model_dump(mode="json"),\n                    "feature_registry_version": self.registry.version,\n                    "search_space_version": self.search_spaces.version,\n                }\n            )\n            records, current_snapshot, previous_snapshot, event_snapshot = self._features(\n                normalized,\n                strategy,\n                decision_time,\n                config_hash,\n            )\n            assert_features_available(\n                records,\n                decision_time,\n                context=LeakageContext(\n                    decision_time=decision_time,\n                    expected_data_version=normalized.data_hash,\n                    expected_code_version=self.code_hash,\n                    expected_configuration_hash=config_hash,\n                    final_holdout_reused=final_holdout_reused,\n                ),\n            )\n            dsl_decision = self.evaluator.evaluate(\n                strategy,\n                EvaluationSnapshot(\n                    features=current_snapshot,\n                    previous_features=previous_snapshot,\n                    events=event_snapshot,\n                    risk={},\n                ),\n            )\n            signal = self._signal(\n                strategy=strategy,\n                decision_time=decision_time,\n                records=records,\n                dsl_side=dsl_decision.side,\n                dsl_action=dsl_decision.action,\n                dsl_reason_codes=dsl_decision.reason_codes,\n                data_hash=normalized.data_hash,\n                config_hash=config_hash,\n            )\n            risk_outcome, risk_reason_codes = self._risk_decision(\n                signal=signal,\n                risk_limits=risk_limits,\n                risk_snapshot=risk_snapshot,\n            )\n            reason_codes = _unique_codes(\n                (\n                    *normalized.reason_codes,\n                    *dsl_decision.reason_codes,\n                    *risk_reason_codes,\n                    Ase00Reason.SHADOW_ONLY,\n                )\n            )\n            evidence = self._evidence(\n                decision_time=decision_time,\n                symbol=symbol,\n                timeframe=timeframe,\n                strategy=strategy,\n                records=records,\n                signal=signal,\n                risk_outcome=risk_outcome,\n                reason_codes=reason_codes,\n                data_hash=normalized.data_hash,\n                config_hash=config_hash,\n            )\n        except StrategyValidationError as exc:\n            evidence = self._rejected_evidence(\n                decision_time=decision_time,\n                symbol=symbol,\n                timeframe=timeframe,\n                strategy_id=strategy_id,\n                strategy_version=strategy_version,\n                data_hash=raw_data_hash,\n                config_hash=_safe_config_hash(strategy_document),\n                reason_codes=(Ase00Reason.STRATEGY_REJECTED, exc.reason_code),\n            )\n        except LeakageError as exc:\n            evidence = self._rejected_evidence(\n                decision_time=decision_time,\n                symbol=symbol,\n                timeframe=timeframe,\n                strategy_id=strategy_id,\n                strategy_version=strategy_version,\n                data_hash=raw_data_hash,\n                config_hash=_safe_config_hash(strategy_document),\n                reason_codes=(Ase00Reason.LEAKAGE_GUARD_REJECTED, exc.reason_code.value),\n            )\n        except Ase00FailClosed as exc:\n            evidence = self._rejected_evidence(\n                decision_time=decision_time,\n                symbol=symbol,\n                timeframe=timeframe,\n                strategy_id=strategy_id,\n                strategy_version=strategy_version,\n                data_hash=raw_data_hash,\n                config_hash=_safe_config_hash(strategy_document),\n                reason_codes=(exc.reason_code, Ase00Reason.SHADOW_ONLY),\n            )\n\n        if evidence_path is not None:\n            self.persist_evidence(evidence_path, evidence)\n        return evidence\n\n    def persist_evidence(self, path: Path, evidence: ShadowDecisionEvidence) -> None:\n        path.parent.mkdir(parents=True, exist_ok=True)\n        encoded = evidence.canonical_json() + "\\n"\n        if path.exists():\n            existing = path.read_text(encoding="utf-8")\n            if existing == encoded:\n                return\n            try:\n                existing_evidence = ShadowDecisionEvidence.model_validate_json(existing)\n            except ValueError as exc:\n                raise Ase00FailClosed(\n                    "EVIDENCE_CONFLICT", "existing evidence is not a valid ASE record"\n                ) from exc\n            if existing_evidence.idempotency_key == evidence.idempotency_key:\n                raise Ase00FailClosed(\n                    "EVIDENCE_CONFLICT", "same idempotency key maps to different evidence"\n                )\n        temporary = path.with_name(f".{path.name}.{os.getpid()}.tmp")\n        temporary.write_text(encoded, encoding="utf-8")\n        temporary.replace(path)\n\n    def _normalize_events(self, events: Sequence[AcceptedSyntheticEvent]) -> NormalizedEvents:\n        if not events:\n            raise Ase00FailClosed(\n                Ase00Reason.MISSING_REQUIRED_DATA,\n                "synthetic flow requires market and liquidation events",\n            )\n        raw_order = [self._event_sort_key(event) for event in events]\n        out_of_order = raw_order != sorted(raw_order)\n        by_idempotency_key: dict[str, AcceptedSyntheticEvent] = {}\n        event_hashes: dict[str, str] = {}\n        duplicate_count = 0\n        delayed_count = 0\n        for event in events:\n            event_hash = canonical_sha256(event.canonical_payload())\n            prior_hash = event_hashes.get(event.idempotency_key)\n            if prior_hash is not None:\n                if prior_hash != event_hash:\n                    raise Ase00FailClosed(\n                        Ase00Reason.CONFLICTING_DUPLICATE_EVENT,\n                        f"conflicting duplicate event: {event.idempotency_key}",\n                    )\n                duplicate_count += 1\n                continue\n            event_hashes[event.idempotency_key] = event_hash\n            by_idempotency_key[event.idempotency_key] = event\n            if event.available_at - event.detected_at > self.processing_delay_threshold:\n                delayed_count += 1\n        normalized = tuple(sorted(by_idempotency_key.values(), key=self._event_sort_key))\n        reason_codes: list[str] = []\n        if duplicate_count:\n            reason_codes.append(Ase00Reason.DUPLICATE_EVENT_IGNORED)\n        if out_of_order:\n            reason_codes.append(Ase00Reason.OUT_OF_ORDER_EVENT_NORMALIZED)\n        if delayed_count:\n            reason_codes.append(Ase00Reason.DELAYED_EVENT_ACCEPTED)\n        data_hash = canonical_sha256([event.canonical_payload() for event in normalized])\n        return NormalizedEvents(normalized, tuple(reason_codes), data_hash)\n\n    @staticmethod\n    def _event_sort_key(event: AcceptedSyntheticEvent) -> tuple[datetime, datetime, datetime, str]:\n        return (\n            event.event_time,\n            event.detected_at,\n            event.available_at,\n            event.idempotency_key,\n        )\n\n    @staticmethod\n    def _require_single_market(\n        events: tuple[AcceptedSyntheticEvent, ...],\n    ) -> tuple[str, str]:\n        market = [event for event in events if event.kind == "market_bar"]\n        liquidations = [event for event in events if event.kind == "liquidation"]\n        if not market or not liquidations:\n            raise Ase00FailClosed(\n                Ase00Reason.MISSING_REQUIRED_DATA,\n                "both accepted market bars and liquidation events are required",\n            )\n        symbols = {event.symbol for event in events}\n        timeframes = {event.timeframe for event in market}\n        if len(symbols) != 1 or len(timeframes) != 1:\n            raise Ase00FailClosed(\n                Ase00Reason.MARKET_BAR_INVALID,\n                "ASE-00 requires one symbol and one market timeframe",\n            )\n        return next(iter(symbols)), next(iter(timeframes))\n\n    def _features(\n        self,\n        normalized: NormalizedEvents,\n        strategy: StrategyDefinition,\n        decision_time: datetime,\n        config_hash: str,\n    ) -> tuple[\n        tuple[FeatureRecord, ...],\n        dict[str, JsonValue | Mapping[str, JsonValue]],\n        dict[str, JsonValue | Mapping[str, JsonValue]],\n        dict[str, JsonValue],\n    ]:\n        market_events = tuple(event for event in normalized.events if event.kind == "market_bar")\n        liquidation_events = tuple(\n            event for event in normalized.events if event.kind == "liquidation"\n        )\n        frame = self._market_frame(market_events)\n        if len(frame) < 25:\n            raise Ase00FailClosed(\n                Ase00Reason.MISSING_REQUIRED_DATA,\n                "at least 25 closed synthetic bars are required",\n            )\n        symbol = market_events[0].symbol\n        timeframe = market_events[0].timeframe\n        latest_market = market_events[-1]\n        feature_parameters = {feature.id: dict(feature.params) for feature in strategy.features}\n\n        squeeze_params = self.registry.validate_parameters(\n            "squeeze_ratio.v1", feature_parameters.get("squeeze_ratio.v1", {})\n        )\n        squeeze_frame = squeeze_features(frame, **cast(dict[str, object], squeeze_params))\n        squeeze_current = self._require_finite_row(\n            squeeze_frame,\n            -1,\n            ("squeeze_ratio", "linreg_momentum", "momentum_slope"),\n            "squeeze",\n        )\n        squeeze_previous = self._require_finite_row(\n            squeeze_frame,\n            -2,\n            ("squeeze_ratio", "linreg_momentum", "momentum_slope"),\n            "squeeze previous",\n        )\n        squeeze_value: dict[str, JsonValue] = {\n            **squeeze_current,\n            "squeeze_on": bool(squeeze_frame["squeeze_on"].iloc[-1]),\n            "squeeze_release": bool(squeeze_frame["squeeze_release"].iloc[-1]),\n        }\n        squeeze_record = make_feature_record(\n            feature_id="squeeze_ratio.v1",\n            symbol=symbol,\n            timeframe=timeframe,\n            event_time=latest_market.event_time,\n            detected_at=latest_market.detected_at,\n            available_at=latest_market.available_at,\n            value=squeeze_value,\n            source="ase00-clean-room-squeeze",\n            is_confirmed=latest_market.is_confirmed,\n            idempotency_key=canonical_sha256(\n                {"feature": "squeeze_ratio.v1", "source": latest_market.idempotency_key}\n            ),\n            code_version=self.code_hash,\n            data_version=normalized.data_hash,\n            configuration_hash=config_hash,\n            producer="ase00-shadow-engine",\n            source_event_id=latest_market.event_id,\n            parameters=cast(dict[str, JsonValue], squeeze_params),\n        )\n\n        supertrend_params = self.registry.validate_parameters(\n            "supertrend_direction.v1",\n            feature_parameters.get("supertrend_direction.v1", {}),\n        )\n        supertrend_frame = supertrend_features(\n            frame,\n            **cast(dict[str, object], supertrend_params),\n        )\n        direction = int(supertrend_frame["supertrend_direction"].iloc[-1])\n        previous_direction = int(supertrend_frame["supertrend_direction"].iloc[-2])\n        band = _finite_float(supertrend_frame["supertrend_band"].iloc[-1], "supertrend band")\n        supertrend_value: dict[str, JsonValue] = {\n            "value": direction,\n            "direction": direction,\n            "band": band,\n            "flip": bool(supertrend_frame["supertrend_flip"].iloc[-1]),\n        }\n        supertrend_record = make_feature_record(\n            feature_id="supertrend_direction.v1",\n            symbol=symbol,\n            timeframe=timeframe,\n            event_time=latest_market.event_time,\n            detected_at=latest_market.detected_at,\n            available_at=latest_market.available_at,\n            value=supertrend_value,\n            source="ase00-clean-room-supertrend",\n            is_confirmed=latest_market.is_confirmed,\n            idempotency_key=canonical_sha256(\n                {"feature": "supertrend_direction.v1", "source": latest_market.idempotency_key}\n            ),\n            code_version=self.code_hash,\n            data_version=normalized.data_hash,\n            configuration_hash=config_hash,\n            producer="ase00-shadow-engine",\n            source_event_id=latest_market.event_id,\n            parameters=cast(dict[str, JsonValue], supertrend_params),\n            provenance_details={"closed_bar": latest_market.is_confirmed},\n        )\n\n        pivot_params = self.registry.validate_parameters(\n            "confirmed_pivot.v1",\n            feature_parameters.get("confirmed_pivot.v1", {"left_bars": 2, "right_bars": 2}),\n        )\n        pivots = confirmed_pivots(\n            frame,\n            left_bars=int(cast(int, pivot_params["left_bars"])),\n            right_bars=int(cast(int, pivot_params["right_bars"])),\n        )\n        if not pivots:\n            raise Ase00FailClosed(\n                Ase00Reason.MISSING_REQUIRED_DATA,\n                "no confirmed synthetic pivot is available",\n            )\n        event_by_time = {event.event_time: event for event in market_events}\n        available_pivots: list[PivotEvent] = []\n        for pivot in pivots:\n            detected_event = event_by_time.get(pivot.detected_at.to_pydatetime())\n            if detected_event is None:\n                continue\n            available_pivots.append(replace(pivot, available_at=detected_event.available_at))\n        if not available_pivots:\n            raise Ase00FailClosed(\n                Ase00Reason.MISSING_REQUIRED_DATA,\n                "pivot detection event is missing",\n            )\n        latest_pivot = available_pivots[-1]\n        pivot_detected_event = event_by_time[latest_pivot.detected_at.to_pydatetime()]\n        pivot_record = make_confirmed_pivot_record(\n            pivot=latest_pivot,\n            symbol=symbol,\n            timeframe=timeframe,\n            decision_time=decision_time,\n            idempotency_key=canonical_sha256(\n                {\n                    "feature": "confirmed_pivot.v1",\n                    "source": pivot_detected_event.idempotency_key,\n                    "pivot_index": latest_pivot.pivot_index,\n                }\n            ),\n            code_version=self.code_hash,\n            data_version=normalized.data_hash,\n            configuration_hash=config_hash,\n            producer="ase00-shadow-engine",\n            source_event_id=pivot_detected_event.event_id,\n            parameters=cast(dict[str, JsonValue], pivot_params),\n            detection_event_confirmed=pivot_detected_event.is_confirmed,\n        )\n\n        latest_liquidation = liquidation_events[-1]\n        notional_z = _payload_number(latest_liquidation.payload, "notional_z")\n        liquidation_record = make_feature_record(\n            feature_id="liquidation_notional_z.v1",\n            symbol=symbol,\n            timeframe=latest_liquidation.timeframe,\n            event_time=latest_liquidation.event_time,\n            detected_at=latest_liquidation.detected_at,\n            available_at=latest_liquidation.available_at,\n            value={"value": notional_z, "notional_z": notional_z},\n            source="accepted-synthetic-liquidation",\n            is_confirmed=latest_liquidation.is_confirmed,\n            idempotency_key=canonical_sha256(\n                {\n                    "feature": "liquidation_notional_z.v1",\n                    "source": latest_liquidation.idempotency_key,\n                }\n            ),\n            code_version=self.code_hash,\n            data_version=normalized.data_hash,\n            configuration_hash=config_hash,\n            producer="ase00-shadow-engine",\n            source_event_id=latest_liquidation.event_id,\n            parameters={},\n        )\n\n        records = (\n            squeeze_record,\n            supertrend_record,\n            pivot_record,\n            liquidation_record,\n        )\n        current: dict[str, JsonValue | Mapping[str, JsonValue]] = {\n            "squeeze_ratio.v1": squeeze_value,\n            "supertrend_direction.v1": supertrend_value,\n            "confirmed_pivot.v1": cast(Mapping[str, JsonValue], pivot_record.value),\n            "liquidation_notional_z.v1": cast(Mapping[str, JsonValue], liquidation_record.value),\n        }\n        previous: dict[str, JsonValue | Mapping[str, JsonValue]] = {\n            "squeeze_ratio.v1": squeeze_previous,\n            "supertrend_direction.v1": {\n                "value": previous_direction,\n                "direction": previous_direction,\n            },\n        }\n        event_snapshot: dict[str, JsonValue] = {\n            "squeeze_release": "up" if squeeze_value["squeeze_release"] else "none",\n            "supertrend_flip": (\n                "up"\n                if supertrend_value["flip"] and direction == 1\n                else "down"\n                if supertrend_value["flip"] and direction == -1\n                else "none"\n            ),\n            "pivot_confirmed": pivot_record.is_confirmed,\n        }\n        return records, current, previous, event_snapshot\n\n    @staticmethod\n    def _market_frame(events: tuple[AcceptedSyntheticEvent, ...]) -> pd.DataFrame:\n        rows: list[dict[str, float]] = []\n        index: list[datetime] = []\n        observed_times: set[datetime] = set()\n        for event in events:\n            if event.event_time in observed_times:\n                raise Ase00FailClosed(\n                    Ase00Reason.DUPLICATE_MARKET_TIMESTAMP,\n                    f"multiple market bars at {event.event_time.isoformat()}",\n                )\n            observed_times.add(event.event_time)\n            row = {\n                key: _payload_number(event.payload, key)\n                for key in ("open", "high", "low", "close", "volume")\n            }\n            if row["low"] > min(row["open"], row["close"], row["high"]):\n                raise Ase00FailClosed(\n                    Ase00Reason.MARKET_BAR_INVALID, "low exceeds an OHLC component"\n                )\n            if row["high"] < max(row["open"], row["close"], row["low"]):\n                raise Ase00FailClosed(\n                    Ase00Reason.MARKET_BAR_INVALID, "high is below an OHLC component"\n                )\n            if row["volume"] < 0:\n                raise Ase00FailClosed(Ase00Reason.MARKET_BAR_INVALID, "volume cannot be negative")\n            rows.append(row)\n            index.append(event.event_time)\n        frame = pd.DataFrame(rows, index=pd.DatetimeIndex(index))\n        return frame.sort_index()\n\n    @staticmethod\n    def _require_finite_row(\n        frame: pd.DataFrame,\n        position: int,\n        columns: tuple[str, ...],\n        label: str,\n    ) -> dict[str, JsonValue]:\n        result: dict[str, JsonValue] = {}\n        for column in columns:\n            result[column] = _finite_float(frame[column].iloc[position], f"{label}.{column}")\n        return result\n\n    def _signal(\n        self,\n        *,\n        strategy: StrategyDefinition,\n        decision_time: datetime,\n        records: tuple[FeatureRecord, ...],\n        dsl_side: Side,\n        dsl_action: Action,\n        dsl_reason_codes: tuple[str, ...],\n        data_hash: str,\n        config_hash: str,\n    ) -> SignalEvent | None:\n        if dsl_action is not Action.ENTER or dsl_side is Side.FLAT:\n            return None\n        latest_event_time = max(record.event_time for record in records)\n        latest_detected_at = max(record.detected_at for record in records)\n        latest_available_at = max(record.available_at for record in records)\n        feature_snapshot: dict[str, JsonValue] = {\n            record.feature_id: record.value for record in records\n        }\n        idempotency_key = canonical_sha256(\n            {\n                "strategy": strategy.strategy_id,\n                "version": strategy.version,\n                "decision_time": decision_time.isoformat(),\n                "feature_ids": [record.idempotency_key for record in records],\n            }\n        )\n        return SignalEvent(\n            signal_id=idempotency_key,\n            signal_version="1",\n            strategy_id=strategy.strategy_id,\n            strategy_version=strategy.version,\n            symbol=records[0].symbol,\n            timeframe=records[0].timeframe,\n            side=dsl_side,\n            action=dsl_action,\n            event_time=latest_event_time,\n            detected_at=latest_detected_at,\n            available_at=latest_available_at,\n            expires_at=None,\n            source="ase00-shadow-engine",\n            is_confirmed=all(record.is_confirmed for record in records),\n            idempotency_key=idempotency_key,\n            code_version=self.code_hash,\n            data_version=data_hash,\n            configuration_hash=config_hash,\n            confidence=None,\n            reason_codes=dsl_reason_codes,\n            feature_snapshot=feature_snapshot,\n            provenance=Provenance(\n                producer="ase00-shadow-engine",\n                source_event_id=idempotency_key,\n                lineage=tuple(record.idempotency_key for record in records),\n                details={\n                    "lineage_complete": True,\n                    "future_shift": 0,\n                    "shadow_only": True,\n                },\n            ),\n            execution_policy={\n                "use_closed_bar": True,\n                "shadow_only": True,\n                "order_submission_allowed": False,\n            },\n        )\n\n    @staticmethod\n    def _risk_decision(\n        *,\n        signal: SignalEvent | None,\n        risk_limits: RiskPolicyLimits,\n        risk_snapshot: RiskEvaluationSnapshot,\n    ) -> tuple[Literal["approved", "rejected", "no_signal"], tuple[str, ...]]:\n        if signal is None:\n            return "no_signal", ("NO_SIGNAL",)\n        outcome, reason_codes, _evaluations = RiskService._evaluate(\n            risk_limits,\n            risk_snapshot,\n            kill_switch_active=False,\n        )\n        if outcome is RiskDecisionOutcome.APPROVED:\n            return "approved", tuple(reason_codes)\n        return "rejected", tuple(reason_codes)\n\n    def _evidence(\n        self,\n        *,\n        decision_time: datetime,\n        symbol: str,\n        timeframe: str,\n        strategy: StrategyDefinition,\n        records: tuple[FeatureRecord, ...],\n        signal: SignalEvent | None,\n        risk_outcome: Literal["approved", "rejected", "no_signal"],\n        reason_codes: tuple[str, ...],\n        data_hash: str,\n        config_hash: str,\n    ) -> ShadowDecisionEvidence:\n        idempotency_key = canonical_sha256(\n            {\n                "decision_time": decision_time.isoformat(),\n                "strategy_hash": strategy.canonical_sha256(),\n                "features": [record.idempotency_key for record in records],\n            }\n        )\n        return ShadowDecisionEvidence.create(\n            evidence_version="1",\n            decision_time=decision_time,\n            symbol=symbol,\n            timeframe=timeframe,\n            strategy_id=strategy.strategy_id,\n            strategy_version=strategy.version,\n            feature_records=records,\n            signal=signal,\n            risk_outcome=risk_outcome,\n            reason_codes=reason_codes,\n            data_hash=data_hash,\n            config_hash=config_hash,\n            code_hash=self.code_hash,\n            idempotency_key=idempotency_key,\n            provenance=Provenance(\n                producer="ase00-shadow-engine",\n                source_event_id=idempotency_key,\n                lineage=tuple(record.idempotency_key for record in records),\n                details={\n                    "lineage_complete": True,\n                    "future_shift": 0,\n                    "risk_core": "ai_platform.portal.risk.service.RiskService._evaluate",\n                    "execution_adapter_used": False,\n                },\n            ),\n            no_order_submitted=True,\n        )\n\n    def _rejected_evidence(\n        self,\n        *,\n        decision_time: datetime,\n        symbol: str,\n        timeframe: str,\n        strategy_id: str,\n        strategy_version: str,\n        data_hash: str,\n        config_hash: str,\n        reason_codes: tuple[str, ...],\n    ) -> ShadowDecisionEvidence:\n        idempotency_key = canonical_sha256(\n            {\n                "decision_time": decision_time.isoformat(),\n                "strategy_id": strategy_id,\n                "strategy_version": strategy_version,\n                "data_hash": data_hash,\n                "reason_codes": list(reason_codes),\n            }\n        )\n        return ShadowDecisionEvidence.create(\n            evidence_version="1",\n            decision_time=decision_time,\n            symbol=symbol,\n            timeframe=timeframe,\n            strategy_id=strategy_id,\n            strategy_version=strategy_version,\n            feature_records=(),\n            signal=None,\n            risk_outcome="rejected",\n            reason_codes=_unique_codes((*reason_codes, Ase00Reason.SHADOW_ONLY)),\n            data_hash=data_hash,\n            config_hash=config_hash,\n            code_hash=self.code_hash,\n            idempotency_key=idempotency_key,\n            provenance=Provenance(\n                producer="ase00-shadow-engine",\n                source_event_id=idempotency_key,\n                lineage=(),\n                details={\n                    "lineage_complete": True,\n                    "future_shift": 0,\n                    "execution_adapter_used": False,\n                    "fail_closed": True,\n                },\n            ),\n            no_order_submitted=True,\n        )\n\n\ndef _payload_number(payload: Mapping[str, JsonValue], key: str) -> float:\n    value = payload.get(key)\n    if not isinstance(value, (int, float)) or isinstance(value, bool):\n        raise Ase00FailClosed(\n            Ase00Reason.MARKET_BAR_INVALID,\n            f"payload field {key} must be numeric",\n        )\n    return _finite_float(value, key)\n\n\ndef _finite_float(value: object, label: str) -> float:\n    if not isinstance(value, (int, float)) or isinstance(value, bool):\n        raise Ase00FailClosed(\n            Ase00Reason.MISSING_REQUIRED_DATA,\n            f"{label} is not numeric",\n        )\n    converted = float(value)\n    if not math.isfinite(converted):\n        raise Ase00FailClosed(\n            Ase00Reason.MISSING_REQUIRED_DATA,\n            f"{label} is not finite",\n        )\n    return converted\n\n\ndef _require_utc(value: datetime, label: str) -> None:\n    if value.tzinfo is None or value.utcoffset() != UTC.utcoffset(value):\n        raise ValueError(f"{label} must be normalized to UTC")\n\n\ndef _require_sha256(value: str, label: str) -> None:\n    if len(value) != 64 or any(char not in "0123456789abcdef" for char in value):\n        raise ValueError(f"{label} must be a lowercase SHA-256")\n\n\ndef _document_string(document: Mapping[str, object], key: str, default: str) -> str:\n    value = document.get(key)\n    return value if isinstance(value, str) and value else default\n\n\ndef _safe_config_hash(strategy_document: Mapping[str, object]) -> str:\n    try:\n        return canonical_sha256(cast(dict[str, object], dict(strategy_document)))\n    except (TypeError, ValueError):\n        return canonical_sha256({"unserializable_strategy": True})\n\n\ndef _unique_codes(codes: Sequence[str]) -> tuple[str, ...]:\n    return tuple(dict.fromkeys(codes))\n'
E         
E         'ExecutionAdapter' is contained here:
E           from __future__ import annotations
E           
E           import math
E           import os
E           from collections.abc import Mapping, Sequence
E           from dataclasses import dataclass, replace
E           from datetime import UTC, datetime, timedelta
E           from pathlib import Path
E           from typing import Literal, cast
E           
E           import pandas as pd
E           from pydantic import JsonValue
E           
E           from ai_platform.portal.contracts.risk import RiskDecisionOutcome
E           from ai_platform.portal.risk.schema import RiskEvaluationSnapshot, RiskPolicyLimits
E           from ai_platform.portal.risk.service import RiskService
E           from strategy_engine.domain.models import (
E               Action,
E               FeatureRecord,
E               Provenance,
E               ShadowDecisionEvidence,
E               Side,
E               SignalEvent,
E               StrategyDefinition,
E               canonical_sha256,
E           )
E           from strategy_engine.dsl.evaluator import EvaluationSnapshot, StrategyEvaluator
E           from strategy_engine.dsl.validator import StrategyValidationError, StrategyValidator
E           from strategy_engine.features.pivots import PivotEvent, confirmed_pivots
E           from strategy_engine.features.records import make_confirmed_pivot_record, make_feature_record
E           from strategy_engine.features.squeeze import squeeze_features
E           from strategy_engine.features.supertrend import supertrend_features
E           from strategy_engine.registry import FeatureRegistry, SearchSpaceRegistry
E           from strategy_engine.validation.leakage import (
E               LeakageContext,
E               LeakageError,
E               assert_features_available,
E           )
E           
E           
E           EventKind = Literal["market_bar", "liquidation"]
E           
E           
E           class Ase00Reason:
E               DUPLICATE_EVENT_IGNORED = "DUPLICATE_EVENT_IGNORED"
E               CONFLICTING_DUPLICATE_EVENT = "CONFLICTING_DUPLICATE_EVENT"
E               OUT_OF_ORDER_EVENT_NORMALIZED = "OUT_OF_ORDER_EVENT_NORMALIZED"
E               DELAYED_EVENT_ACCEPTED = "DELAYED_EVENT_ACCEPTED"
E               MISSING_REQUIRED_DATA = "MISSING_REQUIRED_DATA"
E               MARKET_BAR_INVALID = "MARKET_BAR_INVALID"
E               DUPLICATE_MARKET_TIMESTAMP = "DUPLICATE_MARKET_TIMESTAMP"
E               STRATEGY_REJECTED = "STRATEGY_REJECTED"
E               LEAKAGE_GUARD_REJECTED = "LEAKAGE_GUARD_REJECTED"
E               SHADOW_ONLY = "SHADOW_ONLY"
E           
E           
E           @dataclass(frozen=True)
E           class AcceptedSyntheticEvent:
E               event_id: str
E               idempotency_key: str
E               kind: EventKind
E               symbol: str
E               timeframe: str
E               event_time: datetime
E               detected_at: datetime
E               available_at: datetime
E               source: str
E               is_confirmed: bool
E               source_data_version: str
E               payload: Mapping[str, JsonValue]
E           
E               def __post_init__(self) -> None:
E                   for name in ("event_id", "idempotency_key", "symbol", "timeframe", "source"):
E                       if not getattr(self, name):
E                           raise ValueError(f"{name} cannot be empty")
E                   _require_utc(self.event_time, "event_time")
E                   _require_utc(self.detected_at, "detected_at")
E                   _require_utc(self.available_at, "available_at")
E                   if self.detected_at < self.event_time:
E                       raise ValueError("detected_at cannot precede event_time")
E                   if self.available_at < self.detected_at:
E                       raise ValueError("available_at cannot precede detected_at")
E                   if len(self.source_data_version) != 64 or any(
E                       char not in "0123456789abcdef" for char in self.source_data_version
E                   ):
E                       raise ValueError("source_data_version must be a lowercase SHA-256")
E           
E               def canonical_payload(self) -> dict[str, JsonValue]:
E                   return {
E                       "event_id": self.event_id,
E                       "idempotency_key": self.idempotency_key,
E                       "kind": self.kind,
E                       "symbol": self.symbol,
E                       "timeframe": self.timeframe,
E                       "event_time": self.event_time.isoformat(),
E                       "detected_at": self.detected_at.isoformat(),
E                       "available_at": self.available_at.isoformat(),
E                       "source": self.source,
E                       "is_confirmed": self.is_confirmed,
E                       "source_data_version": self.source_data_version,
E                       "payload": dict(self.payload),
E                   }
E           
E           
E           @dataclass(frozen=True)
E           class NormalizedEvents:
E               events: tuple[AcceptedSyntheticEvent, ...]
E               reason_codes: tuple[str, ...]
E               data_hash: str
E           
E           
E           class Ase00FailClosed(RuntimeError):
E               def __init__(self, reason_code: str, message: str) -> None:
E                   super().__init__(message)
E                   self.reason_code = reason_code
E           
E           
E           class Ase00ShadowEngine:
E               """Synthetic ASE-00 vertical slice.
E           
E               The class intentionally imports only Portal Risk Core models/service. It does not import or
E               construct an ExecutionAdapter and never creates an execution intent or order.
E         ?                  ++++++++++++++++
E               """
E           
E               def __init__(
E                   self,
E                   *,
E                   code_hash: str,
E                   repository_root: Path | None = None,
E                   processing_delay_threshold: timedelta = timedelta(seconds=1),
E               ) -> None:
E                   _require_sha256(code_hash, "code_hash")
E                   if processing_delay_threshold < timedelta(0):
E                       raise ValueError("processing_delay_threshold cannot be negative")
E                   self.code_hash = code_hash
E                   self.processing_delay_threshold = processing_delay_threshold
E                   self.repository_root = repository_root or Path(__file__).resolve().parents[3]
E                   strategy_root = self.repository_root / "ai_strategy_engine"
E                   self.registry = FeatureRegistry.load(strategy_root / "configs/feature_registry.v1.yaml")
E                   self.search_spaces = SearchSpaceRegistry.load(
E                       strategy_root / "configs/search_spaces.v1.yaml"
E                   )
E                   self.validator = StrategyValidator(self.registry, self.search_spaces)
E                   self.evaluator = StrategyEvaluator()
E           
E               def run(
E                   self,
E                   *,
E                   events: Sequence[AcceptedSyntheticEvent],
E                   strategy_document: Mapping[str, object],
E                   decision_time: datetime,
E                   risk_limits: RiskPolicyLimits,
E                   risk_snapshot: RiskEvaluationSnapshot,
E                   evidence_path: Path | None = None,
E                   generated_by_ai: bool = False,
E                   final_holdout_reused: bool = False,
E               ) -> ShadowDecisionEvidence:
E                   _require_utc(decision_time, "decision_time")
E                   raw_data_hash = canonical_sha256([event.canonical_payload() for event in events])
E                   strategy_id = _document_string(strategy_document, "strategy_id", "unknown-strategy")
E                   strategy_version = _document_string(strategy_document, "version", "0.0.0")
E                   symbol = events[0].symbol if events else "UNKNOWN"
E                   timeframe = events[0].timeframe if events else "UNKNOWN"
E           
E                   try:
E                       strategy = self.validator.validate(
E                           strategy_document,
E                           generated_by_ai=generated_by_ai,
E                       )
E                       normalized = self._normalize_events(events)
E                       symbol, timeframe = self._require_single_market(normalized.events)
E                       config_hash = canonical_sha256(
E                           {
E                               "strategy": strategy.model_dump(mode="json"),
E                               "feature_registry_version": self.registry.version,
E                               "search_space_version": self.search_spaces.version,
E                           }
E                       )
E                       records, current_snapshot, previous_snapshot, event_snapshot = self._features(
E                           normalized,
E                           strategy,
E                           decision_time,
E                           config_hash,
E                       )
E                       assert_features_available(
E                           records,
E                           decision_time,
E                           context=LeakageContext(
E                               decision_time=decision_time,
E                               expected_data_version=normalized.data_hash,
E                               expected_code_version=self.code_hash,
E                               expected_configuration_hash=config_hash,
E                               final_holdout_reused=final_holdout_reused,
E                           ),
E                       )
E                       dsl_decision = self.evaluator.evaluate(
E                           strategy,
E                           EvaluationSnapshot(
E                               features=current_snapshot,
E                               previous_features=previous_snapshot,
E                               events=event_snapshot,
E                               risk={},
E                           ),
E                       )
E                       signal = self._signal(
E                           strategy=strategy,
E                           decision_time=decision_time,
E                           records=records,
E                           dsl_side=dsl_decision.side,
E                           dsl_action=dsl_decision.action,
E                           dsl_reason_codes=dsl_decision.reason_codes,
E                           data_hash=normalized.data_hash,
E                           config_hash=config_hash,
E                       )
E                       risk_outcome, risk_reason_codes = self._risk_decision(
E                           signal=signal,
E                           risk_limits=risk_limits,
E                           risk_snapshot=risk_snapshot,
E                       )
E                       reason_codes = _unique_codes(
E                           (
E                               *normalized.reason_codes,
E                               *dsl_decision.reason_codes,
E                               *risk_reason_codes,
E                               Ase00Reason.SHADOW_ONLY,
E                           )
E                       )
E                       evidence = self._evidence(
E                           decision_time=decision_time,
E                           symbol=symbol,
E                           timeframe=timeframe,
E                           strategy=strategy,
E                           records=records,
E                           signal=signal,
E                           risk_outcome=risk_outcome,
E                           reason_codes=reason_codes,
E                           data_hash=normalized.data_hash,
E                           config_hash=config_hash,
E                       )
E                   except StrategyValidationError as exc:
E                       evidence = self._rejected_evidence(
E                           decision_time=decision_time,
E                           symbol=symbol,
E                           timeframe=timeframe,
E                           strategy_id=strategy_id,
E                           strategy_version=strategy_version,
E                           data_hash=raw_data_hash,
E                           config_hash=_safe_config_hash(strategy_document),
E                           reason_codes=(Ase00Reason.STRATEGY_REJECTED, exc.reason_code),
E                       )
E                   except LeakageError as exc:
E                       evidence = self._rejected_evidence(
E                           decision_time=decision_time,
E                           symbol=symbol,
E                           timeframe=timeframe,
E                           strategy_id=strategy_id,
E                           strategy_version=strategy_version,
E                           data_hash=raw_data_hash,
E                           config_hash=_safe_config_hash(strategy_document),
E                           reason_codes=(Ase00Reason.LEAKAGE_GUARD_REJECTED, exc.reason_code.value),
E                       )
E                   except Ase00FailClosed as exc:
E                       evidence = self._rejected_evidence(
E                           decision_time=decision_time,
E                           symbol=symbol,
E                           timeframe=timeframe,
E                           strategy_id=strategy_id,
E                           strategy_version=strategy_version,
E                           data_hash=raw_data_hash,
E                           config_hash=_safe_config_hash(strategy_document),
E                           reason_codes=(exc.reason_code, Ase00Reason.SHADOW_ONLY),
E                       )
E           
E                   if evidence_path is not None:
E                       self.persist_evidence(evidence_path, evidence)
E                   return evidence
E           
E               def persist_evidence(self, path: Path, evidence: ShadowDecisionEvidence) -> None:
E                   path.parent.mkdir(parents=True, exist_ok=True)
E                   encoded = evidence.canonical_json() + "\n"
E                   if path.exists():
E                       existing = path.read_text(encoding="utf-8")
E                       if existing == encoded:
E                           return
E                       try:
E                           existing_evidence = ShadowDecisionEvidence.model_validate_json(existing)
E                       except ValueError as exc:
E                           raise Ase00FailClosed(
E                               "EVIDENCE_CONFLICT", "existing evidence is not a valid ASE record"
E                           ) from exc
E                       if existing_evidence.idempotency_key == evidence.idempotency_key:
E                           raise Ase00FailClosed(
E                               "EVIDENCE_CONFLICT", "same idempotency key maps to different evidence"
E                           )
E                   temporary = path.with_name(f".{path.name}.{os.getpid()}.tmp")
E                   temporary.write_text(encoded, encoding="utf-8")
E                   temporary.replace(path)
E           
E               def _normalize_events(self, events: Sequence[AcceptedSyntheticEvent]) -> NormalizedEvents:
E                   if not events:
E                       raise Ase00FailClosed(
E                           Ase00Reason.MISSING_REQUIRED_DATA,
E                           "synthetic flow requires market and liquidation events",
E                       )
E                   raw_order = [self._event_sort_key(event) for event in events]
E                   out_of_order = raw_order != sorted(raw_order)
E                   by_idempotency_key: dict[str, AcceptedSyntheticEvent] = {}
E                   event_hashes: dict[str, str] = {}
E                   duplicate_count = 0
E                   delayed_count = 0
E                   for event in events:
E                       event_hash = canonical_sha256(event.canonical_payload())
E                       prior_hash = event_hashes.get(event.idempotency_key)
E                       if prior_hash is not None:
E                           if prior_hash != event_hash:
E                               raise Ase00FailClosed(
E                                   Ase00Reason.CONFLICTING_DUPLICATE_EVENT,
E                                   f"conflicting duplicate event: {event.idempotency_key}",
E                               )
E                           duplicate_count += 1
E                           continue
E                       event_hashes[event.idempotency_key] = event_hash
E                       by_idempotency_key[event.idempotency_key] = event
E                       if event.available_at - event.detected_at > self.processing_delay_threshold:
E                           delayed_count += 1
E                   normalized = tuple(sorted(by_idempotency_key.values(), key=self._event_sort_key))
E                   reason_codes: list[str] = []
E                   if duplicate_count:
E                       reason_codes.append(Ase00Reason.DUPLICATE_EVENT_IGNORED)
E                   if out_of_order:
E                       reason_codes.append(Ase00Reason.OUT_OF_ORDER_EVENT_NORMALIZED)
E                   if delayed_count:
E                       reason_codes.append(Ase00Reason.DELAYED_EVENT_ACCEPTED)
E                   data_hash = canonical_sha256([event.canonical_payload() for event in normalized])
E                   return NormalizedEvents(normalized, tuple(reason_codes), data_hash)
E           
E               @staticmethod
E               def _event_sort_key(event: AcceptedSyntheticEvent) -> tuple[datetime, datetime, datetime, str]:
E                   return (
E                       event.event_time,
E                       event.detected_at,
E                       event.available_at,
E                       event.idempotency_key,
E                   )
E           
E               @staticmethod
E               def _require_single_market(
E                   events: tuple[AcceptedSyntheticEvent, ...],
E               ) -> tuple[str, str]:
E                   market = [event for event in events if event.kind == "market_bar"]
E                   liquidations = [event for event in events if event.kind == "liquidation"]
E                   if not market or not liquidations:
E                       raise Ase00FailClosed(
E                           Ase00Reason.MISSING_REQUIRED_DATA,
E                           "both accepted market bars and liquidation events are required",
E                       )
E                   symbols = {event.symbol for event in events}
E                   timeframes = {event.timeframe for event in market}
E                   if len(symbols) != 1 or len(timeframes) != 1:
E                       raise Ase00FailClosed(
E                           Ase00Reason.MARKET_BAR_INVALID,
E                           "ASE-00 requires one symbol and one market timeframe",
E                       )
E                   return next(iter(symbols)), next(iter(timeframes))
E           
E               def _features(
E                   self,
E                   normalized: NormalizedEvents,
E                   strategy: StrategyDefinition,
E                   decision_time: datetime,
E                   config_hash: str,
E               ) -> tuple[
E                   tuple[FeatureRecord, ...],
E                   dict[str, JsonValue | Mapping[str, JsonValue]],
E                   dict[str, JsonValue | Mapping[str, JsonValue]],
E                   dict[str, JsonValue],
E               ]:
E                   market_events = tuple(event for event in normalized.events if event.kind == "market_bar")
E                   liquidation_events = tuple(
E                       event for event in normalized.events if event.kind == "liquidation"
E                   )
E                   frame = self._market_frame(market_events)
E                   if len(frame) < 25:
E                       raise Ase00FailClosed(
E                           Ase00Reason.MISSING_REQUIRED_DATA,
E                           "at least 25 closed synthetic bars are required",
E                       )
E                   symbol = market_events[0].symbol
E                   timeframe = market_events[0].timeframe
E                   latest_market = market_events[-1]
E                   feature_parameters = {feature.id: dict(feature.params) for feature in strategy.features}
E           
E                   squeeze_params = self.registry.validate_parameters(
E                       "squeeze_ratio.v1", feature_parameters.get("squeeze_ratio.v1", {})
E                   )
E                   squeeze_frame = squeeze_features(frame, **cast(dict[str, object], squeeze_params))
E                   squeeze_current = self._require_finite_row(
E                       squeeze_frame,
E                       -1,
E                       ("squeeze_ratio", "linreg_momentum", "momentum_slope"),
E                       "squeeze",
E                   )
E                   squeeze_previous = self._require_finite_row(
E                       squeeze_frame,
E                       -2,
E                       ("squeeze_ratio", "linreg_momentum", "momentum_slope"),
E                       "squeeze previous",
E                   )
E                   squeeze_value: dict[str, JsonValue] = {
E                       **squeeze_current,
E                       "squeeze_on": bool(squeeze_frame["squeeze_on"].iloc[-1]),
E                       "squeeze_release": bool(squeeze_frame["squeeze_release"].iloc[-1]),
E                   }
E                   squeeze_record = make_feature_record(
E                       feature_id="squeeze_ratio.v1",
E                       symbol=symbol,
E                       timeframe=timeframe,
E                       event_time=latest_market.event_time,
E                       detected_at=latest_market.detected_at,
E                       available_at=latest_market.available_at,
E                       value=squeeze_value,
E                       source="ase00-clean-room-squeeze",
E                       is_confirmed=latest_market.is_confirmed,
E                       idempotency_key=canonical_sha256(
E                           {"feature": "squeeze_ratio.v1", "source": latest_market.idempotency_key}
E                       ),
E                       code_version=self.code_hash,
E                       data_version=normalized.data_hash,
E                       configuration_hash=config_hash,
E                       producer="ase00-shadow-engine",
E                       source_event_id=latest_market.event_id,
E                       parameters=cast(dict[str, JsonValue], squeeze_params),
E                   )
E           
E                   supertrend_params = self.registry.validate_parameters(
E                       "supertrend_direction.v1",
E                       feature_parameters.get("supertrend_direction.v1", {}),
E                   )
E                   supertrend_frame = supertrend_features(
E                       frame,
E                       **cast(dict[str, object], supertrend_params),
E                   )
E                   direction = int(supertrend_frame["supertrend_direction"].iloc[-1])
E                   previous_direction = int(supertrend_frame["supertrend_direction"].iloc[-2])
E                   band = _finite_float(supertrend_frame["supertrend_band"].iloc[-1], "supertrend band")
E                   supertrend_value: dict[str, JsonValue] = {
E                       "value": direction,
E                       "direction": direction,
E                       "band": band,
E                       "flip": bool(supertrend_frame["supertrend_flip"].iloc[-1]),
E                   }
E                   supertrend_record = make_feature_record(
E                       feature_id="supertrend_direction.v1",
E                       symbol=symbol,
E                       timeframe=timeframe,
E                       event_time=latest_market.event_time,
E                       detected_at=latest_market.detected_at,
E                       available_at=latest_market.available_at,
E                       value=supertrend_value,
E                       source="ase00-clean-room-supertrend",
E                       is_confirmed=latest_market.is_confirmed,
E                       idempotency_key=canonical_sha256(
E                           {"feature": "supertrend_direction.v1", "source": latest_market.idempotency_key}
E                       ),
E                       code_version=self.code_hash,
E                       data_version=normalized.data_hash,
E                       configuration_hash=config_hash,
E                       producer="ase00-shadow-engine",
E                       source_event_id=latest_market.event_id,
E                       parameters=cast(dict[str, JsonValue], supertrend_params),
E                       provenance_details={"closed_bar": latest_market.is_confirmed},
E                   )
E           
E                   pivot_params = self.registry.validate_parameters(
E                       "confirmed_pivot.v1",
E                       feature_parameters.get("confirmed_pivot.v1", {"left_bars": 2, "right_bars": 2}),
E                   )
E                   pivots = confirmed_pivots(
E                       frame,
E                       left_bars=int(cast(int, pivot_params["left_bars"])),
E                       right_bars=int(cast(int, pivot_params["right_bars"])),
E                   )
E                   if not pivots:
E                       raise Ase00FailClosed(
E                           Ase00Reason.MISSING_REQUIRED_DATA,
E                           "no confirmed synthetic pivot is available",
E                       )
E                   event_by_time = {event.event_time: event for event in market_events}
E                   available_pivots: list[PivotEvent] = []
E                   for pivot in pivots:
E                       detected_event = event_by_time.get(pivot.detected_at.to_pydatetime())
E                       if detected_event is None:
E                           continue
E                       available_pivots.append(replace(pivot, available_at=detected_event.available_at))
E                   if not available_pivots:
E                       raise Ase00FailClosed(
E                           Ase00Reason.MISSING_REQUIRED_DATA,
E                           "pivot detection event is missing",
E                       )
E                   latest_pivot = available_pivots[-1]
E                   pivot_detected_event = event_by_time[latest_pivot.detected_at.to_pydatetime()]
E                   pivot_record = make_confirmed_pivot_record(
E                       pivot=latest_pivot,
E                       symbol=symbol,
E                       timeframe=timeframe,
E                       decision_time=decision_time,
E                       idempotency_key=canonical_sha256(
E                           {
E                               "feature": "confirmed_pivot.v1",
E                               "source": pivot_detected_event.idempotency_key,
E                               "pivot_index": latest_pivot.pivot_index,
E                           }
E                       ),
E                       code_version=self.code_hash,
E                       data_version=normalized.data_hash,
E                       configuration_hash=config_hash,
E                       producer="ase00-shadow-engine",
E                       source_event_id=pivot_detected_event.event_id,
E                       parameters=cast(dict[str, JsonValue], pivot_params),
E                       detection_event_confirmed=pivot_detected_event.is_confirmed,
E                   )
E           
E                   latest_liquidation = liquidation_events[-1]
E                   notional_z = _payload_number(latest_liquidation.payload, "notional_z")
E                   liquidation_record = make_feature_record(
E                       feature_id="liquidation_notional_z.v1",
E                       symbol=symbol,
E                       timeframe=latest_liquidation.timeframe,
E                       event_time=latest_liquidation.event_time,
E                       detected_at=latest_liquidation.detected_at,
E                       available_at=latest_liquidation.available_at,
E                       value={"value": notional_z, "notional_z": notional_z},
E                       source="accepted-synthetic-liquidation",
E                       is_confirmed=latest_liquidation.is_confirmed,
E                       idempotency_key=canonical_sha256(
E                           {
E                               "feature": "liquidation_notional_z.v1",
E                               "source": latest_liquidation.idempotency_key,
E                           }
E                       ),
E                       code_version=self.code_hash,
E                       data_version=normalized.data_hash,
E                       configuration_hash=config_hash,
E                       producer="ase00-shadow-engine",
E                       source_event_id=latest_liquidation.event_id,
E                       parameters={},
E                   )
E           
E                   records = (
E                       squeeze_record,
E                       supertrend_record,
E                       pivot_record,
E                       liquidation_record,
E                   )
E                   current: dict[str, JsonValue | Mapping[str, JsonValue]] = {
E                       "squeeze_ratio.v1": squeeze_value,
E                       "supertrend_direction.v1": supertrend_value,
E                       "confirmed_pivot.v1": cast(Mapping[str, JsonValue], pivot_record.value),
E                       "liquidation_notional_z.v1": cast(Mapping[str, JsonValue], liquidation_record.value),
E                   }
E                   previous: dict[str, JsonValue | Mapping[str, JsonValue]] = {
E                       "squeeze_ratio.v1": squeeze_previous,
E                       "supertrend_direction.v1": {
E                           "value": previous_direction,
E                           "direction": previous_direction,
E                       },
E                   }
E                   event_snapshot: dict[str, JsonValue] = {
E                       "squeeze_release": "up" if squeeze_value["squeeze_release"] else "none",
E                       "supertrend_flip": (
E                           "up"
E                           if supertrend_value["flip"] and direction == 1
E                           else "down"
E                           if supertrend_value["flip"] and direction == -1
E                           else "none"
E                       ),
E                       "pivot_confirmed": pivot_record.is_confirmed,
E                   }
E                   return records, current, previous, event_snapshot
E           
E               @staticmethod
E               def _market_frame(events: tuple[AcceptedSyntheticEvent, ...]) -> pd.DataFrame:
E                   rows: list[dict[str, float]] = []
E                   index: list[datetime] = []
E                   observed_times: set[datetime] = set()
E                   for event in events:
E                       if event.event_time in observed_times:
E                           raise Ase00FailClosed(
E                               Ase00Reason.DUPLICATE_MARKET_TIMESTAMP,
E                               f"multiple market bars at {event.event_time.isoformat()}",
E                           )
E                       observed_times.add(event.event_time)
E                       row = {
E                           key: _payload_number(event.payload, key)
E                           for key in ("open", "high", "low", "close", "volume")
E                       }
E                       if row["low"] > min(row["open"], row["close"], row["high"]):
E                           raise Ase00FailClosed(
E                               Ase00Reason.MARKET_BAR_INVALID, "low exceeds an OHLC component"
E                           )
E                       if row["high"] < max(row["open"], row["close"], row["low"]):
E                           raise Ase00FailClosed(
E                               Ase00Reason.MARKET_BAR_INVALID, "high is below an OHLC component"
E                           )
E                       if row["volume"] < 0:
E                           raise Ase00FailClosed(Ase00Reason.MARKET_BAR_INVALID, "volume cannot be negative")
E                       rows.append(row)
E                       index.append(event.event_time)
E                   frame = pd.DataFrame(rows, index=pd.DatetimeIndex(index))
E                   return frame.sort_index()
E           
E               @staticmethod
E               def _require_finite_row(
E                   frame: pd.DataFrame,
E                   position: int,
E                   columns: tuple[str, ...],
E                   label: str,
E               ) -> dict[str, JsonValue]:
E                   result: dict[str, JsonValue] = {}
E                   for column in columns:
E                       result[column] = _finite_float(frame[column].iloc[position], f"{label}.{column}")
E                   return result
E           
E               def _signal(
E                   self,
E                   *,
E                   strategy: StrategyDefinition,
E                   decision_time: datetime,
E                   records: tuple[FeatureRecord, ...],
E                   dsl_side: Side,
E                   dsl_action: Action,
E                   dsl_reason_codes: tuple[str, ...],
E                   data_hash: str,
E                   config_hash: str,
E               ) -> SignalEvent | None:
E                   if dsl_action is not Action.ENTER or dsl_side is Side.FLAT:
E                       return None
E                   latest_event_time = max(record.event_time for record in records)
E                   latest_detected_at = max(record.detected_at for record in records)
E                   latest_available_at = max(record.available_at for record in records)
E                   feature_snapshot: dict[str, JsonValue] = {
E                       record.feature_id: record.value for record in records
E                   }
E                   idempotency_key = canonical_sha256(
E                       {
E                           "strategy": strategy.strategy_id,
E                           "version": strategy.version,
E                           "decision_time": decision_time.isoformat(),
E                           "feature_ids": [record.idempotency_key for record in records],
E                       }
E                   )
E                   return SignalEvent(
E                       signal_id=idempotency_key,
E                       signal_version="1",
E                       strategy_id=strategy.strategy_id,
E                       strategy_version=strategy.version,
E                       symbol=records[0].symbol,
E                       timeframe=records[0].timeframe,
E                       side=dsl_side,
E                       action=dsl_action,
E                       event_time=latest_event_time,
E                       detected_at=latest_detected_at,
E                       available_at=latest_available_at,
E                       expires_at=None,
E                       source="ase00-shadow-engine",
E                       is_confirmed=all(record.is_confirmed for record in records),
E                       idempotency_key=idempotency_key,
E                       code_version=self.code_hash,
E                       data_version=data_hash,
E                       configuration_hash=config_hash,
E                       confidence=None,
E                       reason_codes=dsl_reason_codes,
E                       feature_snapshot=feature_snapshot,
E                       provenance=Provenance(
E                           producer="ase00-shadow-engine",
E                           source_event_id=idempotency_key,
E                           lineage=tuple(record.idempotency_key for record in records),
E                           details={
E                               "lineage_complete": True,
E                               "future_shift": 0,
E                               "shadow_only": True,
E                           },
E                       ),
E                       execution_policy={
E                           "use_closed_bar": True,
E                           "shadow_only": True,
E                           "order_submission_allowed": False,
E                       },
E                   )
E           
E               @staticmethod
E               def _risk_decision(
E                   *,
E                   signal: SignalEvent | None,
E                   risk_limits: RiskPolicyLimits,
E                   risk_snapshot: RiskEvaluationSnapshot,
E               ) -> tuple[Literal["approved", "rejected", "no_signal"], tuple[str, ...]]:
E                   if signal is None:
E                       return "no_signal", ("NO_SIGNAL",)
E                   outcome, reason_codes, _evaluations = RiskService._evaluate(
E                       risk_limits,
E                       risk_snapshot,
E                       kill_switch_active=False,
E                   )
E                   if outcome is RiskDecisionOutcome.APPROVED:
E                       return "approved", tuple(reason_codes)
E                   return "rejected", tuple(reason_codes)
E           
E               def _evidence(
E                   self,
E                   *,
E                   decision_time: datetime,
E                   symbol: str,
E                   timeframe: str,
E                   strategy: StrategyDefinition,
E                   records: tuple[FeatureRecord, ...],
E                   signal: SignalEvent | None,
E                   risk_outcome: Literal["approved", "rejected", "no_signal"],
E                   reason_codes: tuple[str, ...],
E                   data_hash: str,
E                   config_hash: str,
E               ) -> ShadowDecisionEvidence:
E                   idempotency_key = canonical_sha256(
E                       {
E                           "decision_time": decision_time.isoformat(),
E                           "strategy_hash": strategy.canonical_sha256(),
E                           "features": [record.idempotency_key for record in records],
E                       }
E                   )
E                   return ShadowDecisionEvidence.create(
E                       evidence_version="1",
E                       decision_time=decision_time,
E                       symbol=symbol,
E                       timeframe=timeframe,
E                       strategy_id=strategy.strategy_id,
E                       strategy_version=strategy.version,
E                       feature_records=records,
E                       signal=signal,
E                       risk_outcome=risk_outcome,
E                       reason_codes=reason_codes,
E                       data_hash=data_hash,
E                       config_hash=config_hash,
E                       code_hash=self.code_hash,
E                       idempotency_key=idempotency_key,
E                       provenance=Provenance(
E                           producer="ase00-shadow-engine",
E                           source_event_id=idempotency_key,
E                           lineage=tuple(record.idempotency_key for record in records),
E                           details={
E                               "lineage_complete": True,
E                               "future_shift": 0,
E                               "risk_core": "ai_platform.portal.risk.service.RiskService._evaluate",
E                               "execution_adapter_used": False,
E                           },
E                       ),
E                       no_order_submitted=True,
E                   )
E           
E               def _rejected_evidence(
E                   self,
E                   *,
E                   decision_time: datetime,
E                   symbol: str,
E                   timeframe: str,
E                   strategy_id: str,
E                   strategy_version: str,
E                   data_hash: str,
E                   config_hash: str,
E                   reason_codes: tuple[str, ...],
E               ) -> ShadowDecisionEvidence:
E                   idempotency_key = canonical_sha256(
E                       {
E                           "decision_time": decision_time.isoformat(),
E                           "strategy_id": strategy_id,
E                           "strategy_version": strategy_version,
E                           "data_hash": data_hash,
E                           "reason_codes": list(reason_codes),
E                       }
E                   )
E                   return ShadowDecisionEvidence.create(
E                       evidence_version="1",
E                       decision_time=decision_time,
E                       symbol=symbol,
E                       timeframe=timeframe,
E                       strategy_id=strategy_id,
E                       strategy_version=strategy_version,
E                       feature_records=(),
E                       signal=None,
E                       risk_outcome="rejected",
E                       reason_codes=_unique_codes((*reason_codes, Ase00Reason.SHADOW_ONLY)),
E                       data_hash=data_hash,
E                       config_hash=config_hash,
E                       code_hash=self.code_hash,
E                       idempotency_key=idempotency_key,
E                       provenance=Provenance(
E                           producer="ase00-shadow-engine",
E                           source_event_id=idempotency_key,
E                           lineage=(),
E                           details={
E                               "lineage_complete": True,
E                               "future_shift": 0,
E                               "execution_adapter_used": False,
E                               "fail_closed": True,
E                           },
E                       ),
E                       no_order_submitted=True,
E                   )
E           
E           
E           def _payload_number(payload: Mapping[str, JsonValue], key: str) -> float:
E               value = payload.get(key)
E               if not isinstance(value, (int, float)) or isinstance(value, bool):
E                   raise Ase00FailClosed(
E                       Ase00Reason.MARKET_BAR_INVALID,
E                       f"payload field {key} must be numeric",
E                   )
E               return _finite_float(value, key)
E           
E           
E           def _finite_float(value: object, label: str) -> float:
E               if not isinstance(value, (int, float)) or isinstance(value, bool):
E                   raise Ase00FailClosed(
E                       Ase00Reason.MISSING_REQUIRED_DATA,
E                       f"{label} is not numeric",
E                   )
E               converted = float(value)
E               if not math.isfinite(converted):
E                   raise Ase00FailClosed(
E                       Ase00Reason.MISSING_REQUIRED_DATA,
E                       f"{label} is not finite",
E                   )
E               return converted
E           
E           
E           def _require_utc(value: datetime, label: str) -> None:
E               if value.tzinfo is None or value.utcoffset() != UTC.utcoffset(value):
E                   raise ValueError(f"{label} must be normalized to UTC")
E           
E           
E           def _require_sha256(value: str, label: str) -> None:
E               if len(value) != 64 or any(char not in "0123456789abcdef" for char in value):
E                   raise ValueError(f"{label} must be a lowercase SHA-256")
E           
E           
E           def _document_string(document: Mapping[str, object], key: str, default: str) -> str:
E               value = document.get(key)
E               return value if isinstance(value, str) and value else default
E           
E           
E           def _safe_config_hash(strategy_document: Mapping[str, object]) -> str:
E               try:
E                   return canonical_sha256(cast(dict[str, object], dict(strategy_document)))
E               except (TypeError, ValueError):
E                   return canonical_sha256({"unserializable_strategy": True})
E           
E           
E           def _unique_codes(codes: Sequence[str]) -> tuple[str, ...]:
E               return tuple(dict.fromkeys(codes))

tests/ai_platform_integration/test_ase00_vertical_slice.py:451: AssertionError
=============================== warnings summary ===============================
ai_strategy_engine/.venv/lib/python3.12/site-packages/_pytest/config/__init__.py:1464
  /home/runner/work/freqtrade/freqtrade/ai_strategy_engine/.venv/lib/python3.12/site-packages/_pytest/config/__init__.py:1464: PytestConfigWarning: Unknown config option: asyncio_default_fixture_loop_scope
  
    self._warn_or_fail_if_strict(f"Unknown config option: {key}\n")

ai_strategy_engine/.venv/lib/python3.12/site-packages/_pytest/config/__init__.py:1464
  /home/runner/work/freqtrade/freqtrade/ai_strategy_engine/.venv/lib/python3.12/site-packages/_pytest/config/__init__.py:1464: PytestConfigWarning: Unknown config option: asyncio_mode
  
    self._warn_or_fail_if_strict(f"Unknown config option: {key}\n")

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
=========================== short test summary info ============================
FAILED tests/ai_platform_integration/test_ase00_vertical_slice.py::test_adapter_has_no_execution_or_freqtrade_dependency - assert 'ExecutionAdapter' not in 'from __future__ import annotations\n\nimport math\nimport os\nfrom collections.abc import Mapping, Sequence\nfrom dataclasses import dataclass, replace\nfrom datetime import UTC, datetime, timedelta\nfrom pathlib import Path\nfrom typing import Literal, cast\n\nimport pandas as pd\nfrom pydantic import JsonValue\n\nfrom ai_platform.portal.contracts.risk import RiskDecisionOutcome\nfrom ai_platform.portal.risk.schema import RiskEvaluationSnapshot, RiskPolicyLimits\nfrom ai_platform.portal.risk.service import RiskService\nfrom strategy_engine.domain.models import (\n    Action,\n    FeatureRecord,\n    Provenance,\n    ShadowDecisionEvidence,\n    Side,\n    SignalEvent,\n    StrategyDefinition,\n    canonical_sha256,\n)\nfrom strategy_engine.dsl.evaluator import EvaluationSnapshot, StrategyEvaluator\nfrom strategy_engine.dsl.validator import StrategyValidationError, StrategyValidator\nfrom strategy_engine.features.pivots import PivotEvent, confirmed_pivots\nfrom strategy_engine.features.records import make_confirmed_pivot_record, make_feature_record\nfrom strategy_engine.features.squeeze import squeeze_features\nfrom strategy_engine.features.supertrend import supertrend_features\nfrom strategy_engine.registry import FeatureRegistry, SearchSpaceRegistry\nfrom strategy_engine.validation.leakage import (\n    LeakageContext,\n    LeakageError,\n    assert_features_available,\n)\n\n\nEventKind = Literal["market_bar", "liquidation"]\n\n\nclass Ase00Reason:\n    DUPLICATE_EVENT_IGNORED = "DUPLICATE_EVENT_IGNORED"\n    CONFLICTING_DUPLICATE_EVENT = "CONFLICTING_DUPLICATE_EVENT"\n    OUT_OF_ORDER_EVENT_NORMALIZED = "OUT_OF_ORDER_EVENT_NORMALIZED"\n    DELAYED_EVENT_ACCEPTED = "DELAYED_EVENT_ACCEPTED"\n    MISSING_REQUIRED_DATA = "MISSING_REQUIRED_DATA"\n    MARKET_BAR_INVALID = "MARKET_BAR_INVALID"\n    DUPLICATE_MARKET_TIMESTAMP = "DUPLICATE_MARKET_TIMESTAMP"\n    STRATEGY_REJECTED = "STRATEGY_REJECTED"\n    LEAKAGE_GUARD_REJECTED = "LEAKAGE_GUARD_REJECTED"\n    SHADOW_ONLY = "SHADOW_ONLY"\n\n\n@dataclass(frozen=True)\nclass AcceptedSyntheticEvent:\n    event_id: str\n    idempotency_key: str\n    kind: EventKind\n    symbol: str\n    timeframe: str\n    event_time: datetime\n    detected_at: datetime\n    available_at: datetime\n    source: str\n    is_confirmed: bool\n    source_data_version: str\n    payload: Mapping[str, JsonValue]\n\n    def __post_init__(self) -> None:\n        for name in ("event_id", "idempotency_key", "symbol", "timeframe", "source"):\n            if not getattr(self, name):\n                raise ValueError(f"{name} cannot be empty")\n        _require_utc(self.event_time, "event_time")\n        _require_utc(self.detected_at, "detected_at")\n        _require_utc(self.available_at, "available_at")\n        if self.detected_at < self.event_time:\n            raise ValueError("detected_at cannot precede event_time")\n        if self.available_at < self.detected_at:\n            raise ValueError("available_at cannot precede detected_at")\n        if len(self.source_data_version) != 64 or any(\n            char not in "0123456789abcdef" for char in self.source_data_version\n        ):\n            raise ValueError("source_data_version must be a lowercase SHA-256")\n\n    def canonical_payload(self) -> dict[str, JsonValue]:\n        return {\n            "event_id": self.event_id,\n            "idempotency_key": self.idempotency_key,\n            "kind": self.kind,\n            "symbol": self.symbol,\n            "timeframe": self.timeframe,\n            "event_time": self.event_time.isoformat(),\n            "detected_at": self.detected_at.isoformat(),\n            "available_at": self.available_at.isoformat(),\n            "source": self.source,\n            "is_confirmed": self.is_confirmed,\n            "source_data_version": self.source_data_version,\n            "payload": dict(self.payload),\n        }\n\n\n@dataclass(frozen=True)\nclass NormalizedEvents:\n    events: tuple[AcceptedSyntheticEvent, ...]\n    reason_codes: tuple[str, ...]\n    data_hash: str\n\n\nclass Ase00FailClosed(RuntimeError):\n    def __init__(self, reason_code: str, message: str) -> None:\n        super().__init__(message)\n        self.reason_code = reason_code\n\n\nclass Ase00ShadowEngine:\n    """Synthetic ASE-00 vertical slice.\n\n    The class intentionally imports only Portal Risk Core models/service. It does not import or\n    construct an ExecutionAdapter and never creates an execution intent or order.\n    """\n\n    def __init__(\n        self,\n        *,\n        code_hash: str,\n        repository_root: Path | None = None,\n        processing_delay_threshold: timedelta = timedelta(seconds=1),\n    ) -> None:\n        _require_sha256(code_hash, "code_hash")\n        if processing_delay_threshold < timedelta(0):\n            raise ValueError("processing_delay_threshold cannot be negative")\n        self.code_hash = code_hash\n        self.processing_delay_threshold = processing_delay_threshold\n        self.repository_root = repository_root or Path(__file__).resolve().parents[3]\n        strategy_root = self.repository_root / "ai_strategy_engine"\n        self.registry = FeatureRegistry.load(strategy_root / "configs/feature_registry.v1.yaml")\n        self.search_spaces = SearchSpaceRegistry.load(\n            strategy_root / "configs/search_spaces.v1.yaml"\n        )\n        self.validator = StrategyValidator(self.registry, self.search_spaces)\n        self.evaluator = StrategyEvaluator()\n\n    def run(\n        self,\n        *,\n        events: Sequence[AcceptedSyntheticEvent],\n        strategy_document: Mapping[str, object],\n        decision_time: datetime,\n        risk_limits: RiskPolicyLimits,\n        risk_snapshot: RiskEvaluationSnapshot,\n        evidence_path: Path | None = None,\n        generated_by_ai: bool = False,\n        final_holdout_reused: bool = False,\n    ) -> ShadowDecisionEvidence:\n        _require_utc(decision_time, "decision_time")\n        raw_data_hash = canonical_sha256([event.canonical_payload() for event in events])\n        strategy_id = _document_string(strategy_document, "strategy_id", "unknown-strategy")\n        strategy_version = _document_string(strategy_document, "version", "0.0.0")\n        symbol = events[0].symbol if events else "UNKNOWN"\n        timeframe = events[0].timeframe if events else "UNKNOWN"\n\n        try:\n            strategy = self.validator.validate(\n                strategy_document,\n                generated_by_ai=generated_by_ai,\n            )\n            normalized = self._normalize_events(events)\n            symbol, timeframe = self._require_single_market(normalized.events)\n            config_hash = canonical_sha256(\n                {\n                    "strategy": strategy.model_dump(mode="json"),\n                    "feature_registry_version": self.registry.version,\n                    "search_space_version": self.search_spaces.version,\n                }\n            )\n            records, current_snapshot, previous_snapshot, event_snapshot = self._features(\n                normalized,\n                strategy,\n                decision_time,\n                config_hash,\n            )\n            assert_features_available(\n                records,\n                decision_time,\n                context=LeakageContext(\n                    decision_time=decision_time,\n                    expected_data_version=normalized.data_hash,\n                    expected_code_version=self.code_hash,\n                    expected_configuration_hash=config_hash,\n                    final_holdout_reused=final_holdout_reused,\n                ),\n            )\n            dsl_decision = self.evaluator.evaluate(\n                strategy,\n                EvaluationSnapshot(\n                    features=current_snapshot,\n                    previous_features=previous_snapshot,\n                    events=event_snapshot,\n                    risk={},\n                ),\n            )\n            signal = self._signal(\n                strategy=strategy,\n                decision_time=decision_time,\n                records=records,\n                dsl_side=dsl_decision.side,\n                dsl_action=dsl_decision.action,\n                dsl_reason_codes=dsl_decision.reason_codes,\n                data_hash=normalized.data_hash,\n                config_hash=config_hash,\n            )\n            risk_outcome, risk_reason_codes = self._risk_decision(\n                signal=signal,\n                risk_limits=risk_limits,\n                risk_snapshot=risk_snapshot,\n            )\n            reason_codes = _unique_codes(\n                (\n                    *normalized.reason_codes,\n                    *dsl_decision.reason_codes,\n                    *risk_reason_codes,\n                    Ase00Reason.SHADOW_ONLY,\n                )\n            )\n            evidence = self._evidence(\n                decision_time=decision_time,\n                symbol=symbol,\n                timeframe=timeframe,\n                strategy=strategy,\n                records=records,\n                signal=signal,\n                risk_outcome=risk_outcome,\n                reason_codes=reason_codes,\n                data_hash=normalized.data_hash,\n                config_hash=config_hash,\n            )\n        except StrategyValidationError as exc:\n            evidence = self._rejected_evidence(\n                decision_time=decision_time,\n                symbol=symbol,\n                timeframe=timeframe,\n                strategy_id=strategy_id,\n                strategy_version=strategy_version,\n                data_hash=raw_data_hash,\n                config_hash=_safe_config_hash(strategy_document),\n                reason_codes=(Ase00Reason.STRATEGY_REJECTED, exc.reason_code),\n            )\n        except LeakageError as exc:\n            evidence = self._rejected_evidence(\n                decision_time=decision_time,\n                symbol=symbol,\n                timeframe=timeframe,\n                strategy_id=strategy_id,\n                strategy_version=strategy_version,\n                data_hash=raw_data_hash,\n                config_hash=_safe_config_hash(strategy_document),\n                reason_codes=(Ase00Reason.LEAKAGE_GUARD_REJECTED, exc.reason_code.value),\n            )\n        except Ase00FailClosed as exc:\n            evidence = self._rejected_evidence(\n                decision_time=decision_time,\n                symbol=symbol,\n                timeframe=timeframe,\n                strategy_id=strategy_id,\n                strategy_version=strategy_version,\n                data_hash=raw_data_hash,\n                config_hash=_safe_config_hash(strategy_document),\n                reason_codes=(exc.reason_code, Ase00Reason.SHADOW_ONLY),\n            )\n\n        if evidence_path is not None:\n            self.persist_evidence(evidence_path, evidence)\n        return evidence\n\n    def persist_evidence(self, path: Path, evidence: ShadowDecisionEvidence) -> None:\n        path.parent.mkdir(parents=True, exist_ok=True)\n        encoded = evidence.canonical_json() + "\\n"\n        if path.exists():\n            existing = path.read_text(encoding="utf-8")\n            if existing == encoded:\n                return\n            try:\n                existing_evidence = ShadowDecisionEvidence.model_validate_json(existing)\n            except ValueError as exc:\n                raise Ase00FailClosed(\n                    "EVIDENCE_CONFLICT", "existing evidence is not a valid ASE record"\n                ) from exc\n            if existing_evidence.idempotency_key == evidence.idempotency_key:\n                raise Ase00FailClosed(\n                    "EVIDENCE_CONFLICT", "same idempotency key maps to different evidence"\n                )\n        temporary = path.with_name(f".{path.name}.{os.getpid()}.tmp")\n        temporary.write_text(encoded, encoding="utf-8")\n        temporary.replace(path)\n\n    def _normalize_events(self, events: Sequence[AcceptedSyntheticEvent]) -> NormalizedEvents:\n        if not events:\n            raise Ase00FailClosed(\n                Ase00Reason.MISSING_REQUIRED_DATA,\n                "synthetic flow requires market and liquidation events",\n            )\n        raw_order = [self._event_sort_key(event) for event in events]\n        out_of_order = raw_order != sorted(raw_order)\n        by_idempotency_key: dict[str, AcceptedSyntheticEvent] = {}\n        event_hashes: dict[str, str] = {}\n        duplicate_count = 0\n        delayed_count = 0\n        for event in events:\n            event_hash = canonical_sha256(event.canonical_payload())\n            prior_hash = event_hashes.get(event.idempotency_key)\n            if prior_hash is not None:\n                if prior_hash != event_hash:\n                    raise Ase00FailClosed(\n                        Ase00Reason.CONFLICTING_DUPLICATE_EVENT,\n                        f"conflicting duplicate event: {event.idempotency_key}",\n                    )\n                duplicate_count += 1\n                continue\n            event_hashes[event.idempotency_key] = event_hash\n            by_idempotency_key[event.idempotency_key] = event\n            if event.available_at - event.detected_at > self.processing_delay_threshold:\n                delayed_count += 1\n        normalized = tuple(sorted(by_idempotency_key.values(), key=self._event_sort_key))\n        reason_codes: list[str] = []\n        if duplicate_count:\n            reason_codes.append(Ase00Reason.DUPLICATE_EVENT_IGNORED)\n        if out_of_order:\n            reason_codes.append(Ase00Reason.OUT_OF_ORDER_EVENT_NORMALIZED)\n        if delayed_count:\n            reason_codes.append(Ase00Reason.DELAYED_EVENT_ACCEPTED)\n        data_hash = canonical_sha256([event.canonical_payload() for event in normalized])\n        return NormalizedEvents(normalized, tuple(reason_codes), data_hash)\n\n    @staticmethod\n    def _event_sort_key(event: AcceptedSyntheticEvent) -> tuple[datetime, datetime, datetime, str]:\n        return (\n            event.event_time,\n            event.detected_at,\n            event.available_at,\n            event.idempotency_key,\n        )\n\n    @staticmethod\n    def _require_single_market(\n        events: tuple[AcceptedSyntheticEvent, ...],\n    ) -> tuple[str, str]:\n        market = [event for event in events if event.kind == "market_bar"]\n        liquidations = [event for event in events if event.kind == "liquidation"]\n        if not market or not liquidations:\n            raise Ase00FailClosed(\n                Ase00Reason.MISSING_REQUIRED_DATA,\n                "both accepted market bars and liquidation events are required",\n            )\n        symbols = {event.symbol for event in events}\n        timeframes = {event.timeframe for event in market}\n        if len(symbols) != 1 or len(timeframes) != 1:\n            raise Ase00FailClosed(\n                Ase00Reason.MARKET_BAR_INVALID,\n                "ASE-00 requires one symbol and one market timeframe",\n            )\n        return next(iter(symbols)), next(iter(timeframes))\n\n    def _features(\n        self,\n        normalized: NormalizedEvents,\n        strategy: StrategyDefinition,\n        decision_time: datetime,\n        config_hash: str,\n    ) -> tuple[\n        tuple[FeatureRecord, ...],\n        dict[str, JsonValue | Mapping[str, JsonValue]],\n        dict[str, JsonValue | Mapping[str, JsonValue]],\n        dict[str, JsonValue],\n    ]:\n        market_events = tuple(event for event in normalized.events if event.kind == "market_bar")\n        liquidation_events = tuple(\n            event for event in normalized.events if event.kind == "liquidation"\n        )\n        frame = self._market_frame(market_events)\n        if len(frame) < 25:\n            raise Ase00FailClosed(\n                Ase00Reason.MISSING_REQUIRED_DATA,\n                "at least 25 closed synthetic bars are required",\n            )\n        symbol = market_events[0].symbol\n        timeframe = market_events[0].timeframe\n        latest_market = market_events[-1]\n        feature_parameters = {feature.id: dict(feature.params) for feature in strategy.features}\n\n        squeeze_params = self.registry.validate_parameters(\n            "squeeze_ratio.v1", feature_parameters.get("squeeze_ratio.v1", {})\n        )\n        squeeze_frame = squeeze_features(frame, **cast(dict[str, object], squeeze_params))\n        squeeze_current = self._require_finite_row(\n            squeeze_frame,\n            -1,\n            ("squeeze_ratio", "linreg_momentum", "momentum_slope"),\n            "squeeze",\n        )\n        squeeze_previous = self._require_finite_row(\n            squeeze_frame,\n            -2,\n            ("squeeze_ratio", "linreg_momentum", "momentum_slope"),\n            "squeeze previous",\n        )\n        squeeze_value: dict[str, JsonValue] = {\n            **squeeze_current,\n            "squeeze_on": bool(squeeze_frame["squeeze_on"].iloc[-1]),\n            "squeeze_release": bool(squeeze_frame["squeeze_release"].iloc[-1]),\n        }\n        squeeze_record = make_feature_record(\n            feature_id="squeeze_ratio.v1",\n            symbol=symbol,\n            timeframe=timeframe,\n            event_time=latest_market.event_time,\n            detected_at=latest_market.detected_at,\n            available_at=latest_market.available_at,\n            value=squeeze_value,\n            source="ase00-clean-room-squeeze",\n            is_confirmed=latest_market.is_confirmed,\n            idempotency_key=canonical_sha256(\n                {"feature": "squeeze_ratio.v1", "source": latest_market.idempotency_key}\n            ),\n            code_version=self.code_hash,\n            data_version=normalized.data_hash,\n            configuration_hash=config_hash,\n            producer="ase00-shadow-engine",\n            source_event_id=latest_market.event_id,\n            parameters=cast(dict[str, JsonValue], squeeze_params),\n        )\n\n        supertrend_params = self.registry.validate_parameters(\n            "supertrend_direction.v1",\n            feature_parameters.get("supertrend_direction.v1", {}),\n        )\n        supertrend_frame = supertrend_features(\n            frame,\n            **cast(dict[str, object], supertrend_params),\n        )\n        direction = int(supertrend_frame["supertrend_direction"].iloc[-1])\n        previous_direction = int(supertrend_frame["supertrend_direction"].iloc[-2])\n        band = _finite_float(supertrend_frame["supertrend_band"].iloc[-1], "supertrend band")\n        supertrend_value: dict[str, JsonValue] = {\n            "value": direction,\n            "direction": direction,\n            "band": band,\n            "flip": bool(supertrend_frame["supertrend_flip"].iloc[-1]),\n        }\n        supertrend_record = make_feature_record(\n            feature_id="supertrend_direction.v1",\n            symbol=symbol,\n            timeframe=timeframe,\n            event_time=latest_market.event_time,\n            detected_at=latest_market.detected_at,\n            available_at=latest_market.available_at,\n            value=supertrend_value,\n            source="ase00-clean-room-supertrend",\n            is_confirmed=latest_market.is_confirmed,\n            idempotency_key=canonical_sha256(\n                {"feature": "supertrend_direction.v1", "source": latest_market.idempotency_key}\n            ),\n            code_version=self.code_hash,\n            data_version=normalized.data_hash,\n            configuration_hash=config_hash,\n            producer="ase00-shadow-engine",\n            source_event_id=latest_market.event_id,\n            parameters=cast(dict[str, JsonValue], supertrend_params),\n            provenance_details={"closed_bar": latest_market.is_confirmed},\n        )\n\n        pivot_params = self.registry.validate_parameters(\n            "confirmed_pivot.v1",\n            feature_parameters.get("confirmed_pivot.v1", {"left_bars": 2, "right_bars": 2}),\n        )\n        pivots = confirmed_pivots(\n            frame,\n            left_bars=int(cast(int, pivot_params["left_bars"])),\n            right_bars=int(cast(int, pivot_params["right_bars"])),\n        )\n        if not pivots:\n            raise Ase00FailClosed(\n                Ase00Reason.MISSING_REQUIRED_DATA,\n                "no confirmed synthetic pivot is available",\n            )\n        event_by_time = {event.event_time: event for event in market_events}\n        available_pivots: list[PivotEvent] = []\n        for pivot in pivots:\n            detected_event = event_by_time.get(pivot.detected_at.to_pydatetime())\n            if detected_event is None:\n                continue\n            available_pivots.append(replace(pivot, available_at=detected_event.available_at))\n        if not available_pivots:\n            raise Ase00FailClosed(\n                Ase00Reason.MISSING_REQUIRED_DATA,\n                "pivot detection event is missing",\n            )\n        latest_pivot = available_pivots[-1]\n        pivot_detected_event = event_by_time[latest_pivot.detected_at.to_pydatetime()]\n        pivot_record = make_confirmed_pivot_record(\n            pivot=latest_pivot,\n            symbol=symbol,\n            timeframe=timeframe,\n            decision_time=decision_time,\n            idempotency_key=canonical_sha256(\n                {\n                    "feature": "confirmed_pivot.v1",\n                    "source": pivot_detected_event.idempotency_key,\n                    "pivot_index": latest_pivot.pivot_index,\n                }\n            ),\n            code_version=self.code_hash,\n            data_version=normalized.data_hash,\n            configuration_hash=config_hash,\n            producer="ase00-shadow-engine",\n            source_event_id=pivot_detected_event.event_id,\n            parameters=cast(dict[str, JsonValue], pivot_params),\n            detection_event_confirmed=pivot_detected_event.is_confirmed,\n        )\n\n        latest_liquidation = liquidation_events[-1]\n        notional_z = _payload_number(latest_liquidation.payload, "notional_z")\n        liquidation_record = make_feature_record(\n            feature_id="liquidation_notional_z.v1",\n            symbol=symbol,\n            timeframe=latest_liquidation.timeframe,\n            event_time=latest_liquidation.event_time,\n            detected_at=latest_liquidation.detected_at,\n            available_at=latest_liquidation.available_at,\n            value={"value": notional_z, "notional_z": notional_z},\n            source="accepted-synthetic-liquidation",\n            is_confirmed=latest_liquidation.is_confirmed,\n            idempotency_key=canonical_sha256(\n                {\n                    "feature": "liquidation_notional_z.v1",\n                    "source": latest_liquidation.idempotency_key,\n                }\n            ),\n            code_version=self.code_hash,\n            data_version=normalized.data_hash,\n            configuration_hash=config_hash,\n            producer="ase00-shadow-engine",\n            source_event_id=latest_liquidation.event_id,\n            parameters={},\n        )\n\n        records = (\n            squeeze_record,\n            supertrend_record,\n            pivot_record,\n            liquidation_record,\n        )\n        current: dict[str, JsonValue | Mapping[str, JsonValue]] = {\n            "squeeze_ratio.v1": squeeze_value,\n            "supertrend_direction.v1": supertrend_value,\n            "confirmed_pivot.v1": cast(Mapping[str, JsonValue], pivot_record.value),\n            "liquidation_notional_z.v1": cast(Mapping[str, JsonValue], liquidation_record.value),\n        }\n        previous: dict[str, JsonValue | Mapping[str, JsonValue]] = {\n            "squeeze_ratio.v1": squeeze_previous,\n            "supertrend_direction.v1": {\n                "value": previous_direction,\n                "direction": previous_direction,\n            },\n        }\n        event_snapshot: dict[str, JsonValue] = {\n            "squeeze_release": "up" if squeeze_value["squeeze_release"] else "none",\n            "supertrend_flip": (\n                "up"\n                if supertrend_value["flip"] and direction == 1\n                else "down"\n                if supertrend_value["flip"] and direction == -1\n                else "none"\n            ),\n            "pivot_confirmed": pivot_record.is_confirmed,\n        }\n        return records, current, previous, event_snapshot\n\n    @staticmethod\n    def _market_frame(events: tuple[AcceptedSyntheticEvent, ...]) -> pd.DataFrame:\n        rows: list[dict[str, float]] = []\n        index: list[datetime] = []\n        observed_times: set[datetime] = set()\n        for event in events:\n            if event.event_time in observed_times:\n                raise Ase00FailClosed(\n                    Ase00Reason.DUPLICATE_MARKET_TIMESTAMP,\n                    f"multiple market bars at {event.event_time.isoformat()}",\n                )\n            observed_times.add(event.event_time)\n            row = {\n                key: _payload_number(event.payload, key)\n                for key in ("open", "high", "low", "close", "volume")\n            }\n            if row["low"] > min(row["open"], row["close"], row["high"]):\n                raise Ase00FailClosed(\n                    Ase00Reason.MARKET_BAR_INVALID, "low exceeds an OHLC component"\n                )\n            if row["high"] < max(row["open"], row["close"], row["low"]):\n                raise Ase00FailClosed(\n                    Ase00Reason.MARKET_BAR_INVALID, "high is below an OHLC component"\n                )\n            if row["volume"] < 0:\n                raise Ase00FailClosed(Ase00Reason.MARKET_BAR_INVALID, "volume cannot be negative")\n            rows.append(row)\n            index.append(event.event_time)\n        frame = pd.DataFrame(rows, index=pd.DatetimeIndex(index))\n        return frame.sort_index()\n\n    @staticmethod\n    def _require_finite_row(\n        frame: pd.DataFrame,\n        position: int,\n        columns: tuple[str, ...],\n        label: str,\n    ) -> dict[str, JsonValue]:\n        result: dict[str, JsonValue] = {}\n        for column in columns:\n            result[column] = _finite_float(frame[column].iloc[position], f"{label}.{column}")\n        return result\n\n    def _signal(\n        self,\n        *,\n        strategy: StrategyDefinition,\n        decision_time: datetime,\n        records: tuple[FeatureRecord, ...],\n        dsl_side: Side,\n        dsl_action: Action,\n        dsl_reason_codes: tuple[str, ...],\n        data_hash: str,\n        config_hash: str,\n    ) -> SignalEvent | None:\n        if dsl_action is not Action.ENTER or dsl_side is Side.FLAT:\n            return None\n        latest_event_time = max(record.event_time for record in records)\n        latest_detected_at = max(record.detected_at for record in records)\n        latest_available_at = max(record.available_at for record in records)\n        feature_snapshot: dict[str, JsonValue] = {\n            record.feature_id: record.value for record in records\n        }\n        idempotency_key = canonical_sha256(\n            {\n                "strategy": strategy.strategy_id,\n                "version": strategy.version,\n                "decision_time": decision_time.isoformat(),\n                "feature_ids": [record.idempotency_key for record in records],\n            }\n        )\n        return SignalEvent(\n            signal_id=idempotency_key,\n            signal_version="1",\n            strategy_id=strategy.strategy_id,\n            strategy_version=strategy.version,\n            symbol=records[0].symbol,\n            timeframe=records[0].timeframe,\n            side=dsl_side,\n            action=dsl_action,\n            event_time=latest_event_time,\n            detected_at=latest_detected_at,\n            available_at=latest_available_at,\n            expires_at=None,\n            source="ase00-shadow-engine",\n            is_confirmed=all(record.is_confirmed for record in records),\n            idempotency_key=idempotency_key,\n            code_version=self.code_hash,\n            data_version=data_hash,\n            configuration_hash=config_hash,\n            confidence=None,\n            reason_codes=dsl_reason_codes,\n            feature_snapshot=feature_snapshot,\n            provenance=Provenance(\n                producer="ase00-shadow-engine",\n                source_event_id=idempotency_key,\n                lineage=tuple(record.idempotency_key for record in records),\n                details={\n                    "lineage_complete": True,\n                    "future_shift": 0,\n                    "shadow_only": True,\n                },\n            ),\n            execution_policy={\n                "use_closed_bar": True,\n                "shadow_only": True,\n                "order_submission_allowed": False,\n            },\n        )\n\n    @staticmethod\n    def _risk_decision(\n        *,\n        signal: SignalEvent | None,\n        risk_limits: RiskPolicyLimits,\n        risk_snapshot: RiskEvaluationSnapshot,\n    ) -> tuple[Literal["approved", "rejected", "no_signal"], tuple[str, ...]]:\n        if signal is None:\n            return "no_signal", ("NO_SIGNAL",)\n        outcome, reason_codes, _evaluations = RiskService._evaluate(\n            risk_limits,\n            risk_snapshot,\n            kill_switch_active=False,\n        )\n        if outcome is RiskDecisionOutcome.APPROVED:\n            return "approved", tuple(reason_codes)\n        return "rejected", tuple(reason_codes)\n\n    def _evidence(\n        self,\n        *,\n        decision_time: datetime,\n        symbol: str,\n        timeframe: str,\n        strategy: StrategyDefinition,\n        records: tuple[FeatureRecord, ...],\n        signal: SignalEvent | None,\n        risk_outcome: Literal["approved", "rejected", "no_signal"],\n        reason_codes: tuple[str, ...],\n        data_hash: str,\n        config_hash: str,\n    ) -> ShadowDecisionEvidence:\n        idempotency_key = canonical_sha256(\n            {\n                "decision_time": decision_time.isoformat(),\n                "strategy_hash": strategy.canonical_sha256(),\n                "features": [record.idempotency_key for record in records],\n            }\n        )\n        return ShadowDecisionEvidence.create(\n            evidence_version="1",\n            decision_time=decision_time,\n            symbol=symbol,\n            timeframe=timeframe,\n            strategy_id=strategy.strategy_id,\n            strategy_version=strategy.version,\n            feature_records=records,\n            signal=signal,\n            risk_outcome=risk_outcome,\n            reason_codes=reason_codes,\n            data_hash=data_hash,\n            config_hash=config_hash,\n            code_hash=self.code_hash,\n            idempotency_key=idempotency_key,\n            provenance=Provenance(\n                producer="ase00-shadow-engine",\n                source_event_id=idempotency_key,\n                lineage=tuple(record.idempotency_key for record in records),\n                details={\n                    "lineage_complete": True,\n                    "future_shift": 0,\n                    "risk_core": "ai_platform.portal.risk.service.RiskService._evaluate",\n                    "execution_adapter_used": False,\n                },\n            ),\n            no_order_submitted=True,\n        )\n\n    def _rejected_evidence(\n        self,\n        *,\n        decision_time: datetime,\n        symbol: str,\n        timeframe: str,\n        strategy_id: str,\n        strategy_version: str,\n        data_hash: str,\n        config_hash: str,\n        reason_codes: tuple[str, ...],\n    ) -> ShadowDecisionEvidence:\n        idempotency_key = canonical_sha256(\n            {\n                "decision_time": decision_time.isoformat(),\n                "strategy_id": strategy_id,\n                "strategy_version": strategy_version,\n                "data_hash": data_hash,\n                "reason_codes": list(reason_codes),\n            }\n        )\n        return ShadowDecisionEvidence.create(\n            evidence_version="1",\n            decision_time=decision_time,\n            symbol=symbol,\n            timeframe=timeframe,\n            strategy_id=strategy_id,\n            strategy_version=strategy_version,\n            feature_records=(),\n            signal=None,\n            risk_outcome="rejected",\n            reason_codes=_unique_codes((*reason_codes, Ase00Reason.SHADOW_ONLY)),\n            data_hash=data_hash,\n            config_hash=config_hash,\n            code_hash=self.code_hash,\n            idempotency_key=idempotency_key,\n            provenance=Provenance(\n                producer="ase00-shadow-engine",\n                source_event_id=idempotency_key,\n                lineage=(),\n                details={\n                    "lineage_complete": True,\n                    "future_shift": 0,\n                    "execution_adapter_used": False,\n                    "fail_closed": True,\n                },\n            ),\n            no_order_submitted=True,\n        )\n\n\ndef _payload_number(payload: Mapping[str, JsonValue], key: str) -> float:\n    value = payload.get(key)\n    if not isinstance(value, (int, float)) or isinstance(value, bool):\n        raise Ase00FailClosed(\n            Ase00Reason.MARKET_BAR_INVALID,\n            f"payload field {key} must be numeric",\n        )\n    return _finite_float(value, key)\n\n\ndef _finite_float(value: object, label: str) -> float:\n    if not isinstance(value, (int, float)) or isinstance(value, bool):\n        raise Ase00FailClosed(\n            Ase00Reason.MISSING_REQUIRED_DATA,\n            f"{label} is not numeric",\n        )\n    converted = float(value)\n    if not math.isfinite(converted):\n        raise Ase00FailClosed(\n            Ase00Reason.MISSING_REQUIRED_DATA,\n            f"{label} is not finite",\n        )\n    return converted\n\n\ndef _require_utc(value: datetime, label: str) -> None:\n    if value.tzinfo is None or value.utcoffset() != UTC.utcoffset(value):\n        raise ValueError(f"{label} must be normalized to UTC")\n\n\ndef _require_sha256(value: str, label: str) -> None:\n    if len(value) != 64 or any(char not in "0123456789abcdef" for char in value):\n        raise ValueError(f"{label} must be a lowercase SHA-256")\n\n\ndef _document_string(document: Mapping[str, object], key: str, default: str) -> str:\n    value = document.get(key)\n    return value if isinstance(value, str) and value else default\n\n\ndef _safe_config_hash(strategy_document: Mapping[str, object]) -> str:\n    try:\n        return canonical_sha256(cast(dict[str, object], dict(strategy_document)))\n    except (TypeError, ValueError):\n        return canonical_sha256({"unserializable_strategy": True})\n\n\ndef _unique_codes(codes: Sequence[str]) -> tuple[str, ...]:\n    return tuple(dict.fromkeys(codes))\n'
  
  'ExecutionAdapter' is contained here:
    from __future__ import annotations
    
    import math
    import os
    from collections.abc import Mapping, Sequence
    from dataclasses import dataclass, replace
    from datetime import UTC, datetime, timedelta
    from pathlib import Path
    from typing import Literal, cast
    
    import pandas as pd
    from pydantic import JsonValue
    
    from ai_platform.portal.contracts.risk import RiskDecisionOutcome
    from ai_platform.portal.risk.schema import RiskEvaluationSnapshot, RiskPolicyLimits
    from ai_platform.portal.risk.service import RiskService
    from strategy_engine.domain.models import (
        Action,
        FeatureRecord,
        Provenance,
        ShadowDecisionEvidence,
        Side,
        SignalEvent,
        StrategyDefinition,
        canonical_sha256,
    )
    from strategy_engine.dsl.evaluator import EvaluationSnapshot, StrategyEvaluator
    from strategy_engine.dsl.validator import StrategyValidationError, StrategyValidator
    from strategy_engine.features.pivots import PivotEvent, confirmed_pivots
    from strategy_engine.features.records import make_confirmed_pivot_record, make_feature_record
    from strategy_engine.features.squeeze import squeeze_features
    from strategy_engine.features.supertrend import supertrend_features
    from strategy_engine.registry import FeatureRegistry, SearchSpaceRegistry
    from strategy_engine.validation.leakage import (
        LeakageContext,
        LeakageError,
        assert_features_available,
    )
    
    
    EventKind = Literal["market_bar", "liquidation"]
    
    
    class Ase00Reason:
        DUPLICATE_EVENT_IGNORED = "DUPLICATE_EVENT_IGNORED"
        CONFLICTING_DUPLICATE_EVENT = "CONFLICTING_DUPLICATE_EVENT"
        OUT_OF_ORDER_EVENT_NORMALIZED = "OUT_OF_ORDER_EVENT_NORMALIZED"
        DELAYED_EVENT_ACCEPTED = "DELAYED_EVENT_ACCEPTED"
        MISSING_REQUIRED_DATA = "MISSING_REQUIRED_DATA"
        MARKET_BAR_INVALID = "MARKET_BAR_INVALID"
        DUPLICATE_MARKET_TIMESTAMP = "DUPLICATE_MARKET_TIMESTAMP"
        STRATEGY_REJECTED = "STRATEGY_REJECTED"
        LEAKAGE_GUARD_REJECTED = "LEAKAGE_GUARD_REJECTED"
        SHADOW_ONLY = "SHADOW_ONLY"
    
    
    @dataclass(frozen=True)
    class AcceptedSyntheticEvent:
        event_id: str
        idempotency_key: str
        kind: EventKind
        symbol: str
        timeframe: str
        event_time: datetime
        detected_at: datetime
        available_at: datetime
        source: str
        is_confirmed: bool
        source_data_version: str
        payload: Mapping[str, JsonValue]
    
        def __post_init__(self) -> None:
            for name in ("event_id", "idempotency_key", "symbol", "timeframe", "source"):
                if not getattr(self, name):
                    raise ValueError(f"{name} cannot be empty")
            _require_utc(self.event_time, "event_time")
            _require_utc(self.detected_at, "detected_at")
            _require_utc(self.available_at, "available_at")
            if self.detected_at < self.event_time:
                raise ValueError("detected_at cannot precede event_time")
            if self.available_at < self.detected_at:
                raise ValueError("available_at cannot precede detected_at")
            if len(self.source_data_version) != 64 or any(
                char not in "0123456789abcdef" for char in self.source_data_version
            ):
                raise ValueError("source_data_version must be a lowercase SHA-256")
    
        def canonical_payload(self) -> dict[str, JsonValue]:
            return {
                "event_id": self.event_id,
                "idempotency_key": self.idempotency_key,
                "kind": self.kind,
                "symbol": self.symbol,
                "timeframe": self.timeframe,
                "event_time": self.event_time.isoformat(),
                "detected_at": self.detected_at.isoformat(),
                "available_at": self.available_at.isoformat(),
                "source": self.source,
                "is_confirmed": self.is_confirmed,
                "source_data_version": self.source_data_version,
                "payload": dict(self.payload),
            }
    
    
    @dataclass(frozen=True)
    class NormalizedEvents:
        events: tuple[AcceptedSyntheticEvent, ...]
        reason_codes: tuple[str, ...]
        data_hash: str
    
    
    class Ase00FailClosed(RuntimeError):
        def __init__(self, reason_code: str, message: str) -> None:
            super().__init__(message)
            self.reason_code = reason_code
    
    
    class Ase00ShadowEngine:
        """Synthetic ASE-00 vertical slice.
    
        The class intentionally imports only Portal Risk Core models/service. It does not import or
        construct an ExecutionAdapter and never creates an execution intent or order.
  ?                  ++++++++++++++++
        """
    
        def __init__(
            self,
            *,
            code_hash: str,
            repository_root: Path | None = None,
            processing_delay_threshold: timedelta = timedelta(seconds=1),
        ) -> None:
            _require_sha256(code_hash, "code_hash")
            if processing_delay_threshold < timedelta(0):
                raise ValueError("processing_delay_threshold cannot be negative")
            self.code_hash = code_hash
            self.processing_delay_threshold = processing_delay_threshold
            self.repository_root = repository_root or Path(__file__).resolve().parents[3]
            strategy_root = self.repository_root / "ai_strategy_engine"
            self.registry = FeatureRegistry.load(strategy_root / "configs/feature_registry.v1.yaml")
            self.search_spaces = SearchSpaceRegistry.load(
                strategy_root / "configs/search_spaces.v1.yaml"
            )
            self.validator = StrategyValidator(self.registry, self.search_spaces)
            self.evaluator = StrategyEvaluator()
    
        def run(
            self,
            *,
            events: Sequence[AcceptedSyntheticEvent],
            strategy_document: Mapping[str, object],
            decision_time: datetime,
            risk_limits: RiskPolicyLimits,
            risk_snapshot: RiskEvaluationSnapshot,
            evidence_path: Path | None = None,
            generated_by_ai: bool = False,
            final_holdout_reused: bool = False,
        ) -> ShadowDecisionEvidence:
            _require_utc(decision_time, "decision_time")
            raw_data_hash = canonical_sha256([event.canonical_payload() for event in events])
            strategy_id = _document_string(strategy_document, "strategy_id", "unknown-strategy")
            strategy_version = _document_string(strategy_document, "version", "0.0.0")
            symbol = events[0].symbol if events else "UNKNOWN"
            timeframe = events[0].timeframe if events else "UNKNOWN"
    
            try:
                strategy = self.validator.validate(
                    strategy_document,
                    generated_by_ai=generated_by_ai,
                )
                normalized = self._normalize_events(events)
                symbol, timeframe = self._require_single_market(normalized.events)
                config_hash = canonical_sha256(
                    {
                        "strategy": strategy.model_dump(mode="json"),
                        "feature_registry_version": self.registry.version,
                        "search_space_version": self.search_spaces.version,
                    }
                )
                records, current_snapshot, previous_snapshot, event_snapshot = self._features(
                    normalized,
                    strategy,
                    decision_time,
                    config_hash,
                )
                assert_features_available(
                    records,
                    decision_time,
                    context=LeakageContext(
                        decision_time=decision_time,
                        expected_data_version=normalized.data_hash,
                        expected_code_version=self.code_hash,
                        expected_configuration_hash=config_hash,
                        final_holdout_reused=final_holdout_reused,
                    ),
                )
                dsl_decision = self.evaluator.evaluate(
                    strategy,
                    EvaluationSnapshot(
                        features=current_snapshot,
                        previous_features=previous_snapshot,
                        events=event_snapshot,
                        risk={},
                    ),
                )
                signal = self._signal(
                    strategy=strategy,
                    decision_time=decision_time,
                    records=records,
                    dsl_side=dsl_decision.side,
                    dsl_action=dsl_decision.action,
                    dsl_reason_codes=dsl_decision.reason_codes,
                    data_hash=normalized.data_hash,
                    config_hash=config_hash,
                )
                risk_outcome, risk_reason_codes = self._risk_decision(
                    signal=signal,
                    risk_limits=risk_limits,
                    risk_snapshot=risk_snapshot,
                )
                reason_codes = _unique_codes(
                    (
                        *normalized.reason_codes,
                        *dsl_decision.reason_codes,
                        *risk_reason_codes,
                        Ase00Reason.SHADOW_ONLY,
                    )
                )
                evidence = self._evidence(
                    decision_time=decision_time,
                    symbol=symbol,
                    timeframe=timeframe,
                    strategy=strategy,
                    records=records,
                    signal=signal,
                    risk_outcome=risk_outcome,
                    reason_codes=reason_codes,
                    data_hash=normalized.data_hash,
                    config_hash=config_hash,
                )
            except StrategyValidationError as exc:
                evidence = self._rejected_evidence(
                    decision_time=decision_time,
                    symbol=symbol,
                    timeframe=timeframe,
                    strategy_id=strategy_id,
                    strategy_version=strategy_version,
                    data_hash=raw_data_hash,
                    config_hash=_safe_config_hash(strategy_document),
                    reason_codes=(Ase00Reason.STRATEGY_REJECTED, exc.reason_code),
                )
            except LeakageError as exc:
                evidence = self._rejected_evidence(
                    decision_time=decision_time,
                    symbol=symbol,
                    timeframe=timeframe,
                    strategy_id=strategy_id,
                    strategy_version=strategy_version,
                    data_hash=raw_data_hash,
                    config_hash=_safe_config_hash(strategy_document),
                    reason_codes=(Ase00Reason.LEAKAGE_GUARD_REJECTED, exc.reason_code.value),
                )
            except Ase00FailClosed as exc:
                evidence = self._rejected_evidence(
                    decision_time=decision_time,
                    symbol=symbol,
                    timeframe=timeframe,
                    strategy_id=strategy_id,
                    strategy_version=strategy_version,
                    data_hash=raw_data_hash,
                    config_hash=_safe_config_hash(strategy_document),
                    reason_codes=(exc.reason_code, Ase00Reason.SHADOW_ONLY),
                )
    
            if evidence_path is not None:
                self.persist_evidence(evidence_path, evidence)
            return evidence
    
        def persist_evidence(self, path: Path, evidence: ShadowDecisionEvidence) -> None:
            path.parent.mkdir(parents=True, exist_ok=True)
            encoded = evidence.canonical_json() + "\n"
            if path.exists():
                existing = path.read_text(encoding="utf-8")
                if existing == encoded:
                    return
                try:
                    existing_evidence = ShadowDecisionEvidence.model_validate_json(existing)
                except ValueError as exc:
                    raise Ase00FailClosed(
                        "EVIDENCE_CONFLICT", "existing evidence is not a valid ASE record"
                    ) from exc
                if existing_evidence.idempotency_key == evidence.idempotency_key:
                    raise Ase00FailClosed(
                        "EVIDENCE_CONFLICT", "same idempotency key maps to different evidence"
                    )
            temporary = path.with_name(f".{path.name}.{os.getpid()}.tmp")
            temporary.write_text(encoded, encoding="utf-8")
            temporary.replace(path)
    
        def _normalize_events(self, events: Sequence[AcceptedSyntheticEvent]) -> NormalizedEvents:
            if not events:
                raise Ase00FailClosed(
                    Ase00Reason.MISSING_REQUIRED_DATA,
                    "synthetic flow requires market and liquidation events",
                )
            raw_order = [self._event_sort_key(event) for event in events]
            out_of_order = raw_order != sorted(raw_order)
            by_idempotency_key: dict[str, AcceptedSyntheticEvent] = {}
            event_hashes: dict[str, str] = {}
            duplicate_count = 0
            delayed_count = 0
            for event in events:
                event_hash = canonical_sha256(event.canonical_payload())
                prior_hash = event_hashes.get(event.idempotency_key)
                if prior_hash is not None:
                    if prior_hash != event_hash:
                        raise Ase00FailClosed(
                            Ase00Reason.CONFLICTING_DUPLICATE_EVENT,
                            f"conflicting duplicate event: {event.idempotency_key}",
                        )
                    duplicate_count += 1
                    continue
                event_hashes[event.idempotency_key] = event_hash
                by_idempotency_key[event.idempotency_key] = event
                if event.available_at - event.detected_at > self.processing_delay_threshold:
                    delayed_count += 1
            normalized = tuple(sorted(by_idempotency_key.values(), key=self._event_sort_key))
            reason_codes: list[str] = []
            if duplicate_count:
                reason_codes.append(Ase00Reason.DUPLICATE_EVENT_IGNORED)
            if out_of_order:
                reason_codes.append(Ase00Reason.OUT_OF_ORDER_EVENT_NORMALIZED)
            if delayed_count:
                reason_codes.append(Ase00Reason.DELAYED_EVENT_ACCEPTED)
            data_hash = canonical_sha256([event.canonical_payload() for event in normalized])
            return NormalizedEvents(normalized, tuple(reason_codes), data_hash)
    
        @staticmethod
        def _event_sort_key(event: AcceptedSyntheticEvent) -> tuple[datetime, datetime, datetime, str]:
            return (
                event.event_time,
                event.detected_at,
                event.available_at,
                event.idempotency_key,
            )
    
        @staticmethod
        def _require_single_market(
            events: tuple[AcceptedSyntheticEvent, ...],
        ) -> tuple[str, str]:
            market = [event for event in events if event.kind == "market_bar"]
            liquidations = [event for event in events if event.kind == "liquidation"]
            if not market or not liquidations:
                raise Ase00FailClosed(
                    Ase00Reason.MISSING_REQUIRED_DATA,
                    "both accepted market bars and liquidation events are required",
                )
            symbols = {event.symbol for event in events}
            timeframes = {event.timeframe for event in market}
            if len(symbols) != 1 or len(timeframes) != 1:
                raise Ase00FailClosed(
                    Ase00Reason.MARKET_BAR_INVALID,
                    "ASE-00 requires one symbol and one market timeframe",
                )
            return next(iter(symbols)), next(iter(timeframes))
    
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
            liquidation_events = tuple(
                event for event in normalized.events if event.kind == "liquidation"
            )
            frame = self._market_frame(market_events)
            if len(frame) < 25:
                raise Ase00FailClosed(
                    Ase00Reason.MISSING_REQUIRED_DATA,
                    "at least 25 closed synthetic bars are required",
                )
            symbol = market_events[0].symbol
            timeframe = market_events[0].timeframe
            latest_market = market_events[-1]
            feature_parameters = {feature.id: dict(feature.params) for feature in strategy.features}
    
            squeeze_params = self.registry.validate_parameters(
                "squeeze_ratio.v1", feature_parameters.get("squeeze_ratio.v1", {})
            )
            squeeze_frame = squeeze_features(frame, **cast(dict[str, object], squeeze_params))
            squeeze_current = self._require_finite_row(
                squeeze_frame,
                -1,
                ("squeeze_ratio", "linreg_momentum", "momentum_slope"),
                "squeeze",
            )
            squeeze_previous = self._require_finite_row(
                squeeze_frame,
                -2,
                ("squeeze_ratio", "linreg_momentum", "momentum_slope"),
                "squeeze previous",
            )
            squeeze_value: dict[str, JsonValue] = {
                **squeeze_current,
                "squeeze_on": bool(squeeze_frame["squeeze_on"].iloc[-1]),
                "squeeze_release": bool(squeeze_frame["squeeze_release"].iloc[-1]),
            }
            squeeze_record = make_feature_record(
                feature_id="squeeze_ratio.v1",
                symbol=symbol,
                timeframe=timeframe,
                event_time=latest_market.event_time,
                detected_at=latest_market.detected_at,
                available_at=latest_market.available_at,
                value=squeeze_value,
                source="ase00-clean-room-squeeze",
                is_confirmed=latest_market.is_confirmed,
                idempotency_key=canonical_sha256(
                    {"feature": "squeeze_ratio.v1", "source": latest_market.idempotency_key}
                ),
                code_version=self.code_hash,
                data_version=normalized.data_hash,
                configuration_hash=config_hash,
                producer="ase00-shadow-engine",
                source_event_id=latest_market.event_id,
                parameters=cast(dict[str, JsonValue], squeeze_params),
            )
    
            supertrend_params = self.registry.validate_parameters(
                "supertrend_direction.v1",
                feature_parameters.get("supertrend_direction.v1", {}),
            )
            supertrend_frame = supertrend_features(
                frame,
                **cast(dict[str, object], supertrend_params),
            )
            direction = int(supertrend_frame["supertrend_direction"].iloc[-1])
            previous_direction = int(supertrend_frame["supertrend_direction"].iloc[-2])
            band = _finite_float(supertrend_frame["supertrend_band"].iloc[-1], "supertrend band")
            supertrend_value: dict[str, JsonValue] = {
                "value": direction,
                "direction": direction,
                "band": band,
                "flip": bool(supertrend_frame["supertrend_flip"].iloc[-1]),
            }
            supertrend_record = make_feature_record(
                feature_id="supertrend_direction.v1",
                symbol=symbol,
                timeframe=timeframe,
                event_time=latest_market.event_time,
                detected_at=latest_market.detected_at,
                available_at=latest_market.available_at,
                value=supertrend_value,
                source="ase00-clean-room-supertrend",
                is_confirmed=latest_market.is_confirmed,
                idempotency_key=canonical_sha256(
                    {"feature": "supertrend_direction.v1", "source": latest_market.idempotency_key}
                ),
                code_version=self.code_hash,
                data_version=normalized.data_hash,
                configuration_hash=config_hash,
                producer="ase00-shadow-engine",
                source_event_id=latest_market.event_id,
                parameters=cast(dict[str, JsonValue], supertrend_params),
                provenance_details={"closed_bar": latest_market.is_confirmed},
            )
    
            pivot_params = self.registry.validate_parameters(
                "confirmed_pivot.v1",
                feature_parameters.get("confirmed_pivot.v1", {"left_bars": 2, "right_bars": 2}),
            )
            pivots = confirmed_pivots(
                frame,
                left_bars=int(cast(int, pivot_params["left_bars"])),
                right_bars=int(cast(int, pivot_params["right_bars"])),
            )
            if not pivots:
                raise Ase00FailClosed(
                    Ase00Reason.MISSING_REQUIRED_DATA,
                    "no confirmed synthetic pivot is available",
                )
            event_by_time = {event.event_time: event for event in market_events}
            available_pivots: list[PivotEvent] = []
            for pivot in pivots:
                detected_event = event_by_time.get(pivot.detected_at.to_pydatetime())
                if detected_event is None:
                    continue
                available_pivots.append(replace(pivot, available_at=detected_event.available_at))
            if not available_pivots:
                raise Ase00FailClosed(
                    Ase00Reason.MISSING_REQUIRED_DATA,
                    "pivot detection event is missing",
                )
            latest_pivot = available_pivots[-1]
            pivot_detected_event = event_by_time[latest_pivot.detected_at.to_pydatetime()]
            pivot_record = make_confirmed_pivot_record(
                pivot=latest_pivot,
                symbol=symbol,
                timeframe=timeframe,
                decision_time=decision_time,
                idempotency_key=canonical_sha256(
                    {
                        "feature": "confirmed_pivot.v1",
                        "source": pivot_detected_event.idempotency_key,
                        "pivot_index": latest_pivot.pivot_index,
                    }
                ),
                code_version=self.code_hash,
                data_version=normalized.data_hash,
                configuration_hash=config_hash,
                producer="ase00-shadow-engine",
                source_event_id=pivot_detected_event.event_id,
                parameters=cast(dict[str, JsonValue], pivot_params),
                detection_event_confirmed=pivot_detected_event.is_confirmed,
            )
    
            latest_liquidation = liquidation_events[-1]
            notional_z = _payload_number(latest_liquidation.payload, "notional_z")
            liquidation_record = make_feature_record(
                feature_id="liquidation_notional_z.v1",
                symbol=symbol,
                timeframe=latest_liquidation.timeframe,
                event_time=latest_liquidation.event_time,
                detected_at=latest_liquidation.detected_at,
                available_at=latest_liquidation.available_at,
                value={"value": notional_z, "notional_z": notional_z},
                source="accepted-synthetic-liquidation",
                is_confirmed=latest_liquidation.is_confirmed,
                idempotency_key=canonical_sha256(
                    {
                        "feature": "liquidation_notional_z.v1",
                        "source": latest_liquidation.idempotency_key,
                    }
                ),
                code_version=self.code_hash,
                data_version=normalized.data_hash,
                configuration_hash=config_hash,
                producer="ase00-shadow-engine",
                source_event_id=latest_liquidation.event_id,
                parameters={},
            )
    
            records = (
                squeeze_record,
                supertrend_record,
                pivot_record,
                liquidation_record,
            )
            current: dict[str, JsonValue | Mapping[str, JsonValue]] = {
                "squeeze_ratio.v1": squeeze_value,
                "supertrend_direction.v1": supertrend_value,
                "confirmed_pivot.v1": cast(Mapping[str, JsonValue], pivot_record.value),
                "liquidation_notional_z.v1": cast(Mapping[str, JsonValue], liquidation_record.value),
            }
            previous: dict[str, JsonValue | Mapping[str, JsonValue]] = {
                "squeeze_ratio.v1": squeeze_previous,
                "supertrend_direction.v1": {
                    "value": previous_direction,
                    "direction": previous_direction,
                },
            }
            event_snapshot: dict[str, JsonValue] = {
                "squeeze_release": "up" if squeeze_value["squeeze_release"] else "none",
                "supertrend_flip": (
                    "up"
                    if supertrend_value["flip"] and direction == 1
                    else "down"
                    if supertrend_value["flip"] and direction == -1
                    else "none"
                ),
                "pivot_confirmed": pivot_record.is_confirmed,
            }
            return records, current, previous, event_snapshot
    
        @staticmethod
        def _market_frame(events: tuple[AcceptedSyntheticEvent, ...]) -> pd.DataFrame:
            rows: list[dict[str, float]] = []
            index: list[datetime] = []
            observed_times: set[datetime] = set()
            for event in events:
                if event.event_time in observed_times:
                    raise Ase00FailClosed(
                        Ase00Reason.DUPLICATE_MARKET_TIMESTAMP,
                        f"multiple market bars at {event.event_time.isoformat()}",
                    )
                observed_times.add(event.event_time)
                row = {
                    key: _payload_number(event.payload, key)
                    for key in ("open", "high", "low", "close", "volume")
                }
                if row["low"] > min(row["open"], row["close"], row["high"]):
                    raise Ase00FailClosed(
                        Ase00Reason.MARKET_BAR_INVALID, "low exceeds an OHLC component"
                    )
                if row["high"] < max(row["open"], row["close"], row["low"]):
                    raise Ase00FailClosed(
                        Ase00Reason.MARKET_BAR_INVALID, "high is below an OHLC component"
                    )
                if row["volume"] < 0:
                    raise Ase00FailClosed(Ase00Reason.MARKET_BAR_INVALID, "volume cannot be negative")
                rows.append(row)
                index.append(event.event_time)
            frame = pd.DataFrame(rows, index=pd.DatetimeIndex(index))
            return frame.sort_index()
    
        @staticmethod
        def _require_finite_row(
            frame: pd.DataFrame,
            position: int,
            columns: tuple[str, ...],
            label: str,
        ) -> dict[str, JsonValue]:
            result: dict[str, JsonValue] = {}
            for column in columns:
                result[column] = _finite_float(frame[column].iloc[position], f"{label}.{column}")
            return result
    
        def _signal(
            self,
            *,
            strategy: StrategyDefinition,
            decision_time: datetime,
            records: tuple[FeatureRecord, ...],
            dsl_side: Side,
            dsl_action: Action,
            dsl_reason_codes: tuple[str, ...],
            data_hash: str,
            config_hash: str,
        ) -> SignalEvent | None:
            if dsl_action is not Action.ENTER or dsl_side is Side.FLAT:
                return None
            latest_event_time = max(record.event_time for record in records)
            latest_detected_at = max(record.detected_at for record in records)
            latest_available_at = max(record.available_at for record in records)
            feature_snapshot: dict[str, JsonValue] = {
                record.feature_id: record.value for record in records
            }
            idempotency_key = canonical_sha256(
                {
                    "strategy": strategy.strategy_id,
                    "version": strategy.version,
                    "decision_time": decision_time.isoformat(),
                    "feature_ids": [record.idempotency_key for record in records],
                }
            )
            return SignalEvent(
                signal_id=idempotency_key,
                signal_version="1",
                strategy_id=strategy.strategy_id,
                strategy_version=strategy.version,
                symbol=records[0].symbol,
                timeframe=records[0].timeframe,
                side=dsl_side,
                action=dsl_action,
                event_time=latest_event_time,
                detected_at=latest_detected_at,
                available_at=latest_available_at,
                expires_at=None,
                source="ase00-shadow-engine",
                is_confirmed=all(record.is_confirmed for record in records),
                idempotency_key=idempotency_key,
                code_version=self.code_hash,
                data_version=data_hash,
                configuration_hash=config_hash,
                confidence=None,
                reason_codes=dsl_reason_codes,
                feature_snapshot=feature_snapshot,
                provenance=Provenance(
                    producer="ase00-shadow-engine",
                    source_event_id=idempotency_key,
                    lineage=tuple(record.idempotency_key for record in records),
                    details={
                        "lineage_complete": True,
                        "future_shift": 0,
                        "shadow_only": True,
                    },
                ),
                execution_policy={
                    "use_closed_bar": True,
                    "shadow_only": True,
                    "order_submission_allowed": False,
                },
            )
    
        @staticmethod
        def _risk_decision(
            *,
            signal: SignalEvent | None,
            risk_limits: RiskPolicyLimits,
            risk_snapshot: RiskEvaluationSnapshot,
        ) -> tuple[Literal["approved", "rejected", "no_signal"], tuple[str, ...]]:
            if signal is None:
                return "no_signal", ("NO_SIGNAL",)
            outcome, reason_codes, _evaluations = RiskService._evaluate(
                risk_limits,
                risk_snapshot,
                kill_switch_active=False,
            )
            if outcome is RiskDecisionOutcome.APPROVED:
                return "approved", tuple(reason_codes)
            return "rejected", tuple(reason_codes)
    
        def _evidence(
            self,
            *,
            decision_time: datetime,
            symbol: str,
            timeframe: str,
            strategy: StrategyDefinition,
            records: tuple[FeatureRecord, ...],
            signal: SignalEvent | None,
            risk_outcome: Literal["approved", "rejected", "no_signal"],
            reason_codes: tuple[str, ...],
            data_hash: str,
            config_hash: str,
        ) -> ShadowDecisionEvidence:
            idempotency_key = canonical_sha256(
                {
                    "decision_time": decision_time.isoformat(),
                    "strategy_hash": strategy.canonical_sha256(),
                    "features": [record.idempotency_key for record in records],
                }
            )
            return ShadowDecisionEvidence.create(
                evidence_version="1",
                decision_time=decision_time,
                symbol=symbol,
                timeframe=timeframe,
                strategy_id=strategy.strategy_id,
                strategy_version=strategy.version,
                feature_records=records,
                signal=signal,
                risk_outcome=risk_outcome,
                reason_codes=reason_codes,
                data_hash=data_hash,
                config_hash=config_hash,
                code_hash=self.code_hash,
                idempotency_key=idempotency_key,
                provenance=Provenance(
                    producer="ase00-shadow-engine",
                    source_event_id=idempotency_key,
                    lineage=tuple(record.idempotency_key for record in records),
                    details={
                        "lineage_complete": True,
                        "future_shift": 0,
                        "risk_core": "ai_platform.portal.risk.service.RiskService._evaluate",
                        "execution_adapter_used": False,
                    },
                ),
                no_order_submitted=True,
            )
    
        def _rejected_evidence(
            self,
            *,
            decision_time: datetime,
            symbol: str,
            timeframe: str,
            strategy_id: str,
            strategy_version: str,
            data_hash: str,
            config_hash: str,
            reason_codes: tuple[str, ...],
        ) -> ShadowDecisionEvidence:
            idempotency_key = canonical_sha256(
                {
                    "decision_time": decision_time.isoformat(),
                    "strategy_id": strategy_id,
                    "strategy_version": strategy_version,
                    "data_hash": data_hash,
                    "reason_codes": list(reason_codes),
                }
            )
            return ShadowDecisionEvidence.create(
                evidence_version="1",
                decision_time=decision_time,
                symbol=symbol,
                timeframe=timeframe,
                strategy_id=strategy_id,
                strategy_version=strategy_version,
                feature_records=(),
                signal=None,
                risk_outcome="rejected",
                reason_codes=_unique_codes((*reason_codes, Ase00Reason.SHADOW_ONLY)),
                data_hash=data_hash,
                config_hash=config_hash,
                code_hash=self.code_hash,
                idempotency_key=idempotency_key,
                provenance=Provenance(
                    producer="ase00-shadow-engine",
                    source_event_id=idempotency_key,
                    lineage=(),
                    details={
                        "lineage_complete": True,
                        "future_shift": 0,
                        "execution_adapter_used": False,
                        "fail_closed": True,
                    },
                ),
                no_order_submitted=True,
            )
    
    
    def _payload_number(payload: Mapping[str, JsonValue], key: str) -> float:
        value = payload.get(key)
        if not isinstance(value, (int, float)) or isinstance(value, bool):
            raise Ase00FailClosed(
                Ase00Reason.MARKET_BAR_INVALID,
                f"payload field {key} must be numeric",
            )
        return _finite_float(value, key)
    
    
    def _finite_float(value: object, label: str) -> float:
        if not isinstance(value, (int, float)) or isinstance(value, bool):
            raise Ase00FailClosed(
                Ase00Reason.MISSING_REQUIRED_DATA,
                f"{label} is not numeric",
            )
        converted = float(value)
        if not math.isfinite(converted):
            raise Ase00FailClosed(
                Ase00Reason.MISSING_REQUIRED_DATA,
                f"{label} is not finite",
            )
        return converted
    
    
    def _require_utc(value: datetime, label: str) -> None:
        if value.tzinfo is None or value.utcoffset() != UTC.utcoffset(value):
            raise ValueError(f"{label} must be normalized to UTC")
    
    
    def _require_sha256(value: str, label: str) -> None:
        if len(value) != 64 or any(char not in "0123456789abcdef" for char in value):
            raise ValueError(f"{label} must be a lowercase SHA-256")
    
    
    def _document_string(document: Mapping[str, object], key: str, default: str) -> str:
        value = document.get(key)
        return value if isinstance(value, str) and value else default
    
    
    def _safe_config_hash(strategy_document: Mapping[str, object]) -> str:
        try:
            return canonical_sha256(cast(dict[str, object], dict(strategy_document)))
        except (TypeError, ValueError):
            return canonical_sha256({"unserializable_strategy": True})
    
    
    def _unique_codes(codes: Sequence[str]) -> tuple[str, ...]:
        return tuple(dict.fromkeys(codes))
=================== 1 failed, 11 passed, 2 warnings in 1.36s ===================

```
