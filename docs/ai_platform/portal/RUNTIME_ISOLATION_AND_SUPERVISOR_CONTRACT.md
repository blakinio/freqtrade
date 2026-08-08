# Runtime Isolation Profile and Runtime Supervisor Contract

Status: **owner-accepted binding refinement of ADR-020; effective as trusted-base authority after merge**  
Owner decision date: `2026-08-08`  
Implementation status: `target_only`  
Scope: Portal-managed Freqtrade dry-run runtimes  
Authority expansion: **none**  
Live capital: **not authorized**

This document refines ADR-020. It does not replace ADR-020, ADR-001 through ADR-019, repository safety rules, promotion gates, deployment authorization, or live-capital controls. Per the repository authority-freeze rule, this document cannot expand the authority of the task that creates it; it becomes trusted-base architecture authority only after review and merge.

## 1. Governing invariant

Every executable `RuntimeGeneration` MUST run under exactly one immutable:

```text
RuntimeIsolationProfile
        +
resolved RuntimeIsolationPlan
```

The Portal MUST NOT send raw container-engine configuration to the Runtime Supervisor. In particular, no Portal request may carry arbitrary:

- image or mutable tag selection;
- command, entrypoint or shell instruction;
- environment variables;
- bind mounts, volumes or host paths;
- port publication;
- network mode or network attachment;
- Linux capabilities;
- privileged/device/PID/IPC/UTS namespace settings;
- seccomp/LSM bypasses;
- restart policy;
- resource-engine flags.

The Runtime Supervisor materializes engine-specific configuration only from trusted immutable generation data, an approved isolation profile, a resolved plan and its own reviewed implementation.

## 2. RuntimeIsolationProfile

`RuntimeIsolationProfile` is versioned and immutable.

Minimum logical shape:

```text
RuntimeIsolationProfile
  profile_version
  profile_digest

  process_policy
  filesystem_policy
  resource_policy
  network_policy
  logging_policy
  health_policy
  image_policy
  secret_policy
  lifecycle_policy

  security_invariants[]
  capability_resolved_controls[]
```

A security-policy change creates a new profile version and digest. An existing profile is never edited in place.

The profile describes required security semantics, not raw Docker CLI arguments.

## 3. Control classes

### 3.1 SECURITY_INVARIANT

A `SECURITY_INVARIANT` has no downgrade path. If the selected host cannot enforce it, the runtime MUST NOT start.

Baseline invariants include:

- runtime process is non-root;
- `privileged=false`;
- no privilege gain / `no-new-privileges`;
- Linux capabilities drop `ALL`, add none unless a future profile explicitly replaces this invariant through a separately reviewed architecture change;
- read-only root filesystem;
- no host network;
- no host PID, IPC or UTS namespace;
- no host device passthrough;
- no Docker/container-engine socket;
- no public or host-published Freqtrade port;
- no arbitrary mounts or host paths;
- no `seccomp=unconfined` or equivalent security-profile bypass;
- immutable Freqtrade and Gateway content identity;
- no silent fallback when an invariant cannot be applied or verified.

Failure result:

```text
HOST_INCOMPATIBLE
```

or a narrower machine-readable incompatibility reason.

### 3.2 HOST_CAPABILITY_RESOLVED

A `HOST_CAPABILITY_RESOLVED` control is still mandatory, but the profile may enumerate multiple pre-approved mechanisms that satisfy the same bounded security semantics.

CPU example:

```text
preferred:
  hard CFS/cgroup CPU quota

approved fallback:
  bounded CPUSET, only when it provides a ceiling no weaker than the profile requirement

forbidden:
  no CPU hard containment
  silent fallback
  CPU shares/weight as the sole hard limit
  rounding a fractional CPU requirement to a weaker whole-core CPUSET
```

Alternative mechanisms are not discretionary weakening. They must be explicitly encoded in the profile, semantically bounded and selected before the generation becomes executable.

The same pattern may apply to approved storage, log, network or other enforcement backends. If no approved backend can enforce the required semantics, provisioning fails closed.

## 4. RuntimeHostCapabilityReport

The Runtime Supervisor publishes host capability evidence before generation materialization/provisioning.

Minimum logical shape:

```text
RuntimeHostCapabilityReport
  report_id
  generated_at

  host_identity
  host_boot_id | equivalent reboot identity
  kernel_version
  supervisor_version
  supervisor_build_digest
  container_engine_name
  container_engine_version
  cgroup_mode
  available_cgroup_controllers

  supports_memory_hard_limit
  supports_swap_bound_or_disable
  supports_pid_hard_limit
  supports_cpu_cfs
  supports_cpuset

  supports_readonly_root
  supports_tmpfs
  supports_no_new_privileges
  supports_capability_drop
  supports_required_seccomp

  supports_required_network_policy
  supports_required_storage_bound
  supports_required_log_bound

  probe_evidence_digest
  report_digest
```

The Control Plane MUST NOT guess host capabilities.

