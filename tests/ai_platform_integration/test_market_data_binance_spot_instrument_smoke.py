from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Self

import pytest

from ai_platform.market_data.binance_spot_instrument_smoke import (
    BINANCE_SPOT_REDUCED_PAYLOAD_URL,
    DEFAULT_MAX_RESPONSE_BYTES,
    DEFAULT_TIMEOUT_SECONDS,
    POLICY_VERSION,
    REDUCED_PAYLOAD_POLICY_VERSION,
    REDUCED_PAYLOAD_REQUEST_VERSION,
    REQUEST_VERSION,
    SmokePolicy,
    SmokeRequest,
    run_smoke,
)
from ai_platform.market_data.common import canonical_json_bytes, canonical_sha256
from ai_platform.market_data.instrument_adapters import BINANCE_SPOT_URL


COMMIT = "a" * 40


def _policy(*, reduced_payload: bool = False) -> dict[str, object]:
    return {
        "version": REDUCED_PAYLOAD_POLICY_VERSION if reduced_payload else POLICY_VERSION,
        "source_id": "binance-spot",
        "request_url": BINANCE_SPOT_REDUCED_PAYLOAD_URL if reduced_payload else BINANCE_SPOT_URL,
        "timeout_seconds": DEFAULT_TIMEOUT_SECONDS,
        "max_response_bytes": DEFAULT_MAX_RESPONSE_BYTES,
        "allow_redirects": False,
        "retries": 0,
        "source_acceptance": False,
    }


def _request(*, reduced_payload: bool = False) -> dict[str, object]:
    return {
        "version": REDUCED_PAYLOAD_REQUEST_VERSION if reduced_payload else REQUEST_VERSION,
        "policy_version": (REDUCED_PAYLOAD_POLICY_VERSION if reduced_payload else POLICY_VERSION),
        "source_id": "binance-spot",
        "request_url": BINANCE_SPOT_REDUCED_PAYLOAD_URL if reduced_payload else BINANCE_SPOT_URL,
        "execution_mode": "single_public_rest_snapshot",
        "public_only": True,
        "persist_raw_payload": True,
        "source_acceptance": False,
    }


def _payload() -> dict[str, Any]:
    return {
        "timezone": "UTC",
        "symbols": [
            {
                "symbol": "BTCUSDT",
                "status": "TRADING",
                "baseAsset": "BTC",
                "quoteAsset": "USDT",
                "filters": [
                    {"filterType": "PRICE_FILTER", "tickSize": "0.1"},
                    {"filterType": "LOT_SIZE", "stepSize": "0.00001"},
                ],
            },
            {
                "symbol": "OLDUSDT",
                "status": "BREAK",
                "baseAsset": "OLD",
                "quoteAsset": "USDT",
                "filters": [
                    {"filterType": "PRICE_FILTER", "tickSize": "0.01"},
                    {"filterType": "LOT_SIZE", "stepSize": "1"},
                ],
            },
        ],
    }


class FakeResponse:
    status = 200

    def __init__(
        self,
        payload: bytes,
        *,
        url: str = BINANCE_SPOT_URL,
        content_type: str = "application/json;charset=UTF-8",
    ) -> None:
        self.payload = payload
        self.url = url
        self.headers = {
            "Content-Type": content_type,
            "Content-Length": str(len(payload)),
        }

    def geturl(self) -> str:
        return self.url

    def read(self, amount: int = -1) -> bytes:
        return self.payload if amount < 0 else self.payload[:amount]

    def __enter__(self) -> Self:
        return self

    def __exit__(self, exc_type: object, exc: object, traceback: object) -> None:
        return None


class FakeOpener:
    def __init__(self, response: FakeResponse) -> None:
        self.response = response
        self.calls = 0

    def __call__(self, request: object, *, timeout: float, context: object) -> FakeResponse:
        del request, timeout, context
        self.calls += 1
        return self.response


def _write_inputs(root: Path, *, reduced_payload: bool = False) -> tuple[Path, Path]:
    request_path = root / "request.json"
    policy_path = root / "policy.json"
    request_path.write_bytes(
        canonical_json_bytes(_request(reduced_payload=reduced_payload)) + b"\n"
    )
    policy_path.write_bytes(canonical_json_bytes(_policy(reduced_payload=reduced_payload)) + b"\n")
    return request_path, policy_path


def test_policy_and_request_versions_are_frozen() -> None:
    SmokePolicy.from_mapping(_policy())
    SmokeRequest.from_mapping(_request())
    SmokePolicy.from_mapping(_policy(reduced_payload=True))
    SmokeRequest.from_mapping(_request(reduced_payload=True))

    policy = _policy(reduced_payload=True)
    policy["request_url"] = BINANCE_SPOT_URL
    with pytest.raises(ValueError, match="frozen contract"):
        SmokePolicy.from_mapping(policy)

    policy = _policy(reduced_payload=True)
    policy["retries"] = 1
    with pytest.raises(ValueError, match="exactly one request"):
        SmokePolicy.from_mapping(policy)

    request = _request(reduced_payload=True)
    request["source_acceptance"] = True
    with pytest.raises(ValueError, match="cannot grant source acceptance"):
        SmokeRequest.from_mapping(request)


