# FTAI-20260810 — PAPER G0 Implementation Status Authority

```yaml
task_id: FTAI-20260810-paper-g0-status-authority
programme_id: FTAI-PAPER-PLATFORM
repository: blakinio/freqtrade
project_lane: freqtrade-portal
task_kind: ci_governance
phase: implementation
status: implementing
priority: high
execution_mode: github_only
run_scope: autonomous_program
continuation_policy: continue_until_real_stop
base_branch: develop
trusted_base_sha: 5a19ae32f1f71b112130ea66cb8d56d9a3e44049
delivery_branch: feat/paper-g0-status-authority-20260810
paper_gate: G0
live_capital_authorized: false
protected_production_deployment_authorized: false
```

## Objective

Implement G0 work item 5 from `PAPER_PLATFORM_IMPLEMENTATION_PLAN.md`: establish one explicit, CI-enforced authority hierarchy for architecture/document truth, exact-head implementation inventory, legacy/roll-up status views and GitHub work ownership. Reuse the living exact-head ledger delivered by PR #1150; do not reopen completed #1101 or rewrite its historical snapshot as current truth.

## Acceptance inventory

- `S1`: `ARCHITECTURE_REGISTRY.yaml` is explicitly architecture/document authority, not implementation-completeness authority.
- `S2`: `tools/portal_audit/ledger/index.json` is the sole current exact-head implementation inventory and keeps `mode: living_exact_head_gate`.
- `S3`: `FEATURE_COMPLETENESS_LEDGER.json`/`.md` are classified as the historical #1101 snapshot at their recorded SHA; the legacy embedded `status_authority: true` flag is documented as compatibility metadata, not current authority.
- `S4`: `UI_DELIVERY_STATUS.md` and programme/roadmap status views are classified as validated roll-up, work-ownership roll-up, dependency plan or historical evidence rather than standalone implementation truth.
- `S5`: GitHub Issues are explicitly work ownership/acceptance units, never standalone implementation truth.
- `S6`: one machine-readable status-authority contract is referenced from the living ledger package.
- `S7`: a deterministic network-free CI test rejects missing authority paths, multiple current implementation authorities, mismatched living-ledger schema/mode, unclassified legacy authority surfaces, or a historical snapshot SHA mismatch.
- `S8`: existing legacy #1101 validator compatibility remains green; no historical evidence is silently rewritten.
- `S9`: runtime/browser E2E is `NOT_APPLICABLE` because this package changes status/governance truth only.
- `S10`: fresh independent review, exact-head CI and zero unresolved review threads are required before merge.

## Context checkpoint

```yaml
checkpoint_version: 1
updated_at: 2026-08-10T19:40:00Z
head: 5a19ae32f1f71b112130ea66cb8d56d9a3e44049
branch: feat/paper-g0-status-authority-20260810
pr: none
status: implementing
context_routes:
  - G0 status authority
  - living exact-head portal audit ledger
  - legacy feature-completeness snapshot
owned_paths:
  - docs/ai_platform/portal/IMPLEMENTATION_STATUS_AUTHORITY.md
  - docs/ai_platform/portal/FEATURE_COMPLETENESS_LEDGER.md
  - docs/ai_platform/portal/UI_DELIVERY_STATUS.md
  - tools/portal_audit/ledger/index.json
  - tools/portal_audit/ledger/status_authority.json
  - tools/agents/check_portal_completeness_ledger.py
  - tests/ci/test_portal_status_authority.py
  - docs/agents/tasks/active/FTAI-20260810-paper-g0-status-authority.md
proven:
  - G0 explicitly requires implementation-status authority and CI-enforced roll-up rules.
  - PR 1150 already delivered tools/portal_audit/ledger/index.json as a living exact-head gate.
  - The older FEATURE_COMPLETENESS_LEDGER snapshot is bound to b39b29c3e831ba491aa3376e5de86a8c09e2b537 and still carries a legacy status_authority true field.
  - UI_DELIVERY_STATUS and FEATURE_COMPLETENESS_LEDGER.md currently describe the legacy ledger as active authority.
  - Issue 1101 is closed completed and must remain historical evidence rather than be reopened.
derived:
  - G0 should promote the newer living ledger above the old snapshot without deleting or falsifying #1101 evidence.
  - A sidecar authority contract plus deterministic CI guard can make that hierarchy machine enforceable without network-dependent GitHub state.
unknown:
  - Fresh independent review findings on the final candidate.
  - Exact-head CI result on the final candidate.
conflicts:
  - none found with open PR 1447 or 1448; selected paths are disjoint from their current changed-file sets
first_failure:
  marker: legacy and living ledgers both present status-authority semantics without one explicit supersession contract
  evidence: FEATURE_COMPLETENESS_LEDGER.md says its JSON is the only active authority while tools/portal_audit/ledger/index.json declares living_exact_head_gate
rejected_hypotheses:
  - Reopen Issue 1101; rejected because it is completed and the gap is a new G0 authority migration over later PR 1150 evidence.
  - Rewrite the historical feature ledger snapshot as if generated on the current head; rejected because that would falsify historical evidence.
changed_paths:
  - docs/agents/tasks/active/FTAI-20260810-paper-g0-status-authority.md
validation:
  - command: runtime/browser E2E
    result: NOT_APPLICABLE
    evidence: status/governance-only package; no product runtime or browser behavior changes
blockers:
  - none
next_action: Add the machine-readable authority contract and CI guard, update the two human status surfaces to declare the living ledger as current authority while preserving the legacy compatibility marker, then open a bounded PR for fresh review and exact-head validation.
```
