from __future__ import annotations

import json
import os
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from ai_platform.portal.control_plane.wh09_runtime import (
    WH09_RUNTIME_ROOT_ENV,
    Wh09RuntimeEvidenceError,
    Wh09RuntimeEvidenceReader,
)


HOST = "0.0.0.0"  # noqa: S104 - container is attached only to the private Portal network
PORT = 8080
MAX_RESPONSE_BYTES = 512 * 1024


def _reader() -> Wh09RuntimeEvidenceReader:
    root = os.environ.get(WH09_RUNTIME_ROOT_ENV, "").strip()
    if not root:
        raise Wh09RuntimeEvidenceError("WH09 observer runtime root is not configured")
    return Wh09RuntimeEvidenceReader(Path(root))


class Wh09ObserverHandler(BaseHTTPRequestHandler):
    server_version = "WH09Observer/1"

    def do_GET(self) -> None:
        if self.path not in {"/healthz", "/evidence"}:
            self._json(HTTPStatus.NOT_FOUND, {"detail": "not found"})
            return
        try:
            reader = _reader()
            if self.path == "/healthz":
                source_health, mode = reader.read_health()
                self._json(
                    HTTPStatus.OK,
                    {
                        "status": "ready",
                        "source_health": source_health,
                        "mode": mode.value,
                        "live_capital_authorized": False,
                    },
                )
                return
            evidence = reader.read()
        except Wh09RuntimeEvidenceError:
            self._json(
                HTTPStatus.SERVICE_UNAVAILABLE,
                {"status": "unavailable", "live_capital_authorized": False},
            )
            return
        self._json(HTTPStatus.OK, evidence.model_dump(mode="json"))

    def log_message(self, format_string: str, *args: object) -> None:
        del format_string, args

    def _json(self, status: HTTPStatus, payload: dict[str, object]) -> None:
        body = json.dumps(payload, separators=(",", ":"), sort_keys=True).encode("utf-8")
        if len(body) > MAX_RESPONSE_BYTES:
            body = b'{"status":"unavailable","live_capital_authorized":false}'
            status = HTTPStatus.SERVICE_UNAVAILABLE
        self.send_response(status.value)
        self.send_header("content-type", "application/json")
        self.send_header("content-length", str(len(body)))
        self.send_header("cache-control", "no-store")
        self.end_headers()
        self.wfile.write(body)


def main() -> int:
    server = ThreadingHTTPServer((HOST, PORT), Wh09ObserverHandler)
    server.serve_forever()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