def test_reduced_payload_smoke_writes_exact_bounded_evidence(tmp_path: Path) -> None:
    request_path, policy_path = _write_inputs(tmp_path, reduced_payload=True)
    raw = json.dumps(_payload(), separators=(",", ":")).encode()
    opener = FakeOpener(FakeResponse(raw, url=BINANCE_SPOT_REDUCED_PAYLOAD_URL))
    output = tmp_path / "evidence"
    report = run_smoke(
        request_path=request_path,
        policy_path=policy_path,
        output_root=output,
        collector_commit=COMMIT,
        environment={},
        opener=opener,
    )
    assert opener.calls == 1
    assert report["status"] == "pass"
    assert report["request_url"] == BINANCE_SPOT_REDUCED_PAYLOAD_URL
    assert report["instrument_count"] == 2
    assert report["active_instrument_count"] == 1
    assert report["source_acceptance"] is False
    assert (output / "raw-response.json").read_bytes() == raw
    snapshot = json.loads((output / "instrument-catalog-snapshot.json").read_text())
    assert snapshot["source_id"] == "binance-spot"
    assert snapshot["request_urls"] == [BINANCE_SPOT_REDUCED_PAYLOAD_URL]
    assert len(snapshot["instruments"]) == 2
    stored_report = json.loads((output / "report.json").read_text())
    claimed = stored_report.pop("report_sha256")
    assert claimed == canonical_sha256(stored_report)
    checksums = (output / "checksums.sha256").read_text()
    assert "raw-response.json" in checksums
    assert "instrument-catalog-snapshot.json" in checksums


def test_smoke_refuses_credentials_before_transport(tmp_path: Path) -> None:
    request_path, policy_path = _write_inputs(tmp_path, reduced_payload=True)
    opener = FakeOpener(
        FakeResponse(canonical_json_bytes(_payload()), url=BINANCE_SPOT_REDUCED_PAYLOAD_URL)
    )
    with pytest.raises(RuntimeError, match="BINANCE_API_KEY"):
        run_smoke(
            request_path=request_path,
            policy_path=policy_path,
            output_root=tmp_path / "evidence",
            collector_commit=COMMIT,
            environment={"BINANCE_API_KEY": "secret"},
            opener=opener,
        )
    assert opener.calls == 0


def test_oversized_response_writes_failure_evidence(tmp_path: Path) -> None:
    request_path, policy_path = _write_inputs(tmp_path, reduced_payload=True)
    raw = b"x" * (DEFAULT_MAX_RESPONSE_BYTES + 1)
    opener = FakeOpener(FakeResponse(raw, url=BINANCE_SPOT_REDUCED_PAYLOAD_URL))
    output = tmp_path / "evidence"

    with pytest.raises(RuntimeError, match="max_response_bytes"):
        run_smoke(
            request_path=request_path,
            policy_path=policy_path,
            output_root=output,
            collector_commit=COMMIT,
            environment={},
            opener=opener,
        )

    assert opener.calls == 1
    failure = json.loads((output / "failure-report.json").read_text())
    claimed = failure.pop("failure_report_sha256")
    assert claimed == canonical_sha256(failure)
    assert failure["status"] == "fail"
    assert failure["failure_stage"] == "response_headers"
    assert failure["error_type"] == "ResponseTooLarge"
    assert failure["attempt_count"] == 1
    assert failure["declared_response_bytes"] == len(raw)
    assert failure["max_response_bytes"] == DEFAULT_MAX_RESPONSE_BYTES
    assert failure["raw_payload_persisted"] is False
    assert failure["source_acceptance"] is False
    assert not (output / "raw-response.json").exists()
    assert (output / "run-request.json").exists()
    assert (output / "policy.json").exists()
    checksums = (output / "checksums.sha256").read_text()
    assert "failure-report.json" in checksums


def test_smoke_rejects_redirect_and_content_type_with_evidence(tmp_path: Path) -> None:
    request_path, policy_path = _write_inputs(tmp_path, reduced_payload=True)
    raw = canonical_json_bytes(_payload())
    cases = [
        (FakeResponse(raw, url="https://example.invalid/redirect"), "redirects are forbidden"),
        (
            FakeResponse(
                raw,
                url=BINANCE_SPOT_REDUCED_PAYLOAD_URL,
                content_type="text/html",
            ),
            "unexpected response content type",
        ),
    ]
    for index, (response, message) in enumerate(cases):
        output = tmp_path / f"evidence-{index}"
        with pytest.raises(RuntimeError, match=message):
            run_smoke(
                request_path=request_path,
                policy_path=policy_path,
                output_root=output,
                collector_commit=COMMIT,
                environment={},
                opener=FakeOpener(response),
            )
        assert (output / "failure-report.json").exists()
