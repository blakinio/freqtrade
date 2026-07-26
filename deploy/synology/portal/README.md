# Synology Portal LAN Preview

This package builds and deploys the AI Trading Portal web application as a LAN-only preview on Synology.

## Runtime contract

- image: `local/freqtrade-portal-web:sha-<commit>`;
- container: `freqtrade-portal-staging`;
- bind: `192.168.1.2:3031`;
- browser URL: `http://synology:3031` or `http://192.168.1.2:3031`;
- environment label: `staging`;
- Liquid20 host source: `/volume1/docker/freqtrade-liquidations/data`;
- Liquid20 container source: `/liquid20-data:ro`;
- same-origin read endpoints: `/api/market/liquidations`, `/summary` and `/health`;
- browser page: `/market/liquidations`;
- non-root application user with only the dynamically verified supplementary read group required by the Liquid20 tree;
- no Freqtrade REST/WebSocket or Liquid20 file exposure;
- no Docker socket mount in the portal container;
- no exchange credentials, trading credentials, Cloudflare Tunnel, SSH launcher or live-capital authorization.

`PORTAL_WEB_DATA_MODE=fixture` remains the deterministic portal-wide mode for capabilities that are not connected to an operational backend. Liquidations use the explicitly configured `PORTAL_LIQUIDATIONS_DATA_ROOT=/liquid20-data`, so that module reads real source-labelled Liquid20 evidence through its server-side bounded read-model.

This is a private-LAN research/product preview, not the production-like Cloudflare staging acceptance environment described in `docs/ai_platform/portal/PRODUCTION_LIKE_STAGING.md`. Liquidation data and a successful page deployment do not authorize trading or validate a strategy.

## Deployment

`.github/workflows/portal-synology-lan-preview.yml` checks out the exact trusted commit on the dedicated `freqtrade-staging` runner, builds a commit-tagged local image, validates an isolated candidate and then replaces the previous preview container.

The self-hosted runner is containerized, so the Liquid20 host path is validated through the same Docker daemon that performs the final bind mount. A short root-only preflight container inspects metadata but does not run the portal. It verifies:

- a valid latest Liquid20 run exists;
- required event files are regular, non-symlinked and group-readable;
- the root, run directory and the latest 100 run directories are group-readable and traversable;
- optional summaries and acceptance reports are group-readable when present;
- all inspected paths use one consistent numeric GID.

The portal itself remains the image's non-root Node user. Docker adds only that verified numeric GID as a supplementary group. This grants read/traverse access to the immutable `root:root 750/640` Liquid20 evidence without changing host permissions, copying data, or running the portal as root.

Candidate and final containers must pass:

- the Docker health check;
- internal health, summary, bounded event-list and page probes;
- the health contract invariants `schema_version=1`, `research_preview=true` and `trading_authorized=false`;
- external private-LAN probes for the page and health endpoint;
- an inspect-time proof that `/liquid20-data` is mounted read-only from the fixed host path;
- an inspect-time proof that `/var/run/docker.sock` is not mounted;
- a runtime proof that UID is non-zero and the verified read group is present.

A failed final validation automatically attempts to restore both the previous image and its previous host-port mapping. The rollback container uses the same hardened runtime arguments, but rollback success is judged by its original homepage health boundary so an older pre-Liquid20 image remains recoverable.

The Synology Docker kernel does not expose CPU CFS quota support, so the deployment uses a memory limit, PID limit, dropped capabilities, read-only root filesystem and `no-new-privileges`, but does not set `--cpus`.

## Updating the preview

Changes under `ai_platform/portal/web/`, the portal Dockerfile, workflow or deployment script on `develop` build and deploy a new exact-SHA image. During this integration task, the reviewed feature branch is also deployed to prove the real read-only Liquid20 boundary before merge. The temporary feature-branch trigger is removed after that proof; the final merge to `develop` performs the authoritative deployment.
