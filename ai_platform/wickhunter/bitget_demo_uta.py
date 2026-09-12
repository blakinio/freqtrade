"""Bitget Demo UTA futures adapter. Demo-only: no live mode, transfer, or withdrawal surface."""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
import os
import re
import time
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen


BITGET_REST_BASE = "https://api.bitget.com"
DEMO_HEADER_NAME = "paptrading"
DEMO_HEADER_VALUE = "1"
USDT_FUTURES = "USDT-FUTURES"
_CLIENT_OID_RE = re.compile(r"^[.A-Z:/a-z0-9_-]{1,32}$")


class BitgetDemoError(RuntimeError):
    """Fail-closed error for the Bitget Demo UTA adapter."""


@dataclass(frozen=True)
class BitgetDemoCredentials:
    api_key: str
    api_secret: str
    passphrase: str

    @classmethod
    def from_env(cls, environ: Mapping[str, str] | None = None) -> BitgetDemoCredentials:
        source = os.environ if environ is None else environ
        values = {
            "api_key": source.get("BITGET_DEMO_API_KEY", ""),
            "api_secret": source.get("BITGET_DEMO_SECRET", ""),
            "passphrase": source.get("BITGET_DEMO_PASSPHRASE", ""),
        }
        missing = [name for name, value in values.items() if not value]
        if missing:
            raise BitgetDemoError("missing Bitget Demo API credentials")
        return cls(**values)


@dataclass(frozen=True)
class DemoAccountState:
    account_mode: str
    account_level: str
    hold_mode: str
    usdt_equity: Decimal


