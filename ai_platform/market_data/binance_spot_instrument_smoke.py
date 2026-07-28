from __future__ import annotations

import argparse
import json
import os
import ssl
import time
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from hashlib import sha256
from http.client import HTTPMessage
from pathlib import Path
from typing import Any, Protocol, Self, cast
from urllib.request import HTTPRedirectHandler, HTTPSHandler, Request, build_opener

from ai_platform.market_data.common import (
    canonical_json_bytes,
    canonical_sha256,
    refuse_trading_credentials,
    validate_commit,
)
from ai_platform.market_data.instrument_adapters import (
    BINANCE_SPOT_URL,
    parse_binance_spot_catalog,
)


POLICY_VERSION = "binance-spot-instrument-smoke-policy-v1"
REQUEST_VERSION = "binance-spot-instrument-smoke-request-v1"
REDUCED_PAYLOAD_POLICY_VERSION = "binance-spot-instrument-smoke-policy-v2"
REDUCED_PAYLOAD_REQUEST_VERSION = "binance-spot-instrument-smoke-request-v2"
REPORT_VERSION = "binance-spot-instrument-smoke-report-v1"
FAILURE_REPORT_VERSION = "binance-spot-instrument-smoke-failure-report-v1"
BINANCE_SPOT_REDUCED_PAYLOAD_URL = f"{BINANCE_SPOT_URL}?showPermissionSets=false"
DEFAULT_TIMEOUT_SECONDS = 20
DEFAULT_MAX_RESPONSE_BYTES = 16 * 1024 * 1024
USER_AGENT = "freqtrade-ai-platform-market-data-smoke/1"

_POLICY_CONTRACTS = {
    POLICY_VERSION: BINANCE_SPOT_URL,
    REDUCED_PAYLOAD_POLICY_VERSION: BINANCE_SPOT_REDUCED_PAYLOAD_URL,
}
_REQUEST_CONTRACTS = {
    REQUEST_VERSION: (POLICY_VERSION, BINANCE_SPOT_URL),
    REDUCED_PAYLOAD_REQUEST_VERSION: (
        REDUCED_PAYLOAD_POLICY_VERSION,
        BINANCE_SPOT_REDUCED_PAYLOAD_URL,
    ),
}


class HttpResponse(Protocol):
    status: int
    headers: Mapping[str, str]

    def geturl(self) -> str: ...

    def read(self, amount: int = -1) -> bytes: ...

    def __enter__(self) -> Self: ...

    def __exit__(self, exc_type: object, exc: object, traceback: object) -> None: ...


class UrlOpener(Protocol):
    def __call__(
        self,
        request: Request,
        *,
        timeout: float,
        context: ssl.SSLContext,
    ) -> HttpResponse: ...


class _RejectRedirects(HTTPRedirectHandler):
    def redirect_request(
        self,
        request: Request,
        file_pointer: object,
        code: int,
        message: str,
        headers: HTTPMessage,
        new_url: str,
    ) -> None:
        del request, file_pointer, code, message, headers, new_url


def _open_url(
    request: Request,
    *,
    timeout: float,
    context: ssl.SSLContext,
) -> HttpResponse:
    opener = build_opener(_RejectRedirects(), HTTPSHandler(context=context))
    return cast(HttpResponse, opener.open(request, timeout=timeout))


@dataclass(frozen=True, slots=True)
class SmokeFailureDetails:
    stage: str
    attempt_count: int
    error_type: str
    request_started_ns: int | None = None
    response_completed_ns: int | None = None
    http_status: int | None = None
    content_type: str | None = None
    final_url: str | None = None
    declared_response_bytes: int | None = None
    observed_response_bytes: int | None = None


class SmokeExecutionError(RuntimeError):
    def __init__(self, message: str, *, details: SmokeFailureDetails) -> None:
        super().__init__(message)
        self.details = details


