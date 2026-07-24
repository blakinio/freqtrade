from __future__ import annotations

import json
import re
from collections.abc import Callable, Mapping
from datetime import timedelta
from enum import StrEnum
from typing import Any, Protocol, Self
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode, urlsplit
from urllib.request import Request, urlopen
from uuid import UUID

from pydantic import Field, PositiveInt, model_validator

from ai_platform.portal.contracts.common import ContractModel, NonEmptyStr, UtcDateTime
from ai_platform.portal.contracts.environment import Environment
from ai_platform.portal.contracts.identity import Permission
from ai_platform.portal.control_plane.context import RequestContext
from ai_platform.portal.observability.redaction import redact_sensitive
from ai_platform.portal.security.authorization import require_permission


_MAX_QUERY_RANGE = timedelta(hours=24)
_MAX_RESULTS = 200
_LABEL_VALUE = re.compile(r"^[A-Za-z0-9_.:/-]+$")


class RuntimeObservabilityAvailability(StrEnum):
    AVAILABLE = "AVAILABLE"
    UNAVAILABLE = "UNAVAILABLE"


class RuntimeObservabilitySourceStatus(ContractModel):
    source_id: NonEmptyStr
    availability: RuntimeObservabilityAvailability
    checked_at: UtcDateTime
    reason_code: NonEmptyStr
    log_retention_days: PositiveInt
    trace_retention_days: PositiveInt
    metric_retention_days: PositiveInt
    trace_source: NonEmptyStr
    metric_source: NonEmptyStr
    runbook_path: NonEmptyStr


class RuntimeLogQuery(ContractModel):
    start_at: UtcDateTime
    end_at: UtcDateTime
    correlation_id: UUID | None = None
    runtime_id: NonEmptyStr | None = None
    bot_id: NonEmptyStr | None = None
    service: NonEmptyStr | None = None
    component: NonEmptyStr | None = None
    level: NonEmptyStr | None = None
    limit: int = Field(default=100, ge=1, le=_MAX_RESULTS)

    @model_validator(mode="after")
    def validate_time_range(self) -> Self:
        if self.end_at <= self.start_at:
            raise ValueError("runtime log query end_at must be after start_at")
        if self.end_at - self.start_at > _MAX_QUERY_RANGE:
            raise ValueError("runtime log query range must not exceed 24 hours")
        return self


class RuntimeLogRecord(ContractModel):
    record_id: NonEmptyStr
    tenant_id: NonEmptyStr
    timestamp: UtcDateTime
    service: NonEmptyStr
    component: NonEmptyStr
    environment: Environment
    runtime_id: NonEmptyStr
    bot_id: NonEmptyStr
    correlation_id: UUID
    trace_id: NonEmptyStr | None = None
    span_id: NonEmptyStr | None = None
    level: NonEmptyStr
    message: NonEmptyStr
    fields: dict[str, Any] = Field(default_factory=dict)
    source_id: NonEmptyStr
    retention_expires_at: UtcDateTime
    audit_evidence: bool = False

    @model_validator(mode="after")
    def validate_record(self) -> Self:
        if self.retention_expires_at <= self.timestamp:
            raise ValueError("runtime log retention must expire after the record timestamp")
        if self.audit_evidence:
            raise ValueError("runtime logs cannot be represented as immutable audit evidence")
        return self


class RuntimeLogSearchResult(ContractModel):
    query: RuntimeLogQuery
    source_status: RuntimeObservabilitySourceStatus
    records: tuple[RuntimeLogRecord, ...]
    truncated: bool = False


class RuntimeObservabilityProtocolError(RuntimeError):
    pass


class RuntimeObservabilityUnavailableError(RuntimeError):
    pass


class RuntimeObservabilitySource(Protocol):
    def status(self, tenant_id: str) -> RuntimeObservabilitySourceStatus: ...

    def search_logs(
        self,
        tenant_id: str,
        query: RuntimeLogQuery,
    ) -> tuple[RuntimeLogRecord, ...]: ...


class LokiQueryTransport(Protocol):
    def status(self, tenant_id: str) -> RuntimeObservabilitySourceStatus: ...

    def query_range(
        self,
        *,
        tenant_id: str,
        query: str,
        start_ns: int,
        end_ns: int,
        limit: int,
    ) -> Mapping[str, Any]: ...


