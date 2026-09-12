from __future__ import annotations

import base64
import hashlib
import hmac
import json
from decimal import Decimal
from typing import Any, Self

import pytest

from ai_platform.wickhunter.bitget_demo_uta import (
    BITGET_REST_BASE,
    BitgetDemoCredentials,
    BitgetDemoError,
    BitgetDemoUTAClient,
)


class FakeResponse:
    def __init__(self, payload: dict[str, Any]) -> None:
        self._data = json.dumps(payload).encode()

    def __enter__(self) -> Self:
        return self

    def __exit__(self, *_args: object) -> None:
        return None

    def read(self) -> bytes:
        return self._data


class FakeOpener:
    def __init__(self, *payloads: dict[str, Any]) -> None:
        self.payloads = list(payloads)
        self.requests: list[tuple[Any, float]] = []

    def __call__(self, request: Any, *, timeout: float) -> FakeResponse:
        self.requests.append((request, timeout))
        if not self.payloads:
            raise AssertionError("unexpected request")
        return FakeResponse(self.payloads.pop(0))


def success(data: Any) -> dict[str, Any]:
    return {"code": "00000", "msg": "success", "data": data}


@pytest.fixture
def credentials() -> BitgetDemoCredentials:
    return BitgetDemoCredentials("demo-key", "demo-secret", "demo-passphrase")


def test_credentials_use_demo_environment_only() -> None:
    creds = BitgetDemoCredentials.from_env(
        {
            "BITGET_DEMO_API_KEY": "key",
            "BITGET_DEMO_SECRET": "secret",
            "BITGET_DEMO_PASSPHRASE": "pass",
            "BITGET_API_KEY": "live-key-must-be-ignored",
        }
    )
    assert creds == BitgetDemoCredentials("key", "secret", "pass")

    with pytest.raises(BitgetDemoError, match="missing Bitget Demo API credentials"):
        BitgetDemoCredentials.from_env({"BITGET_API_KEY": "live-only"})


def test_private_request_is_pinned_to_demo_header_and_signature(
    credentials: BitgetDemoCredentials,
) -> None:
    opener = FakeOpener(success({"accountMode": "hybrid"}))
    client = BitgetDemoUTAClient(credentials, opener=opener, clock=lambda: 1234.567)

    assert client.account_settings()["accountMode"] == "hybrid"
    request, timeout = opener.requests[0]
    headers = {key.lower(): value for key, value in request.header_items()}

    assert request.full_url == f"{BITGET_REST_BASE}/api/v3/account/settings"
    assert timeout == 12.0
    assert headers["paptrading"] == "1"
    assert headers["access-key"] == "demo-key"
    assert headers["access-passphrase"] == "demo-passphrase"
    expected = base64.b64encode(
        hmac.new(
            b"demo-secret",
            b"1234567GET/api/v3/account/settings",
            hashlib.sha256,
        ).digest()
    ).decode()
    assert headers["access-sign"] == expected


def test_public_market_request_never_sends_private_headers(
    credentials: BitgetDemoCredentials,
) -> None:
    opener = FakeOpener(success([{"symbol": "BTCUSDT", "type": "perpetual"}]))
    client = BitgetDemoUTAClient(credentials, opener=opener)

    rows = client.instruments("BTCUSDT")
    request, _timeout = opener.requests[0]
    headers = {key.lower(): value for key, value in request.header_items()}

    assert rows[0]["symbol"] == "BTCUSDT"
    assert "paptrading" not in headers
    assert "access-key" not in headers
    assert "category=USDT-FUTURES" in request.full_url
    assert "symbol=BTCUSDT" in request.full_url


def test_validate_uta_hedge_demo_accepts_hybrid_account(
    credentials: BitgetDemoCredentials,
) -> None:
    opener = FakeOpener(
        success({"permissions": ["uta_mgt", "uta_trade"]}),
        success({"accountMode": "hybrid", "accountLevel": "basic", "holdMode": "hedge_mode"}),
        success({"usdtEquity": "1000"}),
    )
    client = BitgetDemoUTAClient(credentials, opener=opener)

    state = client.validate_uta_hedge_demo(minimum_usdt=Decimal(5))

    assert state.account_mode == "hybrid"
    assert state.account_level == "basic"
    assert state.hold_mode == "hedge_mode"
    assert state.usdt_equity == Decimal(1000)


