---
task_id: FTAI-20260811-portal-repository-truth-1468
programme_id: FTAI-PROGRAM-AI-TRADING-PORTAL
project_lane: freqtrade-portal
status: validating
task_kind: ci_governance
priority: high
repository: blakinio/freqtrade
base_branch: develop
branch: docs/portal-repository-truth-1468
related_pr: 1469
issue: 1468
created: 2026-08-11
updated: 2026-08-11
live_capital_authorized: false
production_deployment_authorized: false
---

# Portal repository truth and CODEOWNERS drift guard

## Objective

Make `ai_platform/portal/README.md` and `.github/CODEOWNERS` reflect the exact current Portal implementation boundary without turning target architecture into implementation claims, and add a deterministic CI guard against the verified drift.

## Feature scope

```yaml
feature_scope:
  type: documentation
  user_facing: false
  backend_required: false
  frontend_required: false
  integration_required: true
  e2e_required: false
  completion_claim: internal_only
```

Runtime/browser E2E is `NOT_APPLICABLE`: no product/runtime/deployment behavior changes. Repository documentation build, `tests/ci`, exact-head required CI and independent review remain required.

## Acceptance

- stale `future/unimplemented` Portal wording is absent;
- README points current implementation claims to `tools/portal_audit/ledger/index.json` and architecture claims to `ARCHITECTURE_REGISTRY.yaml` / canonical Portal docs;
- README explicitly preserves PAPER-only / fail-closed LIVE authority;
- CODEOWNERS contains an explicit `/ai_platform/portal/` ownership umbrella plus current sensitive-path overrides, so new Portal roots never silently fall back to repository-wide `*`;
- explicit sensitive coverage includes current control-plane, execution, execution-submission, bot-operations, exchange-connections, signal-control, identity, security, credentials, database, risk, Portal deploy, contracts, web and Synology deployment roots;
- the CI guard validates required patterns, owner fields, wildcard ordering and the effective owner for representative paths rather than token presence only;
- exact-final-head required CI and documentation build pass;
- independent review has zero open material findings before merge.

## Context checkpoint

```yaml
checkpoint_version: 1
updated_at: 2026-08-11T09:54:00Z
head: 12c1b087c841d7fd857dba0a53a5381058a5bc00
branch: docs/portal-repository-truth-1468
pr: 1469
status: validating
invocation_started_at: 2026-08-11T08:57:00Z
last_progress_at: 2026-08-11T09:54:00Z
ci_checks_for_current_head: 0
unchanged_state_checks: 0
identical_failure_retries: 0
repair_cycles_for_current_gate: 3
context_reconstruction_attempts: 0
stall_warnings: 0
context_routes:
  - Portal repository truth
  - CI governance
owned_paths:
  - ai_platform/portal/README.md
  - .github/CODEOWNERS
  - tests/ci/test_portal_repository_truth.py
  - docs/agents/tasks/active/FTAI-20260811-portal-repository-truth-1468.md
proven:
  - develop contains a living exact-head Portal completeness ledger and implemented Portal surfaces that made the old README false.
  - Codex review identified omitted explicit ownership for execution_submission, bot_operations, deploy, exchange_connections and signal_control; each root was verified against live repository contents before repair.
  - all identified roots are now present in CODEOWNERS and REQUIRED_CODEOWNER_PATTERNS, and their material review threads are resolved.
  - `/ai_platform/portal/` is an explicit ownership umbrella, preventing current or future Portal roots from depending only on the repository-wide wildcard while preserving more-specific override capability.
  - final review identified that token-presence-only validation could miss owner removal or rule-order override; the guard now parses full rules, validates expected owners, requires the repository wildcard to precede the Portal rules, and checks effective ownership for representative paths.
  - the branch was synchronized with develop@6577ae896ed5910f82f9e736fe4a007b6dc10e6e before final repairs.
  - PAPER remains the only currently authorized operational mode and LIVE remains unreachable/fail-closed.
derived:
  - documentation truth must defer implementation completeness to exact-head evidence rather than package presence.
  - the Portal-wide umbrella plus effective-rule validation removes both recurring root omission and silent rule-order/owner regression classes covered by Issue 1468.
unknown:
  - terminal exact-head CI result and fresh post-remediation Codex review disposition for the final PR head.
conflicts: []
first_failure:
  marker: CODEOWNERS regression guard validated pattern tokens but not effective owners/order
  evidence: Codex P2 review thread PRRT_kwDOTdDTU86YLkds on exact head e892a89ffa5bfa9bc59b6a0293b1c454b5425e95
rejected_hypotheses:
  - treat stale README as harmless because architecture registry is canonical; rejected because root AGENTS routes Portal workers through this README.
  - rely on generic repository-wide CODEOWNERS fallback for Portal roots; rejected because that does not preserve an explicit Portal review boundary when ownership evolves.
  - validate required CODEOWNERS patterns by first token only; rejected because owner removal or later wildcard override can preserve tokens while changing effective ownership.
changed_paths:
  - ai_platform/portal/README.md
  - .github/CODEOWNERS
  - tests/ci/test_portal_repository_truth.py
  - docs/agents/tasks/active/FTAI-20260811-portal-repository-truth-1468.md
validation:
  - command: exact file/state inspection on develop
    result: PASS
    evidence: verified stale README, living ledger and historical CODEOWNERS mismatch before mutation
  - command: repository inspection of every review-identified sensitive root
    result: PASS
    evidence: reviewed roots exist and contain execution, credential, authentication or deployment-sensitive surfaces
  - command: independent Codex reviews before final repair
    result: FAIL
    evidence: material P2 findings identified incomplete explicit ownership and insufficient effective-rule validation; targeted repairs are now present
  - command: review-thread reconciliation before final review
    result: PASS
    evidence: prior material root-coverage P2 threads were replied to and resolved only after verified repair
  - command: runtime/browser product E2E
    result: NOT_APPLICABLE
    evidence: documentation and network-free CI-governance repair only
blockers: []
next_action: Reply to and resolve the effective-ownership P2, request one fresh independent exact-head review and collect exact-head required CI; because the repair-cycle budget is now exhausted, any further material finding must move to a fresh isolation task rather than another same-gate repair loop.
```

## Recovery checkpoint

```yaml
recovery:
  policy_version: 1
  generation: 5
  session_id: portal-truth-20260811-1142
  session_started_at: 2026-08-11T09:42:00Z
  checkpointed_at: 2026-08-11T09:54:00Z
  last_progress_at: 2026-08-11T09:54:00Z
  phase: terminal_validation_after_effective_ownership_repair
  exact_head: 12c1b087c841d7fd857dba0a53a5381058a5bc00
  pull_request: 1469
  active_operation: final independent audit and exact-head CI
  external_run_ids: []
  operation_started_at: 2026-08-11T09:54:00Z
  wait_deadline_at: null
  check_generation: effective-codeowners-validation
  checks_used: 0
  status: active
  safe_to_resume: true
  resume_condition: current exact head remains unchanged or is only advanced by this checkpoint record
  next_action: Reply to and resolve the effective-ownership P2, request one fresh independent exact-head review and collect exact-head required CI; because the repair-cycle budget is now exhausted, any further material finding must move to a fresh isolation task rather than another same-gate repair loop.
```

## Safety boundary

Documentation/CI-governance only. No deployment, protected environment, private exchange credentials, real order, withdrawal, model/strategy promotion or LIVE/live-capital authority is introduced.
