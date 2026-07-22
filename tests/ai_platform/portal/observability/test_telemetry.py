from __future__ import annotations

import json
from collections.abc import Mapping
from typing import Any
from uuid import uuid4

import pytest

from ai_platform.portal.contracts.environment import Environment
from ai_platform.portal.observability.redaction import REDACTED
from ai_platform.portal.observability.telemetry import TelemetryContext, TelemetryRecorder


class _LogSink:
    def __init__(self) -> None:
        self.records: list[dict[str, Any]] = []

    def emit(self, record: Mapping[str, Any]) -> None:
        self.records.append(dict(record))


class _MetricsSink:
    def __init__(self) -> None:
        self.increments: list[tuple[str, int, dict[str, Any]]] = []
        self.observations: list[tuple[str, float, dict[str, Any]]] = []

    def increment(
        self,
        name: str,
        value: int,
        attributes: Mapping[str, Any],
    ) -> None:
        self.increments.append((name, value, dict(attributes)))

    def observe(
        self,
        name: str,
        value: float,
        attributes: Mapping[str, Any],
    ) -> None:
        self.observations.append((name, value, dict(attributes)))


class _Span:
    def __init__(self, attributes: Mapping[str, Any]) -> None:
        self._trace_id = "trace-1"
        self._span_id = "span-1"
        self.attributes = dict(attributes)
        self.errors: list[str] = []
        self.ended = False

    @property
    def trace_id(self) -> str:
        return self._trace_id

    @property
    def span_id(self) -> str:
        return self._span_id

    def set_attribute(self, key: str, value: Any) -> None:
        self.attributes[key] = value

    def record_error(self, error_type: str) -> None:
        self.errors.append(error_type)

    def end(self) -> None:
        self.ended = True


class _TraceSink:
    def __init__(self) -> None:
        self.spans: list[tuple[str, _Span]] = []

    def start_span(self, name: str, attributes: Mapping[str, Any]) -> _Span:
        span = _Span(attributes)
        self.spans.append((name, span))
        return span


def _context() -> TelemetryContext:
    return TelemetryContext(
        service="portal-events",
        component="outbox-publisher",
        environment=Environment.TEST,
        request_id=uuid4(),
        correlation_id=uuid4(),
        causation_id=uuid4(),
        tenant_id="tenant-a",
        actor_type="service",
        resource_type="event",
        resource_id="event-1",
    )


def _recorder() -> tuple[TelemetryRecorder, _LogSink, _MetricsSink, _TraceSink]:
    logs = _LogSink()
    metrics = _MetricsSink()
    traces = _TraceSink()
    return TelemetryRecorder(logs, metrics, traces), logs, metrics, traces


def test_operation_propagates_correlation_and_redacts_all_sink_attributes() -> None:
    recorder, logs, metrics, traces = _recorder()
    context = _context()

    with recorder.operation(
        "outbox.publish",
        context,
        {
            "api_key": "key-value",
            "nested": {"client_secret": "secret-value"},
        },
    ):
        pass

    assert len(traces.spans) == 1
    name, span = traces.spans[0]
    assert name == "outbox.publish"
    assert span.ended is True
    assert span.attributes["correlation_id"] == str(context.correlation_id)
    assert span.attributes["request_id"] == str(context.request_id)
    assert span.attributes["api_key"] == REDACTED
    assert span.attributes["nested"]["client_secret"] == REDACTED

    assert [record["event"] for record in logs.records] == [
        "outbox.publish.started",
        "outbox.publish.succeeded",
    ]
    assert all(record["correlation_id"] == str(context.correlation_id) for record in logs.records)
    assert all(record["trace_id"] == "trace-1" for record in logs.records)
    assert all(record["span_id"] == "span-1" for record in logs.records)
    assert all(record["fields"]["api_key"] == REDACTED for record in logs.records)

    all_metric_attributes = [item[2] for item in metrics.increments + metrics.observations]
    assert all(
        item["correlation_id"] == str(context.correlation_id)
        for item in all_metric_attributes
    )
    assert all(item["api_key"] == REDACTED for item in all_metric_attributes)


def test_failure_records_exception_type_but_never_exception_message() -> None:
    recorder, logs, metrics, traces = _recorder()
    context = _context()

    with pytest.raises(RuntimeError, match="super-secret-message"):
        with recorder.operation(
            "consumer.handle",
            context,
            {"access_token": "token-value"},
        ):
            raise RuntimeError("super-secret-message")

    serialized = json.dumps(
        {
            "logs": logs.records,
            "increments": metrics.increments,
            "observations": metrics.observations,
            "spans": [span.attributes for _name, span in traces.spans],
            "errors": [span.errors for _name, span in traces.spans],
        },
        default=str,
    )
    assert "super-secret-message" not in serialized
    assert "token-value" not in serialized
    assert "RuntimeError" in serialized
    assert logs.records[-1]["reason_code"] == "RuntimeError"
    assert traces.spans[0][1].errors == ["RuntimeError"]
    assert traces.spans[0][1].ended is True


def test_structured_log_redacts_fields_without_trace_span() -> None:
    recorder, logs, _metrics, _traces = _recorder()
    context = _context()

    recorder.log(
        "WARN",
        "auth.rejected",
        "DENIED",
        context,
        fields={"Authorization": "Bearer secret", "safe": "visible"},
        reason_code="AUTH_DENIED",
    )

    assert logs.records[0]["fields"] == {
        "Authorization": REDACTED,
        "safe": "visible",
    }
    assert logs.records[0]["trace_id"] is None
    assert logs.records[0]["span_id"] is None