def test_validate_uta_hedge_demo_fails_closed_on_classic_or_wrong_hold_mode(
    credentials: BitgetDemoCredentials,
) -> None:
    classic = FakeOpener(
        success({"permissions": ["uta_mgt", "uta_trade"]}),
        success({"accountMode": "classic", "holdMode": "hedge_mode"}),
        success({"usdtEquity": "1000"}),
    )
    with pytest.raises(BitgetDemoError, match="unsupported UTA account mode"):
        BitgetDemoUTAClient(credentials, opener=classic).validate_uta_hedge_demo()

    one_way = FakeOpener(
        success({"permissions": ["uta_mgt", "uta_trade"]}),
        success({"accountMode": "hybrid", "holdMode": "one_way_mode"}),
        success({"usdtEquity": "1000"}),
    )
    with pytest.raises(BitgetDemoError, match="expected hedge_mode"):
        BitgetDemoUTAClient(credentials, opener=one_way).validate_uta_hedge_demo()


def test_market_order_and_close_long_use_uta_hedge_shapes(
    credentials: BitgetDemoCredentials,
) -> None:
    opener = FakeOpener(success({"orderId": "open-1"}), success({"orderId": "close-1"}))
    client = BitgetDemoUTAClient(credentials, opener=opener)

    opened = client.place_market_order(
        symbol="BTCUSDT",
        quantity=Decimal("0.0001"),
        side="buy",
        pos_side="long",
        client_oid="demo-open-1",
    )
    closed = client.close_position(
        symbol="BTCUSDT",
        quantity="0.0001",
        pos_side="long",
        client_oid="demo-close-1",
    )

    assert opened["orderId"] == "open-1"
    assert closed["orderId"] == "close-1"
    open_body = json.loads(opener.requests[0][0].data)
    close_body = json.loads(opener.requests[1][0].data)
    assert open_body == {
        "category": "USDT-FUTURES",
        "symbol": "BTCUSDT",
        "orderType": "market",
        "qty": "0.0001",
        "side": "buy",
        "posSide": "long",
        "clientOid": "demo-open-1",
    }
    assert close_body["side"] == "sell"
    assert close_body["posSide"] == "long"
    assert close_body["qty"] == "0.0001"


def test_close_short_uses_buy_side(credentials: BitgetDemoCredentials) -> None:
    opener = FakeOpener(success({"orderId": "close-short"}))
    client = BitgetDemoUTAClient(credentials, opener=opener)

    client.close_position(
        symbol="BTCUSDT",
        quantity="0.0001",
        pos_side="short",
        client_oid="demo-close-short",
    )

    body = json.loads(opener.requests[0][0].data)
    assert body["side"] == "buy"
    assert body["posSide"] == "short"


def test_cancel_order_uses_uta_endpoint_and_demo_header(
    credentials: BitgetDemoCredentials,
) -> None:
    opener = FakeOpener(success({"orderId": "123"}))
    client = BitgetDemoUTAClient(credentials, opener=opener)

    result = client.cancel_order(order_id="123")

    request, _timeout = opener.requests[0]
    headers = {key.lower(): value for key, value in request.header_items()}
    assert result["orderId"] == "123"
    assert request.full_url == f"{BITGET_REST_BASE}/api/v3/trade/cancel-order"
    assert headers["paptrading"] == "1"
    assert json.loads(request.data) == {"category": "USDT-FUTURES", "orderId": "123"}


def test_vendor_error_redacts_all_demo_credentials(credentials: BitgetDemoCredentials) -> None:
    opener = FakeOpener(
        {
            "code": "40000",
            "msg": "demo-key demo-secret demo-passphrase should never escape",
            "data": None,
        }
    )
    client = BitgetDemoUTAClient(credentials, opener=opener)

    with pytest.raises(BitgetDemoError) as exc_info:
        client.account_settings()

    message = str(exc_info.value)
    assert "demo-key" not in message
    assert "demo-secret" not in message
    assert "demo-passphrase" not in message
    assert "[REDACTED]" in message


def test_adapter_exposes_no_withdraw_or_transfer_surface(
    credentials: BitgetDemoCredentials,
) -> None:
    client = BitgetDemoUTAClient(credentials)
    assert not hasattr(client, "withdraw")
    assert not hasattr(client, "transfer")


@pytest.mark.parametrize("quantity", ["0", "-1", "NaN", "Infinity"])
def test_order_quantity_must_be_positive_finite(
    credentials: BitgetDemoCredentials,
    quantity: str,
) -> None:
    client = BitgetDemoUTAClient(credentials, opener=FakeOpener())
    with pytest.raises(ValueError, match="quantity must be positive"):
        client.place_market_order(
            symbol="BTCUSDT",
            quantity=quantity,
            side="buy",
            pos_side="long",
        )


def test_validate_demo_rejects_withdraw_enabled_key(
    credentials: BitgetDemoCredentials,
) -> None:
    opener = FakeOpener(success({"permissions": ["uta_mgt", "uta_trade", "withdraw"]}))
    client = BitgetDemoUTAClient(credentials, opener=opener)

    with pytest.raises(BitgetDemoError, match="must not have withdrawal permission"):
        client.validate_uta_hedge_demo()
