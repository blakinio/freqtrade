# Liquid20 continuous live/shadow service

This service is separate from accepted Liquid20 evidence runs.

## Data layout

- accepted evidence: `./data/runs/` — never modified by the live service;
- continuous state: `./data/live/live-state-v1.json`;
- rotating live segments: `./data/live/runs/liquid20-*/`;
- source-separated files: `bybit-linear.ndjson`, `binance-usdm.ndjson` and `okx-swap.ndjson`;
- OKX public normalization evidence: `okx-swap-instruments-v1.json`;
- OKX data-only summary: `okx-swap-summary.json` with `orders_submitted: 0`.

The portal receives the whole host directory as `/liquid20-data:ro` and uses `PORTAL_LIQUIDATIONS_DATA_ROOT=/liquid20-data`.

## Local Compose operation

Copy `.env.example` to `.env`, set the exact 40-character commit and the existing non-root UID/GID, then build and start the default service:

```bash
docker compose build liquid20-live
docker compose up -d liquid20-live
```

The service uses `restart: unless-stopped`, has no published ports, no Docker socket and no trading credentials. It starts independent public Binance USD-M, Bybit Linear and OKX SWAP tasks. The dynamic public universe is bounded at 1000 instruments; the observed Bybit and Binance universes exceeded the earlier 500-instrument bound. Compose always enforces the 512 MiB memory limit. It intentionally does not declare CPU or PID cgroup limits because the target Synology kernel exposes neither capability.

OKX uses the public `liquidation-orders` SWAP channel and the public instruments snapshot. Contract count is converted by the accepted parser through validated public `ctVal` metadata. No account endpoint, order endpoint, replay, model training or strategy path is present.

The bounded evidence collector remains opt-in:

```bash
docker compose --profile evidence run --rm liquid20-evidence
```

Do not point the live entrypoint at an accepted run directory. It writes only under `./data/live/`.

## Controlled Synology deployment

Production deployment is performed by `.github/workflows/liquidations-live-synology.yml` after a reviewed commit reaches `develop`.

The deploy script distinguishes paths visible inside the runner container from paths resolved by the host Docker daemon:

- candidate runner path: `/var/lib/freqtrade-staging-state/liquidations-live-candidates/<run>`;
- matching Docker-host path: `/volume1/docker/freqtrade/state/liquidations-live-candidates/<run>`;
- production host data path: `/volume1/docker/freqtrade-liquidations/data`.

The collector always uses a non-zero UID. `LIQUID20_PUID` may override the documented `.env.example` UID; otherwise the checked-in `PUID` is used. The runtime GID is derived from the existing host data root, not trusted from an unset workflow variable, and must match any configured `LIQUID20_PGID`. This keeps the portal on the same minimum read group while the collector owns only the sibling `data/live` directories. A root-only helper may create and set mode/ownership on `data/live` and `data/live/runs`; it does not recurse and never changes `data/runs`.

`deploy-live.sh`:

1. builds `local/liquid20-collector:sha-<exact SHA>`;
2. probes Docker CPU and PID cgroup capabilities using the exact image;
3. applies a 1.0 CPU quota and 128-process limit only when their individual probes succeed;
4. accepts only the known Synology unsupported responses as compatibility fallbacks, while always retaining the 512 MiB memory limit;
5. fails closed for every unexpected capability-probe error;
6. inspects the host data root through a read-only helper mount and resolves a non-root runtime identity;
7. resolves the bounded dynamic universe from `.env.example` (`MAXIMUM_SYMBOLS=1000`);
8. starts an isolated candidate from the runner-state host path;
9. reads readiness directly from `/data` inside the running candidate and requires connected, non-empty public subscriptions before replacement;
10. observes an advancing candidate heartbeat;
11. creates or validates only `data/live` and `data/live/runs`;
12. records the previous production image and replaces `liquid20-live`;
13. requires connected production subscriptions and observes an advancing production heartbeat;
14. verifies non-root UID, the existing data-root GID, `unless-stopped`, no Docker socket, actual resource settings and unchanged accepted-evidence digest;
15. restores the previous image on failure;
16. uploads a JSON operational evidence report and the bounded deployment log.

