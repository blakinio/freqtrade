# FTAI-20260810 — PAPER G0 Implementation Status Authority

```yaml
task_id: FTAI-20260810-paper-g0-status-authority
programme_id: FTAI-PAPER-PLATFORM
repository: blakinio/freqtrade
project_lane: freqtrade-portal
task_kind: ci_governance
phase: validation
status: validating
priority: high
execution_mode: github_only
run_scope: autonomous_program
continuation_policy: continue_until_real_stop
base_branch: develop
trusted_base_sha: 5a19ae32f1f71b112130ea66cb8d56d9a3e44049
delivery_branch: feat/paper-g0-status-authority-20260810
delivery_pr: 1449
paper_gate: G0
live_capital_authorized: false
protected_production_deployment_authorized: false
```

## Objective

Implement G0 work item 5 from `PAPER_PLATFORM_IMPLEMENTATION_PLAN.md`: establish one explicit, CI-enforced authority hierarchy for architecture/document truth, exact-head implementation inventory, legacy/roll-up status views and GitHub work ownership. Reuse the living exact-head ledger delivered by PR #1150; do not reopen completed #1101 or rewrite its historical snapshot as current truth.

## Acceptance inventory

- `S1`: `ARCHITECTURE_REGISTRY.yaml` is explicitly architecture/document authority, not implementation-completeness authority.
- `S2`: `tools/portal_audit/ledger/index.json` is the sole current exact-head implementation inventory and keeps `mode: living_exact_head_gate`.
- `S3`: `FEATURE_COMPLETENESS_LEDGER.json`/`.md` are classified as the historical #1101 snapshot at their recorded SHA; the legacy embedded `status_authority: true` flag is compatibility metadata, not current authority.
- `S4`: `UI_DELIVERY_STATUS.md` and programme/roadmap status views are classified as validated roll-up, work-ownership roll-up, dependency plan or historical evidence rather than standalone implementation truth.
- `S5`: GitHub Issues are work ownership/acceptance units, never standalone implementation truth.
- `S6`: one machine-readable status-authority contract is referenced from the living ledger package.
- `S7`: deterministic network-free CI rejects missing authority paths, mismatched living-ledger schema/mode, unclassified legacy status surfaces, a historical snapshot SHA mismatch or an implicit second current implementation authority.
- `S8`: existing #1101 historical compatibility markers remain intact; historical evidence is not rewritten.
- `S9`: runtime/browser E2E is `NOT_APPLICABLE` because this package changes status/governance truth only.
- `S10`: fresh independent review, exact-head CI and zero unresolved review threads are required before merge.

## Context checkpoint

```yaml
checkpoint_version: 1
updated_at: 2026-08-10T19:49:00Z
head: 0c392ddd6d1c775f435712840c80795815e907e7
branch: feat/paper-g0-status-authority-20260810
pr: 1449
status: validating
ci_checks_for_current_head: 0
unchanged_state_checks: 0
review_checks_for_current_head: 0
context_routes:
  - G0 status authority
  - living exact-head portal audit ledger
  - legacy feature-completeness snapshot
owned_paths:
  - docs/ai_platform/portal/IMPLEMENTATION_STATUS_AUTHORITY.md
  - docs/ai_platform/portal/UI_DELIVERY_STATUS.md
  - tools/portal_audit/ledger/index.json
  - tools/portal_audit/ledger/status_authority.json
  - tests/ci/test_portal_status_authority.py
  - docs/agents/tasks/active/FTAI-20260810-paper-g0-status-authority.md
proven:
  - G0 explicitly requires implementation-status authority and CI-enforced roll-up rules.
  - PR 1150 already delivered tools/portal_audit/ledger/index.json as a living exact-head gate.
  - The older FEATURE_COMPLETENESS_LEDGER snapshot remains unchanged at b39b29c3e831ba491aa3376e5de86a8c09e2b537 with its legacy status_authority true field.
  - The living index now points to tools/portal_audit/ledger/status_authority.json.
  - The authority sidecar classifies architecture, living implementation truth, GitHub Issue ownership and every legacy #1101 status surface separately.
  - UI_DELIVERY_STATUS retains its legacy marker for #1101 compatibility and adds an explicit living-ledger current-authority marker.
  - A network-free tests/ci guard checks authority roles, sidecar linkage, legacy path classification, legacy snapshot SHA and human safety/supersession markers.
  - PR 1449 is the single delivery PR for this bounded G0 package and contains six declared changed paths.
derived:
  - The candidate promotes the newer living exact-head evidence model without falsifying the older completed #1101 snapshot.
  - No runtime, browser, deployment or trading behavior is modified.
unknown:
  - Fresh independent review findings on the successor exact head created by this checkpoint.
  - Exact-head CI result on the successor exact head.
conflicts:
  - none found with PR 1447 or 1448 changed paths
first_failure:
  marker: legacy and living ledgers both presented current-authority semantics without an explicit supersession contract
  evidence: FEATURE_COMPLETENESS_LEDGER.md historical text versus tools/portal_audit/ledger/index.json mode living_exact_head_gate
rejected_hypotheses:
  - Reopen Issue 1101; rejected because it is completed and this is a later G0 authority migration over PR 1150.
  - Rewrite the historical feature ledger snapshot to the current head; rejected because that would falsify historical evidence.
  - Remove the old UI authority marker; rejected because the completed #1101 validator requires it for historical compatibility.
changed_paths:
  - docs/ai_platform/portal/IMPLEMENTATION_STATUS_AUTHORITY.md
  - docs/ai_platform/portal/UI_DELIVERY_STATUS.md
  - tools/portal_audit/ledger/index.json
  - tools/portal_audit/ledger/status_authority.json
  - tests/ci/test_portal_status_authority.py
  - docs/agents/tasks/active/FTAI-20260810-paper-g0-status-authority.md
validation:
  - command: branch compare against develop@5a19ae32f1f71b112130ea66cb8d56d9a3e44049
    result: PASS
    evidence: ahead by 8, behind by 0, exactly six declared changed paths before PR-bound checkpoint successor
  - command: implementer static falsification of authority graph and compatibility markers
    result: PASS
    evidence: living ledger remains v2/living_exact_head_gate; historical snapshot remains unchanged; UI retains legacy marker and adds living marker
  - command: runtime/browser E2E
    result: NOT_APPLICABLE
    evidence: status/governance-only package; no product runtime or browser behavior changes
blockers:
  - none
next_action: Resolve PR 1449 successor exact head, request fresh Codex review and collect the first bounded exact-head CI observation; remediate only a material owned finding or prepare same-PR task archival after all gates are clear.
```