A capability report is point-in-time evidence. It MUST be refreshed after a host reboot, container-engine/cgroup change, Supervisor upgrade or another material host change. A stale report cannot authorize provisioning.

Capability reporting does not replace structural and effective enforcement attestation. A host may accept configuration syntactically yet fail to enforce it effectively. Any effective probe that requires a running cgroup or namespace MUST occur while the generation remains application-quarantined as defined in section 25.

## 5. RuntimeIsolationPlan

A deterministic, versioned policy resolver combines:

```text
RuntimeIsolationProfile
+
RuntimeHostCapabilityReport
```

into an abstract resolved `RuntimeIsolationPlan`.

Example:

```text
RuntimeIsolationPlan
  plan_schema_version
  resolver_version

  isolation_profile_version
  isolation_profile_digest

  cpu_mode = CPUSET
  cpu_bound = 1 core
  memory_hard_limit = 2048 MiB
  swap_policy = disabled-or-bounded
  pids_hard_limit = 256

  durable_state_max_bytes = ...
  durable_state_backend = ...
  tmpfs_max_bytes = ...
  log_max_bytes = ...
  log_rotation_count = ...
  log_backend = ...

  network_backend = ...
  market_data_egress_policy_version = ...
  market_data_egress_policy_digest = ...

  seccomp_profile_identity = ...

  freqtrade_image_digest = ...
  gateway_artifact_kind = container-image | content-addressed-binary
  gateway_artifact_digest = ...
  gateway_contract_version = ...
  gateway_contract_digest = ...

  isolation_plan_digest
```

The plan contains canonical resolved security/resource semantics, exact generation TCB artifact identities and approved enforcement modes. It does not contain arbitrary engine arguments.

The Gateway is part of the generation trusted computing base. Its executable artifact identity is therefore bound independently from the Freqtrade image identity. A Gateway binary/image cannot change while retaining the same isolation-plan identity.

### Digest rule

`isolation_plan_digest` MUST be calculated from a canonical serialization of stable resolved-plan fields, including the exact Freqtrade image identity, exact Gateway artifact identity and Gateway contract identity.

The digest MUST NOT depend on volatile capability-report metadata such as `report_id`, `generated_at`, host name or host boot ID. Otherwise an unchanged effective plan would acquire a new identity merely because capabilities were re-probed or because an equivalent host was selected.

The capability report and report digest remain separate provisioning evidence.

## 6. RuntimeGeneration binding and materialization order

An executable `RuntimeGeneration` MUST bind at least:

```text
isolation_profile_version
isolation_profile_digest
isolation_plan_digest
freqtrade_image_digest
gateway_artifact_digest
gateway_contract_version
gateway_contract_digest
market_data_egress_policy_version
market_data_egress_policy_digest
```

in addition to the generation identities already required by ADR-020.

The materialization sequence is:

```text
immutable authored/desired material
        |
select eligible host
        |
RuntimeHostCapabilityReport
        |
resolve abstract RuntimeIsolationPlan
        |
persist final immutable RuntimeGeneration with plan + TCB digests
        |
EnsureProvisioned(generation_id, generation_spec_digest, command_id)
        |
structural + effective attestation while application-quarantined
        |
EnsureRunning(...)
        |
release fixed application gate only after attestation PASS
```

A pre-plan rollout/materialization request is not an executable `RuntimeGeneration`.

Once the final generation exists, its isolation profile, plan digest, Freqtrade image digest or Gateway artifact/contract identity MUST NOT be mutated. If any of those identities or security/resource semantics need to change, create a new generation.

Implementation consequence: the current draft #1388 `RuntimeGeneration` model contains `isolation_profile_version` and `isolation_profile_digest` but does not yet contain `isolation_plan_digest`; #1388 or a successor implementation must add the plan binding and the exact generation TCB bindings required by this refinement before claiming conformance.

## 7. Recovery of the same generation

The same `RuntimeGeneration` may be recreated only when the target host can reproduce the exact canonical `RuntimeIsolationPlan` and exact generation TCB artifacts.

A different capability report or host is acceptable only if the resolved plan digest remains identical and application-quarantined effective attestation passes before Freqtrade/Gateway application execution.

If migration/recovery requires a material change in any of the following, create a new generation:

- CPU containment mode/bound when it changes plan semantics;
- memory/swap policy;
- PID enforcement;
- storage enforcement or bounds;
- log enforcement or bounds;
- network enforcement or egress policy;
- security profile or process isolation;
- Freqtrade image content;
- Gateway artifact content or Gateway contract identity;
- secret boundary semantics.

No security/resource/TCB envelope change may occur silently during recovery.

## 8. Portal-managed Freqtrade image

The repository root `Dockerfile` is not the Portal security baseline. At the current trusted base it creates `ftuser`, adds it to the `sudo` group and grants passwordless `/bin/chown`.

Portal-managed Freqtrade MUST therefore use a separate approved hardened runtime image derived from an approved immutable Freqtrade artifact.

Baseline image properties:

