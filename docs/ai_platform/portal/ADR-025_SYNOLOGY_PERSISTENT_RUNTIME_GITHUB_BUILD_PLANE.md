# ADR-025 — Synology persistent runtime with GitHub-hosted build and disposable compute

Status: `accepted`  
Accepted by owner: `2026-08-18`  
Issue: `#1604`  
Trusted base at decision: `develop@6510077ea2e7a63c0d489f94391f461a3cab4ac1`

## Decision

The Developer Quant Platform uses a two-plane operational topology:

```text
GitHub repository / GitHub Actions / GHCR
        |
        | CI, test, scan, build, publish, disposable/stateless jobs
        v
Synology persistent application runtime
        |
        | local durable application state + backup/evidence boundary
        v
Synology durable storage / backup
```

GitHub is the repository, CI/build and disposable-compute plane. Synology is the persistent application runtime and durable-storage host for the current private single-owner Developer Quant Platform.

The current target dimensions are:

```text
runtime_location: LOCAL | SYNOLOGY
storage_provider: LOCAL | SYNOLOGY
```

A separate dedicated Linux runtime host is **not required** for current Portal completion.

## Workload placement

### GitHub-hosted by default

Use GitHub-hosted runners for workloads that are stateless, disposable or naturally bounded by a workflow run, including:

- repository CI and policy validation;
- unit/integration/security checks;
- lint, type and dependency checks;
- packaging and documentation builds;
- immutable container/image builds and GHCR publication;
- bounded backtests, replay jobs, data transforms and validation jobs when inputs, runtime and retention fit GitHub Actions lifecycle constraints;
- short-lived containerized jobs whose result is an attributable artifact, report or published image rather than a continuously running service.

GitHub-hosted runners are not a 24/7 hosting service.

### Synology persistent runtime

Run continuously available or stateful application services on Synology, including where applicable:

- the owner-facing Portal web/API/control-plane services;
- persistent Freqtrade simulation/bot runtimes;
- persistent WickHunter/inference processes;
- collectors and workers that require continuous availability, durable local process state or low-latency access to the current application state;
- the persistent databases, queues and supporting containers required by those services.

The exact service set remains determined by current implementation evidence; this ADR defines placement authority rather than claiming every service is already correctly placed.

## Container boundary

Persistent application containers run on Synology. Their images should be built, scanned and published by GitHub-hosted workflows where practical, using immutable digests and GHCR handoff.

GitHub Actions may execute short-lived disposable containers inside a workflow. It must not be represented as the persistent host for Portal, bot, inference, collector, database or scheduler containers.

Ordinary application containers must not receive the Docker/container-engine socket merely because they run on Synology. Container-engine authority remains a narrow deployment/lifecycle boundary.

## GitHub self-hosted runner boundary

A Synology self-hosted GitHub runner may remain only for operations that genuinely require target-host access, such as:

- pulling an approved immutable image;
- applying a bounded deployment update;
- target-specific configuration checks;
- health/restart/persistence verification;
- bounded rollback.

Its target scope is `deploy-only` or an equivalently narrow contract. Synology must not remain the normal repository-wide CI/build/test shell merely because it also hosts the application runtime.

Where a target operation can be performed safely without a self-hosted runner, disabling that runner is preferred.

## Storage and persistence

Co-locating current application compute and durable storage on Synology is an explicit owner choice for this private platform. Persistent data still requires clear ownership and recovery boundaries.

- Active transactional databases may use local Synology filesystem semantics appropriate to the database/container package.
- Datasets, models, evidence, reports and backups remain durable Synology responsibilities.
- Application state and backup copies must not be conflated: a backup/recovery path remains required for state whose loss would break the owner workflow.
- GitHub Actions artifacts and caches are not the durable system of record.

## Security consequences

This decision intentionally accepts more compute/storage co-location on the NAS than ADR-024's dedicated-host target. The current mitigating controls are:

- private single-owner product scope;
- GitHub-hosted default for repository-wide CI/build so untrusted or broad automation does not normally execute on the NAS;
- narrow deploy-only self-hosted runner scope where retained;
- no Docker socket in ordinary application containers;
- bounded service permissions and mounts;
- authenticated/same-origin Portal boundary and existing protected ingress where applicable;
- restart/recovery evidence for persistent state;
- no real-money exchange execution or capital authority.

If future scale, reliability, performance or isolation requirements justify separate compute, `deploy/runtime/**` remains an optional portability reference. Such a future move requires a new explicit owner decision; it is not current completion work.

## Migration impact

1. Retain the GitHub-hosted build-plane work already merged in PR #1609.
2. Complete compatible repairs such as PR #1610 so portable images build/publish on GitHub-hosted Linux and deploy to Synology by immutable identity.
3. Stop the ADR-024 Phase-C programme that required discovery or provisioning of a separate dedicated Linux host.
4. Reconcile current architecture/governance vocabulary from `LOCAL | DEDICATED_LINUX` back to `LOCAL | SYNOLOGY` for persistent runtime placement.
5. Keep `deploy/runtime/**` only as an optional portable-host contract/reference, not current target authority.
6. Continue moving stateless CI/build/test/scan/disposable jobs away from general-purpose Synology self-hosted execution when GitHub-hosted execution is compatible.
7. Keep only the narrow target-specific Synology runner operations that cannot be replaced by GitHub-hosted execution.
8. Preserve exact deployment health, persistence and rollback validation for changes that mutate the persistent Synology runtime.

## Supersession

ADR-025 supersedes **only** the conflicting current-target parts of ADR-024 that:

- require persistent Portal/bot/application compute to move to a separate dedicated Linux host;
- define Synology only as transitional compute;
- make physical dedicated-Linux cutover a current completion requirement;
- reject Synology as the normal persistent application runtime location.

ADR-025 retains the following ADR-024 direction:

- GitHub-hosted runners are the default for stateless CI/build/validation;
- immutable image/artifact publication and attributable delivery are preferred;
- GitHub-hosted Actions are not persistent application runtime hosts;
- self-hosted runners on privileged hosts must be narrow rather than general CI shells;
- application containers should not receive unnecessary container-engine authority.

ADR-023 remains authoritative for current product semantics, simulation, model lifecycle and the prohibition on real-money execution.

Historical ADR-024, PR #1606, PR #1609 and associated evidence remain truthful records and are not rewritten.

## Non-goals

ADR-025 does not authorize:

- real exchange order execution, withdrawals or capital allocation;
- private trading credentials;
- automatic model activation;
- destructive Synology cleanup;
- broad Synology runner privileges;
- treating GitHub Actions as a persistent application host;
- claiming that all remaining workflow/runner migration is already complete.
