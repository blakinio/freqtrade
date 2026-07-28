from __future__ import annotations

import json
import math
import os
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, replace
from datetime import datetime, timedelta, timezone
from decimal import Decimal
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
                (*normalized.reason_codes, *dsl_decision.reason_codes, *risk_reason_codes, Ase00Reason.SHADOW_ONLY)
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
            "liquidation_notional_z.v1": cast(
                Mapping[str, JsonValue], liquidation_record.value
            ),
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
                raise Ase00FailClosed(
                    Ase00Reason.MARKET_BAR_INVALID, "volume cannot be negative"
                )
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
    if value.tzinfo is None or value.utcoffset() != timezone.utc.utcoffset(value):
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
