# FTAI-20260809 Portal Runtime Isolation 1354

```yaml
task_id: FTAI-20260809-portal-runtime-isolation-1354
programme_id: FTAI-PROGRAM-AI-TRADING-PORTAL
repository: blakinio/freqtrade
project_lane: freqtrade-portal
task_kind: implementation
phase: archived
status: completed
priority: high
base_branch: develop
delivery_branch: fix/portal-runtime-isolation-1354
delivery_pr: 1464
delivery_head: 75ed5f73953e0f3db3d2696a7eb69dfe9653b620
delivery_merge_commit: 8e395638f68888f6f8068036a1fd7762d7327315
issue: 1354
related_open_issue: 1355
completed_at: 2026-08-12T07:23:10Z
live_capital_authorized: false
production_deployment_authorized: false
host_firewall_mutation_authorized: false
```

## Terminal result

Issue #1354 is completed by delivery PR #1464. The merged implementation provides the ADR-020 generation-bound isolation envelope for Portal-managed PAPER/dry-run Freqtrade runtimes:

- immutable isolation-profile and resolved-plan identity;
- digest-pinned hardened runtime image and immutable quarantine bootstrap;
- non-root execution, no-new-privileges, capability-drop-all, default seccomp and read-only root;
- hard memory/swap/PID/CPU, tmpfs, durable-state and bounded-log controls;
- Btrfs qgroup enforcement plus exact runtime-state owner/mode attestation;
- generation-scoped deny-by-default networking with explicit public market-data and DNS policy;
- staged and active canonical nftables attestation, with firewall preservation until Docker network teardown is proven;
- exact Gateway artifact/contract attestation;
- pre-release and already-running re-attestation;
- fail-closed paused-runtime reprovision semantics;
- host-controlled application readiness with a driver-owned finite subprocess deadline;
- real privileged Docker/nftables/Btrfs acceptance coverage for release, public-data access, storage, ownership, memory/swap, PID, CPU and cleanup boundaries.

No Runtime Supervisor authority from #1355 is implemented or claimed. PAPER remains the only authorized operational mode; no LIVE/live-capital authority, private exchange credentials, real-order submission, withdrawals, protected production deployment or automatic LIVE promotion was introduced.

## Final delivery evidence

Final delivery head `75ed5f73953e0f3db3d2696a7eb69dfe9653b620` was synchronized with then-current `develop@ec41d2542bff57f74cd10856b7dc22265213d991` with `behind_by=0` and a bounded 22-file runtime-isolation diff.

Exact-head validation on that unchanged head:

- Portal Runtime Isolation E2E run `31572008070`: PASS;
- Freqtrade CI run `31572007973`: PASS;
- Risk-aware component CI run `31572008247`: PASS;
- CodeQL Security Analysis run `31572007991`: PASS;
- GitHub Actions Security Analysis with zizmor run `31572008022`: PASS;
- Portal Exact-Image Supply Chain run `31572007967`: PASS;
- Portal API Mode Browser run `31572007979`: PASS;
- Portal WickHunter Browser E2E run `31572008087`: PASS;
- Pre-commit Types update run `31572007987`: correctly SKIPPED.

A fresh independent Codex closeout review was requested against exact head `75ed5f73953e0f3db3d2696a7eb69dfe9653b620` after the final two audit repairs. It reported no material P0/P1/P2 findings. All PR #1464 review threads were resolved before merge.

PR #1464 was squash-merged into `develop` as `8e395638f68888f6f8068036a1fd7762d7327315`, and Issue #1354 closed automatically with state reason `completed`.

## Final audit repairs

The last material audit findings were repaired before final validation:

1. unconditional workflow cleanup now retains the exact task-owned nftables table whenever corresponding Docker network removal fails or cannot be proven, while still failing cleanup and reporting residual state;
2. the host-controlled `freqtrade list-pairs` readiness probe now has a driver-owned 15-second deadline, with subprocess timeout mapped to bounded failed readiness rather than an indefinitely blocked lifecycle operation.

Earlier material review findings covering re-attestation, DNS policy, nftables canonicalization, immutable bootstrap, real privileged isolation E2E, Btrfs quotas/ownership, active policy, bounded logs, Gateway evidence, STARTING stop behavior, source-independent readiness and real CPU/memory/PID enforcement were also repaired and resolved before the final exact-head review.

## PR and branch hygiene

- PR #1464: merged delivery PR;
- PR #1431: historical closed-unmerged delivery attempt; must remain historical;
- PR #1486: terminal integration-only helper; no unique delivery changes remain outside the final branch history;
- temporary repair/publisher workflows were removed before final validation;
- no duplicate open delivery PR remained at merge time.

## Architecture lifecycle reconciliation

The follow-up lifecycle change for this task:

- moves this durable task record from `docs/agents/tasks/active/` to `docs/agents/tasks/archive/`;
- records #1354 / `FTAI-ARCH-RUNTIME-ISOLATION` as completed in `ARCHITECTURE_REGISTRY.yaml` with evidence PR #1464;
- removes #1354 from `open_architecture_findings`;
- intentionally preserves #1355 / `FTAI-ARCH-RUNTIME-SUPERVISOR` as an open critical finding;
- releases the active task ownership record.

## Final checkpoint

```yaml
checkpoint_version: 3
status: completed
phase: archived
completed_at: 2026-08-12T07:23:10Z
delivery_pr: 1464
delivery_head: 75ed5f73953e0f3db3d2696a7eb69dfe9653b620
delivery_merge_commit: 8e395638f68888f6f8068036a1fd7762d7327315
issue_1354_state: closed_completed
fresh_audit: pass_zero_material_findings
exact_head_ci: pass
runtime_isolation_e2e: pass
review_threads_unresolved: 0
paper_only: true
live_capital_authorized: false
open_related_findings:
  - 1355
blockers: []
next_action: none
```