class HttpResponse(Protocol):
    def __enter__(self) -> HttpResponse: ...

    def __exit__(self, exc_type: object, exc: object, traceback: object) -> None: ...

    def read(self, amount: int = -1) -> bytes: ...


HttpOpener = Callable[..., HttpResponse]
LokiEndpointProvider = Callable[[str], str]
LokiAuthorizationHeaderProvider = Callable[[str], Mapping[str, str]]
RuntimeObservabilityStatusProvider = Callable[[str], RuntimeObservabilitySourceStatus]


class HttpLokiQueryTransport:
    """Bounded server-side Loki query-range transport."""

    def __init__(
        self,
        endpoint_provider: LokiEndpointProvider,
        authorization_headers: LokiAuthorizationHeaderProvider,
        status_provider: RuntimeObservabilityStatusProvider,
        *,
        opener: HttpOpener = urlopen,
        timeout_seconds: int = 5,
        max_body_bytes: int = 1_048_576,
    ) -> None:
        if timeout_seconds < 1:
            raise ValueError("timeout_seconds must be positive")
        if max_body_bytes < 1:
            raise ValueError("max_body_bytes must be positive")
        self._endpoint_provider = endpoint_provider
        self._authorization_headers = authorization_headers
        self._status_provider = status_provider
        self._opener = opener
        self._timeout_seconds = timeout_seconds
        self._max_body_bytes = max_body_bytes

    def status(self, tenant_id: str) -> RuntimeObservabilitySourceStatus:
        return self._status_provider(tenant_id)

    def query_range(
        self,
        *,
        tenant_id: str,
        query: str,
        start_ns: int,
        end_ns: int,
        limit: int,
    ) -> Mapping[str, Any]:
        if start_ns >= end_ns:
            raise ValueError("runtime log query start must precede end")
        if limit < 1 or limit > _MAX_RESULTS:
            raise ValueError("runtime log query limit is outside the supported range")
        endpoint = self._validated_endpoint(self._endpoint_provider(tenant_id))
        request = self._request(
            endpoint,
            tenant_id=tenant_id,
            query=query,
            start_ns=start_ns,
            end_ns=end_ns,
            limit=limit,
        )
        body = self._read_body(request)
        try:
            payload = json.loads(body)
        except (UnicodeDecodeError, json.JSONDecodeError):
            raise RuntimeObservabilityProtocolError("RUNTIME_LOG_SOURCE_INVALID_JSON") from None
        if not isinstance(payload, Mapping):
            raise RuntimeObservabilityProtocolError("RUNTIME_LOG_SOURCE_INVALID_RESPONSE")
        return payload

    @staticmethod
    def _validated_endpoint(endpoint: str) -> str:
        parsed = urlsplit(endpoint)
        if parsed.scheme not in {"http", "https"} or not parsed.hostname:
            raise RuntimeObservabilityProtocolError("RUNTIME_LOG_SOURCE_INVALID_PRIVATE_ENDPOINT")
        if parsed.username is not None or parsed.password is not None:
            raise RuntimeObservabilityProtocolError("RUNTIME_LOG_SOURCE_ENDPOINT_EMBEDS_CREDENTIALS")
        if parsed.fragment:
            raise RuntimeObservabilityProtocolError("RUNTIME_LOG_SOURCE_INVALID_PRIVATE_ENDPOINT")
        return endpoint

    def _request(
        self,
        endpoint: str,
        *,
        tenant_id: str,
        query: str,
        start_ns: int,
        end_ns: int,
        limit: int,
    ) -> Request:
        parameters = urlencode(
            {
                "query": query,
                "start": str(start_ns),
                "end": str(end_ns),
                "limit": str(limit),
                "direction": "backward",
            }
        )
        separator = "&" if urlsplit(endpoint).query else "?"
        headers = {
            **dict(self._authorization_headers(tenant_id)),
            "Accept": "application/json",
        }
        return Request(f"{endpoint}{separator}{parameters}", headers=headers, method="GET")

    def _read_body(self, request: Request) -> bytes:
        try:
            # S310 is safe here because _validated_endpoint permits only HTTP(S) with a hostname.
            with self._opener(request, timeout=self._timeout_seconds) as response:  # noqa: S310
                body = response.read(self._max_body_bytes + 1)
        except HTTPError as exc:
            self._raise_http_error(exc.code)
        except TimeoutError:
            raise RuntimeObservabilityUnavailableError("RUNTIME_LOG_SOURCE_TIMEOUT") from None
        except URLError as exc:
            if isinstance(exc.reason, TimeoutError):
                raise RuntimeObservabilityUnavailableError("RUNTIME_LOG_SOURCE_TIMEOUT") from None
            raise RuntimeObservabilityUnavailableError("RUNTIME_LOG_SOURCE_UNAVAILABLE") from None

        if len(body) > self._max_body_bytes:
            raise RuntimeObservabilityProtocolError("RUNTIME_LOG_SOURCE_RESPONSE_TOO_LARGE")
        return body

    @staticmethod
    def _raise_http_error(status_code: int) -> None:
        if status_code in {401, 403}:
            raise RuntimeObservabilityProtocolError("RUNTIME_LOG_SOURCE_AUTHENTICATION_FAILED")
        if status_code in {408, 429, 502, 503, 504} or status_code >= 500:
            raise RuntimeObservabilityUnavailableError("RUNTIME_LOG_SOURCE_UNAVAILABLE")
        raise RuntimeObservabilityProtocolError("RUNTIME_LOG_SOURCE_HTTP_REJECTED")


