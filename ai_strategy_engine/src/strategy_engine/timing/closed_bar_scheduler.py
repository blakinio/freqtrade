from __future__ import annotations

import hashlib
import json
from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from enum import StrEnum


class ClosedBarErrorCode(StrEnum):
    INVALID_CONFIGURATION = "INVALID_CONFIGURATION"
    INVALID_OBSERVATION = "INVALID_OBSERVATION"
    NAIVE_TIMESTAMP = "NAIVE_TIMESTAMP"
    NON_UTC_TIMESTAMP = "NON_UTC_TIMESTAMP"
    UNKNOWN_TIMEFRAME = "UNKNOWN_TIMEFRAME"
    TIMESTAMP_ORDER = "TIMESTAMP_ORDER"
    UNCONFIRMED_BAR = "UNCONFIRMED_BAR"
    AVAILABLE_AFTER_DECISION = "AVAILABLE_AFTER_DECISION"
    CONFLICTING_DUPLICATE = "CONFLICTING_DUPLICATE"
    OUT_OF_ORDER_BAR = "OUT_OF_ORDER_BAR"


class ClosedBarError(ValueError):
    def __init__(self, code: ClosedBarErrorCode, message: str) -> None:
        super().__init__(message)
        self.code = code


@dataclass(frozen=True, slots=True)
class ClosedBarObservation:
    source_event_id: str
    symbol: str
    timeframe: str
    event_time: datetime
    detected_at: datetime
    decision_time: datetime
    is_closed: bool


@dataclass(frozen=True, slots=True)
class ScheduledClosedBar:
    source_event_id: str
    symbol: str
    timeframe: str
    event_time: datetime
    close_time: datetime
    confirmation_time: datetime
    detected_at: datetime
    available_at: datetime
    decision_time: datetime

    def canonical_payload(self) -> dict[str, str]:
        return {
            "available_at": self.available_at.isoformat(),
            "close_time": self.close_time.isoformat(),
            "confirmation_time": self.confirmation_time.isoformat(),
            "decision_time": self.decision_time.isoformat(),
            "detected_at": self.detected_at.isoformat(),
            "event_time": self.event_time.isoformat(),
            "source_event_id": self.source_event_id,
            "symbol": self.symbol,
            "timeframe": self.timeframe,
        }


BarKey = tuple[str, str, datetime]
StreamKey = tuple[str, str]


