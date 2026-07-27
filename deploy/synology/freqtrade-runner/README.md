# Dedicated Freqtrade Synology runner

This package isolates the Freqtrade repository, AI platform and portal deployment jobs from OteryN.

## Fixed ownership

- repository: `blakinio/freqtrade`;
- Compose project: `freqtrade-deploy-runner`;
- runner name: `freqtrade-synology-staging`;
- custom label: `freqtrade-staging`;
- image: `ghcr.io/blakinio/freqtrade-deploy-runner:develop`;
- Synology state path: `/volume1/docker/freqtrade/state`;
- runner-visible state path: `/var/lib/freqtrade-staging-state`.

The package contains no OteryN repository URL, runner label, image, project or state path. The OteryN project and runner remain independently owned by `blakinio/Oteryn-Platform`.

## Safe migration of the existing Freqtrade runner project

Do not remove or edit the OteryN runner project.

1. Merge the reviewed runner-image package and wait until the `develop` runner image is published.
2. In Synology Container Manager, update only the existing `freqtrade-deploy-runner` project using this directory's `compose.yml` and `.env.example`.
3. Keep the existing `runner_config` and `runner_work` named volumes. They retain the current repository registration, so a new token is normally unnecessary.
4. Ensure `/volume1/docker/freqtrade/state` exists and is reserved only for Freqtrade, portal and AI-platform staging state.
5. Recreate only the Freqtrade runner service and verify that `freqtrade-synology-staging` returns online with label `freqtrade-staging`.
6. Configure GitHub Environment `synology-staging` variable `FREQTRADE_STAGING_STATE_DIR=/var/lib/freqtrade-staging-state`.
7. Run a fresh bounded preflight before any deployment request.

The old Freqtrade runner container must remain available until the new image and mount are ready. Roll back by restoring the previous `freqtrade-deploy-runner` project definition; do not touch OteryN containers or volumes.

## Local validation

```bash
bash -n deploy/synology/freqtrade-runner/entrypoint.sh

docker compose \
  --env-file deploy/synology/freqtrade-runner/.env.example \
  -f deploy/synology/freqtrade-runner/compose.yml \
  config --quiet
```
