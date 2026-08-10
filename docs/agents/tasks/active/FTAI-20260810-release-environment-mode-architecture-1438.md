# FTAI-20260810 Release / Environment / Bot Mode Architecture 1438

```yaml
task_id: FTAI-20260810-release-environment-mode-architecture-1438
programme_id: FTAI-PROGRAM-AI-TRADING-PORTAL
repository: blakinio/freqtrade
project_lane: quant-platform-architecture
task_kind: documentation
phase: validate
status: validating
priority: high
prompting_standard_version: 2.1
execution_policy_version: 2
execution_mode: github_only
run_scope: single_task
continuation_policy: stop_at_task_boundary
task_completion_policy: finalize_archive_and_continue
user_communication: terminal_only
base_branch: develop
base_head: 978621fb358885dbf3c85d1bf837af9270678241
branch: docs/adr-021-release-environment-mode-1438
pull_request: 1439
issue: 1438
implementation_authorized: documentation_and_governance_only
live_capital_authorized: false
protected_production_deployment_authorized: false
owned_paths:
  - ARCHITECTURE_REGISTRY.yaml
  - AGENTS.md
  - docs/agents/BRANCH_POLICY.md
  - docs/agents/evals/BRANCH_RELEASE_ENVIRONMENT_POLICY_V1.md
  - docs/ai_platform/portal/ARCHITECTURE_DECISIONS.md
  - docs/ai_platform/portal/RELEASE_ENVIRONMENT_AND_BOT_MODE_ARCHITECTURE.md
  - docs/agents/tasks/active/FTAI-20260810-release-environment-mode-architecture-1438.md
  - docs/agents/tasks/archive/FTAI-20260810-release-environment-mode-architecture-1438.md
```

## Objective

Record the owner's 2026-08-10 acceptance of a two-branch release/integration architecture and make deployment environment, bot operating mode and release channel explicit orthogonal dimensions without changing runtime behavior or deploying anything.

## Accepted architecture scope

- Deployment environment is `dev | staging | production`.
- Bot operating mode is `SHADOW | PAPER | LIVE` and remains immutable generation material; production does not imply LIVE.
- Release channel is `candidate | stable`.
- `develop` remains the integration/upstream-sync branch.
- `main` becomes the release branch only through the staged repository migration defined by ADR-021.
- Staging/production deploy immutable artifact identities rather than moving branch tips.
- Production consumes stable artifacts after protected authorization; branch advancement alone cannot deploy production.
- Prefer build-once/promote-the-same-digest.
- Staging and production state/secrets/credentials/approval authority remain isolated.
- Historical evidence is preserved; new terminology names environment, release channel and bot mode separately.

## Acceptance inventory

- [x] Owner decision captured in Issue #1438.
- [x] Dedicated architecture branch created from exact `develop@978621fb358885dbf3c85d1bf837af9270678241`.
- [x] Detailed release/environment/mode target architecture created.
- [x] ADR-021 appended to the accepted decision log.
- [x] `ARCHITECTURE_REGISTRY.yaml` indexes ADR-021 and the detailed architecture document.
- [x] Temporary single-trunk governance is superseded in `docs/agents/BRANCH_POLICY.md`.
- [x] Root `AGENTS.md` routes ordinary integration and release-promotion PRs according to ADR-021 without pretending `main` already exists.
- [x] Prompt/governance regression matrix records candidate, baseline and rollback contract.
- [x] Fresh PR diff audit confirms documentation/governance-only scope, preserves LIVE fail-closed authority and separates branch/release/environment/mode semantics.
- [ ] Applicable exact-head CI passes.
- [ ] PR merges through repository rules without bypass.
- [x] Physical `main` migration remains a separately evidenced post-merge operational consequence rather than being falsely claimed complete by documentation.

## Fresh diff audit

PR #1439 contains only seven architecture/governance/task/eval files. No `ai_platform/**` runtime source, `freqtrade/**`, deployment workflow, secret, credential, runtime configuration or protected-target file is changed.

No material authority expansion was found: production environment and stable release remain explicitly insufficient for LIVE; deployment remains protected and artifact-pinned; physical `main` creation/default-branch migration is deferred until post-merge protection/CI prerequisites are proven.

One formatting follow-up remains before terminal validation: ensure final newline hygiene on newly/updated architecture Markdown before relying on exact-head CI.

## Safety boundary

Documentation/governance only. No product/runtime code, deployment, protected-host mutation, secret or exchange credential activation, model promotion, PAPER/LIVE activation, real orders, withdrawals or live capital are authorized.

## Context checkpoint

```yaml
checkpoint_version: 2
updated_at: 2026-08-10T14:22:00+02:00
status: validating
phase: exact_head_validation
base_head: 978621fb358885dbf3c85d1bf837af9270678241
issue: 1438
branch: docs/adr-021-release-environment-mode-1438
pull_request: 1439
safe_to_resume: true
resume_condition: continue only on exact PR #1439 state or if develop advances on owned architecture/governance paths
next_action: repair final newline hygiene, then inspect exact-head CI and mergeability without bypass
```
