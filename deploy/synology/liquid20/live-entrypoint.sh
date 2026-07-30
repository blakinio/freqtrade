#!/bin/sh
set -eu

umask 027

HOST_ID="${LIQUIDATION_STAGING_HOST_ID:-synology-01}"
COLLECTOR_COMMIT="${COLLECTOR_COMMIT:-}"
IMAGE_COMMIT="$(cat /app/COLLECTOR_COMMIT)"
DATA_ROOT="${LIQUID20_DATA_ROOT:-/data}"
HEARTBEAT_SECONDS="${LIQUID20_HEARTBEAT_SECONDS:-5}"
SYMBOL_REFRESH_SECONDS="${LIQUID20_SYMBOL_REFRESH_SECONDS:-3600}"
MAXIMUM_SYMBOLS="${LIQUID20_MAXIMUM_SYMBOLS:-1000}"

if ! printf '%s' "$COLLECTOR_COMMIT" | grep -Eq '^[0-9a-fA-F]{40}$'; then
  echo "COLLECTOR_COMMIT must be the exact 40-character Git commit used to build the image" >&2
  exit 64
fi

if [ "$COLLECTOR_COMMIT" != "$IMAGE_COMMIT" ]; then
  echo "Runtime COLLECTOR_COMMIT does not match the commit embedded in the image" >&2
  exit 64
fi

if [ -n "${BYBIT_API_KEY:-}${BYBIT_API_SECRET:-}${BINANCE_API_KEY:-}${BINANCE_API_SECRET:-}${OKX_API_KEY:-}${OKX_API_SECRET:-}${OKX_SECRET_KEY:-}${OKX_PASSPHRASE:-}${FT_EXCHANGE_KEY:-}${FT_EXCHANGE_SECRET:-}${FREQTRADE__EXCHANGE__KEY:-}${FREQTRADE__EXCHANGE__SECRET:-}" ]; then
  echo "Trading credentials are present; the live data-only container refuses to start" >&2
  exit 64
fi

mkdir -p "$DATA_ROOT/live/runs"

exec python -m ai_platform.scripts.liquidation_live_stream_okx \
  --data-root "$DATA_ROOT" \
  --collector-commit "$COLLECTOR_COMMIT" \
  --host-id "$HOST_ID" \
  --heartbeat-seconds "$HEARTBEAT_SECONDS" \
  --symbol-refresh-seconds "$SYMBOL_REFRESH_SECONDS" \
  --maximum-symbols "$MAXIMUM_SYMBOLS"
