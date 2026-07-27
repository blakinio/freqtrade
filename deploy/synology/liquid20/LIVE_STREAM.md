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

`deploy-live.sh`:

1. builds `local/liquid20-collector:sha-<exact SHA>`;
2. starts an isolated candidate with a temporary data root;
3. observes two advancing heartbeats and non-empty dynamic subscriptions;
4. records the previous production image;
5. replaces `liquid20-live`;
6. observes production heartbeat and file sizes twice;
7. verifies non-root UID, `unless-stopped`, no Docker socket and unchanged accepted-evidence digest;
8. restores the previous image on failure;
9. uploads a JSON operational evidence report.

A real liquidation is not required during a short validation window. When none is observed, the report explicitly records that only heartbeat, subscription and deterministic append tests were proven.

## Rollback

Automatic rollback runs when deployment fails after the old container is replaced. Manual rollback uses the previous exact image with the same hardened runtime arguments and the same `/data` bind mount.

Do not delete `./data/live/` during rollback. A stopped collector is represented by the portal as `STALE` and then `OFFLINE`; accepted evidence remains available separately as `HISTORICAL`.