- dedicated non-root runtime user;
- no sudo group membership;
- no sudo binary or NOPASSWD rule when not required;
- no compiler/build toolchain in the runtime stage;
- no VCS/build secrets;
- no package-manager mutation during runtime;
- remove unnecessary administrative/shell tooling where practical;
- fixed reviewed bootstrap/entrypoint contract;
- immutable content digest.

The fixed bootstrap may implement the pre-application quarantine gate defined in section 25, but it MUST NOT launch Freqtrade before the Supervisor has completed effective attestation and released the gate.

Image hardening is defense in depth and does not replace launch controls. `no-new-privileges`, capability drop, namespace isolation and read-only root remain mandatory regardless of image contents.

## 9. Process isolation

Mandatory launch semantics:

```text
user != root
privileged = false
no_new_privileges = true
capabilities.drop = ALL
capabilities.add = NONE
host_pid = forbidden
host_ipc = forbidden
host_uts = forbidden
host_network = forbidden
host_device_passthrough = forbidden
container_engine_socket = forbidden
seccomp = reviewed default-or-stricter
seccomp_unconfined = forbidden
```

“no devices” means no host device passthrough. Normal minimal container pseudo-devices required by the runtime are not treated as host-device authority.

AppArmor/SELinux or another LSM may provide additional defense in depth. Absence of an optional LSM control does not disable or weaken the mandatory baseline controls.

## 10. Filesystem trust classes

Root filesystem is read-only.

Runtime data is split into explicit trust classes:

```text
CONTROL-OWNED
  RuntimeGeneration
  canonical manifest
  provenance / audit evidence

IMMUTABLE RUNTIME INPUT
  canonical non-secret config
  strategy artifacts
  model artifacts

DURABLE WRITABLE
  generation-scoped Freqtrade DB/state

EPHEMERAL
  tmp/cache/run

SECRET
  generation-local runtime/API material
```

Control-owned evidence is not writable by Freqtrade and SHOULD not be mounted into Freqtrade at all.

Canonical mount model:

```text
/runtime/config/config.json        RO
/runtime/artifacts/strategy/...    RO
/runtime/artifacts/model/...       RO
/runtime/state/...                 RW generation-scoped
/tmp                               bounded tmpfs
/run/runtime-secrets/...           generation-local secret boundary

Portal manifest                    NOT MOUNTED to Freqtrade
```

Host paths are never supplied by requests. The Supervisor derives paths only from fixed approved roots and trusted identifiers/digests.

Path derivation MUST resist `..`, symlink and equivalent path-escape attacks. Prefix-string validation alone is insufficient; the implementation must resolve/canonicalize safely and reject any path that escapes an approved root.

## 11. Temporary and durable storage

Temporary storage MUST be bounded. Baseline semantics:

```text
tmpfs
noexec
nosuid
nodev
hard size limit
```

The current WH09 Compose contains a useful example:

```text
/tmp:rw,noexec,nosuid,nodev,size=64m
```

That example is evidence of a mechanism, not the Portal profile itself.

Durable state is scoped to the generation:

```text
runtime-state/<generation_id>/
```

not merely to `bot_id`.

The profile defines `durable_state_max_bytes`. Hard enforcement requires an approved backend such as a filesystem/project quota or fixed-size bounded volume. Monitoring free space or alerting after growth is not hard isolation.

If no approved hard storage backend exists:

```text
HOST_STORAGE_ISOLATION_UNSUPPORTED
```

The same principle applies to every resource bound: declared intent without enforceable containment is insufficient.

## 12. Logs

Logs are a bounded runtime resource.

The profile defines at least:

- maximum active log bytes;
- maximum rotated files/segments;
- maximum retention where applicable;
- approved bounded logging backend/driver.

A runtime MUST NOT be considered conformant merely because a log-size value is present in configuration. The selected logging backend must enforce the bound.

## 13. Resource isolation

Portal-managed Freqtrade requires effective hard containment for:

- memory;
- swap disabled or explicitly bounded;
- PID/process count;
- CPU;
- generation durable state;
- logs;
- tmpfs/ephemeral storage.

A missing required hard control blocks provisioning or application release.

### WH09 evidence correction

WH09 is evidence that host capability differences are real, not evidence that every declared limit works on Synology.

- merged PR #1392 records Docker rejection of `cpus: 2.0` / NanoCPUs because CPU CFS was unavailable on the observed Synology host;
- open diagnostic PR #1394 reports that the later protected run also observed the configured PID limit being discarded by the host/kernel.

Therefore the Portal MUST validate effective enforcement, not only Compose text, requested Docker options or `docker inspect` intent.

The WH09 research/shadow runtime is also a separate deployment profile and currently uses `restart: unless-stopped`; that does not weaken the Portal-managed Freqtrade `restart=no` rule below.

## 14. Network isolation and public market-data egress

Every generation receives its own isolated network namespace/relationship.

Logical topology:

```text
portal-worker
     |
     | generation-scoped UDS
     v
Runtime Gateway
     |
     | generation-private relationship
     v
Freqtrade
     |
     v
approved public market-data egress
```

