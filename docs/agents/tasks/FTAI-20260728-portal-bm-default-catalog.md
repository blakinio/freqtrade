---
task_id: FTAI-20260728-portal-bm-default-catalog
status: validating
branch: feat/portal-bm-default-catalog-v1
base_branch: develop
created: 2026-07-28
updated: 2026-07-28
related_pr: 601
owned_paths:
  - ai_platform/portal/bot_catalog/default_catalog.py
  - ai_platform/portal/control_plane/bot_management.py
  - tests/ai_platform/portal/bot_catalog/test_default_catalog.py
  - docs/agents/tasks/FTAI-20260728-portal-bm-default-catalog.md
---

# Approved dry-run starter catalog

## Goal

Replace the empty default BM-01 repository with one immutable, reviewed and secret-free dry-run-only catalog that uses identifiers already present in the portal product fixtures. This activates catalog discovery and BM-02 draft validation without adding credentials, runtime submission or live capital.

## Delivered

- immutable `portal-approved-dry-run` catalog revision 1;
- one AI directional dry-run template;
- existing portal strategy, model, runtime and risk identifiers;
- simulated spot exchange capability metadata only;
- deterministic SHA-256 evidence derived from canonical payloads;
- default application composition with the approved snapshot;
- tests for dry-run-only scope, secret exclusion and read-only discovery.

## Safety boundary

The catalog contains no exchange connection, credential reference, API key, passphrase or secret-store path. It authorizes configuration compatibility only and does not create a bot, resolve a credential, submit to Freqtrade or activate live capital.

## Context checkpoint

```yaml
checkpoint_version: 1
updated_at: 2026-07-28T12:32:00+02:00
head_parent: 1a1b54d5140ac7728a1171e0f7ca20cf432056fd
branch: feat/portal-bm-default-catalog-v1
pr: 601
status: validating
context_routes:
  - AGENTS.md
  - docs/agents/CONTEXT_HANDOFF.md
  - docs/ai_platform/portal/BOT_MANAGEMENT_PRODUCT_ARCHITECTURE.md
  - docs/ai_platform/portal/BOT_MANAGEMENT_AGENT_PLAN.md
owned_paths:
  - ai_platform/portal/bot_catalog/default_catalog.py
  - ai_platform/portal/control_plane/bot_management.py
  - tests/ai_platform/portal/bot_catalog/test_default_catalog.py
  - docs/agents/tasks/FTAI-20260728-portal-bm-default-catalog.md
proven:
  - BM-01 and BM-02 are merged and registered in the canonical control-plane application.
  - The previous default repository was explicitly empty, making catalog discovery return CATALOG_NOT_FOUND.
  - Existing portal fixtures already use ai-directional-v1, model-validated-2026-07, freqtrade-2026.7 and risk-default-v1.
  - Focused implementation tests, Ruff and compilation passed on the pre-format head.
  - Formatter workflow 30349666613 succeeded and removed its own workflow file.
derived:
  - A reviewed built-in dry-run snapshot is the smallest safe prerequisite for BMW-01.
unknown:
  - Exact-head standard CI results for this connector-authored commit.
conflicts: []
first_failure:
  marker: DEFAULT_BM_CATALOG_EMPTY
  evidence: build_default_bot_management_services constructed InMemoryBotCatalogRepository with no snapshots.
rejected_hypotheses:
  - Let the browser type arbitrary version identifiers.
  - Add an exchange credential or resolved secret to the catalog.
  - Claim catalog compatibility is execution authority.
changed_paths:
  - ai_platform/portal/bot_catalog/default_catalog.py
  - ai_platform/portal/control_plane/bot_management.py
  - tests/ai_platform/portal/bot_catalog/test_default_catalog.py
  - docs/agents/tasks/FTAI-20260728-portal-bm-default-catalog.md
validation:
  - command: formatter workflow 30349666613
    result: PASS
    evidence: Ruff 0.15.21 formatter committed exact output and removed the temporary workflow.
  - command: exact-head AI Platform CI, Freqtrade CI and security analysis
    result: NOT_RUN
    evidence: This connector-authored checkpoint commit creates the authoritative validation head.
blockers: []
next_action: Run exact-head CI, audit scope and merge before BMW-01 web work.
```