class UnavailableRuntimeObservabilitySource:
    def __init__(
        self,
        *,
        checked_at: UtcDateTime,
        reason_code: str = "CENTRALIZED_RUNTIME_OBSERVABILITY_SOURCE_NOT_CONFIGURED",
    ) -> None:
        self._status = RuntimeObservabilitySourceStatus(
            source_id="runtime-observability-unconfigured",
            availability=RuntimeObservabilityAvailability.UNAVAILABLE,
            checked_at=checked_at,
            reason_code=reason_code,
            log_retention_days=14,
            trace_retention_days=7,
            metric_retention_days=30,
            trace_source="tempo-compatible-private-source",
            metric_source="prometheus-compatible-private-source",
            runbook_path="/docs/ai_platform/portal/runbooks/RUNTIME_OBSERVABILITY.md",
        )

    def status(self, tenant_id: str) -> RuntimeObservabilitySourceStatus:
        del tenant_id
        return self._status

    def search_logs(
        self,
        tenant_id: str,
        query: RuntimeLogQuery,
    ) -> tuple[RuntimeLogRecord, ...]:
        del tenant_id, query
        return ()


class LokiRuntimeObservabilitySource:
    """Private Loki-compatible query adapter. It is never exposed to browser code."""

    def __init__(self, transport: LokiQueryTransport) -> None:
        self._transport = transport

    def status(self, tenant_id: str) -> RuntimeObservabilitySourceStatus:
        return self._transport.status(tenant_id)

    def search_logs(
        self,
        tenant_id: str,
        query: RuntimeLogQuery,
    ) -> tuple[RuntimeLogRecord, ...]:
        response = self._transport.query_range(
            tenant_id=tenant_id,
            query=self._logql(tenant_id, query),
            start_ns=int(query.start_at.timestamp() * 1_000_000_000),
            end_ns=int(query.end_at.timestamp() * 1_000_000_000),
            limit=query.limit,
        )
        return self._decode_response(response, tenant_id)

    @classmethod
    def _logql(cls, tenant_id: str, query: RuntimeLogQuery) -> str:
        labels = {"tenant_id": tenant_id}
        for key in ("runtime_id", "bot_id", "service", "component", "level"):
            value = getattr(query, key)
            if value is not None:
                labels[key] = value
        selector = ",".join(
            f"{key}={json.dumps(cls._label_value(value))}" for key, value in sorted(labels.items())
        )
        expression = f"{{{selector}}}"
        if query.correlation_id is not None:
            expression += f" | json | correlation_id={json.dumps(str(query.correlation_id))}"
        return expression

    @staticmethod
    def _label_value(value: str) -> str:
        if not _LABEL_VALUE.fullmatch(value):
            raise ValueError("runtime observability label contains unsupported characters")
        return value

    @staticmethod
    def _decode_response(
        response: Mapping[str, Any],
        tenant_id: str,
    ) -> tuple[RuntimeLogRecord, ...]:
        data = response.get("data")
        if response.get("status") != "success" or not isinstance(data, Mapping):
            raise RuntimeObservabilityProtocolError("RUNTIME_LOG_SOURCE_INVALID_RESPONSE")
        streams = data.get("result")
        if not isinstance(streams, list):
            raise RuntimeObservabilityProtocolError("RUNTIME_LOG_SOURCE_INVALID_RESULT")

        records: list[RuntimeLogRecord] = []
        for stream in streams:
            if not isinstance(stream, Mapping):
                raise RuntimeObservabilityProtocolError("RUNTIME_LOG_SOURCE_INVALID_STREAM")
            values = stream.get("values")
            if not isinstance(values, list):
                raise RuntimeObservabilityProtocolError("RUNTIME_LOG_SOURCE_INVALID_VALUES")
            for value in values:
                records.append(LokiRuntimeObservabilitySource._decode_line(value, tenant_id))
        records.sort(key=lambda record: (record.timestamp, record.record_id), reverse=True)
        return tuple(records)

    @staticmethod
    def _decode_line(value: object, tenant_id: str) -> RuntimeLogRecord:
        if not isinstance(value, list) or len(value) != 2 or not isinstance(value[1], str):
            raise RuntimeObservabilityProtocolError("RUNTIME_LOG_SOURCE_INVALID_LINE")
        try:
            payload = json.loads(value[1])
        except json.JSONDecodeError:
            raise RuntimeObservabilityProtocolError("RUNTIME_LOG_SOURCE_INVALID_JSON") from None
        if not isinstance(payload, dict):
            raise RuntimeObservabilityProtocolError("RUNTIME_LOG_SOURCE_INVALID_PAYLOAD")
        if payload.get("tenant_id") != tenant_id:
            raise RuntimeObservabilityProtocolError("RUNTIME_LOG_SOURCE_TENANT_MISMATCH")
        safe_payload = redact_sensitive(payload)
        if not isinstance(safe_payload, dict):
            raise RuntimeObservabilityProtocolError("RUNTIME_LOG_SOURCE_INVALID_PAYLOAD")
        try:
            return RuntimeLogRecord.model_validate(safe_payload)
        except ValueError:
            raise RuntimeObservabilityProtocolError("RUNTIME_LOG_SOURCE_INVALID_RECORD") from None


