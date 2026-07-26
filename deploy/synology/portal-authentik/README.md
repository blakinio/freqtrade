# PI-06 Authentik on Synology

This directory is a **secret-free, repository-validated deployment package** for a small Authentik identity stack on Synology Container Manager or another Linux Docker Compose host.

It does not provision a real user, MFA device, DNS record, Cloudflare resource, certificate or portal client secret. It does not prove target acceptance.

## Included

- digest-pinned Authentik server/worker and PostgreSQL images;
- loopback-only host ingress and an internal database network;
- no Redis, Docker socket, host network, privileged container or timezone mount;
- fail-closed runtime environment validation;
- one-shot hashed-password bootstrap with steady-state recreation;
- encrypted database and volume backups using `age`;
- checksum-verified destructive restore with an explicit confirmation phrase;
- owner-run deployment, recovery, upgrade and rollback runbook.

## Repository validation

```bash
python3 validate.py --env-file .env.example --example
python3 -m pytest -q tests/ai_platform/portal/deployment/test_authentik_synology_deployment.py
```

For a real runtime file:

```bash
cp .env.example /volume1/docker/portal-authentik/runtime.env
chmod 600 /volume1/docker/portal-authentik/runtime.env
python3 validate.py --env-file /volume1/docker/portal-authentik/runtime.env

docker compose \
  --env-file /volume1/docker/portal-authentik/runtime.env \
  -f compose.yml config --quiet
```

Follow `docs/ai_platform/portal/runbooks/PI06_AUTHENTIK_SYNOLOGY.md` before starting the stack.
