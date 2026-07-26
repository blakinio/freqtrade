from __future__ import annotations

import json
import os
import time
import urllib.error
import urllib.parse
import urllib.request
from typing import Any

BASE_URL = "https://rest.coinapi.io"
KEY = os.environ.get("COINAPI_KEY", "")
TARGETS = (
    ("BYBIT", "BYBIT_PERP_BTC_USDT"),
    ("BYBIT", "BYBIT_PERP_ETH_USDT"),
    ("BINANCEFTS", "BINANCEFTS_PERP_BTC_USDT"),
    ("BINANCEFTS", "BINANCEFTS_PERP_ETH_USDT"),
)
PREFERRED_METRICS = (
    "LIQUIDATION_FILLED_ACCUMULATED_QUANTITY",
    "LIQUIDATION_QUANTITY",
    "LIQUIDATION_PRICE",
    "LIQUIDATION_TIME",
)

if not KEY:
    print("COINAPI_SECRET_PRESENT=false")
    raise SystemExit(2)
print("COINAPI_SECRET_PRESENT=true")

request_count = 0


def request_json(path: str, params: dict[str, str]) -> tuple[int, Any]:
    global request_count
    query = urllib.parse.urlencode(params)
    url = f"{BASE_URL}{path}?{query}" if query else f"{BASE_URL}{path}"
    request = urllib.request.Request(
        url,
        headers={
            "Accept": "application/json",
            "User-Agent": "freqtrade-liquid20-coinapi-trial/1",
            "X-CoinAPI-Key": KEY,
        },
    )
    request_count += 1
    try:
        with urllib.request.urlopen(request, timeout=45) as response:
            status = response.status
            body = response.read()
    except urllib.error.HTTPError as exc:
        status = exc.code
        body = exc.read()
    finally:
        time.sleep(1.1)
    try:
        return status, json.loads(body)
    except json.JSONDecodeError:
        return status, {"non_json_bytes": len(body)}


def summarize_error(payload: Any) -> dict[str, Any]:
    if isinstance(payload, dict):
        return {"response_keys": sorted(payload)}
    return {"response_type": type(payload).__name__}


results: list[dict[str, Any]] = []
for exchange_id, symbol_id in TARGETS:
    target: dict[str, Any] = {
        "exchange_id": exchange_id,
        "symbol_id": symbol_id,
    }

    symbol_status, symbol_payload = request_json(
        f"/v1/symbols/{exchange_id}/active",
        {"filter_symbol_id": symbol_id},
    )
    target["symbol_http_status"] = symbol_status
    if symbol_status == 200 and isinstance(symbol_payload, list):
        exact = [
            row
            for row in symbol_payload
            if isinstance(row, dict) and row.get("symbol_id") == symbol_id
        ]
        target["symbol_match_count"] = len(exact)
        if exact:
            row = exact[0]
            target["symbol_type"] = row.get("symbol_type")
            target["data_start"] = row.get("data_start")
            target["data_end"] = row.get("data_end")
    else:
        target["symbol_error"] = summarize_error(symbol_payload)

    listing_status, listing_payload = request_json(
        "/v1/metrics/symbol/listing",
        {"symbol_id": symbol_id},
    )
    target["listing_http_status"] = listing_status
    metrics: list[str] = []
    if listing_status == 200 and isinstance(listing_payload, list):
        metrics = sorted(
            {
                row["metric_id"]
                for row in listing_payload
                if isinstance(row, dict)
                and row.get("symbol_id") == symbol_id
                and isinstance(row.get("metric_id"), str)
                and "LIQUIDATION" in row["metric_id"]
            }
        )
        target["liquidation_metrics"] = metrics
    else:
        target["listing_error"] = summarize_error(listing_payload)

    selected_metric = next(
        (metric for metric in PREFERRED_METRICS if metric in metrics),
        None,
    )
    target["selected_metric"] = selected_metric
    if selected_metric:
        history_status, history_payload = request_json(
            "/v1/metrics/symbol/history",
            {
                "metric_id": selected_metric,
                "symbol_id": symbol_id,
                "time_start": "2025-02-26T00:00:00Z",
                "time_end": "2025-03-02T00:00:00Z",
                "period_id": "1SEC",
                "limit": "100",
            },
        )
        target["history_http_status"] = history_status
        if history_status == 200 and isinstance(history_payload, list):
            rows = [row for row in history_payload if isinstance(row, dict)]
            target["history_row_count"] = len(rows)
            target["history_response_keys"] = sorted({key for row in rows for key in row})
            starts = [
                row.get("time_period_start")
                for row in rows
                if isinstance(row.get("time_period_start"), str)
            ]
            if starts:
                target["history_first_period_start"] = min(starts)
                target["history_last_period_start"] = max(starts)
            counts = [
                row.get("count")
                for row in rows
                if isinstance(row.get("count"), (int, float))
            ]
            target["history_max_count"] = max(counts) if counts else None
            target["history_has_multi_value_bucket"] = any(value > 1 for value in counts)
            target["history_has_entry_time"] = any("entry_time" in row for row in rows)
            target["history_has_recv_time"] = any("recv_time" in row for row in rows)
        else:
            target["history_error"] = summarize_error(history_payload)

        current_status, current_payload = request_json(
            "/v1/metrics/symbol/current",
            {"metric_id": selected_metric, "symbol_id": symbol_id},
        )
        target["current_http_status"] = current_status
        if current_status == 200 and isinstance(current_payload, list):
            rows = [row for row in current_payload if isinstance(row, dict)]
            target["current_row_count"] = len(rows)
            target["current_response_keys"] = sorted({key for row in rows for key in row})
            target["current_has_entry_time"] = any("entry_time" in row for row in rows)
            target["current_has_recv_time"] = any("recv_time" in row for row in rows)
        else:
            target["current_error"] = summarize_error(current_payload)

    results.append(target)
    print("COINAPI_TARGET_SUMMARY=" + json.dumps(target, sort_keys=True))

print(f"COINAPI_REQUEST_COUNT={request_count}")
print(
    "COINAPI_TRIAL_SUMMARY="
    + json.dumps(
        {
            "target_count": len(results),
            "all_symbols_present": all(
                item.get("symbol_match_count") == 1 for item in results
            ),
            "all_listings_authorized": all(
                item.get("listing_http_status") == 200 for item in results
            ),
            "all_have_liquidation_metrics": all(
                bool(item.get("liquidation_metrics")) for item in results
            ),
            "all_history_authorized": all(
                item.get("history_http_status") == 200 for item in results
            ),
            "all_history_have_provider_receive_time": all(
                item.get("history_has_entry_time") is True
                and item.get("history_has_recv_time") is True
                for item in results
            ),
        },
        sort_keys=True,
    )
)
