# WickHunter market-evidence collector on Synology

## Boundary

This Compose project runs the public-only WickHunter market-evidence collector as a persistent Linux service. It acquires Binance USD-M and Bybit Linear public data and writes durable, source-separated evidence.

It does not accept exchange credentials, submit orders, expose an HTTP port or authorize model execution.

## Required values

Create an environment file outside the repository with:

```text
COLLECTOR_COMMIT=<exact lowercase 40-character Git SHA>
MARKET_EVIDENCE_REQUEST_FILE=<absolute path to immutable request JSON>
MARKET_EVIDENCE_STATE_DIR=<absolute durable Synology directory>
PUID=<non-root Synology UID>
PGID=<Synology group ID>
```

Optional values:

```text
IMAGE_TAG=<local image tag>
MARKET_EVIDENCE_LOOP_SECONDS=60
MARKET_EVIDENCE_HEALTH_MAX_AGE_SECONDS=600
```

Do not put API keys, secrets, passphrases, proxy credentials or Freqtrade exchange configuration in this file.

## Directory preparation

The state directory must:

- exist before startup;
- be owned or writable by `PUID:PGID`;
- be outside the container filesystem;
- not be a symlink;
- not contain an unrelated active pointer;
- not be automatically pruned after an immutable package is accepted.

Example:

```bash
install -d -m 0750 -o "$PUID" -g "$PGID" \
  /volume1/docker/freqtrade-staging-state/wickhunter-production-market-evidence
```

## Validate configuration

```bash
docker compose \
  --env-file /path/to/market-evidence.env \
  -f deploy/synology/wickhunter-market-evidence/compose.yaml \
  config --quiet
```

Review the rendered configuration and confirm:

- `read_only: true`;
- all capabilities are dropped;
- `no-new-privileges:true` is present;
- there is no `ports` section;
- there is no host network;
- only the state mount is writable;
- the request mount is read-only.

## Start or resume

```bash
docker compose \
  --env-file /path/to/market-evidence.env \
  -f deploy/synology/wickhunter-market-evidence/compose.yaml \
  up -d --build
```

The daemon resumes from the active pointer and self-hashed incremental state. It does not restart the interval from zero and does not overwrite a completed package.

## Health

```bash
docker inspect --format '{{json .State.Health}}' wickhunter-market-evidence
docker logs --tail 100 wickhunter-market-evidence
cat /volume1/docker/freqtrade-staging-state/wickhunter-production-market-evidence/collector-health.json
```

A collector health payload separates process liveness from operational readiness:

- `live=true` means the daemon loop completed and wrote a fresh atomic observation;
- `ready=true` means the mounted immutable request is valid and the lifecycle result is in the
  explicit ready-state allowlist;
- `healthy` remains a compatibility readiness field and always equals `ready`;
- `blocked` means the loop is alive but cannot perform its configured capture duty;
- `failed` means a collector operation failed closed.

Docker/Compose health and deployment gates require a fresh `live=true`, `ready=true`,
`healthy=true` payload, a matching schema version, zero authority and an explicitly allowed result.
`blocked/CAPTURE_REQUEST_UNAVAILABLE` is never ready. A fresh file alone is not readiness.

Read the `result` field to distinguish:

- initialized;
- sampled;
- not due;
- published;
- blocked;
- failed.

## Restart and recovery

A normal container or NAS restart requires no state edit:

```bash
docker compose \
  --env-file /path/to/market-evidence.env \
  -f deploy/synology/wickhunter-market-evidence/compose.yaml \
  restart
```

Investigate instead of deleting state when any of these exist:

- `.immutable-package.partial`;
- a failed sample report;
- a missing expected sample directory;
- a hash mismatch;
- a future source timestamp;
- a changed active pointer;
- a different request identity;
- an existing final package with failed verification.

Never repair a gap by copying a later row, changing a timestamp or substituting another source.

## Verify a completed package

From an exact repository checkout matching `COLLECTOR_COMMIT`:

```bash
PYTHONPATH=. python -m ai_platform.wickhunter.production_market_evidence_service \
  verify \
  --package-root \
  /volume1/docker/freqtrade-staging-state/wickhunter-production-market-evidence/<run-id>/immutable-package
```

An accepted result does not authorize WH-01 materialization by itself. A matching accepted Liquid20 import must still be bound through the WH-01 adapter.

## Retention

Recommended policy:

- retain every accepted immutable package;
- retain its request, policy, manifest, checksum and verification report permanently;
- rotate ordinary container logs through the Synology/Docker logging policy;
- do not automatically remove accepted package directories;
- remove rejected or incomplete runs only after a documented operator investigation and backup.

## Portal mount

The Portal reads the state root through a separate read-only mount. Use:

```text
deploy/synology/portal/deploy-market-evidence-preview.sh
```

The collector and Portal must not share a writable container mount. The collector owns writes; the Portal receives read-only group access.
