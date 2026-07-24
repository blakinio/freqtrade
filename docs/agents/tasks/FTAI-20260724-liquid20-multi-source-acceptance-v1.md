---
task_id: FTAI-20260724-liquid20-multi-source-acceptance-v1
status: validating
branch: feat/liquid20-multi-source-acceptance-v1
base_branch: develop
created: 2026-07-24
updated: 2026-07-24
related_pr: "#256"
owned_paths:
  - ai_platform/research/liquidations/multi-source-acceptance-policy-v1.json
  - ai_platform/research/liquidations/multi_source_acceptance.py
  - ai_platform/scripts/liquidation_multi_source_runner.py
  - ai_platform/scripts/liquidation_multi_source_evaluator.py
  - tests/ai_platform_integration/test_liquidation_multi_source_acceptance.py
  - tests/ai_platform_integration/test_liquidation_symbol_universe.py
  - docs/ai_platform/LIQUIDATION_MULTI_SOURCE.md
  - docs/agents/tasks/FTAI-20260724-liquid20-multi-source-acceptance-v1.md
required_reads:
  - AGENTS.md
  - docs/agents/CONTEXT_HANDOFF.md
  - docs/ai_platform/ARCHITECTURE.md
  - docs/ai_platform/ROADMAP.md
  - docs/ai_platform/LIQUIDATION_MULTI_SOURCE.md
---

# Liquid20 Multi-Source Acceptance v1

## Goal

Declare and implement a deterministic 24-hour acceptance package for the frozen `liquid20-v1` Bybit and Binance public liquidation collectors without enabling replay, trading, credentials, protected-holdout use, or live capital.

## Context checkpoint

```yaml
checkpoint_version: 1
updated_at: 2026-07-24T14:25:00Z
head: b1e84e4b68e6f5e25391e9bef3f0d6a67654a188
branch: feat/liquid20-multi-source-acceptance-v1
pr: "#256"
status: validating
context_routes:
  - docs/ai_platform/LIQUIDATION_MULTI_SOURCE.md
owned_paths:
  - ai_platform/research/liquidations/multi-source-acceptance-policy-v1.json
  - ai_platform/research/liquidations/multi_source_acceptance.py
  - ai_platform/scripts/liquidation_multi_source_runner.py
  - ai_platform/scripts/liquidation_multi_source_evaluator.py
  - tests/ai_platform_integration/test_liquidation_multi_source_acceptance.py
  - tests/ai_platform_integration/test_liquidation_symbol_universe.py
  - docs/ai_platform/LIQUIDATION_MULTI_SOURCE.md
  - docs/agents/tasks/FTAI-20260724-liquid20-multi-source-acceptance-v1.md
proven:
  - develop head 9fdacb856cc9a26bc0783d567f7f919e9e053013 contains the merged liquid20-v1 universe and checkpoint.
  - Production public WebSocket subscription acknowledgements already accepted all 20 symbols on both sources.
  - PR #254 broad core CI failed only because one project test recreated the existing pytest tmp_path directory; the same job reported 4960 other tests passed.
  - The immutable-target test is corrected on this branch by writing directly into tmp_path.
  - The policy freezes 24-hour health, latency, event, coverage, clock, identity, and artifact-integrity gates.
  - The evaluator verifies the manifest, both summaries, actual NDJSON hashes, sizes and line counts, source semantics, start/end clocks, and cross-source coverage.
  - The runner preserves a manifest even when either collector or summary normalization fails and refuses trading credentials.
  - Focused compilation, tests, Ruff check, and Ruff format passed in validation run 30092764694.
derived:
  - Subscription acknowledgement alone is insufficient for operational acceptance.
  - Source and union/intersection coverage gates are more rigorous than forcing an event from every contract regardless of market activity.
  - Start and end clock probes are required because a startup probe cannot prove clock health across 24 hours.
unknown:
  - Final Freqtrade CI and documentation result for PR #256.
  - Whether the intended non-restricted always-on staging host passes every frozen gate for 24 hours.
conflicts:
  - Repository-wide Ruff 0.16 currently reports pre-existing findings in unrelated portal and script files; changed liquid20 files pass targeted Ruff.
first_failure:
  marker: prior-test-fixture-mkdir
  evidence: PR #254 core job 89469318418 failed because tmp_path already existed; 4960 other tests passed.
rejected_hypotheses:
  - Treat successful subscription acknowledgement as operational acceptance.
  - Require at least one event from every symbol regardless of market conditions.
  - Hide one source failure behind availability from the other source.
  - Expand this PR into an unrelated repository-wide Ruff migration.
changed_paths:
  - ai_platform/research/liquidations/multi-source-acceptance-policy-v1.json
  - ai_platform/research/liquidations/multi_source_acceptance.py
  - ai_platform/scripts/liquidation_multi_source_runner.py
  - ai_platform/scripts/liquidation_multi_source_evaluator.py
  - tests/ai_platform_integration/test_liquidation_multi_source_acceptance.py
  - tests/ai_platform_integration/test_liquidation_symbol_universe.py
  - docs/ai_platform/LIQUIDATION_MULTI_SOURCE.md
  - docs/agents/tasks/FTAI-20260724-liquid20-multi-source-acceptance-v1.md
validation:
  - command: prior CI first-failure diagnostic run 30090591684 job 89472762876
    result: PASS
    evidence: Exact prior project-test fixture failure was extracted.
  - command: focused validation run 30092764694 job 89479561403
    result: PASS
    evidence: Compile, focused tests, Ruff check, and Ruff format passed; only the then-invalid checkpoint status failed.
  - command: repository-wide AI Platform Ruff
    result: BLOCKED
    evidence: Ruff 0.16 reports pre-existing findings outside changed paths; targeted changed-path Ruff passes.
blockers:
  - No accepted 24-hour run exists on the intended non-restricted always-on staging host.
next_action: Complete final checkpoint and repository validation for PR #256, merge the package, then execute its unchanged 24-hour runbook on the intended staging host.
```
