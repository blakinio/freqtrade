---
task_id: FTAI-20260727-okx-liquidation-staging-readiness-probe-v1
status: ready
branch: feat/okx-staging-readiness-probe-v1
base_branch: develop
created: 2026-07-27
updated: 2026-07-27
related_pr: "#421"
owned_paths:
  - .github/workflows/ai-platform-okx-liquidation-staging-readiness.yml
  - docs/ai_platform/LIQUIDATION_OKX_STAGING_READINESS.md
  - docs/agents/tasks/FTAI-20260727-okx-liquidation-staging-readiness-probe-v1.md
required_reads:
  - AGENTS.md
  - docs/agents/CONTEXT_HANDOFF.md
  - docs/ai_platform/LIQUIDATION_OKX_SHADOW_ACCEPTANCE_EXECUTION.md
  - docs/agents/tasks/FTAI-20260727-liquidation-okx-shadow-acceptance-infrastructure-v1.md
search_first:
  - current develop and PR 421 mergeability and exact-head CI
  - protected staging environment and self-hosted runner readiness
optional_reads: []
---

# OKX liquidation staging readiness probe v1

## Result

The inert, exact-one-file readiness probe is implemented for the protected
`okx-liquidation-staging` environment. It verifies the required variables, durable storage,
runner labels and absence of recognized trading credentials without starting the collector,
performing an OKX network probe or writing to the acceptance run directory.

## Context checkpoint

```yaml
checkpoint_version: 1
updated_at: 2026-07-27T09:17:13+02:00
head: 70b0b60cb1737d650689f86689ef819ca9a0a699
branch: feat/okx-staging-readiness-probe-v1
pr: "#421"
status: ready
context_routes:
  - docs/ai_platform/LIQUIDATION_OKX_SHADOW_ACCEPTANCE_EXECUTION.md
  - docs/ai_platform/LIQUIDATION_OKX_STAGING_READINESS.md
  - .github/workflows/ai-platform-okx-liquidation-staging-readiness.yml
owned_paths:
  - .github/workflows/ai-platform-okx-liquidation-staging-readiness.yml
  - docs/ai_platform/LIQUIDATION_OKX_STAGING_READINESS.md
  - docs/agents/tasks/FTAI-20260727-okx-liquidation-staging-readiness-probe-v1.md
proven:
  - PR 417 merged the inert OKX 24-hour acceptance infrastructure as develop commit 237196b2b5b3bfbdd52609e139f55f585711d4d5.
  - The acceptance workflow requires environment okx-liquidation-staging, runner labels self-hosted/Linux/okx-liquidation-staging and variables OKX_ACCEPTANCE_HOST_ID, OKX_ACCEPTANCE_DURABLE_ROOT and OKX_ACCEPTANCE_DURABLE_URI.
  - The available GitHub connector cannot directly list protected-environment variables or self-hosted runner status.
  - The readiness workflow never installs the collector dependency, performs an OKX network probe, starts collection or writes to the durable acceptance directory.
  - PR 421 changes exactly the readiness workflow, its runbook and this checkpoint; it contains no readiness request or 24-hour acceptance request.
  - Head 70b0b60cb1737d650689f86689ef819ca9a0a699 passed AI Platform CI 30245488714, Freqtrade CI 30245488880 and zizmor 30245488570.
derived:
  - A started readiness job proves an online runner matches all required labels.
  - A successful readiness job proves the three environment variables are non-empty, the durable root is acceptable and no recognized trading credential is present.
  - The bounded readiness artifact may publish only the declared non-sensitive host identity, credential-free durable URI, runner metadata and boolean checks.
unknown:
  - Whether the protected environment and labelled runner will pass the separate readiness request.
conflicts: []
first_failure:
  marker: okx-staging-readiness-not-yet-executed
  evidence: The readiness infrastructure passed repository CI, but no exact-one-file readiness request has run on the protected self-hosted staging boundary.
rejected_hypotheses:
  - Guess the host identity or durable URI in the canonical 24-hour request.
  - Start the 24-hour collector merely to test runner availability.
  - Publish the durable filesystem root or any credential inventory.
  - Execute branch-controlled collector code on a self-hosted runner during readiness verification.
changed_paths:
  - .github/workflows/ai-platform-okx-liquidation-staging-readiness.yml
  - docs/ai_platform/LIQUIDATION_OKX_STAGING_READINESS.md
  - docs/agents/tasks/FTAI-20260727-okx-liquidation-staging-readiness-probe-v1.md
validation:
  - command: AI Platform CI exact-head validation
    result: PASS
    evidence: Run 30245488714 passed checkpoint validation, compile, tests, Ruff, formatting, codespell and JSON checks on 70b0b60cb1737d650689f86689ef819ca9a0a699.
  - command: Freqtrade CI exact-head validation
    result: PASS
    evidence: Run 30245488880 passed scope classification, pre-commit, documentation and CI Gate on 70b0b60cb1737d650689f86689ef819ca9a0a699.
  - command: zizmor exact-head workflow security analysis
    result: PASS
    evidence: Run 30245488570 passed on 70b0b60cb1737d650689f86689ef819ca9a0a699.
blockers: []
next_action: Merge PR 421 after final exact-head checks pass, then create the separate exact-one-file readiness request PR and inspect its bounded artifact before creating any 24-hour acceptance request.
```
