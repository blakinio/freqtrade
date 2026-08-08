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
status: completed
base_branch: develop
trusted_base_sha: c64df386a4fa3ba739b6eaa1a223ca798a7bcae2
branch: docs/adr-020-runtime-isolation-supervisor-refinement-20260808
pr: 1395
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

## Delivered

- Added `docs/ai_platform/portal/RUNTIME_ISOLATION_AND_SUPERVISOR_CONTRACT.md` as the detailed owner-accepted ADR-020 refinement, effective as trusted-base authority only after merge.
- Bound executable `RuntimeGeneration` to immutable isolation-profile and resolved isolation-plan identity.
- Added explicit `RuntimeHostCapabilityReport` and deterministic capability-aware plan resolution.
- Split controls into no-fallback security invariants and pre-approved capability-resolved hard-containment mechanisms.
- Required structural plus effective host/kernel enforcement attestation; Compose/Docker intent alone is not accepted as proof.
- Corrected WH09 interpretation: Synology rejected CPU CFS/NanoCPUs and later diagnostic evidence reported the configured PID limit was discarded.
- Defined hard CPU, memory/swap, PID, durable-state, log and tmpfs containment.
- Defined generation-scoped state, immutable input/control evidence separation, generation-local secret boundary and deterministic safe mount roots.
- Defined hardened Portal Freqtrade image requirements without relying on the repository root Dockerfile sudo/NOPASSWD convenience.
- Defined isolated generation networking, versioned public-market-data egress policy, no host/public Freqtrade port and no Portal/control/data-plane reachability.
- Kept Runtime Supervisor as the sole Portal container-engine authority with narrow identity/lifecycle API and no raw engine parameters.
- Kept Gateway + authoritative reconciliation as trading truth; Supervisor state remains lifecycle/isolation evidence only.
- Preserved explicit stop-then-replace, one-generation safety fencing, stale-generation denial, idempotency and engine `restart=NO` semantics.
- Aligned ADR-020, architecture registry, system architecture and security architecture.
- Recorded that open implementation PR #1388 still lacks `isolation_plan_digest` and cannot claim full conformance with this refinement until that binding exists.

## Validation and evidence

```yaml
trusted_base:
  branch: develop
  sha: c64df386a4fa3ba739b6eaa1a223ca798a7bcae2
architecture_preflight:
  result: PASS
  evidence:
    - ADR-020 accepted and remains parent decision.
    - issues 1353, 1354, 1355 and 1357 remain implementation work.
    - root Dockerfile currently grants ftuser sudo membership and NOPASSWD /bin/chown.
    - PR 1392 records Synology CPU CFS/NanoCPUs incompatibility.
    - PR 1394 diagnostic evidence reports the configured PID limit was discarded by the observed target.
    - PR 1388 models isolation profile identity but not isolation_plan_digest.
diff_audit:
  result: PASS
  evidence:
    - cumulative PR 1395 diff reviewed.
    - accidental first-pass removal of two existing multi-tenancy constraints was detected and restored.
    - accidental first-pass replacement of baseline identity/CSRF/RBAC security test inventory was detected and restored additively.
    - no implementation code, workflow, deployment or protected-host path is changed.
review_threads:
  result: PASS
  evidence: no open inline review threads at final documentation audit checkpoint before archival commit.
exact_head_ci_before_archival_record:
  sha: 5920c62ea86dcd3f307986fcc134ab098a330d72
  freqtrade_ci: success
  codeql_security_analysis: success
  risk_aware_component_ci: success
  zizmor_security_analysis: success
  precommit_types_update: skipped
runtime_e2e:
  result: NOT_APPLICABLE
  reason: documentation-only architecture refinement; no runtime implementation, deployment or protected-host mutation is authorized or claimed.
```

The archival commit changes only task-governance documentation after the green exact-head architecture payload. Required PR checks must still be evaluated on the final PR head before merge.

## Acceptance inventory

- `A1` PASS — ADR-020 remains parent accepted decision; no new authority grant.
- `A2` PASS — profile, host capability evidence and resolved plan are defined without raw engine passthrough.
- `A3` PASS — executable generation binds immutable profile/plan identity in target contract.
- `A4` PASS — security invariants fail closed; alternative mechanisms are allow-listed and bounded.
- `A5` PASS — WH09 CPU/PID evidence represented accurately.
- `A6` PASS — hardened Portal Freqtrade image baseline defined separately from root Dockerfile convenience.
- `A7` PASS — control evidence, immutable inputs, durable state, ephemeral state/logs and secrets separated.
- `A8` PASS — generation network isolation and approved market-data egress defined.
- `A9` PASS — Runtime Supervisor sole engine authority; narrow Ensure* logical API.
- `A10` PASS — structural and effective-enforcement attestation required.
- `A11` PASS — generation-safe lifecycle/recovery/concurrency/retirement semantics defined.
- `A12` PASS — negative and positive acceptance inventory expanded.
- `A13` PASS — registry, ADR-020, system and security target architecture aligned.
- `A14` PASS — #1388 left untouched; isolation-plan schema gap recorded as implementation consequence.
- `A15` PASS — no deployment, private exchange credential activation or live capital authorized.

## Remaining implementation work

This documentation task is complete; runtime implementation is deliberately not complete. The remaining implementation stays in the existing work graph:

1. #1357 / #1388 — generation state and immutable executable generation identity, including the new plan-digest consequence.
2. #1353 — physical trusted/control vs runtime-writable storage separation.
3. #1354 — profile/capability/plan resolver, hard resource/storage/log/network containment and effective attestation.
4. #1355 — Runtime Supervisor process/API/UDS/engine-authority boundary.
5. Gateway/secret/reconciliation packages defined by ADR-020.

Future multi-host Supervisor execution remains outside the initial single-host scope and must receive a separate bounded design for cross-host placement/fencing and workload identity before activation; transport substitution alone is not sufficient evidence of safe multi-host execution.

## Completion claim

`COMPLETED` means only that the ADR-020 refinement has been verified, corrected, recorded and aligned as target architecture in PR #1395. It does **not** mean the runtime isolation/Supervisor implementation exists, that Synology satisfies the Portal profile, that protected deployment was performed, or that live/private trading authority exists.
