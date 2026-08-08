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
- immutable image content identity;
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

Capability reporting does not replace post-create/post-start attestation. A host may accept configuration syntactically yet fail to enforce it effectively.

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
  image_digest = ...

  isolation_plan_digest
```

The plan contains canonical resolved security/resource semantics and approved enforcement modes. It does not contain arbitrary engine arguments.

### Digest rule

`isolation_plan_digest` MUST be calculated from a canonical serialization of stable resolved-plan fields.

The digest MUST NOT depend on volatile capability-report metadata such as `report_id`, `generated_at`, host name or host boot ID. Otherwise an unchanged effective plan would acquire a new identity merely because capabilities were re-probed or because an equivalent host was selected.

The capability report and report digest remain separate provisioning evidence.

## 6. RuntimeGeneration binding and materialization order

An executable `RuntimeGeneration` MUST bind at least:

```text
isolation_profile_version
isolation_profile_digest
isolation_plan_digest
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
persist final immutable RuntimeGeneration with plan digest
        |
EnsureProvisioned(generation_id, generation_spec_digest, command_id)
```

A pre-plan rollout/materialization request is not an executable `RuntimeGeneration`.

Once the final generation exists, its isolation profile or plan digest MUST NOT be mutated. If security/resource semantics need to change, create a new generation.

Implementation consequence: the current draft #1388 `RuntimeGeneration` model contains `isolation_profile_version` and `isolation_profile_digest` but does not yet contain `isolation_plan_digest`; #1388 or a successor implementation must add the binding before claiming conformance with this refinement.

## 7. Recovery of the same generation

The same `RuntimeGeneration` may be recreated only when the target host can reproduce the exact canonical `RuntimeIsolationPlan`.

A different capability report or host is acceptable only if the resolved plan digest remains identical and post-provision effective attestation passes.

If migration/recovery requires a material change in any of the following, create a new generation:

- CPU containment mode/bound when it changes plan semantics;
- memory/swap policy;
- PID enforcement;
- storage enforcement or bounds;
- log enforcement or bounds;
- network enforcement or egress policy;
- security profile or process isolation;
- image content;
- secret boundary semantics.

No security/resource envelope change may occur silently during recovery.

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
- fixed reviewed entrypoint/command contract;
- immutable content digest.

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

A missing required hard control blocks provisioning or startup.

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

`--network none` is not the Portal baseline because dry-run Freqtrade requires public market/exchange data connectivity.

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

## 16. Inbound network and Runtime Gateway

Freqtrade has:

- no host-published port;
- no public listener route;
- no browser route;
- no reverse-proxy route from public/Portal ingress.

Its API is reachable only by the exact generation-local Gateway relationship.

The Gateway:

- is generation-bound;
- exposes a generation-scoped UDS to the authorized lifecycle/reconciliation worker where applicable;
- talks to Freqtrade only inside the generation boundary;
- exposes no public HTTP endpoint;
- is not a general-purpose Freqtrade reverse proxy;
- does not expose arbitrary configuration reload, shell, plugin or raw RPC capabilities.

Freqtrade does not receive the worker-to-Gateway UDS mount.

## 17. Generation-local Freqtrade API secret

The generation-local Freqtrade API credential:

- is not stored in Docker labels;
- is not passed through CLI arguments;
- is not stored in inspectable environment variables;
- is not part of the canonical `RuntimeGeneration` manifest;
- rotates for each new generation;
- is consumed only by Freqtrade and its Gateway.

The Supervisor may manage the lifecycle of an approved generation-secret mount/reference, but MUST NOT receive plaintext credential material through its API or persist plaintext in its local state.

If Freqtrade requires a secret inside its effective runtime configuration, the approved hardened image may use a fixed reviewed bootstrap to create an ephemeral derived config inside the secret/tmpfs boundary from the immutable non-secret config plus the secret file. That derived file is not Portal-authoritative evidence and is never persisted back into the canonical config mount.

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

## 19. Image presence and supply chain

The Supervisor does not build or pull images.

It accepts only an immutable image digest/content identity already present on the host.

Accepted identity is either a digest-pinned approved image reference or exact local content-addressed image identity. Mutable tag-only identity is forbidden.

If the exact artifact is absent:

```text
IMAGE_NOT_PRESENT
```

A separate deployment/artifact pipeline is responsible for delivery and image verification. This keeps registry, git and build secrets outside the Supervisor TCB.

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

## 22. Rollout, active-generation fence and concurrency

Replacement remains explicit stop-then-replace:

```text
EnsureStopped(G1)
  -> reconcile STOPPED
  -> persist/finalize G2 with its isolation plan
  -> EnsureProvisioned(G2)
  -> EnsureRunning(G2)
```

There is no magical `Replace(G1,G2)` that hides transaction boundaries from the Control Plane.

For one `(tenant_id, bot_id)`, the Supervisor provides an independent safety fence. A second generation cannot enter an execution-owned active state while another different generation is active.

Active/execution-owned states include at least:

```text
PROVISIONING
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