A generation network MUST NOT provide reachability to:

- Portal API/Web;
- PostgreSQL;
- Redis;
- NATS;
- Vault/secret-management endpoints;
- training/research workers;
- container-engine endpoints;
- host-management endpoints;
- cloud/host metadata endpoints where present;
- unrelated generations;
- RFC1918/link-local/loopback/platform ranges except an explicitly approved generation-local relationship.

The policy applies consistently to IPv4 and IPv6. DNS resolution must not provide a bypass to forbidden address classes.

A normal Docker bridge by itself is not an egress firewall. The resolved plan MUST name an approved enforcement backend, for example a reviewed host firewall/nftables policy, eBPF policy or constrained egress proxy. If the required deny/allow semantics cannot be enforced, the host is incompatible.

`--network none` is not the final Portal runtime baseline because dry-run Freqtrade requires public market/exchange data connectivity. It MAY be used as part of the pre-application quarantine phase before the final approved egress policy has been installed and attested.

## 15. MarketDataEgressPolicy

Public egress policy is versioned and immutable:

```text
MarketDataEgressPolicy
  version
  digest
  allowed_destination_classes
  required_dns_policy
  denied_platform_ranges
```

The generation and isolation plan bind its version/digest.

Baseline intent:

```text
ALLOW
  required public exchange / market-data connectivity
  required approved DNS resolution

DENY
  Portal/control/data/management networks
  host-management endpoints
  container engine
  Vault
  PostgreSQL
  Redis
  NATS
  unrelated generations
  link-local/metadata endpoints
```

Exact destination allow-listing may be hostname/IP/backend dependent and must account for exchange/CDN address changes without reducing the deny boundary.

Before application release, the final egress backend and policy MUST already be installed and effectively attested while Freqtrade and Gateway application code remain blocked.

## 16. Inbound network and Runtime Gateway

Freqtrade has:

- no host-published port;
- no public listener route;
- no browser route;
- no reverse-proxy route from public/Portal ingress.

Its API is reachable only by the exact generation-local Gateway relationship.

The Gateway:

- is generation-bound;
- executes only from the exact immutable `gateway_artifact_digest` bound by the generation and isolation plan;
- implements the exact bound `gateway_contract_version` / `gateway_contract_digest`;
- exposes a generation-scoped UDS to the authorized lifecycle/reconciliation worker where applicable;
- talks to Freqtrade only inside the generation boundary;
- exposes no public HTTP endpoint;
- is not a general-purpose Freqtrade reverse proxy;
- does not expose arbitrary configuration reload, shell, plugin or raw RPC capabilities;
- MUST NOT start its application listener or receive generation-local API credentials before the section 25 attestation gate passes.

Freqtrade does not receive the worker-to-Gateway UDS mount.

A replacement Gateway artifact, even if API-compatible, changes the generation TCB identity and therefore requires a new `RuntimeGeneration` unless the exact same immutable artifact digest and plan are reproduced.

## 17. Generation-local Freqtrade API secret

The generation-local Freqtrade API credential:

- is not stored in Docker labels;
- is not passed through CLI arguments;
- is not stored in inspectable environment variables;
- is not part of the canonical `RuntimeGeneration` manifest;
- rotates for each new generation;
- is consumed only by Freqtrade and its Gateway;
- is not exposed to either application while the generation remains in pre-application attestation quarantine.

The Supervisor may manage the lifecycle of an approved generation-secret mount/reference, but MUST NOT receive plaintext credential material through its API or persist plaintext in its local state.

If Freqtrade requires a secret inside its effective runtime configuration, the approved hardened image may use a fixed reviewed bootstrap to create an ephemeral derived config inside the secret/tmpfs boundary from the immutable non-secret config plus the secret file. That derived file is not Portal-authoritative evidence and is never persisted back into the canonical config mount. Secret material must become readable to the Freqtrade/Gateway applications only after attestation PASS and gate release.

Dry-run exchange mode remains `PUBLIC_DATA`; private exchange trading credentials are not introduced by this contract.

## 18. Runtime Supervisor authority and TCB

`RuntimeSupervisor` is the only Portal component with container-engine authority.

```text
portal-api                  NO engine authority
portal-web                  NO engine authority
portal-worker               NO engine authority
training-worker             NO engine authority
exchange-verification-worker NO engine authority

runtime-supervisor          ONLY engine authority
```

The Supervisor is intentionally small.

It may have:

- container-engine lifecycle authority;
- a dedicated read-only trusted generation view;
- minimal crash-safe lifecycle/idempotency journal;
- host capability/attestation logic.

It MUST NOT have:

- exchange trading credentials;
- Vault token/SecretID/general secret-store authority;
- model-training credentials;
- browser/OIDC sessions;
- general NATS/Redis credentials;
- arbitrary Portal database write access;
- registry credentials;
- git credentials;
- live-capital authority;
- trading truth ownership.

