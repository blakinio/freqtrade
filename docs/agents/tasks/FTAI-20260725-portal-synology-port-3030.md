---
task_id: FTAI-20260725-portal-synology-port-3030
status: active
branch: fix/portal-synology-port-3030
base_branch: develop
created: 2026-07-25
updated: 2026-07-25
---

# Move Synology portal preview to port 3030

Change the private-LAN AI Trading Portal preview host port from `3000` to `3030` because port `3000` is already occupied.

## Boundaries

- keep the container application port at `3000`;
- publish only `192.168.1.2:3030` on the Synology LAN;
- preserve fixture mode, the dedicated `freqtrade-staging` runner, health checks and rollback;
- do not add SSH, Cloudflare Tunnel, trading credentials or direct Freqtrade API exposure.

## Validation target

After merge, the `Portal Synology LAN Preview` workflow must replace the existing container mapping and pass its HTTP probe at `http://192.168.1.2:3030/`.
