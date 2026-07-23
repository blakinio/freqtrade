---
task_id: FTAI-20260723-portal-p11-cloudflare-staging
status: active
branch: feat/portal-p11-cloudflare-staging
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
  - current develop and open PRs/tasks overlapping Cloudflare staging ownership
  - existing staging deployment, Tunnel, Access and protected GitHub environment evidence
  - current P10 deterministic simulator and universal E2E merge state
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
updated_at: 2026-07-23T12:39:00+02:00
head: e44e1a5d817a8c5cbe4ae4ac955144058f44e44d
branch: feat/portal-p11-cloudflare-staging
pr: "#180"
status: ready
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
  - P10 deterministic simulator and universal E2E were merged to develop as 4c1971d9eced5913ed4fb6121d351c30e63ba9c2 and formally closed out on develop as ce3ba464afcd111dd4c7c4dd47de6ebdb275ee11.
  - Portal architecture requires Internet -> Cloudflare edge -> Access where privileged -> Tunnel -> private staging portal, with Freqtrade remaining private.
  - No open overlapping P11 Cloudflare staging pull request was found during live preflight.
  - No installed Cloudflare connector/plugin is available in this session for direct external-account mutation.
  - Repository-side P11 policy/probe implementation keeps execution simulated and contains no live-capital or exchange-execution path.
  - Final implementation diff is synchronized with develop and contains exactly the 13 declared P11-owned files.
  - Portal Staging Policy, AI Platform, Freqtrade and zizmor validation all passed on implementation head e44e1a5d817a8c5cbe4ae4ac955144058f44e44d.
derived:
  - Repository-side policy, CI and runbooks are ready to merge independently from external Cloudflare account provisioning.
  - Real P11 staging acceptance must remain blocked unless owner-approved Cloudflare resources and protected GitHub staging configuration are available and the external E2E passes.
unknown:
  - Whether owner-approved Cloudflare staging Tunnel, DNS, Access, WAF/rate-limit and origin firewall resources currently exist.
  - Whether the repository GitHub staging environment currently has the required protected variables and secrets.
conflicts: []
first_failure:
  marker: external-infrastructure-unverified
  evidence: Repository validation is green, but no authorized Cloudflare account connector or verified staging environment credentials are available in this execution context, so real external acceptance has not run.
rejected_hypotheses:
  - Treat static/unit CI as proof that real Cloudflare staging ingress is correctly provisioned.
  - Add a test-only Access bypass or expose the origin/Freqtrade directly to simplify staging E2E.
  - Use production exchange credentials or live capital for P11 validation.
  - Keep temporary Ruff diagnostic or write-enabled formatter workflows in the final diff.
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
  - command: Portal Staging Policy 29999348943
    result: PASS
    evidence: Fail-closed staging manifest validation and all targeted Cloudflare staging policy/probe tests passed on implementation head e44e1a5d817a8c5cbe4ae4ac955144058f44e44d.
  - command: AI Platform CI 29999348891
    result: PASS
    evidence: AI Platform tests, Ruff, Ruff format, codespell and remaining validation passed on implementation head e44e1a5d817a8c5cbe4ae4ac955144058f44e44d.
  - command: Freqtrade CI 29999348830
    result: PASS
    evidence: Pre-commit, CI scope, documentation and the full required platform matrix passed on implementation head e44e1a5d817a8c5cbe4ae4ac955144058f44e44d.
  - command: GitHub Actions Security Analysis with zizmor 29999348787
    result: PASS
    evidence: Workflow security analysis passed on implementation head e44e1a5d817a8c5cbe4ae4ac955144058f44e44d.
  - command: compare develop...feat/portal-p11-cloudflare-staging
    result: PASS
    evidence: Before this checkpoint-only update, behind_by=0 and exactly 13 P11-owned files differed from develop.
blockers: []
next_action: Verify checkpoint-only required CI and review/base state on PR #180, squash-merge the repository-side P11 foundation if green, then run Portal Staging External E2E only if owner-approved Cloudflare resources and protected GitHub staging variables/secrets are available; otherwise mark P11 blocked on that external acceptance gate.
```
