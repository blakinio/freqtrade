# Synology Portal LAN Preview

This package builds and deploys the AI Trading Portal web application as a LAN-only preview on Synology.

## Runtime contract

- image: `ghcr.io/blakinio/freqtrade-portal-web:sha-<commit>`;
- container: `freqtrade-portal-staging`;
- bind: `192.168.1.2:3000`;
- browser URL: `http://synology:3000` or `http://192.168.1.2:3000`;
- data mode: explicit deterministic `fixture` mode;
- environment label: `staging`;
- no Freqtrade REST/WebSocket exposure;
- no exchange credentials, trading credentials, Cloudflare Tunnel, SSH launcher or live-capital authorization.

This is a private-LAN product preview, not the production-like Cloudflare staging acceptance environment described in `docs/ai_platform/portal/PRODUCTION_LIKE_STAGING.md`.

## Deployment

`.github/workflows/portal-synology-lan-preview.yml` builds the web image on a GitHub-hosted runner, publishes the exact commit image to GHCR, validates it as an isolated candidate on the Synology Docker host and then replaces the previous preview container.

The deployment job runs only on the dedicated `freqtrade-staging` self-hosted runner. A failed final health check automatically attempts to restore the previous image.

## Updating the preview

After the workflow is merged, changes under `ai_platform/portal/web/` or this deployment package on `develop` build and deploy a new exact-SHA image. Manual redeployment is also available through `workflow_dispatch`.
