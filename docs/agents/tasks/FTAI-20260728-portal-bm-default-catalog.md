---
task_id: FTAI-20260728-portal-bm-default-catalog
status: validating
branch: feat/portal-bm-default-catalog-v2
base_branch: develop
created: 2026-07-28
updated: 2026-07-28
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
updated_at: 2026-07-28T13:02:00+02:00
head_parent: ebe2fbf45bd23aee68f7f14ddca7f6c5907b1fe8
branch: feat/portal-bm-default-catalog-v2
pr: null
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
  - The original implementation passed focused tests, Ruff and formatter checks before develop advanced.
  - Develop advancement from cf2f4233921f11435ba14b43c2d31183a7a376cb to fda21a72ea8e4cd3f70623e2bd44bddea5b32683 has no path overlap with this package.
derived:
  - A reviewed built-in dry-run snapshot is the smallest safe prerequisite for BMW-01.
unknown:
  - Exact-head standard CI results for the fresh branch.
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
  - command: exact-head AI Platform CI, Freqtrade CI and security analysis
    result: NOT_RUN
    evidence: New PR head will be the source of truth.
blockers: []
next_action: Open a fresh PR, run exact-head CI, audit and merge before BMW-01.
```
