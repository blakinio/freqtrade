from __future__ import annotations

import math
import os
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import Literal, cast

import pandas as pd
from pydantic import JsonValue
from strategy_engine.domain.models import (
    Action,
    FeatureRecord,
    FeatureReference,
    Provenance,
    ShadowDecisionEvidence,
    Side,
    SignalEvent,
    StrategyDefinition,
    canonical_sha256,
)
from strategy_engine.dsl.evaluator import (
    DslEvaluationError,
    EvaluationSnapshot,
    StrategyEvaluator,
)
from strategy_engine.dsl.validator import StrategyValidationError, StrategyValidator
from strategy_engine.features.pivots import confirmed_pivots
from strategy_engine.features.records import make_confirmed_pivot_record, make_feature_record
from strategy_engine.features.squeeze import squeeze_features
from strategy_engine.features.supertrend import supertrend_features
from strategy_engine.registry import FeatureRegistry, SearchSpaceRegistry
from strategy_engine.validation.leakage import (
    LeakageContext,
    LeakageError,
    assert_features_available,
)

from ai_platform.portal.contracts.risk import RiskDecisionOutcome
from ai_platform.portal.risk.schema import RiskEvaluationSnapshot, RiskPolicyLimits
from ai_platform.portal.risk.service import RiskService


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
        _require_sha256(self.source_data_version, "source_data_version")

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
    """Deterministic ASE-00 shadow slice using the existing Portal Risk Core."""

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
            records, current, previous, event_snapshot = self._features(
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
                    features=current,
                    previous_features=previous,
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
            evidence = self._evidence(
                decision_time=decision_time,
                symbol=symbol,
                timeframe=timeframe,
                strategy=strategy,
                records=records,
                signal=signal,
                risk_outcome=risk_outcome,
                reason_codes=_unique_codes(
                    (
                        *normalized.reason_codes,
                        *dsl_decision.reason_codes,
                        *risk_reason_codes,
                        Ase00Reason.SHADOW_ONLY,
                    )
                ),
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
        except DslEvaluationError as exc:
            evidence = self._rejected_evidence(
                decision_time=decision_time,
                symbol=symbol,
                timeframe=timeframe,
                strategy_id=strategy_id,
                strategy_version=strategy_version,
                data_hash=raw_data_hash,
                config_hash=_safe_config_hash(strategy_document),
                reason_codes=(Ase00Reason.STRATEGY_REJECTED, type(exc).__name__),
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
                    "EVIDENCE_CONFLICT",
                    "existing evidence is not a valid ASE record",
                ) from exc
            if existing_evidence.idempotency_key == evidence.idempotency_key:
                raise Ase00FailClosed(
                    "EVIDENCE_CONFLICT",
                    "same idempotency key maps to different evidence",
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
        by_key: dict[str, AcceptedSyntheticEvent] = {}
        hashes: dict[str, str] = {}
        duplicate_count = 0
        delayed_count = 0
        for event in events:
            event_hash = canonical_sha256(event.canonical_payload())
            prior_hash = hashes.get(event.idempotency_key)
            if prior_hash is not None:
                if prior_hash != event_hash:
                    raise Ase00FailClosed(
                        Ase00Reason.CONFLICTING_DUPLICATE_EVENT,
                        f"conflicting duplicate event: {event.idempotency_key}",
                    )
                duplicate_count += 1
                continue
            hashes[event.idempotency_key] = event_hash
            by_key[event.idempotency_key] = event
            if event.available_at - event.detected_at > self.processing_delay_threshold:
                delayed_count += 1
        normalized = tuple(sorted(by_key.values(), key=self._event_sort_key))
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
                "events must resolve to one symbol and one market timeframe",
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
        frame = self._market_frame(market_events)
        latest_market = market_events[-1]
        configured = {feature.id: feature for feature in strategy.features}
        records: list[FeatureRecord] = []
        current: dict[str, JsonValue | Mapping[str, JsonValue]] = {}
        previous: dict[str, JsonValue | Mapping[str, JsonValue]] = {}
        event_snapshot: dict[str, JsonValue] = {}

        squeeze_ref = configured.get("squeeze_ratio.v1")
        if squeeze_ref is not None:
            squeeze = squeeze_features(frame, **squeeze_ref.params)
            squeeze_columns = (
                "squeeze_ratio",
                "squeeze_state",
                "squeeze_duration",
                "bars_since_release",
                "linreg_momentum",
                "momentum_slope",
                "momentum_acceleration",
            )
            value = _row_mapping(squeeze, -1, squeeze_columns)
            record = self._market_feature_record(
                reference=squeeze_ref,
                event=latest_market,
                value=value,
                data_hash=normalized.data_hash,
                config_hash=config_hash,
            )
            records.append(record)
            current[squeeze_ref.id] = value
            previous[squeeze_ref.id] = _row_mapping(squeeze, -2, squeeze_columns)

        supertrend_ref = configured.get("supertrend_direction.v1")
        if supertrend_ref is not None:
            supertrend = supertrend_features(frame, **supertrend_ref.params)
            supertrend_columns = (
                "supertrend_band",
                "supertrend_direction",
                "supertrend_flip",
                "supertrend_distance_atr",
            )
            value = _row_mapping(supertrend, -1, supertrend_columns)
            value["direction"] = value["supertrend_direction"]
            prior = _row_mapping(supertrend, -2, supertrend_columns)
            prior["direction"] = prior["supertrend_direction"]
            record = self._market_feature_record(
                reference=supertrend_ref,
                event=latest_market,
                value=value,
                data_hash=normalized.data_hash,
                config_hash=config_hash,
            )
            records.append(record)
            current[supertrend_ref.id] = value
            previous[supertrend_ref.id] = prior
            event_snapshot["supertrend_flip"] = _supertrend_flip_event(value)

        pivot_ref = configured.get("confirmed_pivot.v1")
        if pivot_ref is not None:
            pivot_params = dict(pivot_ref.params)
            latency = _numeric_parameter(
                pivot_params,
                "processing_latency_seconds",
                default=0.0,
            )
            pivots = confirmed_pivots(
                frame,
                left_bars=cast(int, pivot_params["left_bars"]),
                right_bars=cast(int, pivot_params["right_bars"]),
                processing_latency=pd.to_timedelta(latency, unit="s"),
            )
            eligible = [pivot for pivot in pivots if pivot.available_at <= decision_time]
            if not eligible:
                raise Ase00FailClosed(
                    Ase00Reason.MISSING_REQUIRED_DATA,
                    "no confirmed pivot is available at decision time",
                )
            pivot = eligible[-1]
            detection_event = market_events[pivot.detected_index]
            record = make_confirmed_pivot_record(
                symbol=latest_market.symbol,
                timeframe=pivot_ref.timeframe,
                pivot=pivot,
                decision_time=decision_time,
                idempotency_key=(
                    f"feature:{pivot_ref.id}:{latest_market.symbol}:"
                    f"{pivot.available_at.isoformat()}"
                ),
                data_version=normalized.data_hash,
                code_version=self.code_hash,
                configuration_hash=config_hash,
                producer="ase00-feature-engine",
                source_event_id=detection_event.event_id,
                parameters=cast(dict[str, JsonValue], pivot_params),
                detection_event_confirmed=detection_event.is_confirmed,
            )
            records.append(record)
            pivot_value = cast(Mapping[str, JsonValue], record.value)
            current[pivot_ref.id] = pivot_value
            previous[pivot_ref.id] = pivot_value

        event_snapshot.update(self._liquidation_snapshot(normalized.events, decision_time))
        liquidation_ref = configured.get("liquidation_notional_z.v1")
        if liquidation_ref is not None:
            liquidations = [
                event
                for event in normalized.events
                if event.kind == "liquidation" and event.available_at <= decision_time
            ]
            latest_liquidation = liquidations[-1]
            liquidation_value: dict[str, JsonValue] = {
                "notional_z": event_snapshot["liquidation_notional_z"],
                "liquidation_burst": event_snapshot["liquidation_burst"],
            }
            record = make_feature_record(
                feature_id=liquidation_ref.id,
                symbol=latest_liquidation.symbol,
                timeframe=liquidation_ref.timeframe,
                event_time=latest_liquidation.event_time,
                detected_at=latest_liquidation.detected_at,
                available_at=latest_liquidation.available_at,
                value=liquidation_value,
                source=latest_liquidation.source,
                is_confirmed=latest_liquidation.is_confirmed,
                idempotency_key=(
                    f"feature:{liquidation_ref.id}:{latest_liquidation.symbol}:"
                    f"{latest_liquidation.available_at.isoformat()}"
                ),
                code_version=self.code_hash,
                data_version=normalized.data_hash,
                configuration_hash=config_hash,
                producer="ase00-feature-engine",
                source_event_id=latest_liquidation.event_id,
                parameters=dict(liquidation_ref.params),
            )
            records.append(record)
            current[liquidation_ref.id] = liquidation_value
            previous[liquidation_ref.id] = liquidation_value

        return (
            tuple(sorted(records, key=lambda item: item.feature_id)),
            current,
            previous,
            event_snapshot,
        )

    def _market_feature_record(
        self,
        *,
        reference: FeatureReference,
        event: AcceptedSyntheticEvent,
        value: dict[str, JsonValue],
        data_hash: str,
        config_hash: str,
    ) -> FeatureRecord:
        feature_id = reference.id
        timeframe = reference.timeframe
        parameters = dict(reference.params)
        return make_feature_record(
            feature_id=feature_id,
            symbol=event.symbol,
            timeframe=timeframe,
            event_time=event.event_time,
            detected_at=event.detected_at,
            available_at=event.available_at,
            value=value,
            source=event.source,
            is_confirmed=event.is_confirmed,
            idempotency_key=(
                f"feature:{feature_id}:{event.symbol}:{event.available_at.isoformat()}"
            ),
            code_version=self.code_hash,
            data_version=data_hash,
            configuration_hash=config_hash,
            producer="ase00-feature-engine",
            source_event_id=event.event_id,
            parameters=parameters,
        )

    @staticmethod
    def _market_frame(events: tuple[AcceptedSyntheticEvent, ...]) -> pd.DataFrame:
        rows: list[dict[str, float]] = []
        times: list[datetime] = []
        seen_times: set[datetime] = set()
        for event in events:
            if event.event_time in seen_times:
                raise Ase00FailClosed(
                    Ase00Reason.DUPLICATE_MARKET_TIMESTAMP,
                    f"duplicate market timestamp: {event.event_time.isoformat()}",
                )
            seen_times.add(event.event_time)
            values: dict[str, float] = {}
            for name in ("open", "high", "low", "close", "volume"):
                value = event.payload.get(name)
                if not isinstance(value, (int, float)) or isinstance(value, bool):
                    raise Ase00FailClosed(
                        Ase00Reason.MARKET_BAR_INVALID,
                        f"market event {event.event_id} has invalid {name}",
                    )
                number = float(value)
                if not math.isfinite(number) or number < 0:
                    raise Ase00FailClosed(
                        Ase00Reason.MARKET_BAR_INVALID,
                        f"market event {event.event_id} has invalid {name}",
                    )
                values[name] = number
            if values["high"] < max(
                values["open"],
                values["close"],
                values["low"],
            ):
                raise Ase00FailClosed(
                    Ase00Reason.MARKET_BAR_INVALID,
                    f"market event {event.event_id} has inconsistent high",
                )
            if values["low"] > min(
                values["open"],
                values["close"],
                values["high"],
            ):
                raise Ase00FailClosed(
                    Ase00Reason.MARKET_BAR_INVALID,
                    f"market event {event.event_id} has inconsistent low",
                )
            rows.append(values)
            times.append(event.event_time)
        frame = pd.DataFrame(rows, index=pd.DatetimeIndex(times))
        return frame.sort_index() if not frame.index.is_monotonic_increasing else frame

    @staticmethod
    def _liquidation_snapshot(
        events: tuple[AcceptedSyntheticEvent, ...],
        decision_time: datetime,
    ) -> dict[str, JsonValue]:
        liquidations = [
            event
            for event in events
            if event.kind == "liquidation" and event.available_at <= decision_time
        ]
        if not liquidations:
            raise Ase00FailClosed(
                Ase00Reason.MISSING_REQUIRED_DATA,
                "no point-in-time liquidation event is available",
            )
        latest = liquidations[-1]
        notional_z = latest.payload.get("notional_z")
        if not isinstance(notional_z, (int, float)) or isinstance(notional_z, bool):
            raise Ase00FailClosed(
                Ase00Reason.MISSING_REQUIRED_DATA,
                "liquidation event requires numeric notional_z",
            )
        normalized_z = float(notional_z)
        if not math.isfinite(normalized_z):
            raise Ase00FailClosed(
                Ase00Reason.MISSING_REQUIRED_DATA,
                "liquidation notional_z must be finite",
            )
        return {
            "liquidation_burst": normalized_z >= 1.0,
            "liquidation_notional_z": normalized_z,
        }

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
        lineage = tuple(record.idempotency_key for record in records)
        feature_snapshot = {record.feature_id: record.value for record in records}
        signal_id = canonical_sha256(
            {
                "strategy_id": strategy.strategy_id,
                "strategy_version": strategy.version,
                "decision_time": decision_time.isoformat(),
                "lineage": list(lineage),
            }
        )
        return SignalEvent(
            signal_id=signal_id,
            signal_version="1",
            strategy_id=strategy.strategy_id,
            strategy_version=strategy.version,
            symbol=records[0].symbol,
            timeframe=records[0].timeframe,
            side=dsl_side,
            action=dsl_action,
            event_time=decision_time,
            detected_at=decision_time,
            available_at=decision_time,
            source="ase00-strategy-evaluator",
            is_confirmed=True,
            idempotency_key=f"signal:{strategy.strategy_id}:{decision_time.isoformat()}",
            code_version=self.code_hash,
            data_version=data_hash,
            configuration_hash=config_hash,
            confidence=_confidence(records),
            reason_codes=dsl_reason_codes,
            feature_snapshot=feature_snapshot,
            provenance=Provenance(
                producer="ase00-strategy-evaluator",
                source_event_id=canonical_sha256(list(lineage)),
                lineage=lineage,
                details={
                    "lineage_complete": True,
                    "future_shift": 0,
                    "reason_codes": list(dsl_reason_codes),
                },
            ),
            execution_policy=dict(strategy.execution),
        )

    @staticmethod
    def _risk_decision(
        *,
        signal: SignalEvent | None,
        risk_limits: RiskPolicyLimits,
        risk_snapshot: RiskEvaluationSnapshot,
    ) -> tuple[str, tuple[str, ...]]:
        if signal is None:
            return "no_signal", ("NO_ENTRY_SIGNAL",)
        outcome, reason_codes, evaluations = RiskService._evaluate(
            risk_limits,
            risk_snapshot,
            kill_switch_active=False,
        )
        if outcome is RiskDecisionOutcome.REJECTED:
            return "rejected", tuple(reason_codes)
        if any(not evaluation.passed for evaluation in evaluations):
            raise Ase00FailClosed(
                "RISK_EVIDENCE_INCONSISTENT",
                "risk evidence is inconsistent",
            )
        return "approved", tuple(reason_codes)

    def _evidence(
        self,
        *,
        decision_time: datetime,
        symbol: str,
        timeframe: str,
        strategy: StrategyDefinition,
        records: tuple[FeatureRecord, ...],
        signal: SignalEvent | None,
        risk_outcome: str,
        reason_codes: tuple[str, ...],
        data_hash: str,
        config_hash: str,
    ) -> ShadowDecisionEvidence:
        lineage = tuple(record.idempotency_key for record in records)
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
            idempotency_key=f"ase00:{strategy.strategy_id}:{symbol}:{decision_time.isoformat()}",
            provenance=Provenance(
                producer="ase00-shadow-engine",
                source_event_id=canonical_sha256(list(lineage)),
                lineage=lineage,
                details={
                    "lineage_complete": True,
                    "future_shift": 0,
                    "risk_core": "ai_platform.portal.risk.service.RiskService._evaluate",
                    "shadow_only": True,
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
            idempotency_key=(f"ase00-rejected:{strategy_id}:{symbol}:{decision_time.isoformat()}"),
            provenance=Provenance(
                producer="ase00-shadow-engine",
                source_event_id=canonical_sha256(
                    {
                        "strategy_id": strategy_id,
                        "symbol": symbol,
                        "decision_time": decision_time.isoformat(),
                        "reason_codes": list(reason_codes),
                    }
                ),
                details={
                    "lineage_complete": True,
                    "future_shift": 0,
                    "shadow_only": True,
                    "execution_adapter_used": False,
                },
            ),
            no_order_submitted=True,
        )


def _supertrend_flip_event(value: Mapping[str, JsonValue]) -> str:
    if value.get("supertrend_flip") is not True:
        return "none"
    direction = value.get("direction")
    if direction == 1:
        return "up"
    if direction == -1:
        return "down"
    return "none"


def _confidence(records: tuple[FeatureRecord, ...]) -> float:
    strengths: list[float] = []
    for record in records:
        value = record.value
        if not isinstance(value, Mapping):
            continue
        if record.feature_id == "squeeze_ratio.v1":
            ratio = value.get("squeeze_ratio")
            if isinstance(ratio, (int, float)) and not isinstance(ratio, bool):
                strengths.append(max(0.0, min(1.0, float(ratio) / 2.0)))
        elif record.feature_id == "supertrend_direction.v1":
            if value.get("direction") in (-1, 1):
                strengths.append(1.0)
        elif record.feature_id == "confirmed_pivot.v1":
            strengths.append(1.0 if record.is_confirmed else 0.0)
        elif record.feature_id == "liquidation_notional_z.v1":
            notional_z = value.get("notional_z")
            if isinstance(notional_z, (int, float)) and not isinstance(notional_z, bool):
                strengths.append(max(0.0, min(1.0, abs(float(notional_z)) / 5.0)))
    return sum(strengths) / len(strengths) if strengths else 0.0


def _row_mapping(
    frame: pd.DataFrame,
    position: int,
    columns: tuple[str, ...],
) -> dict[str, JsonValue]:
    if len(frame) < abs(position):
        return {column: None for column in columns}
    return {column: _json_scalar(frame[column].iloc[position]) for column in columns}


def _json_scalar(value: object) -> JsonValue:
    if pd.isna(value):
        return None
    if isinstance(value, bool):
        return value
    if isinstance(value, int):
        return int(value)
    if isinstance(value, float):
        return float(value) if math.isfinite(value) else None
    if hasattr(value, "item"):
        return _json_scalar(value.item())
    return str(value)


def _numeric_parameter(
    parameters: Mapping[str, JsonValue],
    name: str,
    *,
    default: float,
) -> float:
    value = parameters.get(name, default)
    if not isinstance(value, (int, float)) or isinstance(value, bool):
        raise Ase00FailClosed(
            Ase00Reason.STRATEGY_REJECTED,
            f"{name} must be numeric",
        )
    result = float(value)
    if not math.isfinite(result) or result < 0:
        raise Ase00FailClosed(
            Ase00Reason.STRATEGY_REJECTED,
            f"{name} must be finite and non-negative",
        )
    return result


def _safe_config_hash(document: Mapping[str, object]) -> str:
    return canonical_sha256(document)


def _document_string(document: Mapping[str, object], key: str, default: str) -> str:
    value = document.get(key)
    return value if isinstance(value, str) else default


def _unique_codes(codes: Sequence[str]) -> tuple[str, ...]:
    return tuple(dict.fromkeys(codes))


def _require_utc(value: datetime, name: str) -> None:
    if value.tzinfo is None or value.utcoffset() != timedelta(0):
        raise ValueError(f"{name} must be UTC-aware")


def _require_sha256(value: str, name: str) -> None:
    if len(value) != 64 or any(char not in "0123456789abcdef" for char in value):
        raise ValueError(f"{name} must be a lowercase SHA-256")