Repeating `EnsureRunning(G2)` when G2 is already correctly running and attested returns the stable state without a second lifecycle side effect.

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

## 25. Provision and effective-enforcement attestation

Successful container creation is not sufficient proof of provisioning.

Attestation has two stages.

### Stage A — structural/static attestation

After create, compare expected plan to observed container structure:

- exact image digest;
- runtime user;
- privileged flag;
- security options;
- capabilities;
- namespaces;
- mounts and mount modes;
- network attachments;
- no published ports;
- requested resource controls;
- restart policy;
- labels/identity metadata.

Mismatch:

```text
ISOLATION_ATTESTATION_FAILED
```

### Stage B — effective enforcement attestation

Before a generation is considered operational, verify that the host/kernel actually enforces required controls, including as applicable:

- cgroup memory and swap bounds;
- PID hard bound;
- CPU quota/CPUSET assignment and effective ceiling;
- storage quota/bounded volume;
- tmpfs size/options;
- bounded log backend;
- active network/egress policy;
- read-only filesystem and immutable mount behaviour.

Configured Docker/Compose values or `docker inspect` alone are not sufficient when effective kernel state can differ.

The WH09 Synology evidence is the concrete reason for this rule.

Only:

```text
EXPECTED PLAN == OBSERVED STRUCTURE == EFFECTIVE ENFORCEMENT
```

may produce the Supervisor-side operational state used by reconciliation.

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

- container absent/created/running/paused/stopped;
- engine health;
- structural/effective isolation attestation;
- host compatibility.

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
GENERATION_SPEC_CONFLICT
ISOLATION_PLAN_MISMATCH
ISOLATION_ATTESTATION_FAILED
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
- arbitrary image;
- mutable tag-only image identity;
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
- stale/retired generation restart;
- concurrent G1/G2 activation;
- `command_id` replay with different generation/spec/operation semantics;
- image content mismatch after tag mutation.

Expected outcome is a controlled `REJECT`, `DENY`, `HOST_INCOMPATIBLE` or hard `RESOURCE LIMIT`, not silent weakening.

## 31. Required positive acceptance tests

Hardening must not break valid Portal dry-run operation. Positive acceptance includes:

- hardened Freqtrade boot;
- `PUBLIC_DATA` connectivity;
- market metadata/data access through approved egress;
- generation-local Gateway communication;
- worker-to-Gateway UDS path;
- `EnsureProvisioned`, `EnsureRunning`, `EnsurePaused`, `EnsureStopped` idempotency;
- state persistence within one generation;
- Gateway reads;
- authoritative reconciliation;
- Supervisor restart and reconstruction;
- host/runtime recovery with exact unchanged plan;
- replacement creating a new generation when plan/security semantics change.

## 32. Implementation sequencing

This refinement preserves ADR-020 dependency order and makes the following implementation consequences explicit:

1. #1357 / #1388 must bind executable generations to the resolved isolation-plan digest before claiming ADR-020 runtime-materialization completeness.
2. #1353 must physically separate control-owned evidence, immutable inputs and runtime-writable state.
3. #1354 must implement profile, capability discovery, plan resolution, effective resource/network/storage/log enforcement and negative isolation tests.
4. #1355 must implement the narrow Supervisor boundary and remove raw engine authority from normal Portal roles.
5. Gateway/secret work must preserve generation-local credentials and no direct browser/worker-to-Freqtrade path.
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
5. Security invariants have no fallback.
6. Capability-resolved controls may use only pre-approved mechanisms that preserve the required bound.
7. Missing hard CPU, memory/swap, PID, durable-state, log or tmpfs containment blocks a Portal-managed runtime.
8. Configured intent is not enforcement proof; structural and effective post-start attestation are both required.
9. Portal uses a hardened Freqtrade runtime image without the root Dockerfile's sudo/NOPASSWD convenience as a trust dependency.
10. Root filesystem is read-only and control-owned evidence is never runtime-writable.
11. Durable Freqtrade state is generation-scoped and hard-bounded.
12. Each generation has isolated networking and a versioned market-data egress policy.
13. Freqtrade has no host/public port and is reachable only through its generation-local Gateway relationship.
14. Runtime Supervisor is the only Portal component with container-engine authority.
15. Supervisor accepts identity/lifecycle operations, never raw engine parameters.
16. Supervisor does not pull/build images and has no registry/git credentials.
17. Supervisor uses a minimal read-only trusted generation view and no general Portal DB write access.
18. No magical `Replace`/`Restart` hides rollout state transitions.
19. Only one generation per bot may occupy an execution-owned active state at a time.
20. Portal-managed Freqtrade engine restart policy is `NO`; recovery is explicit reconciliation.
21. Freqtrade API credentials are generation-local, ephemeral and absent from CLI/labels/env/canonical generation evidence.
22. Supervisor lifecycle state never becomes trading truth.
23. WH09 CPU/PID observations are host-capability evidence only and may not justify weakening Portal hard-containment requirements.
24. This refinement authorizes no production deployment, private exchange trading credentials or live capital.
