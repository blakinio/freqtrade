---
task_id: FTAI-20260818-synology-runtime-github-build-plane-1604
repository: blakinio/freqtrade
issue: 1604
branch: arch/1604-synology-runtime-github-build-plane
status: validating
execution_mode: github_only
trusted_base: 6510077ea2e7a63c0d489f94391f461a3cab4ac1
pr: 1611
---

# Synology persistent runtime + GitHub-hosted build/disposable plane

## Objective

Record and reconcile the owner's 2026-08-18 decision that the current private Developer Quant Platform keeps persistent Portal/bot/application runtime on Synology while GitHub-hosted Actions remains the default for stateless/disposable CI, test, scan, build, GHCR publication and bounded workflow jobs.

## Authority and scope

- Issue #1604 records the owner decision.
- ADR-023 remains current product authority.
- ADR-025 is the proposed current runtime/CI-placement overlay and supersedes only ADR-024's separate-dedicated-Linux current target.
- PR #1609 hosted build-plane work is retained.
- Persistent application containers remain on Synology; GitHub-hosted runners are not a 24/7 application host.
- `deploy/runtime/**` remains optional future portability reference only.
- No runtime deployment, Synology mutation, runner registration/removal, secret change, model activation or capital authority is in this task.

## Risk

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

## Owned paths

- `AGENTS.md`
- `ARCHITECTURE_REGISTRY.yaml`
- `deploy/runtime/README.md`
- `docs/ai_platform/portal/ADR-024_DEDICATED_LINUX_RUNTIME.md`
- `docs/ai_platform/portal/ADR-025_SYNOLOGY_PERSISTENT_RUNTIME_GITHUB_BUILD_PLANE.md`
- `docs/ai_platform/portal/ARCHITECTURE_DECISIONS.md`
- `docs/ai_platform/portal/DEVELOPER_QUANT_PORTAL_ARCHITECTURE.md`
- `docs/agents/tasks/active/FTAI-20260818-synology-runtime-github-build-plane-1604.md`

## Acceptance

- current architecture no longer requires provisioning or physical cutover to a separate dedicated Linux runtime host;
- Synology is canonical persistent runtime for Portal/bots/stateful long-lived services;
- GitHub-hosted Actions is canonical default for compatible stateless/disposable CI/build/test/scan/jobs;
- persistent containers are explicitly distinguished from short-lived workflow containers;
- Synology self-hosted runner target is narrow/deploy-only or disabled;
- ADR-024 remains truthful historical evidence and PR #1609 build-plane work remains valid;
- exact-head relevant CI and selected governance gates pass with no unresolved material finding.

## Context checkpoint

```yaml
checkpoint_version: 1
updated_at: 2026-08-18T17:14:00+02:00
head: 2268d898bd85925bf5712a65f1e80821d9b2a31b
branch: arch/1604-synology-runtime-github-build-plane
pr: 1611
status: validating
context_routes:
  - Issue #1604 owner runtime-topology decision
  - ADR-023 current Developer Quant product authority
  - ADR-024 historical dedicated-Linux runtime decision
  - ADR-025 current Synology-runtime/GitHub-build proposal
  - PR #1609 hosted build-plane implementation evidence
  - PR #1610 compatible Liquid20 GHCR repair in progress
owned_paths:
  - AGENTS.md
  - ARCHITECTURE_REGISTRY.yaml
  - deploy/runtime/README.md
  - docs/ai_platform/portal/ADR-024_DEDICATED_LINUX_RUNTIME.md
  - docs/ai_platform/portal/ADR-025_SYNOLOGY_PERSISTENT_RUNTIME_GITHUB_BUILD_PLANE.md
  - docs/ai_platform/portal/ARCHITECTURE_DECISIONS.md
  - docs/ai_platform/portal/DEVELOPER_QUANT_PORTAL_ARCHITECTURE.md
  - docs/agents/tasks/active/FTAI-20260818-synology-runtime-github-build-plane-1604.md
proven:
  - develop trusted base is 6510077ea2e7a63c0d489f94391f461a3cab4ac1
  - PR #1609 already moved portable Portal WickHunter and Liquid20 build publication toward GitHub-hosted runners
  - Issue #1604 now records that a separate dedicated Linux host is not current target authority
  - PR #1611 was opened from the exact trusted base with the intended architecture-only scope
  - initial PR diff inspection found only the expected architecture governance paths before this task record was added
derived:
  - PR #1610 remains implementation-compatible because it builds on GitHub-hosted Linux and deploys an immutable image to Synology
unknown:
  - exact-head CI results after the final task checkpoint and registry update
  - independent audit disposition on the final PR head
conflicts: []
first_failure:
  marker: none-current
  evidence: no material diff inconsistency found in initial exact PR patch review
rejected_hypotheses:
  - use GitHub-hosted Actions as a 24/7 Portal or bot runtime
  - provision a separate Linux host solely to satisfy superseded ADR-024
  - revert the already merged GitHub-hosted build-plane work from PR #1609
changed_paths:
  - AGENTS.md
  - ARCHITECTURE_REGISTRY.yaml
  - deploy/runtime/README.md
  - docs/ai_platform/portal/ADR-024_DEDICATED_LINUX_RUNTIME.md
  - docs/ai_platform/portal/ADR-025_SYNOLOGY_PERSISTENT_RUNTIME_GITHUB_BUILD_PLANE.md
  - docs/ai_platform/portal/ARCHITECTURE_DECISIONS.md
  - docs/ai_platform/portal/DEVELOPER_QUANT_PORTAL_ARCHITECTURE.md
  - docs/agents/tasks/active/FTAI-20260818-synology-runtime-github-build-plane-1604.md
validation:
  - command: compare develop to architecture branch and inspect PR #1611 diff
    result: PASS
    evidence: exact trusted base with only intended architecture governance changes before checkpoint record
  - command: exact-head repository CI and selected governance gates
    result: NOT_RUN
    evidence: final checkpoint and registry reconciliation must land before exact-head CI is authoritative
blockers: []
next_action: Update the architecture registry task pointer and PR inventory, then validate the exact final PR head and remediate only concrete CI or audit findings.
```
