from __future__ import annotations

import json
import socket
import threading
import time
from collections.abc import Generator
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any

import pytest

from ai_platform.portal.runtime_gateway.errors import GatewayError, UpstreamError
from ai_platform.portal.runtime_gateway.upstream import (
    LocalFreqtradeBinding,
    LocalFreqtradeHttpClient,
)


class FakeFreqtradeHandler(BaseHTTPRequestHandler):
    response_status = 200
    response_body: bytes = b'{"status":"pong"}'
    delay = 0.0
    requests: list[tuple[str, str | None]] = []

    def do_GET(self) -> None:
        type(self).requests.append((self.path, self.headers.get("Authorization")))
        if type(self).delay:
            time.sleep(type(self).delay)
        self.send_response(type(self).response_status)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(type(self).response_body)

    def log_message(self, format_string: str, *args: Any) -> None:
        return


@pytest.fixture
def fake_freqtrade() -> Generator[tuple[ThreadingHTTPServer, type[FakeFreqtradeHandler]]]:
    FakeFreqtradeHandler.response_status = 200
    FakeFreqtradeHandler.response_body = b'{"status":"pong"}'
    FakeFreqtradeHandler.delay = 0.0
    FakeFreqtradeHandler.requests = []
    server = ThreadingHTTPServer(("127.0.0.1", 0), FakeFreqtradeHandler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield server, FakeFreqtradeHandler
    finally:
        server.shutdown()
        server.server_close()


def client(server: ThreadingHTTPServer, **overrides: Any) -> LocalFreqtradeHttpClient:
    return LocalFreqtradeHttpClient(
        LocalFreqtradeBinding("127.0.0.1", server.server_port, "gateway", "local-secret"),
        timeout_seconds=overrides.get("timeout_seconds", 0.5),
        max_response_bytes=overrides.get("max_response_bytes", 1024),
    )


def test_deterministic_local_freqtrade_read(fake_freqtrade: Any) -> None:
    server, handler = fake_freqtrade
    assert client(server).get("/api/v1/ping") == {"status": "pong"}
    assert handler.requests[0][0] == "/api/v1/ping"
    assert handler.requests[0][1].startswith("Basic ")


@pytest.mark.parametrize("host", ["example.com", "10.0.0.2", "169.254.169.254"])
def test_rejects_arbitrary_upstream_target(host: str) -> None:
    with pytest.raises(GatewayError) as error:
        LocalFreqtradeBinding(host, 8080, "gateway", "secret")
    assert error.value.code == "ARBITRARY_UPSTREAM_FORBIDDEN"


def test_rejects_arbitrary_endpoint_and_method_surface(fake_freqtrade: Any) -> None:
    server, _ = fake_freqtrade
    with pytest.raises(GatewayError) as error:
        client(server).get("/api/v1/config")
    assert error.value.code == "ARBITRARY_ENDPOINT_FORBIDDEN"


@pytest.mark.parametrize(
    "payload",
    [
        {"nested": {"api_key": "leak"}},
        {"nested": {"api_secret": "leak"}},
        {"nested": {"clientSecret": "leak"}},
        {"nested": {"refresh_token": "leak"}},
        {"nested": {"accessToken": "leak"}},
        {"nested": {"authorization": "Bearer secret-value"}},
    ],
)
def test_shared_classifier_blocks_credential_bearing_response(
    fake_freqtrade: Any, payload: dict[str, Any]
) -> None:
    server, handler = fake_freqtrade
    handler.response_body = json.dumps(payload).encode()
    with pytest.raises(UpstreamError) as error:
        client(server).get("/api/v1/status")
    assert error.value.code == "CREDENTIAL_DISCLOSURE_BLOCKED"
    assert "leak" not in error.value.message
    assert "secret-value" not in error.value.message


def test_malformed_response_is_blocked(fake_freqtrade: Any) -> None:
    server, handler = fake_freqtrade
    handler.response_body = b"not-json"
    with pytest.raises(UpstreamError) as error:
        client(server).get("/api/v1/status")
    assert error.value.code == "MALFORMED_UPSTREAM_RESPONSE"


def test_excessive_upstream_response_is_blocked(fake_freqtrade: Any) -> None:
    server, handler = fake_freqtrade
    handler.response_body = b'"' + b"x" * 2000 + b'"'
    with pytest.raises(UpstreamError) as error:
        client(server, max_response_bytes=128).get("/api/v1/status")
    assert error.value.code == "UPSTREAM_RESPONSE_TOO_LARGE"


def test_upstream_timeout_is_finite(fake_freqtrade: Any) -> None:
    server, handler = fake_freqtrade
    handler.delay = 0.2
    with pytest.raises((UpstreamError, socket.timeout)) as error:
        client(server, timeout_seconds=0.05).get("/api/v1/status")
    if isinstance(error.value, UpstreamError):
        assert error.value.code == "UPSTREAM_UNAVAILABLE"
