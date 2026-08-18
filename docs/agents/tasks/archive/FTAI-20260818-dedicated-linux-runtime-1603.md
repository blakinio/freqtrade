---
task_id: FTAI-20260818-dedicated-linux-runtime-1603
repository: blakinio/freqtrade
issue: 1603
status: completed_historical
execution_mode: github_only
trusted_base: 2389e5e70161325c7f39b8ecd9da766f078bcf3e
implementation_pr: 1606
implementation_final_head: ecf6bcc6b75ceeeae307a4df908521e661c5290e
implementation_merge: aabed2a54676edacdc9319c93dc96788e9eb3a8e
follow_up_issue: 1604
---

# Dedicated Linux runtime architecture migration — terminal record

## Terminal disposition

`COMPLETE — PHASE A ARCHITECTURE + PORTABLE RUNTIME CONTRACT MERGED`

Issue #1603 was completed by PR #1606 and squash merge `aabed2a54676edacdc9319c93dc96788e9eb3a8e` into `develop`.

This terminal record does **not** claim a physical runtime cutover. The exact dedicated Linux host identity, address, architecture, access method and Synology mount/synchronization protocol remain unverified. Physical/service portability and cutover are owned by Issue #1604.

## Proven delivered state

- ADR-024 is accepted and merged as the binding runtime/deployment topology overlay.
- ADR-023 remains the current Developer Quant product authority.
- Target topology is `GitHub/GitHub-hosted CI/build/orchestration -> dedicated Linux persistent runtime -> Synology durable storage/evidence/backup`.
- Current target runtime vocabulary is `LOCAL | DEDICATED_LINUX`.
- Current storage-provider vocabulary is `LOCAL | SYNOLOGY`.
- `deploy/runtime/**` provides a generic host/storage contract with no Synology-specific `/volume1` target assumption.
- The host contract restricts a retained self-hosted GitHub runner to `disabled | deploy-only` and requires application container-engine socket exposure to remain disabled.
- Existing `deploy/synology/**` and running Synology-hosted application services were preserved as transitional current implementation; this task made no Synology/runtime/runner/external-system mutation.
- Issue #1561 was reconciled after ADR-024 merged: WickHunter's target persistent runtime is now `DEDICATED_LINUX`, while current Synology compute remains transitional and Synology remains the durable storage/evidence/backup provider.
- Issue #1603 closed automatically from PR #1606.

## Risk closeout

```yaml
risk:
  persistent_data: false
  research_integrity: false
  model_activation: false
  auth_or_secrets: false
  shared_synology_mutation: false
  deployment: false
  user_workflow_change: false
  destructive_operation: false
  real_capital: false
  governance_or_ci: true
risk_gates:
  - policy_regression
  - trusted_base_self_validation
  - independent_audit
```

The task remained repository-only. It introduced no physical deployment, persistent-data mutation, secret/environment change, model activation or real-capital capability.

## Validation evidence

Exact implementation PR head: `ecf6bcc6b75ceeeae307a4df908521e661c5290e`.

- Freqtrade CI `32132147873`: **SUCCESS** on exact final head before readiness.
- Risk-aware component CI `32132148209`: **SUCCESS** on exact final head; includes Portal completeness audit and Universal Portal E2E.
- CodeQL `32132147922`: **SUCCESS**.
- zizmor `32132147878`: **SUCCESS**.
- Ready-for-review Freqtrade CI `32134005087`: **SUCCESS** on the same exact final head, including required `CI Gate`.
- Ready-for-review Risk-aware component CI `32134005308`: **SUCCESS** on the same exact final head.
- Fresh independent final-diff audit recorded in PR comment `5327777102`: **PASS**, no unresolved material/P0/P1 finding.
- Final implementation diff: exactly 10 expected paths; no `.github/workflows/**` or `deploy/synology/**` changes.
- `develop` remained at trusted base until implementation merge; merge commit is `aabed2a54676edacdc9319c93dc96788e9eb3a8e`.

## CI remediation history

Initial validation surfaced real repository-contract failures rather than being bypassed:

- missing ADR-024 entry in the binding decision log;
- invalid PR-title routing;
- Ruff complexity and EOF normalization findings;
- ADR-023 diagnostic-authority markers removed from the architecture registry, causing the Portal completeness audit to select an obsolete legacy gate.

All were corrected in repository content. No workflow or audit gate was weakened to obtain green CI.

## Source branch closeout

Implementation PR #1606 is merged. Source branch deletion is not claimed here unless independently proven by repository branch state or lifecycle automation.

## Remaining work

```yaml
unknown:
  - physical dedicated Linux host identity, address, architecture and access method
  - exact Synology mount or synchronization protocol for that host
  - physical cutover date and exact service-by-service target state
blockers:
  - physical migration requires a verified dedicated Linux target and task-specific deployment/persistence authority
next_action: none
```

Phase A has no continuation action. Issue #1604 independently owns the next runtime-portability/cutover programme and must reconstruct current live state before mutating any runtime or storage target.
