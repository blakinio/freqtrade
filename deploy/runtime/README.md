# Optional portable Linux runtime contract

Status: **optional portability reference**, not the current persistent-runtime target.  
Originally introduced by ADR-024.  
Current runtime authority: ADR-025 / Issue #1604.

The current Developer Quant Platform keeps persistent Portal/bot/application runtime on Synology and moves stateless/disposable CI/build/validation work to GitHub-hosted runners where compatible.

This directory is retained because a repository-neutral Linux host contract is still useful for future portability, diagnostics or a later owner-approved compute split. It does **not** make a separate dedicated Linux host a completion requirement and it does **not** make Synology compute invalid under current architecture.

## Current topology

```text
GitHub / Actions / GHCR
  CI + test + scan + build + immutable image publication
  disposable/stateless bounded jobs
                |
                v
Synology persistent runtime
  Portal / bots / collectors / WickHunter / supporting services
  persistent application containers and state
```

GitHub Actions is not the long-lived application runtime. Persistent application containers run on Synology. A short-lived workflow may execute disposable containers when the workload fits Actions lifecycle constraints.

## Optional portable-host profile

The files in this directory describe what a **future separate Linux runtime host** would need to satisfy if the owner later chooses to move persistent compute away from Synology.

That optional profile deliberately contains no Synology DSM path, Synology runner identity, production-trading authority or target-host secret.

A portable target host would require:

- Linux container execution;
- local runtime/transactional state outside a separately defined durable-storage mount;
- application containers without the container-engine socket;
- optional GitHub self-hosted runner restricted to `deploy-only` or absent;
- immutable image/artifact identity;
- no real-money trading credentials or execution capability;
- no Synology-specific `/volume1/...` assumptions on that separate compute host.

Validate the optional static profile with:

```bash
python deploy/runtime/validate_host_contract.py \
  --env-file deploy/runtime/runtime-host.env.example
```

A PASS proves only that the **optional portability profile** is internally consistent. It is not current deployment acceptance, it does not prove such a host exists, and it must not be used to reject the current Synology persistent runtime defined by ADR-025.

## Current Synology runner boundary

The current architecture still prefers GitHub-hosted execution for repository-wide stateless work. A Synology self-hosted runner should therefore be retained only for bounded target-specific operations such as immutable image pull, deployment update, health/restart/persistence verification and rollback.

Target runner scope:

```text
runner_scope = disabled | deploy-only
```

Do not use the privileged Synology runtime/storage host as the normal repository-wide CI, dependency-build or unrestricted model-training shell merely because a self-hosted runner is installed there.

## Persistent container boundary

Current persistent Portal, Freqtrade simulation/bot, WickHunter/inference, collector and supporting containers remain on Synology when they require continuous availability or durable state.

Their portable images should be built/scanned/published by GitHub-hosted workflows where practical. Deployment then consumes an exact attributable revision or immutable digest.

Application containers must not mount the Docker/Podman socket unless a separately justified narrow lifecycle component explicitly requires container-engine authority.

## State and recovery

Current Synology runtime state and durable storage may coexist on the NAS, but state ownership and backup copies must remain explicit.

- active databases use filesystem/database semantics appropriate to the deployed package;
- datasets, models, evidence, reports and backups remain durable Synology responsibilities;
- GitHub Actions caches/artifacts are disposable and are not the durable system of record;
- deployment changes that touch persistent state require proportionate restart/recovery evidence.

## Future portability

If scale, performance, reliability or isolation requirements later justify a separate compute host, this directory may be reused as a starting contract. That would require a new explicit owner decision and fresh target-host evidence. ADR-025 does not pre-authorize such a migration.
