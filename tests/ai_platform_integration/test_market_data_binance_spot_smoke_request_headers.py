from __future__ import annotations

import ssl
from urllib.request import Request

import pytest

from ai_platform.market_data.binance_spot_instrument_smoke import (
    BINANCE_SPOT_REDUCED_PAYLOAD_URL,
    DEFAULT_MAX_RESPONSE_BYTES,
    DEFAULT_TIMEOUT_SECONDS,
    POLICY_VERSION,
    REDUCED_PAYLOAD_POLICY_VERSION,
    SmokePolicy,
    _fetch_once,
)
from ai_platform.market_data.instrument_adapters import BINANCE_SPOT_URL


class _JsonResponse:
    status = 200
    headers = {"Content-Type": "application/json"}

    def __init__(self, url: str) -> None:
        self.url = url

    def geturl(self) -> str:
        return self.url

    def read(self, amount: int = -1) -> bytes:
        del amount
        return b"{}"

    def __enter__(self) -> _JsonResponse:
        return self

    def __exit__(self, exc_type: object, exc: object, traceback: object) -> None:
        del exc_type, exc, traceback


@pytest.mark.parametrize(
    ("version", "request_url"),
    (
        (POLICY_VERSION, BINANCE_SPOT_URL),
        (REDUCED_PAYLOAD_POLICY_VERSION, BINANCE_SPOT_REDUCED_PAYLOAD_URL),
    ),
)
def test_fetch_once_sends_exact_url_and_valid_json_accept_header(
    version: str,
    request_url: str,
) -> None:
    captured: list[Request] = []

    def opener(
        request: Request,
        *,
        timeout: float,
        context: ssl.SSLContext,
    ) -> _JsonResponse:
        assert timeout == DEFAULT_TIMEOUT_SECONDS
        assert isinstance(context, ssl.SSLContext)
        captured.append(request)
        return _JsonResponse(request_url)

    policy = SmokePolicy(
        version=version,
        source_id="binance-spot",
        request_url=request_url,
        timeout_seconds=DEFAULT_TIMEOUT_SECONDS,
        max_response_bytes=DEFAULT_MAX_RESPONSE_BYTES,
        allow_redirects=False,
        retries=0,
        source_acceptance=False,
    )

    _fetch_once(policy, opener=opener)

    assert len(captured) == 1
    assert captured[0].full_url == request_url
    assert captured[0].get_header("Accept") == "application/json"
