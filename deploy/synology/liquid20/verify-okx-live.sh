#!/usr/bin/env bash
set -Eeuo pipefail

container_name="${LIQUID20_CONTAINER_NAME:-liquid20-live}"
portal_url="${LIQUID20_PORTAL_HEALTH_URL:-}"

observation="$(docker exec --interactive "$container_name" python - <<'PY'
import json
from pathlib import Path

root = Path('/data')
pointer = root / 'live' / 'live-state-v1.json'
if not pointer.is_file() or pointer.is_symlink():
    raise SystemExit('live-state pointer is unavailable')
payload = json.loads(pointer.read_text(encoding='utf-8'))
state = payload.get('state', {})
sources = state.get('sources', {})
for source in ('bybit-linear', 'binance-usdm', 'okx-swap'):
    item = sources.get(source)
    if not isinstance(item, dict):
        raise SystemExit(f'missing source state: {source}')
    if item.get('configured') is not True or item.get('connected') is not True:
        raise SystemExit(f'source is not connected: {source}')
    if not isinstance(item.get('last_heartbeat_at_ms'), int):
        raise SystemExit(f'source heartbeat is missing: {source}')
okx = sources['okx-swap']
run_root = root / 'live' / 'runs' / str(state.get('run_id'))
output = run_root / 'okx-swap.ndjson'
summary = run_root / 'okx-swap-summary.json'
if not output.is_file() or output.is_symlink():
    raise SystemExit('OKX NDJSON is unavailable')
if not summary.is_file() or summary.is_symlink():
    raise SystemExit('OKX summary is unavailable')
summary_payload = json.loads(summary.read_text(encoding='utf-8'))
if summary_payload.get('orders_submitted') != 0:
    raise SystemExit('orders_submitted is not zero')
print(json.dumps({
    'run_id': state.get('run_id'),
    'collector_heartbeat_at_ms': state.get('collector_heartbeat_at_ms'),
    'okx': okx,
    'binance': sources['binance-usdm'],
    'bybit': sources['bybit-linear'],
    'okx_file_bytes': output.stat().st_size,
    'orders_submitted': summary_payload.get('orders_submitted'),
}, separators=(',', ':'), sort_keys=True))
PY
)"

python3 - "$observation" <<'PY'
import json
import sys
payload = json.loads(sys.argv[1])
assert payload['okx']['configured'] is True
assert payload['okx']['connected'] is True
assert payload['orders_submitted'] == 0
print(json.dumps(payload, indent=2, sort_keys=True))
PY

if [[ -n "$portal_url" ]]; then
    portal="$(curl --fail --silent --show-error --header 'accept: application/json' "$portal_url")"
    python3 - "$portal" <<'PY'
import json
import sys
health = json.loads(sys.argv[1])
okx = health.get('sources', {}).get('okx-swap', {})
if okx.get('configured') is not True or okx.get('connected') is not True:
    raise SystemExit('Portal does not expose connected OKX SWAP')
print('Portal OKX SWAP verified')
PY
fi
