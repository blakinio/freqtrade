from __future__ import annotations

from collections.abc import Iterator, Mapping
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import UTC, datetime
from time import monotonic
from typing import Any, Protocol
from uuid import UUID

from ai_platform.portal.contracts.environment import Environment
from ai_platform.portal.observability.redaction import redact_sensitive


class LogSink(Protocol):
    def emit(self, record: Mapping[str, Any]) -> None: ...


class MetricsSink(Protocol):
    def increment(
        self,
        name: str,
        value: int,
        attributes: Mapping[str, Any],
    ) -> None: ...

    def observe(
        self,
        name: str,
        value: float,
        attributes: Mapping[str, Any],
    ) -> None: ...


class Span(Protocol):
    @property
    def trace_id(self) -> str: ...

    @property
    def span_id(self) -> str: ...

    def set_attribute(self, key: str, value: Any) -> None: ...

    def record_error(self, error_type: str) -> None: ...

    def end(self) -> None: ...


class TraceSink(Protocol):
    def start_span(self, name: str, attributes: Mapping[str, Any]) -> Span: ...


@dataclass(frozen=True)
class TelemetryContext:
    service: str
    component: str
    environment: Environment
    request_id: UUID
    correlation_id: UUID
    causation_id: UUID | None = None
    tenant_id: str | None = None
    actor_type: str | None = None
    resource_type: str | None = None
    resource_id: str | None = None


class TelemetryRecorder:
    def __init__(
        self,
        log_sink: LogSink,
        metrics_sink: MetricsSink,
        trace_sink: TraceSink,
    ) -> None:
        self._log_sink = log_sink
        self._metrics_sink = metrics_sink
        self._trace_sink = trace_sink

    @contextmanager
    def operation(
        self,
        name: str,
        context: TelemetryContext,
        attributes: Mapping[str, Any] | None = None,
    ) -> Iterator[Span]:
        safe_attributes = self._operation_attributes(name, context, attributes)
        span = self._trace_sink.start_span(name, safe_attributes)
        started = monotonic()
        self._emit_log(
            level="INFO",
            event=f"{name}.started",
            result="STARTED",
            context=context,
            span=span,
            fields=safe_attributes,
        )
        self._metrics_sink.increment("portal.operation.started", 1, safe_attributes)
        try:
            yield span
        except Exception as exc:
            duration_ms = (monotonic() - started) * 1000
            error_type = type(exc).__name__
            span.record_error(error_type)
            self._metrics_sink.increment(
                "portal.operation.failed",
                1,
                {**safe_attributes, "error_type": error_type},
            )
            self._metrics_sink.observe(
                "portal.operation.duration_ms",
                duration_ms,
                {**safe_attributes, "result": "FAILED"},
            )
            self._emit_log(
                level="ERROR",
                event=f"{name}.failed",
                result="FAILED",
                reason_code=error_type,
                context=context,
                span=span,
                fields={**safe_attributes, "error_type": error_type},
            )
            raise
        else:
            duration_ms = (monotonic() - started) * 1000
            self._metrics_sink.increment("portal.operation.succeeded", 1, safe_attributes)
            self._metrics_sink.observe(
                "portal.operation.duration_ms",
                duration_ms,
                {**safe_attributes, "result": "SUCCEEDED"},
            )
            self._emit_log(
                level="INFO",
                event=f"{name}.succeeded",
                result="SUCCEEDED",
                context=context,
                span=span,
                fields=safe_attributes,
            )
        finally:
            span.end()

    def log(
        self,
        level: str,
        event: str,
        result: str,
        context: TelemetryContext,
        fields: Mapping[str, Any] | None = None,
        reason_code: str | None = None,
    ) -> None:
        self._emit_log(
            level=level,
            event=event,
            result=result,
            reason_code=reason_code,
            context=context,
            span=None,
            fields=fields or {},
        )

    def _emit_log(
        self,
        *,
        level: str,
        event: str,
        result: str,
        context: TelemetryContext,
        span: Span | None,
        fields: Mapping[str, Any],
        reason_code: str | None = None,
    ) -> None:
        record = {
            "timestamp": datetime.now(UTC).isoformat(),
            "level": level,
            "service": context.service,
            "component": context.component,
            "environment": context.environment.value,
            "request_id": str(context.request_id),
            "correlation_id": str(context.correlation_id),
            "causation_id": str(context.causation_id) if context.causation_id else None,
            "trace_id": span.trace_id if span is not None else None,
            "span_id": span.span_id if span is not None else None,
            "tenant_id": context.tenant_id,
            "actor_type": context.actor_type,
            "resource_type": context.resource_type,
            "resource_id": context.resource_id,
            "event": event,
            "result": result,
            "reason_code": reason_code,
            "fields": redact_sensitive(dict(fields)),
        }
        self._log_sink.emit(record)

    @staticmethod
    def _operation_attributes(
        name: str,
        context: TelemetryContext,
        attributes: Mapping[str, Any] | None,
    ) -> dict[str, Any]:
        base = {
            "operation": name,
            "service": context.service,
            "component": context.component,
            "environment": context.environment.value,
            "request_id": str(context.request_id),
            "correlation_id": str(context.correlation_id),
            "causation_id": str(context.causation_id) if context.causation_id else None,
            "tenant_id": context.tenant_id,
            "actor_type": context.actor_type,
            "resource_type": context.resource_type,
            "resource_id": context.resource_id,
        }
        if attributes:
            base.update(attributes)
        return redact_sensitive(base)
