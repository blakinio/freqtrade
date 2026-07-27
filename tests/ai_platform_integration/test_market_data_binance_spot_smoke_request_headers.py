from __future__ import annotations

import ssl
from urllib.request import Request

from ai_platform.market_data.binance_spot_instrument_smoke import (
    DEFAULT_MAX_RESPONSE_BYTES,
    DEFAULT_TIMEOUT_SECONDS,
    POLICY_VERSION,
    SmokePolicy,
    _fetch_once,
)
from ai_platform.market_data.instrument_adapters import BINANCE_SPOT_URL


class _JsonResponse:
    status = 200
    headers = {"Content-Type": "application/json"}

    def geturl(self) -> str:
        return BINANCE_SPOT_URL

    def read(self, amount: int = -1) -> bytes:
        del amount
        return b"{}"

    def __enter__(self) -> _JsonResponse:
        return self

    def __exit__(self, exc_type: object, exc: object, traceback: object) -> None:
        del exc_type, exc, traceback


def test_fetch_once_sends_valid_json_accept_header() -> None:
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
        return _JsonResponse()

    policy = SmokePolicy(
        version=POLICY_VERSION,
        source_id="binance-spot",
        request_url=BINANCE_SPOT_URL,
        timeout_seconds=DEFAULT_TIMEOUT_SECONDS,
        max_response_bytes=DEFAULT_MAX_RESPONSE_BYTES,
        allow_redirects=False,
        retries=0,
        source_acceptance=False,
    )

    _fetch_once(policy, opener=opener)

    assert len(captured) == 1
    assert captured[0].get_header("Accept") == "application/json"