class RuntimeObservabilityService:
    def __init__(self, source: RuntimeObservabilitySource) -> None:
        self._source = source

    def availability(self, context: RequestContext) -> RuntimeObservabilitySourceStatus:
        require_permission(context.permissions, Permission.AUDIT_READ)
        return self._source.status(context.tenant_id)

    def search_logs(
        self,
        context: RequestContext,
        query: RuntimeLogQuery,
    ) -> RuntimeLogSearchResult:
        require_permission(context.permissions, Permission.AUDIT_READ)
        status = self._source.status(context.tenant_id)
        if status.availability is RuntimeObservabilityAvailability.UNAVAILABLE:
            return RuntimeLogSearchResult(
                query=query,
                source_status=status,
                records=(),
                truncated=False,
            )

        records = self._source.search_logs(context.tenant_id, query)
        safe_records: list[RuntimeLogRecord] = []
        for record in records:
            if record.tenant_id != context.tenant_id:
                raise RuntimeObservabilityProtocolError("RUNTIME_LOG_SOURCE_TENANT_MISMATCH")
            payload = record.model_dump(mode="python")
            payload["fields"] = redact_sensitive(payload["fields"])
            safe_records.append(RuntimeLogRecord.model_validate(payload))
        safe_records.sort(key=lambda record: (record.timestamp, record.record_id), reverse=True)
        truncated = len(safe_records) > query.limit
        return RuntimeLogSearchResult(
            query=query,
            source_status=status,
            records=tuple(safe_records[: query.limit]),
            truncated=truncated,
        )