The exact merged implementation is then verified through:

```bash
bash deploy/synology/liquid20/verify-okx-live.sh
```

This bounded step requires all three sources to be configured and connected, verifies source heartbeats, the OKX NDJSON and summary, and `orders_submitted == 0`. `LIQUID20_PORTAL_HEALTH_URL` may point to the authenticated same-origin Portal health endpoint to prove that the Portal exposes OKX.

The operational report records the universe bound, actual CPU/PID capability and application state, and the mandatory memory limit. Direct container observation avoids the repeated helper-container polling that exhausted the earlier 45-minute workflow timeout.

A real liquidation is not required during a short validation window. When none is observed, the report explicitly records that only heartbeat, subscription and deterministic append tests were proven.

## Automated operational health

`.github/workflows/liquidations-live-operational-health.yml` runs on the Synology runner every five minutes, after monitor changes reach `develop`, and on manual dispatch.

The collector checks cover:

- Docker container state, restart state and OOM state;
- the `liquidation-live-state-v1` contract and an active run;
- collector heartbeat freshness within 60 seconds;
- configured, connected and non-empty Binance, Bybit and OKX subscriptions;
- source heartbeat freshness within 60 seconds;
- missing writes and stale receive timestamps;
- parse errors and uncontrolled reconnect growth;
- continued execution-disabled, unauthorized and credential-free data-only state;
- data-volume usage below 90% and at least 20 GiB free.

The same run also checks the portal read path without production credentials:

- the running `freqtrade-portal-staging` container remains non-root, `unless-stopped`, read-only on `/liquid20-data` and without a Docker-socket mount;
- `/market/liquidations` returns `200`;
- the unauthenticated production health API remains protected by exact `401 SESSION_MISSING` and `Cache-Control: no-store`;
- the existing trusted `prove-liquidations-live.sh` creates an isolated candidate from the exact production image and image ID with the real Liquid20 root read-only, a read-only root filesystem, bounded tmpfs, `cap-drop ALL`, `no-new-privileges`, a 768 MiB memory limit and no Docker socket;
- fixture identity and its ephemeral session exist only inside that isolated candidate;
- candidate health/list/summary APIs return `200` and `no-store`;
- the portal health contract reports the current `LIVE`, `STALE` or `OFFLINE` state, active/completed run state, collector and portal timestamps, three-source connectivity, subscriptions, event counts, errors and reconnects;
- runtime and Portal source state must agree;
- only `LIVE` with fresh connected sources is healthy; `STALE`, `OFFLINE`, `HISTORICAL`, API/auth failures or candidate-security drift create an alert.

No cookie, token, authorization header or session payload is written to the combined report, workflow summary, issue or artifact.

An unhealthy check creates or updates one deduplicated GitHub issue named `[liquidations-live] operational health alert`, publishes the `liquidations-live-health` commit status as failure, fails the workflow and uploads the bounded collector/portal JSON reports for 14 days. Healthy checks publish success and do not upload artifacts. After full recovery, the monitor posts a recovery comment and closes the alert issue automatically.

Repository Issues must remain enabled for alert delivery. The Issues API channel was verified on 2026-07-29 by creating and immediately closing technical verification issue #728.

The combined check can be run manually on the Synology runner:

```bash
GH_TOKEN=... GITHUB_REPOSITORY=blakinio/freqtrade \
LIQUID20_REQUIRE_PORTAL_HEALTH=true \
LIQUID20_PORTAL_HEALTH_REPORT=/tmp/liquidations-live-portal-health.json \
LIQUID20_PORTAL_PROOF_SCRIPT=deploy/synology/portal/prove-liquidations-live.sh \
PORTAL_LIVE_PROOF_DELAY_SECONDS=5 \
python -m ai_platform.scripts.liquidation_operational_health
```

## Rollback

Automatic rollback runs when deployment fails after the old container is replaced. Manual rollback uses the previous exact image with the same hardened runtime arguments and the same `/data` bind mount.

Do not delete `./data/live/` during rollback. A stopped collector is represented by the portal as `STALE` and then `OFFLINE`; accepted evidence remains available separately as `HISTORICAL`.
