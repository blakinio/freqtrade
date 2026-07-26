---
task_id: FTAI-20260726-liquid20-h2-tardis-importer
status: completed
branch: feat/liquid20-h2-tardis-importer
base_branch: develop
created: 2026-07-26
updated: 2026-07-26
related_pr: "#370"
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
updated_at: 2026-07-26T16:30:00Z
head: d8e9438a1ec913e027479bc9ca9857d6cc887667
merge_commit: dc3df608362e75ee30f4e50b4ffb3cc5ceeb05bf
branch: feat/liquid20-h2-tardis-importer
pr: "#370"
status: completed
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
  - The local-only Tardis adapter supports normalized liquidation CSV for Bybit and Binance Futures.
  - Immutable input size and SHA-256 are verified before parsing.
  - Exchange and provider-local microsecond timestamps are preserved without populating first-party received_at_ms.
  - Invalid headers, row shapes, exchanges, symbols, sides, decimals and semantic eras fail closed and parser rejections count toward acceptance.
  - Import artifacts are deterministically ordered, serialized, hashed and atomically published without overwrite.
  - All four frozen public free samples validated successfully with 5,585 records and zero parser rejections.
  - PR 370 merged as dc3df608362e75ee30f4e50b4ffb3cc5ceeb05bf.
derived:
  - The repository is ready for an owner-authorized H3 paid backfill without further importer implementation.
unknown:
  - Commercial access, exact quote, license acceptance, approved historical start window and Oteryn-only credential provisioning remain owner-gated.
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
  - command: public Tardis free-sample validation
    result: PASS
    evidence: Run 30201913799 validated Bybit and Binance Futures BTCUSDT/ETHUSDT samples with frozen hashes, 5,585 records and zero parser rejections.
  - command: AI Platform CI
    result: PASS
    evidence: Run 30202469769 completed successfully with tests, compile, Ruff, formatting, codespell and JSON validation.
  - command: Freqtrade CI
    result: PASS
    evidence: Run 30202469765 completed successfully through pre-commit, Mypy, Python matrices, docs, package build and CI Gate.
  - command: GitHub Actions Security Analysis with zizmor
    result: PASS
    evidence: Run 30202469781 completed successfully.
blockers:
  - Owner approval for Tardis commercial access and exact quote.
  - Owner acceptance of license and raw-redistribution restrictions.
  - Owner choice of the 2025-02-26 common start or authorization to clarify 2025-02-20 through 2025-02-25 with the provider.
  - Owner authorization for future Oteryn-only API-key provisioning before H3.
next_action: Obtain the owner decisions for Tardis purchase, license, historical start window and Oteryn-only credential provisioning; do not start H3 paid backfill until all are approved.
```