Supervisor-local state may prove lifecycle/idempotency facts but never replaces Gateway/reconciliation data as trading truth.

## 19. Generation artifact presence and supply chain

The Supervisor does not build or pull Freqtrade or Gateway artifacts.

It accepts only exact immutable content identities already delivered to the host:

```text
Freqtrade runtime:
  digest-pinned approved image / exact local content-addressed image

Runtime Gateway:
  digest-pinned approved image
  OR exact content-addressed executable artifact
```

Mutable tag-only identity and unqualified "installed Gateway version" identity are forbidden. The Supervisor MUST independently verify both `freqtrade_image_digest` and `gateway_artifact_digest` before provisioning, and structural attestation MUST verify that the provisioned generation uses those exact identities.

If either exact artifact is absent:

```text
IMAGE_NOT_PRESENT
```

or a narrower stable artifact-not-present reason.

A separate deployment/artifact pipeline is responsible for delivery and artifact verification. This keeps registry, git and build secrets outside the Supervisor TCB.

## 20. Trusted generation lookup

The worker sends only identity and operation data, for example:

```text
generation_id
generation_spec_digest
operation
command_id
idempotency_identity
correlation_identity
```

It does not send image/mount/command/port/env/network/capability parameters.

The Supervisor obtains exact materialization data from a minimal trusted read-only view, initially preferably PostgreSQL:

```text
runtime_generation_supervisor_view
```

Use a dedicated database role with `SELECT` only on the minimum required view/relation set. The view contains no exchange/user/model-training secrets or unrelated tenant data beyond fields required to materialize the requested generation safely.

## 21. Supervisor logical API

Minimum logical API:

```text
GetHostCapabilities

EnsureProvisioned(
  generation_id,
  generation_spec_digest,
  command_id
)

EnsureRunning(...)
EnsurePaused(...)
EnsureStopped(...)
InspectGeneration(...)
EnsureRetired(...)
```

There is intentionally no:

```text
Exec
Shell
RunCommand
CreateContainer(raw)
Replace(raw or magical)
Restart(raw or magical)
Mount
PublishPort
SetEnv
SetCapabilities
SetNetwork
PullImage
BuildImage
```

The abstract isolation plan is resolved through versioned policy logic from the approved profile and host report; it is not supplied as user-controlled engine parameters.

`EnsureRunning` does not authorize immediate application execution. If the generation has not yet completed section 25 attestation for the exact generation/spec/plan/TCB identity, the Supervisor must first keep or place it in the application-quarantined attestation state and may release the application gate only after attestation succeeds.

## 22. Rollout, active-generation fence and concurrency

Replacement remains explicit stop-then-replace:

```text
EnsureStopped(G1)
  -> reconcile STOPPED
  -> persist/finalize G2 with its isolation plan
  -> EnsureProvisioned(G2)
  -> application-quarantined structural/effective attestation
  -> EnsureRunning(G2)
  -> release application gate after PASS
```

There is no magical `Replace(G1,G2)` that hides transaction boundaries from the Control Plane.

For one `(tenant_id, bot_id)`, the Supervisor provides an independent safety fence. A second generation cannot enter an execution-owned or attestation-owned active state while another different generation is active.

Active/execution-owned states include at least:

```text
PROVISIONING
PROVISIONED_QUARANTINED
ATTESTING
STARTING
RUNNING
DEGRADED
PAUSED
STOPPING
```

If G1 is active and `EnsureRunning(G2)` arrives:

```text
CONFLICTING_GENERATION_ACTIVE
```

The Supervisor never auto-stops G1 to satisfy G2.

Lifecycle operations are serialized at least by `(tenant_id, bot_id)` and by generation so concurrent Start/Stop/Start requests have deterministic ordering.

## 23. Idempotency and stale generation safety

All mutating Supervisor operations use `Ensure*` semantics.

Repeating `EnsureRunning(G2)` when G2 is already correctly running and attested returns the stable state without a second lifecycle side effect. Repeating it while G2 is correctly quarantined/attesting resumes or verifies the same idempotent attestation path; it does not bypass the gate.

The tuple `(command_id, generation_id, generation_spec_digest, operation)` is replay-safe. Reuse of an idempotency/command identity with conflicting semantic content is rejected.

If trusted control state says a generation is retired, `EnsureProvisioned` and `EnsureRunning` fail closed. A stale queue message cannot resurrect a retired generation.

A request naming an existing `generation_id` with a different `generation_spec_digest` is always a conflict.

## 24. Engine restart policy and recovery

Portal-managed Freqtrade uses:

```text
container restart policy = NO
```

The container engine must not independently resurrect a historical generation after host/daemon restart.

Recovery belongs to:

```text
Control Plane desired state
+
reconciliation
+
Runtime Supervisor
```

The Supervisor may be restarted safely; after restart it reconstructs lifecycle state from trusted generation data, its minimal idempotency journal and current engine observation. It does not infer trading truth from container state.

