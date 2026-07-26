---
task_id: FTAI-20260726-liquid20-h2-tardis-importer
status: in_progress
branch: feat/liquid20-h2-tardis-importer
base_branch: develop
created: 2026-07-26
updated: 2026-07-26
related_pr: pending
owned_paths:
  - ai_platform/research/liquidations/historical/acceptance.py
  - ai_platform/research/liquidations/historical/importer.py
  - ai_platform/research/liquidations/historical/providers/
  - ai_platform/research/liquidations/historical/__init__.py
  - tests/ai_platform_integration/test_liquidation_history_tardis_importer.py
  - docs/ai_platform/LIQUID20_TARDIS_LOCAL_IMPORTER.md
  - docs/agents/tasks/FTAI-20260726-liquid20-h2-tardis-importer.md
required_reads:
  - AGENTS.md
  - docs/agents/CONTEXT_HANDOFF.md
  - docs/ai_platform/LIQUID20_HISTORICAL_AI_TRAINING_ARCHITECTURE.md
  - docs/ai_platform/LIQUID20_HISTORICAL_PROVIDER_PREFLIGHT.md
  - docs/ai_platform/LIQUID20_HISTORICAL_CONTRACTS.md
search_first:
  - current develop HEAD and open Liquid20 historical PRs
optional_reads: []
---

# Liquid20 H2 Tardis local importer

## Goal

Implement the local-only Tardis normalized liquidation CSV adapter, deterministic atomic importer, row-rejection accounting and public free-sample validation. No paid provider access, credential, bulk backfill, Synology mutation, feature generation, model training, protected-holdout access or execution.

## Context checkpoint

```yaml
checkpoint_version: 1
updated_at: 2026-07-26T12:20:00Z
head: pending
branch: feat/liquid20-h2-tardis-importer
pr: pending
status: in_progress
context_routes:
  - docs/ai_platform/LIQUID20_TARDIS_LOCAL_IMPORTER.md
  - docs/ai_platform/LIQUID20_HISTORICAL_CONTRACTS.md
owned_paths:
  - ai_platform/research/liquidations/historical/acceptance.py
  - ai_platform/research/liquidations/historical/importer.py
  - ai_platform/research/liquidations/historical/providers/
  - ai_platform/research/liquidations/historical/__init__.py
  - tests/ai_platform_integration/test_liquidation_history_tardis_importer.py
  - docs/ai_platform/LIQUID20_TARDIS_LOCAL_IMPORTER.md
  - docs/agents/tasks/FTAI-20260726-liquid20-h2-tardis-importer.md
proven:
  - H1 is merged and its deterministic historical contracts are available.
  - Tardis normalized liquidation CSV exposes exchange and provider-local timestamps in microseconds.
  - Public first-day-of-month samples can be used without paid credentials.
derived:
  - H2 can be completed without owner purchase or credential provisioning.
unknown:
  - Full paid backfill remains deferred to H3.
conflicts: []
first_failure: null
rejected_hypotheses:
  - Ignore malformed rows when computing import acceptance.
  - Let the importer download provider data.
  - Overwrite an existing import output.
  - Commit or upload raw public sample files.
changed_paths:
  - ai_platform/research/liquidations/historical/acceptance.py
  - ai_platform/research/liquidations/historical/importer.py
  - ai_platform/research/liquidations/historical/providers/
  - ai_platform/research/liquidations/historical/__init__.py
  - tests/ai_platform_integration/test_liquidation_history_tardis_importer.py
  - docs/ai_platform/LIQUID20_TARDIS_LOCAL_IMPORTER.md
  - docs/agents/tasks/FTAI-20260726-liquid20-h2-tardis-importer.md
validation:
  - command: targeted H1 and H2 tests
    result: PASS
    evidence: 16 synthetic tests passed before repository CI.
  - command: public Tardis free-sample validation and exact-head repository CI
    result: PENDING
    evidence: Run after implementation commit.
blockers: []
next_action: Validate all four frozen public samples, remove temporary workflow code, merge H2 when exact-head CI and review are clean, then stop before owner-gated H3 paid backfill.
```
