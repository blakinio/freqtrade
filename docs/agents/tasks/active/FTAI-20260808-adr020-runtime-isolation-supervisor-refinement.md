# FTAI-20260808 — ADR-020 Runtime Isolation and Supervisor Refinement

```yaml
task_id: FTAI-20260808-adr020-runtime-isolation-supervisor-refinement
project_lane: freqtrade-portal
programme: AI Trading Portal
policy_version: 2
prompting_standard_version: 2.1
task_kind: implementation
feature_scope:
  type: documentation
  user_facing: false
  backend_required: false
  frontend_required: false
  integration_required: true
  e2e_required: false
  completion_claim: internal_only
decomposition_decision: single
execution_mode: chat_github
run_scope: single_task
continuation_policy: stop_at_task_boundary
task_completion_policy: finalize_archive_and_continue
implementation_authorized: true
status: implementing
base_branch: develop
trusted_base_sha: c64df386a4fa3ba739b6eaa1a223ca798a7bcae2
branch: docs/adr-020-runtime-isolation-supervisor-refinement-20260808
pr: none
related_adr: ADR-020
related_issues:
  - 1353
  - 1354
  - 1355
  - 1357
related_prs:
  - 1388
  - 1392
  - 1394
live_capital_authorized: false
production_deployment_authorized: false
```

## Objective

Refine accepted ADR-020 with one binding, fail-closed contract for Portal-managed Freqtrade dry-run runtime isolation and the Runtime Supervisor boundary, using current repository and Synology/WH09 evidence without expanding execution, production, credential or live-capital authority.

## Owned paths

- `ARCHITECTURE_REGISTRY.yaml`
- `docs/ai_platform/portal/ARCHITECTURE_DECISIONS.md`
- `docs/ai_platform/portal/RUNTIME_ISOLATION_AND_SUPERVISOR_CONTRACT.md`
- `docs/ai_platform/portal/SYSTEM_ARCHITECTURE.md`
- `docs/ai_platform/portal/SECURITY_ARCHITECTURE.md`
- `docs/agents/tasks/active/FTAI-20260808-adr020-runtime-isolation-supervisor-refinement.md`

## Acceptance inventory

- `A1`: ADR-020 remains the parent accepted decision; this work is a refinement, not a new authority grant.
- `A2`: `RuntimeIsolationProfile`, host capability evidence and a resolved immutable `RuntimeIsolationPlan` are defined without raw container-engine parameter passthrough.
- `A3`: an executable `RuntimeGeneration` binds immutable isolation profile and plan digests; no existing generation can silently change its security/resource envelope.
- `A4`: security invariants fail closed when the host cannot enforce them; capability-resolved alternatives are allow-listed and semantically bounded.
- `A5`: WH09 evidence is represented accurately: CPU CFS/NanoCPUs failed on Synology and latest diagnostic evidence reports that a configured PID limit was discarded, so configured intent alone is not accepted enforcement proof.
- `A6`: Portal-managed Freqtrade uses a hardened image baseline and does not inherit the repository Dockerfile's sudo/NOPASSWD convenience as its trust boundary.
- `A7`: trusted control evidence, immutable inputs, generation-scoped durable state, temporary state, logs and secret material have distinct explicit boundaries.
- `A8`: every generation has generation-scoped network isolation, no public/host Freqtrade port, and only approved market-data egress plus its local Gateway relationship.
- `A9`: Runtime Supervisor is the only Portal component with container-engine authority and has a narrow idempotent lifecycle API with no raw Exec/Shell/Docker controls.
- `A10`: provisioning requires both structural and effective-enforcement attestation; Docker/Compose configuration or inspect output alone is insufficient.
- `A11`: restart/recovery, one-generation fencing, concurrency, retirement and stale-message behaviour remain generation-safe and reconciliation-authoritative.
- `A12`: negative and positive acceptance suites cover the security/resource/network/storage/supervisor contract, including host-capability downgrade and enforcement-loss cases.
- `A13`: `ARCHITECTURE_REGISTRY.yaml`, ADR-020 and target security/system architecture remain mutually consistent.
- `A14`: open PR #1388 is not modified; its current `RuntimeGeneration` schema gap for `isolation_plan_digest` is recorded as implementation consequence rather than silently claimed complete.
- `A15`: no production deployment, protected-host mutation, private exchange credential activation or live capital is authorized.

## Context checkpoint

```yaml
checkpoint_version: 1
updated_at: 2026-08-08T20:23:08Z
head: c64df386a4fa3ba739b6eaa1a223ca798a7bcae2
branch: docs/adr-020-runtime-isolation-supervisor-refinement-20260808
pr: none
status: implementing
context_routes:
  - ARCHITECTURE_REGISTRY.yaml
  - docs/ai_platform/portal/ARCHITECTURE_DECISIONS.md
  - issues/1353
  - issues/1354
  - issues/1355
  - pull/1388
  - pull/1392
  - pull/1394
owned_paths:
  - ARCHITECTURE_REGISTRY.yaml
  - docs/ai_platform/portal/ARCHITECTURE_DECISIONS.md
  - docs/ai_platform/portal/RUNTIME_ISOLATION_AND_SUPERVISOR_CONTRACT.md
  - docs/ai_platform/portal/SYSTEM_ARCHITECTURE.md
  - docs/ai_platform/portal/SECURITY_ARCHITECTURE.md
  - docs/agents/tasks/active/FTAI-20260808-adr020-runtime-isolation-supervisor-refinement.md
proven:
  - develop is the repository default branch and trusted task base is c64df386a4fa3ba739b6eaa1a223ca798a7bcae2.
  - ADR-020 is accepted and already binds RuntimeGeneration, Runtime Supervisor, per-runtime Gateway, public-data dry-run and a mandatory RuntimeIsolationProfile.
  - Issues 1353, 1354 and 1355 remain open implementation work after ADR-020.
  - The repository Dockerfile gives ftuser sudo membership and NOPASSWD /bin/chown.
  - WH09 PR 1392 records Synology rejection of CPU CFS/NanoCPUs; open diagnostic PR 1394 reports that the same host discarded the configured PID limit.
  - Draft PR 1388 currently models isolation_profile_version and isolation_profile_digest but not isolation_plan_digest.
derived:
  - Host capability intent must be independently verified by effective post-start enforcement attestation.
  - Isolation plan identity must describe canonical resolved controls, not volatile capability-report timestamps or host identity.
  - RuntimeGeneration materialization must not become executable before the resolved plan digest is immutable.
unknown:
  - final exact-head CI result for this documentation branch.
  - independent post-change audit result.
conflicts:
  - WH09 compose declares pids_limit but current host evidence reports the kernel discarded it; declaration cannot be treated as proof of enforcement.
first_failure:
  marker: none
  evidence: none
rejected_hypotheses:
  - main is the canonical branch; repository metadata and registry prove develop is canonical.
  - WH09 proves working CPU/PID containment on Synology; current protected-run evidence disproves both assumptions for the observed mechanisms.
changed_paths:
  - docs/agents/tasks/active/FTAI-20260808-adr020-runtime-isolation-supervisor-refinement.md
validation:
  - command: repository/live-state architecture preflight
    result: PASS
    evidence: develop@c64df386a4fa3ba739b6eaa1a223ca798a7bcae2; ADR-020; issues 1353-1355; PRs 1388/1392/1394
blockers:
  - none
next_action: write the binding runtime isolation and supervisor contract, then align ADR-020, registry and target architecture documents
```