If attestation completion cannot be proven for the exact current host boot, generation spec, plan and TCB identities after recovery, the Supervisor MUST treat the generation as not released: application execution remains stopped/quarantined until the required attestation is repeated successfully.

## 25. Provision, quarantine and effective-enforcement attestation

Successful artifact delivery, container creation or process start is not sufficient proof of provisioning. **Freqtrade and Runtime Gateway application code MUST NOT execute before the complete isolation plan has been structurally and effectively attested.**

Attestation is a pre-application release gate.

### 25.1 Pre-application quarantine invariant

Before any untrusted/runtime application execution, the Supervisor MUST establish all controls that can be established externally, including as applicable:

- generation-specific durable-state quota/bounded volume;
- bounded log backend;
- read-only/immutable mount topology;
- deny-all or stricter quarantine network policy;
- no host/public ports;
- namespace/security options;
- exact Freqtrade and Gateway artifact identities.

While attestation is incomplete:

```text
Freqtrade application process        BLOCKED / NOT EXECUTED
Gateway application/listener         BLOCKED / NOT EXECUTED
worker-to-Gateway application path   NOT RELEASED
generation API secret                NOT EXPOSED TO APPLICATIONS
public market-data egress            DENIED
Portal/control/data-plane egress     DENIED
```

The implementation MUST NOT rely on "start application, then inspect quickly" or "start then immediately pause" because both create a race window before isolation proof.

If an effective control can be verified only after a cgroup/network namespace/process exists, the approved hardened artifact may start **only** a fixed reviewed attestation bootstrap/gate. That bootstrap:

- is part of the immutable attested artifact;
- runs under the same non-root, no-new-privileges, capability-drop and namespace baseline;
- cannot launch Freqtrade or the Gateway application before Supervisor release;
- receives no generation API credential or private secret;
- has no public/market egress while quarantined;
- exposes no worker/Gateway application endpoint;
- has no arbitrary command/shell path controlled by the Portal request.

The Supervisor-controlled release mechanism is fixed by the profile/implementation and is not a general `Exec` or arbitrary command API.

### 25.2 Stage A — structural/static attestation

While the generation remains application-quarantined, compare the expected plan to observed structure, including:

- exact Freqtrade image digest;
- exact Gateway artifact digest and Gateway contract identity;
- runtime users;
- privileged flags;
- security options;
- capabilities;
- namespaces;
- mounts and mount modes;
- network attachments / quarantine state;
- no published ports;
- requested resource controls;
- restart policy;
- labels/identity metadata.

Mismatch:

```text
ISOLATION_ATTESTATION_FAILED
```

The generation remains quarantined and is stopped/removed according to lifecycle policy. Application release is forbidden.

### 25.3 Stage B — effective enforcement attestation

Still before application release, verify that the host/kernel/backend actually enforces required controls, including as applicable:

- cgroup memory and swap bounds;
- PID hard bound;
- CPU quota/CPUSET assignment and effective ceiling;
- storage quota/bounded volume;
- tmpfs size/options;
- bounded log backend;
- read-only filesystem and immutable mount behaviour;
- final generation network segmentation and deny rules;
- final `MarketDataEgressPolicy` backend and effective policy.

The final network/egress policy may be installed while the fixed bootstrap remains blocked; Freqtrade and Gateway application execution still must not be released until that policy is verified. The bootstrap itself does not exercise application credentials or market connectivity.

Configured Docker/Compose values or `docker inspect` alone are not sufficient when effective kernel/backend state can differ.

The WH09 Synology evidence is the concrete reason for this rule.

### 25.4 Release rule

Only:

```text
EXPECTED PLAN
  == OBSERVED STRUCTURE
  == EFFECTIVE ENFORCEMENT
  == EXACT FREQTRADE ARTIFACT
  == EXACT GATEWAY ARTIFACT / CONTRACT
```

may transition the exact generation from `PROVISIONED_QUARANTINED/ATTESTING` to an attested state eligible for application release.

After PASS, and only after PASS, the Supervisor may release the fixed application gate, make generation-local secret material available to its intended consumers and allow the Gateway/Freqtrade application processes to enter `STARTING/RUNNING` under the already-attested final network/resource envelope.

Any attestation failure or inability to prove a required control remains fail-closed. The generation MUST NOT be presented as `PROVISIONED`/`RUNNING` merely because the engine reports a created/running bootstrap container.

## 26. Retirement

`EnsureRetired(G1)` is permitted only after the Control Plane has durable proof that rollout/lifecycle rules allow retirement.

Retirement may remove:

- container;
- ephemeral generation network;
- ephemeral Gateway;
- generation-local temporary secret material;
- other explicitly ephemeral generation resources.

It does not automatically remove:

- `RuntimeGeneration` identity;
- audit/provenance evidence;
- historical reconciliation;
- durable state still subject to retention policy.

Retention deletion is a separate controlled lifecycle action.

## 27. Supervisor is not trading truth

The Supervisor may know:

- container absent/created/quarantined/running/paused/stopped;
- engine health;
- structural/effective isolation attestation;
- host compatibility;
- exact Freqtrade/Gateway TCB artifact attestation.

