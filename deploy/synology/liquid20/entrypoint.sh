#!/bin/sh
set -eu

umask 027

MODE="${LIQUID20_MODE:-smoke}"
HOST_ID="${LIQUIDATION_STAGING_HOST_ID:-synology-01}"
COLLECTOR_COMMIT="${COLLECTOR_COMMIT:-}"
IMAGE_COMMIT="$(cat /app/COLLECTOR_COMMIT)"
RUN_ID="${RUN_ID:-liquid20-$(date -u +%Y%m%dT%H%M%SZ)-$$}"
DATA_ROOT="${LIQUID20_DATA_ROOT:-/data/runs}"
POLICY="/app/ai_platform/research/liquidations/multi-source-acceptance-policy-v1.json"
RUN_ROOT="$DATA_ROOT/$RUN_ID"
REPORT="$RUN_ROOT/multi-source-acceptance-report.json"

case "$MODE" in
  smoke)
    DURATION_SECONDS="${LIQUID20_DURATION_SECONDS:-60}"
    case "$DURATION_SECONDS" in
      *[!0-9]* | "")
        echo "LIQUID20_DURATION_SECONDS must be a positive integer" >&2
        exit 64
        ;;
    esac
    if [ "$DURATION_SECONDS" -lt 1 ] || [ "$DURATION_SECONDS" -gt 3600 ]; then
      echo "Smoke duration must be between 1 and 3600 seconds" >&2
      exit 64
    fi
    ;;
  acceptance)
    DURATION_SECONDS=86400
    ;;
  *)
    echo "LIQUID20_MODE must be smoke or acceptance" >&2
    exit 64
    ;;
esac

if ! printf '%s' "$COLLECTOR_COMMIT" | grep -Eq '^[0-9a-fA-F]{40}$'; then
  echo "COLLECTOR_COMMIT must be the exact 40-character Git commit used to build the image" >&2
  exit 64
fi

if [ "$COLLECTOR_COMMIT" != "$IMAGE_COMMIT" ]; then
  echo "Runtime COLLECTOR_COMMIT does not match the commit embedded in the image" >&2
  exit 64
fi

if [ -n "${BYBIT_API_KEY:-}${BYBIT_API_SECRET:-}${BINANCE_API_KEY:-}${BINANCE_API_SECRET:-}${FT_EXCHANGE_KEY:-}${FT_EXCHANGE_SECRET:-}${FREQTRADE__EXCHANGE__KEY:-}${FREQTRADE__EXCHANGE__SECRET:-}" ]; then
  echo "Trading credentials are present; the data-only container refuses to start" >&2
  exit 64
fi

mkdir -p "$DATA_ROOT"

if [ -e "$RUN_ROOT" ]; then
  echo "Run directory already exists: $RUN_ROOT" >&2
  exit 73
fi

printf 'Starting liquid20 mode=%s run_id=%s host_id=%s commit=%s duration=%ss\n' \
  "$MODE" "$RUN_ID" "$HOST_ID" "$COLLECTOR_COMMIT" "$DURATION_SECONDS"

collector_rc=0
LIQUIDATION_STAGING_HOST_ID="$HOST_ID" \
python -m ai_platform.scripts.liquidation_multi_source_runner \
  --profile liquid20-v1 \
  --duration-seconds "$DURATION_SECONDS" \
  --require-new-output \
  --run-id "$RUN_ID" \
  --host-id "$HOST_ID" \
  --collector-commit "$COLLECTOR_COMMIT" \
  --output-root "$RUN_ROOT" || collector_rc=$?

evaluator_rc=0
if [ "$MODE" = "acceptance" ]; then
  if [ -f "$RUN_ROOT/multi-source-manifest.json" ]; then
    python -m ai_platform.scripts.liquidation_multi_source_evaluator \
      --run-root "$RUN_ROOT" \
      --policy "$POLICY" \
      --output "$REPORT" || evaluator_rc=$?
  else
    echo "Acceptance manifest is missing; evaluator cannot run" >&2
    evaluator_rc=66
  fi
fi

hash_rc=0
if [ -d "$RUN_ROOT" ]; then
  (
    cd "$RUN_ROOT"
    find . -maxdepth 1 -type f ! -name artifact-sha256.txt -print0 \
      | sort -z \
      | xargs -0 -r sha256sum > artifact-sha256.txt
    sha256sum --check artifact-sha256.txt
  ) || hash_rc=$?
fi

if [ "$collector_rc" -ne 0 ] || [ "$evaluator_rc" -ne 0 ] || [ "$hash_rc" -ne 0 ]; then
  printf 'Liquid20 run failed: collector=%s evaluator=%s hashes=%s root=%s\n' \
    "$collector_rc" "$evaluator_rc" "$hash_rc" "$RUN_ROOT" >&2
  exit 1
fi

if [ "$MODE" = "smoke" ]; then
  printf 'Smoke completed. Inspect artifacts in %s before starting acceptance mode.\n' "$RUN_ROOT"
else
  printf 'Acceptance collection completed. Review %s and preserve the entire run directory unchanged.\n' "$REPORT"
fi
