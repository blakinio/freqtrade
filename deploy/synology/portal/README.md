# Synology Portal LAN Preview

This package builds and deploys the AI Trading Portal web application as a LAN-only preview on Synology.

## Runtime contract

- image: `local/freqtrade-portal-web:sha-<commit>`;
- container: `freqtrade-portal-staging`;
- bind: `192.168.1.2:3031`;
- browser URL: `http://synology:3031` or `http://192.168.1.2:3031`;
- data mode: explicit deterministic `fixture` mode;
- environment label: `staging`;
- no Freqtrade REST/WebSocket exposure;
- no exchange credentials, trading credentials, Cloudflare Tunnel, SSH launcher or live-capital authorization.

This is a private-LAN product preview, not the production-like Cloudflare staging acceptance environment described in `docs/ai_platform/portal/PRODUCTION_LIKE_STAGING.md`.

## Deployment

`.github/workflows/portal-synology-lan-preview.yml` checks out the exact trusted commit on the dedicated `freqtrade-staging` runner, builds a commit-tagged local image, validates an isolated candidate and then replaces the previous preview container.

The final container is accepted only after its Docker health check passes and the runner can reach `http://192.168.1.2:3031/`. A failed final health check automatically attempts to restore both the previous image and its previous host-port mapping.

The Synology Docker kernel does not expose CPU CFS quota support, so the deployment uses a memory limit, PID limit, dropped capabilities, read-only root filesystem and `no-new-privileges`, but does not set `--cpus`.

## Updating the preview

After the workflow is merged, changes under `ai_platform/portal/web/`, the portal Dockerfile or the deployment script on `develop` build and deploy a new exact-SHA image. Manual redeployment is also available through `workflow_dispatch`.
