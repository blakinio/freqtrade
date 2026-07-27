# Liquid20 continuous live/shadow service

This service is separate from accepted Liquid20 evidence runs.

## Data layout

- accepted evidence: `./data/runs/` — never modified by the live service;
- continuous state: `./data/live/live-state-v1.json`;
- rotating live segments: `./data/live/runs/liquid20-*/`.

The portal receives the whole host directory as `/liquid20-data:ro` and uses `PORTAL_LIQUIDATIONS_DATA_ROOT=/liquid20-data`.

## Local Compose operation

Copy `.env.example` to `.env`, set the exact 40-character commit and the existing non-root UID/GID, then build and start the default service:

```bash
docker compose build liquid20-live
docker compose up -d liquid20-live
```

The service uses `restart: unless-stopped`, has no published ports, no Docker socket and no trading credentials.

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

The collector always uses a non-zero UID. `LIQUID20_PUID` may override the documented `.env.example` UID; otherwise the checked-in `PUID` is used. The runtime GID is derived from the existing host data root, not trusted from an unset workflow variable, and must match any configured `LIQUID20_PGID`. This keeps the portal on the same minimum read group while the collector owns only the sibling `data/live` directories. A root-only helper may create and set mode/ownership on `data/live` and `data/live/runs`; it does not recurse and never changes `data/runs`. The controlled Synology path intentionally omits Docker `NanoCPUs`/`--cpus` because the target kernel may not expose CPU CFS; the 512 MiB memory and 128-process limits remain enforced.

`deploy-live.sh`:

1. builds `local/liquid20-collector:sha-<exact SHA>`;
2. inspects the host data root through a read-only helper mount and resolves a non-root runtime identity;
3. starts an isolated candidate from the runner-state host path;
4. observes two advancing heartbeats and non-empty dynamic subscriptions;
5. creates or validates only `data/live` and `data/live/runs`;
6. records the previous production image;
7. replaces `liquid20-live`;
8. observes production heartbeat and file sizes twice;
9. verifies non-root UID, the existing data-root GID, `unless-stopped`, no Docker socket and unchanged accepted-evidence digest;
10. restores the previous image on failure;
11. uploads a JSON operational evidence report and the bounded deployment log.

A real liquidation is not required during a short validation window. When none is observed, the report explicitly records that only heartbeat, subscription and deterministic append tests were proven.

## Rollback

Automatic rollback runs when deployment fails after the old container is replaced. Manual rollback uses the previous exact image with the same hardened runtime arguments and the same `/data` bind mount.

Do not delete `./data/live/` during rollback. A stopped collector is represented by the portal as `STALE` and then `OFFLINE`; accepted evidence remains available separately as `HISTORICAL`.