@dataclass(frozen=True, slots=True)
class SmokePolicy:
    version: str
    source_id: str
    request_url: str
    timeout_seconds: int
    max_response_bytes: int
    allow_redirects: bool
    retries: int
    source_acceptance: bool

    @classmethod
    def from_mapping(cls, value: Mapping[str, object]) -> SmokePolicy:
        policy = cls(
            version=_text(value.get("version"), field="version"),
            source_id=_text(value.get("source_id"), field="source_id"),
            request_url=_text(value.get("request_url"), field="request_url"),
            timeout_seconds=_integer(value.get("timeout_seconds"), field="timeout_seconds"),
            max_response_bytes=_integer(
                value.get("max_response_bytes"), field="max_response_bytes"
            ),
            allow_redirects=_boolean(value.get("allow_redirects"), field="allow_redirects"),
            retries=_integer(value.get("retries"), field="retries", minimum=0),
            source_acceptance=_boolean(value.get("source_acceptance"), field="source_acceptance"),
        )
        policy.validate()
        return policy

    def validate(self) -> None:
        expected_url = _POLICY_CONTRACTS.get(self.version)
        if expected_url is None:
            raise ValueError("unsupported smoke policy version")
        if self.source_id != "binance-spot":
            raise ValueError("smoke policy source_id must be binance-spot")
        if self.request_url != expected_url:
            raise ValueError("smoke policy request_url must match its frozen contract")
        if self.timeout_seconds != DEFAULT_TIMEOUT_SECONDS:
            raise ValueError("smoke policy timeout_seconds must remain frozen")
        if self.max_response_bytes != DEFAULT_MAX_RESPONSE_BYTES:
            raise ValueError("smoke policy max_response_bytes must remain frozen")
        if self.allow_redirects:
            raise ValueError("smoke policy must reject redirects")
        if self.retries != 0:
            raise ValueError("smoke policy must perform exactly one request")
        if self.source_acceptance:
            raise ValueError("smoke policy cannot grant source acceptance")


@dataclass(frozen=True, slots=True)
class SmokeRequest:
    version: str
    policy_version: str
    source_id: str
    request_url: str
    execution_mode: str
    public_only: bool
    persist_raw_payload: bool
    source_acceptance: bool

    @classmethod
    def from_mapping(cls, value: Mapping[str, object]) -> SmokeRequest:
        request = cls(
            version=_text(value.get("version"), field="version"),
            policy_version=_text(value.get("policy_version"), field="policy_version"),
            source_id=_text(value.get("source_id"), field="source_id"),
            request_url=_text(value.get("request_url"), field="request_url"),
            execution_mode=_text(value.get("execution_mode"), field="execution_mode"),
            public_only=_boolean(value.get("public_only"), field="public_only"),
            persist_raw_payload=_boolean(
                value.get("persist_raw_payload"), field="persist_raw_payload"
            ),
            source_acceptance=_boolean(value.get("source_acceptance"), field="source_acceptance"),
        )
        request.validate()
        return request

    def validate(self) -> None:
        contract = _REQUEST_CONTRACTS.get(self.version)
        if contract is None:
            raise ValueError("unsupported smoke request version")
        expected_policy_version, expected_url = contract
        if self.policy_version != expected_policy_version:
            raise ValueError("request policy_version mismatch")
        if self.source_id != "binance-spot":
            raise ValueError("smoke request source_id must be binance-spot")
        if self.request_url != expected_url:
            raise ValueError("smoke request URL must match its frozen contract")
        if self.execution_mode != "single_public_rest_snapshot":
            raise ValueError("unsupported smoke execution mode")
        if not self.public_only:
            raise ValueError("smoke request must be public-only")
        if not self.persist_raw_payload:
            raise ValueError("smoke request must preserve exact raw payload evidence")
        if self.source_acceptance:
            raise ValueError("smoke request cannot grant source acceptance")


def _text(value: object, *, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field} must be a non-empty string")
    return value.strip()


def _integer(value: object, *, field: str, minimum: int = 1) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < minimum:
        raise ValueError(f"{field} must be an integer >= {minimum}")
    return value


def _boolean(value: object, *, field: str) -> bool:
    if not isinstance(value, bool):
        raise TypeError(f"{field} must be a boolean")
    return value


def _load_object(path: Path) -> dict[str, object]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise TypeError(f"{path} must contain a JSON object")
    return value


