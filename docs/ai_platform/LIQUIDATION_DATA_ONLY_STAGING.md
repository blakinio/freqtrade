# Liquidation Data-Only Staging Runbook

## Purpose

Operate only the public liquidation collector long enough to produce measurable transport and data-integrity
evidence. This stage does not load Freqtrade, does not create entry intent, and must not receive exchange API
credentials.

Authoritative policy:

`ai_platform/research/liquidations/data-only-staging-policy-v1.json`

## Safety boundary

The staging process must satisfy all of these conditions:

- public Bybit REST and WebSocket endpoints only;
- dedicated unprivileged service account;
- no exchange keys, secrets, wallet credentials, or withdrawal capability;
- no Freqtrade strategy, RPC, execution adapter, order endpoint, DCA, TP, SL, or leverage;
- a unique new output file for every judged run;
- the collector Git commit recorded in the summary;
- files overlapping `20260801-20260930` cannot be selected for training, tuning, replay, or iterative
  evaluation of the protected final holdout.

The collector checks common Bybit and Freqtrade credential environment names and records only a boolean. It
never records credential values.

## Evidence files

A bounded run produces:

```text
events.ndjson
collector-summary.json
staging-evaluation.json
```

The summary records:

- source endpoint and exact subscribed symbols;
- collector commit;
- local-versus-Bybit clock probe;
- start, end, and bounded duration;
- successful connection intervals and availability;
- disconnect count and hourly rate;
- received control and liquidation messages;
- parsed, written, duplicate, and rejected event counts;
- per-symbol event counts;
- event ingest-latency histogram;
- initial and final file size;
- event line count;
- SHA-256 of the NDJSON file;
- execution-disabled and credential-presence booleans.

## Transport smoke

A smoke confirms that the code can reach the public endpoints and generate internally consistent evidence. It
does not establish representative event volume or Stage 1 acceptance.

From a clean checkout of the candidate commit:

```bash
set -euo pipefail

POLICY=ai_platform/research/liquidations/data-only-staging-policy-v1.json
RUN_DIR="$(mktemp -d)"
COMMIT="$(git rev-parse HEAD)"

PYTHONPATH=. python -m ai_platform.scripts.liquidation_collector \
  --symbol BTCUSDT \
  --symbol ETHUSDT \
  --duration-seconds 30 \
  --require-new-output \
  --collector-commit "$COMMIT" \
  --output "$RUN_DIR/events.ndjson" \
  --summary "$RUN_DIR/collector-summary.json"

PYTHONPATH=. python -m ai_platform.scripts.liquidation_staging_evaluator \
  --summary "$RUN_DIR/collector-summary.json" \
  --policy "$POLICY" \
  --mode smoke \
  --output "$RUN_DIR/staging-evaluation.json"
```

A smoke may pass with zero liquidation events. The public topic sends actual liquidation updates, while the
subscription acknowledgement is sufficient to prove an established and responsive transport.

## Twenty-four-hour acceptance run

Run this only on an always-on host with synchronized time and durable local storage. Do not use a short-lived
CI runner as the Stage 1 acceptance host.

Example host preparation:

```bash
sudo useradd --system --home /var/lib/freqtrade/liquidations \
  --shell /usr/sbin/nologin ft-liquidation || true
sudo install -d -m 0750 -o ft-liquidation -g ft-liquidation \
  /var/lib/freqtrade/liquidations/runs
```

Select a unique run directory and verify the checkout:

```bash
set -euo pipefail

REPO=/opt/freqtrade
RUN_ID="$(date -u +%Y%m%dT%H%M%SZ)"
RUN_DIR="/var/lib/freqtrade/liquidations/runs/$RUN_ID"
COMMIT="$(git -C "$REPO" rev-parse HEAD)"

sudo install -d -m 0750 -o ft-liquidation -g ft-liquidation "$RUN_DIR"
git -C "$REPO" status --short
git -C "$REPO" rev-parse "$COMMIT^{commit}"
```

Start the bounded collector as the unprivileged account:

```bash
sudo -u ft-liquidation env \
  PYTHONPATH="$REPO" \
  "$REPO/.venv/bin/python" -m ai_platform.scripts.liquidation_collector \
  --symbol BTCUSDT \
  --symbol ETHUSDT \
  --duration-seconds 86400 \
  --require-new-output \
  --collector-commit "$COMMIT" \
  --output "$RUN_DIR/events.ndjson" \
  --summary "$RUN_DIR/collector-summary.json"
```

Evaluate the frozen acceptance policy:

```bash
sudo -u ft-liquidation env \
  PYTHONPATH="$REPO" \
  "$REPO/.venv/bin/python" -m ai_platform.scripts.liquidation_staging_evaluator \
  --summary "$RUN_DIR/collector-summary.json" \
  --policy "$REPO/ai_platform/research/liquidations/data-only-staging-policy-v1.json" \
  --mode acceptance \
  --output "$RUN_DIR/staging-evaluation.json"
```

## Acceptance gates

The prospective acceptance mode requires:

- duration at least 86,400 seconds;
- exact Bybit linear endpoint and exact `BTCUSDT`, `ETHUSDT` subscription;
- synchronized clock with absolute server-time skew at most two seconds;
- availability at least `0.995`;
- zero parse failures;
- at most two disconnects per hour;
- duplicate ratio at most `0.01`;
- at least ten latency samples;
- no more than `0.01` of latency samples above five seconds;
- at least one observed event for each symbol;
- new output file, matching event line count, and valid SHA-256;
- recorded 40-character Git commit;
- execution disabled and no detected trading credential environment.

Failure is evidence. Do not edit the policy after seeing the run. Start a new declared policy/version if a gate
must change.

## Freeze or quarantine

After evaluation:

```bash
sha256sum \
  "$RUN_DIR/events.ndjson" \
  "$RUN_DIR/collector-summary.json" \
  "$RUN_DIR/staging-evaluation.json" \
  > "$RUN_DIR/artifact-sha256.txt"

chmod 0440 \
  "$RUN_DIR/events.ndjson" \
  "$RUN_DIR/collector-summary.json" \
  "$RUN_DIR/staging-evaluation.json" \
  "$RUN_DIR/artifact-sha256.txt"
```

If `staging-evaluation.json` reports `passed: true`, preserve the directory unchanged as accepted Stage 1
evidence. If it reports `passed: false`, move the complete directory to quarantine and retain the failed gates;
do not delete, rewrite, merge, or fabricate missing intervals.

## Operational response

- Process exit before the bounded duration: preserve the partial summary and quarantine the run.
- Clock probe unknown or false: quarantine the run.
- Credential detection true: stop immediately, remove credentials from the service environment, and start a
  new run with a new directory.
- Output file already non-empty: do not append to a judged run; select a new run ID.
- Parse failure: preserve the raw run, repair the parser on a new branch, and restart under a new policy/commit.
- Disconnect: preserve the recorded connection intervals; never conceal the disconnected window.
- Storage full or filesystem error: stop and quarantine; never continue without durable writes.

## Promotion boundary

An accepted Stage 1 directory permits preparation of a separately declared frozen research dataset. It does
not authorize deterministic replay, signal-only dry-run, Freqtrade dry-run, DCA, live-small, or any
profitability claim.