class ClosedBarScheduler:
    def __init__(
        self,
        *,
        timeframe_durations: Mapping[str, timedelta],
        confirmation_delays: Mapping[str, timedelta] | None = None,
    ) -> None:
        delays = dict(confirmation_delays or {})
        unknown_delays = set(delays).difference(timeframe_durations)
        if unknown_delays:
            unknown = ", ".join(sorted(unknown_delays))
            raise ClosedBarError(
                ClosedBarErrorCode.INVALID_CONFIGURATION,
                f"confirmation delay configured for unknown timeframe(s): {unknown}",
            )
        if not timeframe_durations:
            raise ClosedBarError(
                ClosedBarErrorCode.INVALID_CONFIGURATION,
                "at least one timeframe duration is required",
            )

        self._timeframe_durations: dict[str, timedelta] = {}
        self._confirmation_delays: dict[str, timedelta] = {}
        for timeframe in sorted(timeframe_durations):
            duration = timeframe_durations[timeframe]
            delay = delays.get(timeframe, timedelta(0))
            if not timeframe:
                raise ClosedBarError(
                    ClosedBarErrorCode.INVALID_CONFIGURATION,
                    "timeframe names cannot be empty",
                )
            if duration <= timedelta(0):
                raise ClosedBarError(
                    ClosedBarErrorCode.INVALID_CONFIGURATION,
                    f"timeframe duration must be positive: {timeframe}",
                )
            if delay < timedelta(0):
                raise ClosedBarError(
                    ClosedBarErrorCode.INVALID_CONFIGURATION,
                    f"confirmation delay cannot be negative: {timeframe}",
                )
            self._timeframe_durations[timeframe] = duration
            self._confirmation_delays[timeframe] = delay

        self._records: list[ScheduledClosedBar] = []
        self._records_by_key: dict[BarKey, ScheduledClosedBar] = {}
        self._last_event_time_by_stream: dict[StreamKey, datetime] = {}

    @property
    def records(self) -> tuple[ScheduledClosedBar, ...]:
        return tuple(self._records)

    @property
    def canonical_sha256(self) -> str:
        return canonical_schedule_sha256(self._records)

    def ingest(self, observation: ClosedBarObservation) -> ScheduledClosedBar:
        self._validate_observation_text(observation)
        event_time = _require_utc("event_time", observation.event_time)
        detected_at = _require_utc("detected_at", observation.detected_at)
        decision_time = _require_utc("decision_time", observation.decision_time)

        duration = self._timeframe_durations.get(observation.timeframe)
        if duration is None:
            raise ClosedBarError(
                ClosedBarErrorCode.UNKNOWN_TIMEFRAME,
                f"unknown timeframe: {observation.timeframe}",
            )
        if detected_at < event_time:
            raise ClosedBarError(
                ClosedBarErrorCode.TIMESTAMP_ORDER,
                "detected_at cannot precede event_time",
            )
        if not observation.is_closed:
            raise ClosedBarError(
                ClosedBarErrorCode.UNCONFIRMED_BAR,
                "bar must be explicitly closed before scheduling",
            )

        close_time = event_time + duration
        if detected_at < close_time:
            raise ClosedBarError(
                ClosedBarErrorCode.UNCONFIRMED_BAR,
                "bar cannot be detected as closed before its close time",
            )
        confirmation_time = close_time + self._confirmation_delays[observation.timeframe]
        available_at = max(detected_at, confirmation_time)
        if available_at > decision_time:
            raise ClosedBarError(
                ClosedBarErrorCode.AVAILABLE_AFTER_DECISION,
                f"bar is available at {available_at.isoformat()} after decision_time "
                f"{decision_time.isoformat()}",
            )

        key = (observation.symbol, observation.timeframe, event_time)
        existing = self._records_by_key.get(key)
        if existing is not None:
            if existing.source_event_id != observation.source_event_id:
                raise ClosedBarError(
                    ClosedBarErrorCode.CONFLICTING_DUPLICATE,
                    "the same bar identity was observed with a different source_event_id",
                )
            return existing

        stream = (observation.symbol, observation.timeframe)
        last_event_time = self._last_event_time_by_stream.get(stream)
        if last_event_time is not None and event_time < last_event_time:
            raise ClosedBarError(
                ClosedBarErrorCode.OUT_OF_ORDER_BAR,
                "a late bar cannot be inserted before already emitted history",
            )

        scheduled = ScheduledClosedBar(
            source_event_id=observation.source_event_id,
            symbol=observation.symbol,
            timeframe=observation.timeframe,
            event_time=event_time,
            close_time=close_time,
            confirmation_time=confirmation_time,
            detected_at=detected_at,
            available_at=available_at,
            decision_time=decision_time,
        )
        self._records.append(scheduled)
        self._records_by_key[key] = scheduled
        self._last_event_time_by_stream[stream] = event_time
        return scheduled

    @staticmethod
    def _validate_observation_text(observation: ClosedBarObservation) -> None:
        fields = (
            ("source_event_id", observation.source_event_id),
            ("symbol", observation.symbol),
            ("timeframe", observation.timeframe),
        )
        for field_name, value in fields:
            if not value or value.strip() != value:
                raise ClosedBarError(
                    ClosedBarErrorCode.INVALID_OBSERVATION,
                    f"{field_name} must be a non-empty trimmed string",
                )


def replay_closed_bars(
    observations: Iterable[ClosedBarObservation],
    *,
    timeframe_durations: Mapping[str, timedelta],
    confirmation_delays: Mapping[str, timedelta] | None = None,
) -> tuple[ScheduledClosedBar, ...]:
    scheduler = ClosedBarScheduler(
        timeframe_durations=timeframe_durations,
        confirmation_delays=confirmation_delays,
    )
    for observation in observations:
        scheduler.ingest(observation)
    return scheduler.records


def canonical_schedule_sha256(records: Iterable[ScheduledClosedBar]) -> str:
    payload = [record.canonical_payload() for record in records]
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


def _require_utc(field_name: str, value: datetime) -> datetime:
    if value.tzinfo is None:
        raise ClosedBarError(
            ClosedBarErrorCode.NAIVE_TIMESTAMP,
            f"{field_name} must be timezone-aware",
        )
    if value.utcoffset() != UTC.utcoffset(value):
        raise ClosedBarError(
            ClosedBarErrorCode.NON_UTC_TIMESTAMP,
            f"{field_name} must be normalized to UTC",
        )
    return value