class BitgetDemoUTAClient:
    """Minimal UTA futures client permanently pinned to Bitget Demo semantics."""

    def __init__(
        self,
        credentials: BitgetDemoCredentials,
        *,
        timeout: float = 12.0,
        opener: Callable[..., Any] = urlopen,
        clock: Callable[[], float] = time.time,
    ) -> None:
        self._credentials = credentials
        self._timeout = timeout
        self._opener = opener
        self._clock = clock

    def _redact(self, value: object) -> str:
        text = str(value)
        for secret in (
            self._credentials.api_key,
            self._credentials.api_secret,
            self._credentials.passphrase,
        ):
            if secret:
                text = text.replace(secret, "[REDACTED]")
        return text[:300]

    @staticmethod
    def _query(params: Mapping[str, object] | None) -> str:
        if not params:
            return ""
        items = sorted((str(key), str(value)) for key, value in params.items())
        return urlencode(items)

    def _signature(self, timestamp: str, method: str, path_with_query: str, body: str) -> str:
        message = f"{timestamp}{method}{path_with_query}{body}".encode()
        digest = hmac.new(
            self._credentials.api_secret.encode(),
            message,
            hashlib.sha256,
        ).digest()
        return base64.b64encode(digest).decode()

    def _request(
        self,
        method: str,
        path: str,
        *,
        params: Mapping[str, object] | None = None,
        body: Mapping[str, object] | None = None,
        private: bool,
    ) -> dict[str, Any]:
        method = method.upper()
        if not path.startswith("/api/v3/") or "://" in path or ".." in path:
            raise BitgetDemoError("invalid Bitget UTA API path")
        query = self._query(params)
        suffix = f"?{query}" if query else ""
        path_with_query = f"{path}{suffix}"
        raw_body = "" if body is None else json.dumps(body, separators=(",", ":"))
        headers = {"Content-Type": "application/json", "locale": "en-US"}
        if private:
            timestamp = str(int(self._clock() * 1000))
            headers.update(
                {
                    "ACCESS-KEY": self._credentials.api_key,
                    "ACCESS-SIGN": self._signature(timestamp, method, path_with_query, raw_body),
                    "ACCESS-PASSPHRASE": self._credentials.passphrase,
                    "ACCESS-TIMESTAMP": timestamp,
                    DEMO_HEADER_NAME: DEMO_HEADER_VALUE,
                }
            )
        request = Request(  # noqa: S310 -- base URL is fixed HTTPS and paths are internal.
            f"{BITGET_REST_BASE}{path_with_query}",
            data=raw_body.encode() if raw_body else None,
            headers=headers,
            method=method,
        )
        try:
            with self._opener(request, timeout=self._timeout) as response:
                payload = json.loads(response.read().decode())
        except HTTPError as exc:
            raise BitgetDemoError(f"Bitget Demo HTTP error {exc.code}") from None
        except (URLError, TimeoutError, json.JSONDecodeError) as exc:
            raise BitgetDemoError(f"Bitget Demo request failed: {self._redact(exc)}") from None
        if not isinstance(payload, dict) or payload.get("code") != "00000":
            code = payload.get("code") if isinstance(payload, dict) else "invalid-response"
            msg = payload.get("msg") if isinstance(payload, dict) else "invalid response"
            raise BitgetDemoError(
                f"Bitget Demo API error code={self._redact(code)} msg={self._redact(msg)}"
            )
        return payload

    @staticmethod
    def _data_rows(payload: Mapping[str, Any]) -> list[dict[str, Any]]:
        data = payload.get("data")
        if isinstance(data, list):
            return [item for item in data if isinstance(item, dict)]
        if isinstance(data, dict):
            for key in ("list", "positions", "positionList"):
                rows = data.get(key)
                if isinstance(rows, list):
                    return [item for item in rows if isinstance(item, dict)]
        return []

    @staticmethod
    def _positive_decimal(value: Decimal | str | float, *, field: str) -> str:
        try:
            parsed = Decimal(str(value))
        except (InvalidOperation, ValueError) as exc:
            raise ValueError(f"{field} must be a decimal") from exc
        if not parsed.is_finite() or parsed <= 0:
            raise ValueError(f"{field} must be positive")
        return format(parsed, "f")

    @staticmethod
    def _client_oid(value: str | None) -> str | None:
        if value is None:
            return None
        if not _CLIENT_OID_RE.fullmatch(value):
            raise ValueError("client_oid is not valid for Bitget")
        return value

    def instruments(self, symbol: str | None = None) -> list[dict[str, Any]]:
        params: dict[str, object] = {"category": USDT_FUTURES}
        if symbol:
            params["symbol"] = symbol
        payload = self._request("GET", "/api/v3/market/instruments", params=params, private=False)
        return self._data_rows(payload)

    def ticker(self, symbol: str) -> dict[str, Any]:
        payload = self._request(
            "GET",
            "/api/v3/market/tickers",
            params={"category": USDT_FUTURES, "symbol": symbol},
            private=False,
        )
        rows = self._data_rows(payload)
        if not rows:
            raise BitgetDemoError("Bitget Demo ticker response contained no rows")
        return rows[0]

    def account_info(self) -> dict[str, Any]:
        payload = self._request("GET", "/api/v3/account/info", private=True)
        data = payload.get("data")
        return data if isinstance(data, dict) else {}

    def account_settings(self) -> dict[str, Any]:
        payload = self._request("GET", "/api/v3/account/settings", private=True)
        data = payload.get("data")
        return data if isinstance(data, dict) else {}

    def account_assets(self) -> dict[str, Any]:
        payload = self._request("GET", "/api/v3/account/assets", private=True)
        data = payload.get("data")
        return data if isinstance(data, dict) else {}

    def current_positions(self, symbol: str | None = None) -> list[dict[str, Any]]:
        params: dict[str, object] = {"category": USDT_FUTURES}
        if symbol:
            params["symbol"] = symbol
        payload = self._request(
            "GET", "/api/v3/position/current-position", params=params, private=True
        )
        return self._data_rows(payload)

    def open_orders(self, symbol: str | None = None) -> list[dict[str, Any]]:
        params: dict[str, object] = {"category": USDT_FUTURES}
        if symbol:
            params["symbol"] = symbol
        payload = self._request("GET", "/api/v3/trade/unfilled-orders", params=params, private=True)
        return self._data_rows(payload)

    def validate_uta_hedge_demo(self, *, minimum_usdt: Decimal | str = "0") -> DemoAccountState:
        info = self.account_info()
        permissions = info.get("permissions")
        if isinstance(permissions, list) and "withdraw" in permissions:
            raise BitgetDemoError("Bitget Demo API key must not have withdrawal permission")
        settings = self.account_settings()
        assets = self.account_assets()
        account_mode = str(settings.get("accountMode") or "")
        hold_mode = str(settings.get("holdMode") or "")
        if account_mode not in {"hybrid", "unified"}:
            raise BitgetDemoError(f"unsupported UTA account mode: {self._redact(account_mode)}")
        if hold_mode != "hedge_mode":
            raise BitgetDemoError(f"expected hedge_mode, got {self._redact(hold_mode)}")
        try:
            equity = Decimal(str(assets.get("usdtEquity") or "0"))
            minimum = Decimal(str(minimum_usdt))
        except InvalidOperation as exc:
            raise BitgetDemoError("invalid Bitget Demo USDT equity") from exc
        if equity < minimum:
            raise BitgetDemoError(f"insufficient Bitget Demo USDT equity: {equity}")
        return DemoAccountState(
            account_mode=account_mode,
            account_level=str(settings.get("accountLevel") or ""),
            hold_mode=hold_mode,
            usdt_equity=equity,
        )

    def place_market_order(
        self,
        *,
        symbol: str,
        quantity: Decimal | str | float,
        side: str,
        pos_side: str,
        client_oid: str | None = None,
    ) -> dict[str, Any]:
        if side not in {"buy", "sell"}:
            raise ValueError("side must be buy or sell")
        if pos_side not in {"long", "short"}:
            raise ValueError("pos_side must be long or short")
        body: dict[str, object] = {
            "category": USDT_FUTURES,
            "symbol": symbol,
            "orderType": "market",
            "qty": self._positive_decimal(quantity, field="quantity"),
            "side": side,
            "posSide": pos_side,
        }
        validated_oid = self._client_oid(client_oid)
        if validated_oid:
            body["clientOid"] = validated_oid
        payload = self._request("POST", "/api/v3/trade/place-order", body=body, private=True)
        data = payload.get("data")
        return data if isinstance(data, dict) else {}

    def close_position(
        self,
        *,
        symbol: str,
        quantity: Decimal | str | float,
        pos_side: str,
        client_oid: str | None = None,
    ) -> dict[str, Any]:
        if pos_side == "long":
            side = "sell"
        elif pos_side == "short":
            side = "buy"
        else:
            raise ValueError("pos_side must be long or short")
        return self.place_market_order(
            symbol=symbol,
            quantity=quantity,
            side=side,
            pos_side=pos_side,
            client_oid=client_oid,
        )

    def cancel_order(
        self,
        *,
        order_id: str | None = None,
        client_oid: str | None = None,
    ) -> dict[str, Any]:
        if not order_id and not client_oid:
            raise ValueError("order_id or client_oid is required")
        body: dict[str, object] = {"category": USDT_FUTURES}
        if order_id:
            body["orderId"] = str(order_id)
        elif client_oid:
            body["clientOid"] = self._client_oid(client_oid)
        payload = self._request("POST", "/api/v3/trade/cancel-order", body=body, private=True)
        data = payload.get("data")
        return data if isinstance(data, dict) else {}