def _write_bytes(path: Path, value: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(value)


def _sha256_bytes(value: bytes) -> str:
    return sha256(value).hexdigest()


def _validate_content_type(headers: Mapping[str, str]) -> str:
    content_type = headers.get("Content-Type") or headers.get("content-type") or ""
    normalized = content_type.split(";", 1)[0].strip().lower()
    if normalized not in {"application/json", "application/vnd.api+json"}:
        raise RuntimeError(f"unexpected response content type: {content_type!r}")
    return content_type


def _failure(
    message: str,
    *,
    stage: str,
    error_type: str,
    started_ns: int,
    ended_ns: int | None = None,
    status: int | None = None,
    content_type: str | None = None,
    final_url: str | None = None,
    declared_response_bytes: int | None = None,
    observed_response_bytes: int | None = None,
) -> SmokeExecutionError:
    return SmokeExecutionError(
        message,
        details=SmokeFailureDetails(
            stage=stage,
            attempt_count=1,
            error_type=error_type,
            request_started_ns=started_ns,
            response_completed_ns=ended_ns,
            http_status=status,
            content_type=content_type,
            final_url=final_url,
            declared_response_bytes=declared_response_bytes,
            observed_response_bytes=observed_response_bytes,
        ),
    )


def _fetch_once(
    policy: SmokePolicy,
    *,
    opener: UrlOpener = _open_url,
) -> tuple[bytes, int, str, str, int, int]:
    started_ns = time.time_ns()
    request = Request(  # noqa: S310
        policy.request_url,
        headers={"Accept": "application/json", "User-Agent": USER_AGENT},
        method="GET",
    )
    try:
        with opener(
            request,
            timeout=float(policy.timeout_seconds),
            context=ssl.create_default_context(),
        ) as response:
            status = response.status
            final_url = response.geturl()
            if status != 200:
                raise _failure(
                    f"unexpected HTTP status: {status}",
                    stage="transport",
                    error_type="UnexpectedHttpStatus",
                    started_ns=started_ns,
                    ended_ns=time.time_ns(),
                    status=status,
                    final_url=final_url,
                )
            if not policy.allow_redirects and final_url != policy.request_url:
                raise _failure(
                    f"redirects are forbidden: {final_url}",
                    stage="transport",
                    error_type="RedirectRefused",
                    started_ns=started_ns,
                    ended_ns=time.time_ns(),
                    status=status,
                    final_url=final_url,
                )
            try:
                content_type = _validate_content_type(response.headers)
            except RuntimeError as exc:
                raise _failure(
                    str(exc),
                    stage="response_headers",
                    error_type="UnexpectedContentType",
                    started_ns=started_ns,
                    ended_ns=time.time_ns(),
                    status=status,
                    final_url=final_url,
                ) from exc
            content_length = response.headers.get("Content-Length") or response.headers.get(
                "content-length"
            )
            declared: int | None = None
            if content_length:
                try:
                    declared = int(content_length)
                except ValueError as exc:
                    raise _failure(
                        "invalid Content-Length header",
                        stage="response_headers",
                        error_type="InvalidContentLength",
                        started_ns=started_ns,
                        ended_ns=time.time_ns(),
                        status=status,
                        content_type=content_type,
                        final_url=final_url,
                    ) from exc
                if declared > policy.max_response_bytes:
                    raise _failure(
                        "response exceeds max_response_bytes",
                        stage="response_headers",
                        error_type="ResponseTooLarge",
                        started_ns=started_ns,
                        ended_ns=time.time_ns(),
                        status=status,
                        content_type=content_type,
                        final_url=final_url,
                        declared_response_bytes=declared,
                    )
            payload = response.read(policy.max_response_bytes + 1)
    except SmokeExecutionError:
        raise
    except Exception as exc:
        raise _failure(
            str(exc) or exc.__class__.__name__,
            stage="transport",
            error_type=exc.__class__.__name__,
            started_ns=started_ns,
            ended_ns=time.time_ns(),
        ) from exc

    ended_ns = time.time_ns()
    if len(payload) > policy.max_response_bytes:
        raise _failure(
            "response exceeds max_response_bytes",
            stage="response_body",
            error_type="ResponseTooLarge",
            started_ns=started_ns,
            ended_ns=ended_ns,
            status=status,
            content_type=content_type,
            final_url=final_url,
            declared_response_bytes=declared,
            observed_response_bytes=len(payload),
        )
    if not payload:
        raise _failure(
            "response payload is empty",
            stage="response_body",
            error_type="EmptyResponse",
            started_ns=started_ns,
            ended_ns=ended_ns,
            status=status,
            content_type=content_type,
            final_url=final_url,
            declared_response_bytes=declared,
            observed_response_bytes=0,
        )
    return payload, status, content_type, final_url, started_ns, ended_ns


def _decode_object(payload: bytes) -> dict[str, object]:
    try:
        value = json.loads(payload.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise RuntimeError("response is not valid UTF-8 JSON") from exc
    if not isinstance(value, dict):
        raise TypeError("response JSON must be an object")
    return value


def _checksums(entries: Sequence[tuple[str, bytes]]) -> bytes:
    return "".join(f"{_sha256_bytes(value)}  {name}\n" for name, value in entries).encode("utf-8")


def _write_failure_evidence(
    *,
    output_root: Path,
    policy: SmokePolicy,
    policy_mapping: Mapping[str, object],
    request_mapping: Mapping[str, object],
    collector_commit: str,
    error: Exception,
    stage: str,
    attempt_count: int,
) -> dict[str, Any]:
    if isinstance(error, SmokeExecutionError):
        details = error.details
    else:
        details = SmokeFailureDetails(
            stage=stage,
            attempt_count=attempt_count,
            error_type=error.__class__.__name__,
        )

    request_name = "run-request.json"
    policy_name = "policy.json"
    failure_name = "failure-report.json"
    checksums_name = "checksums.sha256"

    request_bytes = canonical_json_bytes(request_mapping) + b"\n"
    policy_bytes = canonical_json_bytes(policy_mapping) + b"\n"
    failure_seed: dict[str, Any] = {
        "failure_report_version": FAILURE_REPORT_VERSION,
        "status": "fail",
        "source_id": policy.source_id,
        "request_url": policy.request_url,
        "failure_stage": details.stage,
        "error_type": details.error_type,
        "error_message": str(error),
        "collector_commit": collector_commit,
        "attempt_count": details.attempt_count,
        "timeout_seconds": policy.timeout_seconds,
        "max_response_bytes": policy.max_response_bytes,
        "request_started_ns": details.request_started_ns,
        "response_completed_ns": details.response_completed_ns,
        "http_status": details.http_status,
        "content_type": details.content_type,
        "final_url": details.final_url,
        "declared_response_bytes": details.declared_response_bytes,
        "observed_response_bytes": details.observed_response_bytes,
        "raw_payload_persisted": False,
        "source_acceptance": False,
        "broad_capture": False,
        "websocket": False,
    }
    failure_report = {
        **failure_seed,
        "failure_report_sha256": canonical_sha256(failure_seed),
    }
    failure_bytes = canonical_json_bytes(failure_report) + b"\n"
    checksum_bytes = _checksums(
        (
            (request_name, request_bytes),
            (policy_name, policy_bytes),
            (failure_name, failure_bytes),
        )
    )

    output_root.mkdir(parents=True, exist_ok=False)
    _write_bytes(output_root / request_name, request_bytes)
    _write_bytes(output_root / policy_name, policy_bytes)
    _write_bytes(output_root / failure_name, failure_bytes)
    _write_bytes(output_root / checksums_name, checksum_bytes)
    return failure_report


def run_smoke(
    *,
    request_path: Path,
    policy_path: Path,
    output_root: Path,
    collector_commit: str,
    environment: Mapping[str, str] | None = None,
    opener: UrlOpener = _open_url,
) -> dict[str, Any]:
    commit = validate_commit(collector_commit, field="collector_commit")
    refuse_trading_credentials(environment if environment is not None else os.environ)
    policy_mapping = _load_object(policy_path)
    request_mapping = _load_object(request_path)
    policy = SmokePolicy.from_mapping(policy_mapping)
    request = SmokeRequest.from_mapping(request_mapping)
    if request.policy_version != policy.version:
        raise ValueError("request and policy versions do not match")
    if request.request_url != policy.request_url or request.source_id != policy.source_id:
        raise ValueError("request and policy source identity do not match")

    stage = "transport"
    attempt_count = 1
    try:
        raw_payload, status, content_type, final_url, started_ns, ended_ns = _fetch_once(
            policy, opener=opener
        )
        stage = "decode"
        payload_mapping = _decode_object(raw_payload)
        captured_at_ms = ended_ns // 1_000_000
        stage = "parse_and_normalize"
        snapshot = parse_binance_spot_catalog(
            payload_mapping,
            captured_at_ms=captured_at_ms,
            request_url=policy.request_url,
        )
    except Exception as exc:
        _write_failure_evidence(
            output_root=output_root,
            policy=policy,
            policy_mapping=policy_mapping,
            request_mapping=request_mapping,
            collector_commit=commit,
            error=exc,
            stage=stage,
            attempt_count=attempt_count,
        )
        raise

    active_count = sum(1 for item in snapshot.instruments if item.active)

    raw_name = "raw-response.json"
    snapshot_name = "instrument-catalog-snapshot.json"
    request_name = "run-request.json"
    policy_name = "policy.json"
    report_name = "report.json"
    checksums_name = "checksums.sha256"

    request_bytes = canonical_json_bytes(request_mapping) + b"\n"
    policy_bytes = canonical_json_bytes(policy_mapping) + b"\n"
    snapshot_bytes = canonical_json_bytes(snapshot.as_json_dict()) + b"\n"
    raw_sha = _sha256_bytes(raw_payload)
    report_seed: dict[str, Any] = {
        "report_version": REPORT_VERSION,
        "status": "pass",
        "source_id": policy.source_id,
        "request_url": policy.request_url,
        "final_url": final_url,
        "http_status": status,
        "content_type": content_type,
        "request_started_ns": started_ns,
        "response_completed_ns": ended_ns,
        "duration_ms": (ended_ns - started_ns) / 1_000_000,
        "captured_at_ms": captured_at_ms,
        "response_bytes": len(raw_payload),
        "raw_response_sha256": raw_sha,
        "instrument_count": len(snapshot.instruments),
        "active_instrument_count": active_count,
        "inactive_instrument_count": len(snapshot.instruments) - active_count,
        "source_snapshot_id": snapshot.source_snapshot_id,
        "source_snapshot_sha256": snapshot.source_snapshot_sha256,
        "catalog_snapshot_sha256": snapshot.snapshot_sha256,
        "collector_commit": commit,
        "attempt_count": 1,
        "redirect_count": 0,
        "credential_policy": "recognized_trading_credentials_refused",
        "source_acceptance": False,
        "broad_capture": False,
        "websocket": False,
    }
    report = {**report_seed, "report_sha256": canonical_sha256(report_seed)}
    report_bytes = canonical_json_bytes(report) + b"\n"
    checksum_bytes = _checksums(
        (
            (raw_name, raw_payload),
            (snapshot_name, snapshot_bytes),
            (request_name, request_bytes),
            (policy_name, policy_bytes),
            (report_name, report_bytes),
        )
    )

    output_root.mkdir(parents=True, exist_ok=False)
    _write_bytes(output_root / raw_name, raw_payload)
    _write_bytes(output_root / snapshot_name, snapshot_bytes)
    _write_bytes(output_root / request_name, request_bytes)
    _write_bytes(output_root / policy_name, policy_bytes)
    _write_bytes(output_root / report_name, report_bytes)
    _write_bytes(output_root / checksums_name, checksum_bytes)
    return report


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run one bounded Binance Spot catalog smoke")
    parser.add_argument("--request", type=Path, required=True)
    parser.add_argument("--policy", type=Path, required=True)
    parser.add_argument("--output-root", type=Path, required=True)
    parser.add_argument("--collector-commit", required=True)
    return parser


def main() -> int:
    args = _parser().parse_args()
    report = run_smoke(
        request_path=args.request,
        policy_path=args.policy,
        output_root=args.output_root,
        collector_commit=args.collector_commit,
    )
    print(canonical_json_bytes(report).decode("utf-8"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
