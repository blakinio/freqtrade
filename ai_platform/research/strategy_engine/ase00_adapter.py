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
    """Synthetic ASE-00 vertical slice using only the existing Portal Risk Core.

    This provider has no order-submission, runtime-management, or private trading-engine dependency.
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
                "events must resolve to exactly one symbol and market timeframe",
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
            record = make_feature_record(
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
            records.append(record)
            current_snapshot[squeeze_ref.id] = value
            previous_snapshot[squeeze_ref.id] = _row_mapping(
                squeeze,
                -2,
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

        supertrend_ref = configured.get("supertrend_direction.v1")
        if supertrend_ref is not None:
            supertrend = supertrend_features(frame, **supertrend_ref.params)
            value = _row_mapping(
                supertrend,
                -1,
                (
                    "supertrend",
                    "supertrend_direction",
                    "supertrend_flip",
                    "supertrend_distance_atr",
                ),
            )
            record = make_feature_record(
                registry=self.registry,
                feature_id=supertrend_ref.id,
                symbol=latest_event.symbol,
                timeframe=supertrend_ref.timeframe,
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
                parameters=dict(supertrend_ref.params),
            )
            records.append(record)
            current_snapshot[supertrend_ref.id] = value
            previous_snapshot[supertrend_ref.id] = _row_mapping(
                supertrend,
                -2,
                (
                    "supertrend",
                    "supertrend_direction",
                    "supertrend_flip",
                    "supertrend_distance_atr",
                ),
            )

        pivot_ref = configured.get("confirmed_pivot.v1")
        if pivot_ref is not None:
            pivot_params = dict(pivot_ref.params)
            pivots = confirmed_pivots(
                frame,
                left_bars=cast(int, pivot_params["left_bars"]),
                right_bars=cast(int, pivot_params["right_bars"]),
                processing_latency=pd.to_timedelta(
                    cast(float, pivot_params["processing_latency_seconds"]), unit="s"
                ),
            )
            eligible = [pivot for pivot in pivots if pivot.available_at <= decision_time]
            pivot = eligible[-1] if eligible else _unavailable_pivot(frame, pivot_params)
            pivot_detected_event = market_events[pivot.detection_position]
            record = make_confirmed_pivot_record(
                registry=self.registry,
                feature_id=pivot_ref.id,
                symbol=latest_event.symbol,
                timeframe=pivot_ref.timeframe,
                pivot=pivot,
                decision_time=decision_time,
                source=pivot_detected_event.source,
                data_version=normalized.data_hash,
                code_version=self.code_hash,
                configuration_hash=config_hash,
                source_event_id=pivot_detected_event.event_id,
                parameters=cast(dict[str, JsonValue], pivot_params),
                detection_event_confirmed=pivot_detected_event.is_confirmed,
            )
            records.append(record)
            value = cast(Mapping[str, JsonValue], record.value)
            current_snapshot[pivot_ref.id] = value
            previous_snapshot[pivot_ref.id] = value

        event_snapshot = self._liquidation_snapshot(normalized.events, decision_time)
        return (
            tuple(sorted(records, key=lambda item: item.feature_id)),
            current_snapshot,
            previous_snapshot,
            event_snapshot,
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
            if values["high"] < max(values["open"], values["close"], values["low"]):
                raise Ase00FailClosed(
                    Ase00Reason.MARKET_BAR_INVALID,
                    f"market event {event.event_id} has inconsistent high",
                )
            if values["low"] > min(values["open"], values["close"], values["high"]):
                raise Ase00FailClosed(
                    Ase00Reason.MARKET_BAR_INVALID,
                    f"market event {event.event_id} has inconsistent low",
                )
            rows.append(values)
            times.append(event.event_time)
        frame = pd.DataFrame(rows, index=pd.DatetimeIndex(times))
        if not frame.index.is_monotonic_increasing:
            frame = frame.sort_index()
        return frame

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
        return {
            "liquidation_burst": bool(float(notional_z) >= 1.0),
            "liquidation_notional_z": float(notional_z),
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
        detected_at = max(record.available_at for record in records)
        confidence = _confidence(records)
        provenance = Provenance(
            producer="ase00-strategy-evaluator",
            source_event_id=canonical_sha256([record.idempotency_key for record in records]),
            parent_ids=tuple(record.idempotency_key for record in records),
            details={
                "lineage_complete": True,
                "future_shift": 0,
                "reason_codes": list(dsl_reason_codes),
            },
        )
        return SignalEvent(
            signal_version="1",
            strategy_id=strategy.strategy_id,
            strategy_version=strategy.version,
            symbol=records[0].symbol,
            timeframe=records[0].timeframe,
            event_time=decision_time,
            detected_at=detected_at,
            available_at=detected_at,
            side=dsl_side,
            action=dsl_action,
            confidence=confidence,
            source="ase00-strategy-evaluator",
            is_confirmed=True,
            idempotency_key=f"signal:{strategy.strategy_id}:{decision_time.isoformat()}",
            code_version=self.code_hash,
            data_version=data_hash,
            configuration_hash=config_hash,
            provenance=provenance,
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
        projected_open_positions = risk_snapshot.current_open_positions + 1
        service = object.__new__(RiskService)
        outcome, reason_codes, evaluations = service._evaluate(
            limits=risk_limits,
            snapshot=risk_snapshot,
            projected_open_positions=projected_open_positions,
        )
        risk_codes = tuple(
            reason.value for reason in reason_codes
        ) or ("RISK_APPROVED_NO_REJECTIONS",)
        if outcome is RiskDecisionOutcome.REJECTED:
            return "rejected", risk_codes
        if any(not evaluation.passed for evaluation in evaluations):
            raise Ase00FailClosed("RISK_EVIDENCE_INCONSISTENT", "risk evidence is inconsistent")
        return "approved_shadow_only", risk_codes

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
        provenance = Provenance(
            producer="ase00-shadow-engine",
            source_event_id=canonical_sha256([record.idempotency_key for record in records]),
            parent_ids=tuple(record.idempotency_key for record in records),
            details={
                "lineage_complete": True,
                "future_shift": 0,
                "risk_core": "ai_platform.portal.risk.service.RiskService._evaluate",
                "shadow_only": True,
            },
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
            idempotency_key=f"ase00:{strategy.strategy_id}:{symbol}:{decision_time.isoformat()}",
            provenance=provenance,
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
            idempotency_key=f"ase00-rejected:{strategy_id}:{symbol}:{decision_time.isoformat()}",
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
                details={"lineage_complete": True, "future_shift": 0, "shadow_only": True},
            ),
            no_order_submitted=True,
        )


def _unavailable_pivot(frame: pd.DataFrame, params: Mapping[str, JsonValue]) -> PivotEvent:
    right_bars = cast(int, params["right_bars"])
    processing_latency = pd.to_timedelta(
        cast(float, params["processing_latency_seconds"]), unit="s"
    )
    position = max(0, len(frame) - right_bars - 1)
    detection_position = min(len(frame) - 1, position + right_bars)
    event_time = cast(datetime, frame.index[position].to_pydatetime())
    detected_at = cast(datetime, frame.index[detection_position].to_pydatetime())
    return PivotEvent(
        kind="high",
        position=position,
        detection_position=detection_position,
        event_time=event_time,
        detected_at=detected_at,
        available_at=detected_at + processing_latency,
        price=float(frame["high"].iloc[position]),
        left_bars=cast(int, params["left_bars"]),
        right_bars=right_bars,
    )


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
            direction = value.get("supertrend_direction")
            if direction in (-1, 1):
                strengths.append(1.0)
        elif record.feature_id == "confirmed_pivot.v1":
            strengths.append(1.0 if record.is_confirmed else 0.0)
    if not strengths:
        return 0.0
    return sum(strengths) / len(strengths)


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
        if not math.isfinite(value):
            return None
        return float(value)
    if hasattr(value, "item"):
        return _json_scalar(value.item())
    return str(value)


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