It does not authoritatively know:

- positions;
- orders;
- trades;
- valuation;
- execution success;
- exchange truth.

Those remain within the generation-bound Gateway plus authoritative reconciliation defined by ADR-020.

## 28. Transport

Initial single-host worker-to-Supervisor transport:

```text
Unix Domain Socket
+
filesystem ACL
+
OS peer credentials
```

Example logical path:

```text
/run/quant-platform/runtime-supervisor.sock
```

Only the runtime-lifecycle worker identity receives access. Browser, Portal API, training workers, Freqtrade and the Gateway do not receive that socket.

Future multi-host transport preserves the logical API and changes transport to:

```text
mTLS
+
workload identity
+
explicit service authorization
```

Plain HTTP, public Supervisor endpoints and browser-accessible Supervisor endpoints are forbidden.

Multi-host activation additionally requires an explicit cross-host placement/fencing design that proves single-active-generation semantics, generation ownership and recovery across host/network partitions. Replacing UDS with mTLS alone is not sufficient evidence of safe multi-host execution.

## 29. Required reason codes

Implementations should expose stable machine-readable errors including at least the semantics of:

```text
HOST_INCOMPATIBLE
HOST_CPU_ISOLATION_UNSUPPORTED
HOST_PID_ISOLATION_UNSUPPORTED
HOST_STORAGE_ISOLATION_UNSUPPORTED
HOST_NETWORK_ISOLATION_UNSUPPORTED
HOST_LOG_ISOLATION_UNSUPPORTED
HOST_CAPABILITY_REPORT_STALE
IMAGE_NOT_PRESENT
GATEWAY_ARTIFACT_NOT_PRESENT
GENERATION_SPEC_CONFLICT
ISOLATION_PLAN_MISMATCH
ISOLATION_ATTESTATION_FAILED
APPLICATION_RELEASE_FORBIDDEN
CONFLICTING_GENERATION_ACTIVE
STALE_OR_RETIRED_GENERATION
```

Names may be versioned before implementation, but failure classes must remain explicit and fail closed.

## 30. Required negative acceptance tests

The implementation is incomplete until tests attempt and prove controlled rejection/containment of at least:

- root user;
- `privileged=true`;
- capability addition;
- disabling `no-new-privileges`;
- writable root filesystem;
- host network;
- host PID/IPC/UTS;
- host device passthrough;
- Docker/container-engine socket mount;
- `/etc` mount;
- arbitrary bind mount;
- symlink/path traversal escape from an approved root;
- arbitrary command/entrypoint;
- arbitrary Freqtrade image;
- mutable tag-only Freqtrade image identity;
- Gateway artifact substitution/tamper;
- Gateway contract digest/version mismatch;
- mutable/unqualified Gateway artifact identity;
- public/host port publication;
- Portal DB/Vault/NATS/Redis reachability from a generation;
- cross-bot/cross-generation network access;
- IPv6/private/link-local/metadata network bypass;
- write to immutable config/artifacts;
- write/read of Portal control manifest from Freqtrade;
- oversized tmpfs;
- PID exhaustion;
- memory/swap overrun;
- CPU containment loss;
- durable-state quota exhaustion;
- unbounded log growth;
- stale capability report;
- capability-report/plan digest mismatch;
- configured-but-not-effective cgroup enforcement;
- attempt to launch Freqtrade before effective attestation PASS;
- attempt to launch/ expose Gateway listener before effective attestation PASS;
- attempt to expose generation API secret before effective attestation PASS;
- attempt to enable public market egress while still in deny-all quarantine before final egress-policy attestation;
- attestation failure followed by attempted application release;
- stale/retired generation restart;
- concurrent G1/G2 activation or attestation;
- `command_id` replay with different generation/spec/operation semantics;
- Freqtrade image content mismatch after tag mutation;
- Gateway artifact content mismatch after mutable alias/tag mutation.

Expected outcome is a controlled `REJECT`, `DENY`, `HOST_INCOMPATIBLE`, `APPLICATION_RELEASE_FORBIDDEN` or hard `RESOURCE LIMIT`, not silent weakening.

## 31. Required positive acceptance tests

Hardening must not break valid Portal dry-run operation. Positive acceptance includes:

- exact immutable Freqtrade image identity verified;
- exact immutable Gateway artifact and Gateway contract identity verified;
- generation enters application quarantine without launching Freqtrade/Gateway application code;
- fixed attestation bootstrap can establish/probe required effective host controls without secrets or public egress;
- structural and effective attestation completes before application release;
- final network/egress policy is verified before Gateway/Freqtrade application start;
- hardened Freqtrade boot only after attestation PASS;
- generation-bound Gateway boot/listener only after attestation PASS;
- generation-local secret becomes available only after attestation PASS;
- `PUBLIC_DATA` connectivity after release;
- market metadata/data access through approved egress;
- generation-local Gateway communication;
- worker-to-Gateway UDS path;
- `EnsureProvisioned`, `EnsureRunning`, `EnsurePaused`, `EnsureStopped` idempotency;
- state persistence within one generation;
- Gateway reads;
- authoritative reconciliation;
- Supervisor restart and reconstruction;
- host/runtime recovery with exact unchanged plan and exact TCB artifacts;
- replacement creating a new generation when plan/security/TCB semantics change.

