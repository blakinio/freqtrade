---
task_id: FTAI-20260724-liquid20-multi-source-acceptance-v1
status: active
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
updated_at: 2026-07-24T14:05:00Z
head: 7fe07b76ee7912b86b4b97ad79dbf1ceba8aae5f
branch: feat/liquid20-multi-source-acceptance-v1
pr: "#256"
status: active
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
  - The failing immutable-target test is corrected on this branch by writing directly into tmp_path.
  - The prospective policy freezes 24-hour source-specific health, latency, event, coverage, clock, identity, and artifact-integrity gates.
  - The evaluator verifies the manifest, both summaries, actual NDJSON hashes, sizes and line counts, source semantics, start/end clocks, and cross-source coverage.
  - The runner preserves a manifest even when either collector or summary normalization fails and refuses trading credentials.
derived:
  - Subscription acknowledgement alone is insufficient for operational acceptance.
  - Per-symbol minimum event gates are inappropriate for all 20 contracts in one day; source and union/intersection coverage gates preserve rigor without forcing artificial activity.
  - Start and end clock probes are required because a single startup probe cannot prove clock health across a 24-hour run.
unknown:
  - Final focused and repository CI result for PR #256.
  - Whether the intended non-restricted always-on staging host passes every frozen gate for 24 hours.
conflicts: []
first_failure:
  marker: prior-test-fixture-mkdir
  evidence: PR #254 core job 89469318418 failed at tests/ai_platform_integration/test_liquidation_symbol_universe.py because tmp_path already existed; 4960 other tests passed.
rejected_hypotheses:
  - Treat successful subscription acknowledgement as operational acceptance.
  - Require at least one event from every symbol regardless of market conditions.
  - Hide one source failure behind availability from the other source.
  - Run the 24-hour package on a known restricted GitHub-hosted US runner.
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
    evidence: Exact project-test fixture failure was extracted without modifying prior evidence.
blockers:
  - No accepted 24-hour run exists on the intended non-restricted always-on staging host.
next_action: Complete focused and repository validation for PR #256, merge the acceptance package, then execute its unchanged 24-hour runbook on the intended staging host.
```
