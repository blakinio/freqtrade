---
task_id: FTAI-20260816-github-build-plane-1561
status: validating
repository: blakinio/freqtrade
lane: freqtrade-portal
related_issue: 1561
branch: infra/github-build-plane-1561
base_head: ff4979f5c14b0d584d11eaff4260a65423abf3aa
owner: chatgpt
task_kind: infrastructure
phase: validate
prompting_standard_version: 2.1
execution_policy_version: 2
context_pressure: medium
decomposition_decision: phased
execution_mode: chat
run_scope: single_task
continuation_policy: stop_at_task_boundary
task_completion_policy: finalize_archive_and_continue
user_communication: low_noise
feature_scope:
  type: infrastructure
  user_facing: false
  backend_required: false
  frontend_required: false
  integration_required: true
  e2e_required: true
  completion_claim: internal_only
next_action: Validate the final PR #1569 exact head, merge only when required gates are green, then prove the canonical Liquid20 GitHub-to-GHCR-to-Synology deployment on develop before closing the task.
---

# GitHub build-plane migration for Developer Quant Portal

## Objective

Move portable Portal, WickHunter and current Liquid20 build/package/scan work off the persistent Synology runner while keeping persistent Portal/bot/data runtime, durable state and target-specific deployment verification on Synology.

## Authority and boundaries

- ADR-023 and Issue #1561 remain product authority.
- Current runtime locations remain `LOCAL | SYNOLOGY`; GitHub Actions is CI/build orchestration, not a persistent bot runtime.
- Real-money exchange execution, private order credentials, withdrawals and capital authority remain forbidden.
- Do not weaken exact-image, restart, persistence, health or real API/browser acceptance.
- Do not touch unrelated Synology/OteryN resources.

## Owned paths

- `.github/workflows/portal-oidc-public-deploy.yml`
- `.github/workflows/ai-platform-wickhunter-wh09-production-research-runtime-deploy.yml`
- `.github/workflows/liquidations-live-synology.yml`
- `.github/workflows/packages-cleanup.yml`
- `deploy/synology/liquid20/deploy-live.sh`
- `tests/ci/test_github_build_plane.py`
- this task record

## Acceptance

- [x] Portal exact images are built and scanned on a GitHub-hosted Linux runner, not `freqtrade-staging`.
- [x] Portal deploy job on `freqtrade-staging` only materializes already-built exact images and performs Synology-specific deploy/health/E2E operations.
- [x] WickHunter runtime image is built on a GitHub-hosted Linux runner and the Synology job pulls/verifies that exact image before host-specific deployment.
- [x] Active Liquid20 collector image is built on a GitHub-hosted Linux runner and `freqtrade-staging` only pulls/verifies/deploys it.
- [x] Portal/WickHunter image handoff is attributable to exact source SHA/run identity and fails closed on image-ID/revision mismatch.
- [x] Liquid20 prebuilt-image handoff is immutable, exact-SHA verified and cannot silently fall back to a Synology build in GitHub Actions.
- [x] Existing no-live-capital/no-trading-credential invariants remain unchanged in the edited Portal/WickHunter paths.
- [x] Existing Liquid20 candidate, rollback, persistence, health and public-data-only invariants remain in the deploy path and have focused regression coverage.
- [x] Focused CI regression coverage includes Portal, WickHunter and Liquid20 hosted-build/Synology-deploy separation plus `bash -n` for the changed Liquid20 deploy script.
- [x] New build-plane GHCR package retention is allowlisted to four exact fork packages and retains the latest 10 versions without a broad prune or new recurring trigger.
- [ ] Exact-head required CI is green and review findings are resolved before merge.
- [ ] Post-merge canonical Liquid20 deployment proves the real GitHub-hosted build -> GHCR immutable image -> Synology pull/deploy path.

## Context checkpoint

