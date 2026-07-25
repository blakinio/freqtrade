---
task_id: FTAI-20260725-portal-synology-port-3030
status: active
branch: fix/portal-synology-port-3030
base_branch: develop
created: 2026-07-25
updated: 2026-07-25
---

# Move Synology portal preview to a free LAN port

Port `3000` is already occupied. The requested candidate `3030` responds through an existing nginx service, so the portal preview is moved to the next validated free port, `3031`.

## Boundaries

- keep the container application port at `3000`;
- publish only `192.168.1.2:3031` on the Synology LAN;
- preserve fixture mode, the dedicated `freqtrade-staging` runner, health checks and rollback;
- restore the previous host-port mapping if the replacement fails;
- do not add SSH, Cloudflare Tunnel, trading credentials or direct Freqtrade API exposure.

## Validation

Workflow run `30172227677` successfully built and deployed the portal, passed the Docker health check and reached `http://192.168.1.2:3031/` from the Synology runner.
