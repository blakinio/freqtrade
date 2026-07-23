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
updated_at: 2026-07-23T12:55:00+02:00
head: 99c659242d8c59d85c6d23182a928d323d617f72
branch: develop
pr: "#180"
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
  - The merged staging contract requires Tunnel ingress, forbids public origin/Freqtrade ingress and fixes execution to simulated mode.
  - The merged external verifier checks public portal reachability, Access anonymous denial, Access service identity, direct-origin denial and direct-Freqtrade denial without printing endpoint or token secrets.
  - Portal Staging Policy, AI Platform, Freqtrade and zizmor validation passed on both the implementation and final checkpoint merge-state heads before merge.
  - No installed Cloudflare connector/plugin, GitHub workflow-dispatch action or GitHub environment-inspection action is available in this execution context.
derived:
  - Repository-side autonomous work for P11 is complete.
  - P12 cannot start until real production-like staging External E2E is stable because the execution plan makes P11 staging E2E a prerequisite.
unknown:
  - Whether owner-approved Cloudflare staging Tunnel, DNS, Access, WAF/rate-limit and origin firewall resources currently exist.
  - Whether the repository GitHub staging environment currently has all required protected variables and secrets.
conflicts: []
first_failure:
  marker: external-infrastructure-unverified
  evidence: The repository-side P11 foundation is merged and green, but real Portal Staging External E2E cannot be executed or verified without authorized external Cloudflare resources and protected staging configuration.
rejected_hypotheses:
  - Treat repository CI or mock probes as proof of real Cloudflare staging acceptance.
  - Add a test-only Access bypass or expose origin/Freqtrade directly to make external E2E easier.
  - Start P12 before P11 real staging E2E is stable.
  - Enable production exchange credentials or live capital as part of P11.
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
  - command: Portal Staging External E2E
    result: BLOCKED
    evidence: Owner-approved real Cloudflare resources and protected GitHub staging variables/secrets are unavailable or unverifiable from the current execution context, and no workflow-dispatch tool is available.
blockers:
  - Owner-approved real Cloudflare staging Tunnel, DNS, Access, WAF/rate-limit and origin firewall resources are unavailable or unverified in the current execution context.
  - Protected GitHub staging environment variables and secrets required by Portal Staging External E2E are unavailable or unverified in the current execution context.
  - No available Cloudflare connector/plugin or GitHub workflow-dispatch/environment-inspection action can provision, inspect or run the real external acceptance from this session.
next_action: An authorized owner must provision or confirm the real Cloudflare staging resources and protected GitHub staging environment, then run Portal Staging External E2E and require all five ingress/Access/direct-denial probes to pass before P12 starts.
```