```yaml
checkpoint_version: 1
updated_at: 2026-08-16T10:06:00Z
head: 353203c71717da3fecb8c2f522e934b198a833a5
head_note: This is the exact implementation head immediately before this checkpoint-only task-record commit.
branch: infra/github-build-plane-1561
pr: 1569
status: validating
context_routes:
  - Issue #1561 Developer Quant MVP
  - PR #1569 GitHub build-plane migration
  - ADR-023 Developer Quant Portal
  - Portal exact-image supply-chain workflow
  - WickHunter persistent research runtime
  - Liquidations Live Synology canonical collector deployment
  - reusable fork package cleanup policy
  - dedicated freqtrade-staging Synology runner
owned_paths:
  - .github/workflows/portal-oidc-public-deploy.yml
  - .github/workflows/ai-platform-wickhunter-wh09-production-research-runtime-deploy.yml
  - .github/workflows/liquidations-live-synology.yml
  - .github/workflows/packages-cleanup.yml
  - deploy/synology/liquid20/deploy-live.sh
  - tests/ci/test_github_build_plane.py
  - docs/agents/tasks/active/FTAI-20260816-github-build-plane-1561.md
proven:
  - develop exact base at PR creation is ff4979f5c14b0d584d11eaff4260a65423abf3aa.
  - PR #1569 targets develop from infra/github-build-plane-1561 and remained mergeable before this checkpoint.
  - Portal Web CI and AI Platform CI already run on GitHub-hosted ubuntu-24.04.
  - Portal deployment now separates hosted build/scan/publish from Synology pull/deploy/target verification.
  - WH09 deployment now separates hosted image build/publish from Synology pull/host validation/runtime verification.
  - workflow registry classifies .github/workflows/liquidations-live-synology.yml as canonical, active and high-risk.
  - Liquid20 now builds and publishes ghcr.io/blakinio/liquid20-collector on ubuntu-24.04 and the Synology deploy job only pulls/verifies that exact digest before invoking deploy-live.sh.
  - deploy-live.sh requires an immutable approved Liquid20 GHCR digest under GitHub Actions, verifies OCI revision equals GITHUB_SHA, and refuses a Synology build fallback; manual non-Actions execution retains the explicit local build fallback.
  - historical real workflow run 31326580829 job 93277819212 proves freqtrade-synology-staging is Linux X64, matching the hosted linux/amd64 image path; the new deploy path also fails closed on a non-X64 runner.
  - the package retention workflow is fork-only for exactly freqtrade-portal-control-plane, freqtrade-portal-web, wickhunter-production-research-runtime and liquid20-collector; it keeps 10 versions and adds no schedule.
  - PR review inventory before this checkpoint contained zero submitted reviews and zero unresolved review threads; the automated Codex review bot only reported exhausted quota and supplied no review finding.
  - owner-funded Codex/OpenAI quota was not invoked for this task.
derived:
  - current Portal/WickHunter/Liquid20 deployment architecture now uses GitHub as build plane and Synology as persistent runtime/deployment plane while preserving ADR-023 runtime semantics.
  - historical and unrelated Synology workflows were intentionally not mass-rewritten because their current ownership/necessity was not proven by #1561.
unknown:
  - final exact-head required CI after this checkpoint commit.
  - post-merge Liquid20 GHCR package publication/pull permissions and target deployment result; these require the canonical develop push workflow to run.
  - automatic invocation of fork package cleanup is not introduced in this change; the reusable allowlisted retention path is available without adding a new recurring destructive trigger.
conflicts: []
first_failure:
  marker: SYNLOGY_BUILD_PLANE_COUPLING
  evidence: base Portal, WH09 and active Liquid20 deploy paths performed portable image build/scan work on freqtrade-staging; PR #1569 moves those operations to hosted Linux runners.
rejected_hypotheses:
  - GitHub-hosted runners should host persistent bots or collectors; rejected because ADR-023 uses SYNOLOGY for persistent runtime and Actions jobs are ephemeral.
  - every historical workflow mentioning Synology should be rewritten in one PR; rejected because current-path ownership/need is not proven for all historical diagnostics/cutovers.
  - broad GHCR pruning is acceptable; rejected in favor of an exact four-package allowlist and a 10-version retention floor.
changed_paths:
  - .github/workflows/portal-oidc-public-deploy.yml
  - .github/workflows/ai-platform-wickhunter-wh09-production-research-runtime-deploy.yml
  - .github/workflows/liquidations-live-synology.yml
  - .github/workflows/packages-cleanup.yml
  - deploy/synology/liquid20/deploy-live.sh
  - tests/ci/test_github_build_plane.py
  - docs/agents/tasks/active/FTAI-20260816-github-build-plane-1561.md
validation:
  - command: repository/PR overlap preflight
    result: PASS
    evidence: no open PR matched freqtrade-staging or Synology migration scope at task start; the branch was created from exact develop head.
  - command: initial PR #1569 Freqtrade CI lightweight required gate
    result: FAIL_REPAIRED
    evidence: run 31939534137 job 95146602830 found Ruff E501 only in the new regression test; the exact formatting failure was repaired.
  - command: subsequent Freqtrade CI lightweight required gate on 590b5a751af4d5ca7879e09f52348496d12ea920
    result: PASS
    evidence: run 31940162116 job 95148093645; tests/ci reported 119 passed and 1 skipped and validate_workflows.py reported workflow syntax, routing, registry lifecycle, local references and pins valid.
  - command: pre-commit on 590b5a751af4d5ca7879e09f52348496d12ea920
    result: PASS
    evidence: run 31940162116 job 95148093692.
  - command: CodeQL and zizmor on 590b5a751af4d5ca7879e09f52348496d12ea920
    result: PASS
    evidence: CodeQL run 31940162102 and zizmor run 31940162094 completed success.
  - command: current code-head lightweight required gate on 353203c71717da3fecb8c2f522e934b198a833a5
    result: PASS
    evidence: run 31940633100 job 95149178307 completed success, including workflow syntax/routing/action-security validation after the package-retention change.
  - command: current code-head zizmor on 353203c71717da3fecb8c2f522e934b198a833a5
    result: PASS
    evidence: run 31940633078 completed success.
  - command: direct PR diff/review audit
    result: PASS_WITH_OPEN_FINAL_GATES
    evidence: exact seven-file changed-path inventory reviewed; no submitted review or unresolved thread; no material authority/rollback weakening found. Final exact-head CI and real post-merge Liquid20 E2E remain required.
blockers: []
next_action: Validate the final PR #1569 exact head, merge only when required gates are green, then prove the canonical Liquid20 GitHub-to-GHCR-to-Synology deployment on develop before closing the task.
```
