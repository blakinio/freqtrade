---
task_id: FTAI-20260723-portal-p11-cloudflare-staging
status: blocked
branch: develop
base_branch: develop
created: 2026-07-23
updated: 2026-07-23
related_pr: "#180"
owned_paths:
  - ai_platform/portal/deploy/cloudflare/
  - tests/ai_platform/portal/deploy/cloudflare/
  - .github/workflows/portal-staging-policy.yml
  - .github/workflows/portal-staging-external-e2e.yml
  - docs/ai_platform/portal/PRODUCTION_LIKE_STAGING.md
  - docs/ai_platform/portal/runbooks/STAGING_SECRET_ROTATION.md
  - docs/ai_platform/portal/runbooks/STAGING_INCIDENT_AND_KILL_SWITCH.md
  - docs/agents/tasks/FTAI-20260723-portal-p11-cloudflare-staging.md
required_reads:
  - AGENTS.md
  - docs/agents/CONTEXT_HANDOFF.md
  - docs/agents/programs/FTAI_AI_TRADING_PORTAL_PROGRAM.md
  - docs/ai_platform/portal/SECURITY_ARCHITECTURE.md
  - docs/ai_platform/portal/QUALITY_AND_AUTONOMOUS_E2E.md
  - docs/ai_platform/portal/DELIVERY_ROADMAP.md
  - docs/ai_platform/portal/AGENT_EXECUTION_PLAN.md
search_first:
  - owner-approved Cloudflare staging Tunnel, DNS, Access, WAF and origin firewall state
  - protected GitHub staging environment variables and secrets
  - Portal Staging External E2E run evidence
optional_reads:
  - external Cloudflare account configuration only after explicit owner authorization and available access
---

# AI Trading Portal P11 — Cloudflare Production-Like Staging

## Goal

Establish the repository-side fail-closed contract and validation path for production-like staging through Cloudflare edge, Access and Tunnel while keeping execution simulated and preserving private origin/Freqtrade boundaries.

## Acceptance criteria

1. A machine-readable staging policy requires Tunnel ingress and forbids public origin/Freqtrade ingress.
2. Privileged surfaces and sensitive endpoint families have explicit Access/WAF/rate-limit coverage requirements.
3. A read-only external verifier proves public portal reachability, anonymous privileged denial, staging service-identity access, direct-origin denial and direct-Freqtrade denial.
4. External verifier evidence cannot disclose configured endpoints or service-token values.
5. CI validates the static staging policy and probe behavior on every relevant PR.
6. Real external staging acceptance runs only through owner-approved protected GitHub staging variables/secrets.
7. Secret rotation and incident/kill-switch runbooks are documented.
8. No test-only security bypass, live-capital enablement or production order-submission bypass is introduced.
9. P11 is not considered fully accepted until a real external staging run passes against authorized Cloudflare resources.

## Context checkpoint

