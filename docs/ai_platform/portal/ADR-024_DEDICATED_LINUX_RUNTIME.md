# ADR-024 — Dedicated Linux runtime with GitHub CI and Synology durable storage

Status: `superseded by ADR-025`  
Originally accepted by owner: `2026-08-18`  
Superseded by owner: `2026-08-18` via Issue `#1604` and `ADR-025`  
Issue: `#1603`  
Trusted base at decision: `develop@2389e5e70161325c7f39b8ecd9da766f078bcf3e`

## Supersession note

This document is preserved as historical architecture evidence. ADR-025 supersedes the current-target requirement for a separate dedicated Linux application host and restores Synology as the normal persistent runtime location for the current private Developer Quant Platform.

ADR-025 **retains** ADR-024's GitHub-hosted build-plane direction: stateless CI/test/build/scan/disposable work belongs on GitHub-hosted runners where compatible; persistent application runtime does not belong on GitHub Actions; privileged self-hosted runner access should remain narrow.

The historical decision below is intentionally not rewritten.

## Decision

The Developer Quant Platform adopts a three-plane deployment topology:

```text
GitHub repository / GitHub Actions
        |
        | test, build, verify, publish, orchestrate
        v
Dedicated Linux runtime host
        |
        | bounded durable-storage boundary
        v
Synology durable storage / backup
```

GitHub is the repository and automation control plane. GitHub-hosted runners are the default execution environment for stateless CI, tests, lint/type/security checks, packaging, immutable image builds and other disposable validation.

Persistent Portal, Freqtrade simulation, public-market collectors, WickHunter/inference and ordinary long-lived workers target a **dedicated Linux runtime host**. GitHub-hosted Actions runners are not application runtime hosts.

Synology becomes primarily a **durable storage, evidence and backup provider**. It is no longer the target application-compute host. Existing Synology-hosted services remain valid current-state evidence during migration and may stay running until their replacement is individually proven.

## Current vocabulary

Runtime location and storage provider are separate dimensions.

```text
runtime_location: LOCAL | DEDICATED_LINUX
storage_provider: LOCAL | SYNOLOGY
```

`SYNOLOGY` may remain in historical evidence and current implementation records describing services that have not yet migrated. It is not the target runtime location for new persistent application deployment.

This distinction prevents repository branch names, deployment environments, runtime compute and storage location from being conflated.

## GitHub Actions boundary

GitHub-hosted runners should perform:

- repository CI and policy validation;
- unit/integration/security checks;
- documentation and packaging builds;
- immutable container/image builds and publication;
- bounded disposable backtests or validation jobs when their inputs fit Actions lifecycle constraints.

They must not be used as a substitute for a 24/7 Portal, collector, inference service, scheduler, model runtime or other persistent application process.

Self-hosted GitHub runners, when used for deployment, must have the narrowest practical role. The target contract is `deploy-only` or disabled. A deployment runner must not become a general-purpose CI/training shell merely because it has access to the runtime host.

## Dedicated Linux runtime boundary

The target runtime host:

- runs Linux containers or equivalent Linux-compatible processes;
- receives exact attributable images/artifacts produced by the repository pipeline;
- owns local transactional/runtime state that requires low-latency filesystem/database semantics;
- does not expose the container-engine socket inside ordinary application containers;
- runs persistent Portal, collectors, WickHunter/inference, Freqtrade simulation and supporting workers as independently restartable services;
- keeps health, restart and rollback behavior observable;
- may mount approved durable Synology storage through a narrow filesystem or synchronization boundary.

The physical host, address, hardware, operating-system image and access method are **UNKNOWN until separately verified**. This ADR does not invent that infrastructure.

## Storage boundary

Synology is retained because it is well suited to durable data and backup, not because it should also be the application compute plane.

Target Synology responsibilities include, where applicable:

- chronological research datasets and evidence;
- model packages and immutable/reproducible artifacts that require durable retention;
- exported reports and long-lived evidence promoted out of GitHub Actions retention;
- database backups and recovery material;
- secondary/off-host copies of runtime state according to the applicable recovery policy.

Active transactional databases must not be moved onto a network filesystem merely to satisfy the storage split. A database may run locally on the dedicated Linux host and back up or replicate to Synology. Any future database migration requires its own persistence/recovery validation.

## Local compute

`LOCAL` remains valid for developer workflows such as model training, experiments and bounded analysis. Local training may create `CHALLENGER` models but must not silently change `ACTIVE`.

A local workstation is not the default persistent Portal runtime.

## Migration strategy

Migration is service-by-service and reversible.

1. Establish the generic host/storage contract under `deploy/runtime/**`.
2. Build/publish service images in GitHub-hosted Actions where practical.
3. Migrate public-data collectors first because they have the smallest private-state boundary.
4. Migrate WickHunter/inference and durable research workers.
5. Migrate Portal/control-plane application services and their transactional state through an explicitly validated persistence path.
6. Migrate Freqtrade simulation workers and remaining supporting services.
7. Remove Synology application-compute responsibilities only after replacement health, restart and rollback are proven.
8. Retain Synology storage/backup responsibilities and validate recovery after the compute cutover.

Issue `#1604` owned the post-ADR service portability/cutover programme before the owner superseded that target with ADR-025.

## Cutover and rollback rules

A physical cutover requires current evidence for the exact target host and service group. At minimum:

- exact artifact/image provenance;
- target host identity and expected architecture;
- required storage mounts or synchronization paths;
- pre-cutover current-service health;
- startup and health on the new host;
- restart persistence appropriate to the service;
- rollback to the previously known-good service/runtime state;
- no loss or silent reinterpretation of durable evidence.

A merge of repository code is not deployment authority. Protected environment, secret, shared-state or destructive operations must select their normal risk gates.

## Security consequences

This split reduces the blast radius of the Synology NAS and of GitHub self-hosted automation:

- ordinary CI no longer needs NAS/container-engine access;
- application containers do not need the Docker socket;
- deployment credentials can be scoped to the dedicated runtime host;
- storage permissions can be separated into read-only and read/write roots by service;
- a runtime compromise does not automatically imply unrestricted NAS administration;
- a NAS maintenance/DSM event is less likely to stop application compute once cutover is complete.

## Supersession

ADR-024 was a scoped runtime/deployment refinement of ADR-023.

It formerly superseded conflicting current-target statements that defined `SYNOLOGY` as a normal target runtime location or made Synology the primary persistent application-compute target. ADR-025 now supersedes that part of ADR-024.

ADR-023 remains authoritative for the private single-owner Developer Quant product, `REALTIME_PUBLIC | REPLAY`, integrated simulation, `BASELINE | CHALLENGER | ACTIVE | ARCHIVED`, deliberate model activation and the prohibition on real-money execution.

Historical Synology deployment evidence is not rewritten.

## Implementation truth at acceptance time

At ADR-024 acceptance time:

- GitHub-hosted CI/build capability was already directly proven in repository Actions history;
- Synology self-hosted workflows and deployments still existed;
- `deploy/` was still Synology-centric;
- no dedicated Linux runtime host had been verified for this task;
- no physical runtime/storage cutover was claimed.

Therefore ADR-024 was an **accepted target pending implementation**. ADR-025 superseded the unimplemented dedicated-Linux target while preserving the GitHub-hosted build-plane direction.

## Non-goals

ADR-024 did not authorize:

- real exchange order execution, withdrawals or capital allocation;
- private trading credentials;
- automatic model activation;
- destructive Synology cleanup;
- runner registration/removal by itself;
- DNS/Cloudflare mutation;
- physical deployment to an unverified host.