## 32. Implementation sequencing

This refinement preserves ADR-020 dependency order and makes the following implementation consequences explicit:

1. #1357 / #1388 must bind executable generations to the resolved isolation-plan digest and exact generation TCB artifacts before claiming ADR-020 runtime-materialization completeness.
2. #1353 must physically separate control-owned evidence, immutable inputs and runtime-writable state.
3. #1354 must implement profile, capability discovery, plan resolution, application-quarantined effective resource/network/storage/log enforcement and negative isolation tests.
4. #1355 must implement the narrow Supervisor boundary, pre-application release gate and remove raw engine authority from normal Portal roles.
5. Gateway/secret work must preserve generation-local credentials, exact immutable Gateway artifact identity and no direct browser/worker-to-Freqtrade path.
6. PI-01/reconciliation remains authoritative for runtime/trading observation.
7. Exposure-increasing execution work remains fail closed until all preceding safety gates pass.

No step may claim implementation merely because this target contract is accepted.

## 33. Final topology

```text
Browser
   |
Portal Web
   |
Portal API
   |
PostgreSQL
   |
Portal Worker
   |
   | UDS + ACL + peer credentials
   v
Runtime Supervisor
   |
   | only Portal component with engine authority
   v
Container Engine
   |
   +------------------------------------------------+
   | RuntimeGeneration G42                          |
   |                                                |
   |  Gateway <------ private ------> Freqtrade    |
   |     ^                              |           |
   |     | generation UDS               |           |
   |     +---------------- worker       |           |
   |                                    v           |
   |                     approved public market    |
   |                     data egress only          |
   +------------------------------------------------+

Before attestation PASS the generation remains application-quarantined:
no Freqtrade/Gateway application execution, no application secrets,
no worker application path and no public market egress.

Generation network has NO path to:
Portal DB / Vault / NATS / Redis / container engine /
other tenant runtime / public Freqtrade port.
```

## 34. Binding refinement decisions

The following are binding refinements of ADR-020 after merge:

1. `RuntimeIsolationProfile` is immutable and versioned.
2. Host capability evidence is explicit and never guessed by the Control Plane.
3. A resolved immutable `RuntimeIsolationPlan` is required for every executable generation.
4. `RuntimeGeneration` binds both profile and plan identity; isolation semantics do not mutate in place.
5. The isolation plan and generation separately bind the exact immutable Freqtrade image identity and exact immutable Gateway artifact/contract identity; changing either TCB artifact requires a new generation.
6. Security invariants have no fallback.
7. Capability-resolved controls may use only pre-approved mechanisms that preserve the required bound.
8. Missing hard CPU, memory/swap, PID, durable-state, log or tmpfs containment blocks a Portal-managed runtime.
9. Configured intent is not enforcement proof. Structural and effective attestation MUST complete **before Freqtrade or Gateway application execution**. Controls requiring a live cgroup/namespace are probed only through a fixed reviewed application-quarantined bootstrap with no secrets, worker application path or public market egress.
10. Portal uses a hardened Freqtrade runtime image without the root Dockerfile's sudo/NOPASSWD convenience as a trust dependency.
11. Root filesystem is read-only and control-owned evidence is never runtime-writable.
12. Durable Freqtrade state is generation-scoped and hard-bounded.
13. Each generation has isolated networking and a versioned market-data egress policy; the final egress policy is installed and attested before application release.
14. Freqtrade has no host/public port and is reachable only through its generation-local Gateway relationship after attestation PASS.
15. Runtime Supervisor is the only Portal component with container-engine authority.
16. Supervisor accepts identity/lifecycle operations, never raw engine parameters.
17. Supervisor does not pull/build Freqtrade or Gateway artifacts and has no registry/git credentials.
18. Supervisor uses a minimal read-only trusted generation view and no general Portal DB write access.
19. No magical `Replace`/`Restart` hides rollout state transitions.
20. Only one generation per bot may occupy an attestation-owned or execution-owned active state at a time.
21. Portal-managed Freqtrade engine restart policy is `NO`; recovery is explicit reconciliation and re-attestation when exact current-host attestation cannot be proven.
22. Freqtrade API credentials are generation-local, ephemeral and absent from CLI/labels/env/canonical generation evidence; applications do not receive them before attestation PASS.
23. Supervisor lifecycle state never becomes trading truth.
24. WH09 CPU/PID observations are host-capability evidence only and may not justify weakening Portal hard-containment requirements.
25. Future multi-host Supervisor transport additionally requires explicit placement/fencing semantics; mTLS transport alone is insufficient.
26. This refinement authorizes no production deployment, private exchange trading credentials or live capital.