```yaml
checkpoint_version: 1
updated_at: 2026-07-23T16:35:00+02:00
head: f7c3d14c87da91686950c1925dfe227c7668e3bf
branch: develop
pr: pending
status: blocked
context_routes:
  - docs/agents/programs/FTAI_AI_TRADING_PORTAL_PROGRAM.md
  - docs/ai_platform/portal/SECURITY_ARCHITECTURE.md
  - docs/ai_platform/portal/QUALITY_AND_AUTONOMOUS_E2E.md
  - docs/ai_platform/portal/DELIVERY_ROADMAP.md
  - docs/ai_platform/portal/AGENT_EXECUTION_PLAN.md
owned_paths:
  - ai_platform/portal/deploy/cloudflare/
  - tests/ai_platform/portal/deploy/cloudflare/
  - .github/workflows/portal-staging-policy.yml
  - .github/workflows/portal-staging-external-e2e.yml
  - docs/ai_platform/portal/PRODUCTION_LIKE_STAGING.md
  - docs/ai_platform/portal/runbooks/STAGING_SECRET_ROTATION.md
  - docs/ai_platform/portal/runbooks/STAGING_INCIDENT_AND_KILL_SWITCH.md
  - docs/agents/tasks/FTAI-20260723-portal-p11-cloudflare-staging.md
proven:
  - Repository-side P11 was squash-merged from PR #180 to develop as 99c659242d8c59d85c6d23182a928d323d617f72.
  - PR #181 durably recorded the external staging blocker after the P11 implementation merge and is merged.
  - Live-state refresh before PR #203 verified develop at d158e759b968419dfef39da809cdd48e4571e4b9; comparison from PR #180 merge showed no P11 implementation-owned path changed afterward except this task record.
  - PR #203 refreshed this blocker checkpoint and squash-merged as cc617105a75b4a1089de578b42e74964a569fc4a after Freqtrade CI and zizmor passed.
  - PR #204 stabilized the P11 post-merge handoff and squash-merged as f7c3d14c87da91686950c1925dfe227c7668e3bf after required checkpoint CI passed.
  - The merged staging contract requires Tunnel ingress, forbids public origin/Freqtrade ingress and fixes execution to simulated mode.
  - The merged external verifier checks public portal reachability, Access anonymous denial, Access service identity, direct-origin denial and direct-Freqtrade denial without printing endpoint or token secrets.
  - The owner explicitly decided on 2026-07-23 to defer real Cloudflare and protected GitHub staging infrastructure until the software platform is otherwise ready.
  - The current GitHub connector exposes workflow run read/rerun actions but no workflow-dispatch or GitHub environment-inspection action; no Cloudflare connector/plugin is installed in this execution context.
derived:
  - Repository-side autonomous work for P11 is complete; real P11 external acceptance remains blocked and must not be inferred from simulation.
  - Owner-approved sequencing allows P12 to proceed simulation-first against deterministic P10/local/CI evidence once the accompanying governance change merges, while real P11 External E2E remains mandatory for production-like staging acceptance.
unknown:
  - Whether owner-approved Cloudflare staging Tunnel, DNS, Access, WAF/rate-limit and origin firewall resources currently exist.
  - Whether the repository GitHub staging environment currently has all required protected variables and secrets.
conflicts: []
first_failure:
  marker: external-infrastructure-deferred
  evidence: The repository-side P11 foundation is merged and green, but the owner has intentionally deferred real Cloudflare/protected GitHub staging provisioning and verification until the software platform is otherwise ready.
rejected_hypotheses:
  - Treat repository CI, mocks or simulated Cloudflare probes as proof of real P11 staging acceptance.
  - Add a test-only Access bypass or expose origin/Freqtrade directly to make external E2E easier.
  - Treat simulation-first P12 results as evidence that real Cloudflare ingress or production-like staging acceptance passed.
  - Enable production exchange credentials or live capital as part of P11 or simulation-first P12.
changed_paths:
  - ai_platform/portal/deploy/cloudflare/__init__.py
  - ai_platform/portal/deploy/cloudflare/schema.py
  - ai_platform/portal/deploy/cloudflare/policy.py
  - ai_platform/portal/deploy/cloudflare/probe.py
  - ai_platform/portal/deploy/cloudflare/staging-policy.example.json
  - tests/ai_platform/portal/deploy/cloudflare/test_policy.py
  - tests/ai_platform/portal/deploy/cloudflare/test_probe.py
  - .github/workflows/portal-staging-policy.yml
  - .github/workflows/portal-staging-external-e2e.yml
  - docs/ai_platform/portal/PRODUCTION_LIKE_STAGING.md
  - docs/ai_platform/portal/runbooks/STAGING_SECRET_ROTATION.md
  - docs/ai_platform/portal/runbooks/STAGING_INCIDENT_AND_KILL_SWITCH.md
  - docs/agents/tasks/FTAI-20260723-portal-p11-cloudflare-staging.md
validation:
  - command: Portal Staging Policy 30000167017
    result: PASS
    evidence: Final checkpoint-only staging policy validation and targeted policy/probe tests passed before PR #180 merge.
  - command: AI Platform CI 30000167011
    result: PASS
    evidence: Final checkpoint-only AI Platform tests, Ruff, Ruff format and remaining validation passed before PR #180 merge.
  - command: Freqtrade CI 30000167039
    result: PASS
    evidence: Final checkpoint-only pre-commit, documentation and full required platform matrix passed before PR #180 merge.
  - command: GitHub Actions Security Analysis with zizmor 30000167234
    result: PASS
    evidence: Final checkpoint-only workflow security analysis passed before PR #180 merge.
  - command: Freqtrade CI 30014255383
    result: PASS
    evidence: PR #203 checkpoint refresh passed CI scope, pre-commit, documentation build and CI Gate; unrelated core/platform matrices were skipped by scope.
  - command: GitHub Actions Security Analysis with zizmor 30014253478
    result: PASS
    evidence: PR #203 checkpoint refresh workflow security analysis passed.
  - command: Portal Staging External E2E
    result: BLOCKED
    evidence: Real Cloudflare resources and protected GitHub staging variables/secrets are intentionally deferred and remain unavailable or unverifiable from this execution context; this does not block simulation-first P12 implementation.
blockers:
  - Real P11 production-like staging acceptance remains deferred until owner-approved Cloudflare Tunnel, DNS, Access, WAF/rate-limit and origin firewall resources are provisioned or confirmed.
  - Protected GitHub staging variables and secrets required by Portal Staging External E2E remain deferred until the real infrastructure phase.
next_action: Merge the owner-approved P11/P12 sequencing governance change, then declare and execute P12 in simulation-first mode using deterministic P10/local/CI evidence while preserving real P11 External E2E as the later mandatory production-like staging acceptance gate.
```
