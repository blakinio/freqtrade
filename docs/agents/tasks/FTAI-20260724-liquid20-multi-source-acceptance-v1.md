---
task_id: FTAI-20260724-liquid20-multi-source-acceptance-v1
status: blocked
branch: develop
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
updated_at: 2026-07-24T14:50:00Z
head: 5408db5bf61f70245e17988f9e8f15c95127f728
branch: develop
pr: "#256"
status: blocked
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
  - PR #256 merged to develop as 5408db5bf61f70245e17988f9e8f15c95127f728.
  - The frozen policy declares exact 24-hour source, health, latency, activity, coverage, identity, clock, and artifact-integrity gates for liquid20-v1.
  - The evaluator independently verifies the root manifest, both summaries, actual NDJSON hashes, sizes and line counts, source semantics, start and end clocks, and cross-source coverage.
  - The runner records stable run and host identity, preserves separate venue outputs, refuses recognized trading credentials, and writes a failure-preserving manifest when either source fails.
  - The prior immutable-target test fixture was corrected and passed across Linux, macOS, and Windows in the final matrix.
  - Candidate e72467068c271579e93654f2adb0c4b02a505bb1 passed AI Platform CI run 30093410136 and zizmor run 30093410163.
  - Freqtrade CI run 30093410126 passed pre-commit, documentation, Python 3.11 through 3.14 Linux jobs, macOS, Windows, coverage, generated-file checks, backtesting, Hyperopt, Ruff, Ruff format, mypy, and Pester where applicable.
  - Focused acceptance validation run 30092947208 job 89480131688 passed compile, focused tests, Ruff, Ruff format, and checkpoint validation.
derived:
  - Subscription acknowledgement alone is insufficient for operational acceptance.
  - Source and union/intersection coverage gates are more rigorous than forcing an event from every contract regardless of legitimate market activity.
  - Start and end clock probes are required because a startup probe cannot prove clock health across a 24-hour run.
unknown:
  - Whether the intended non-restricted always-on staging host passes every frozen gate for 24 hours.
conflicts: []
first_failure:
  marker: no-operational-liquid20-acceptance-run
  evidence: The policy, runner, evaluator, tests, and runbook are merged, but no immutable 24-hour package from the intended staging host exists.
rejected_hypotheses:
  - Treat successful subscription acknowledgement as operational acceptance.
  - Require at least one event from every symbol regardless of market conditions.
  - Hide one source failure behind availability from the other source.
  - Weaken policy thresholds after observing a run.
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
  - command: AI Platform CI run 30093410136
    result: PASS
  - command: zizmor run 30093410163
    result: PASS
  - command: Freqtrade CI run 30093410126
    result: PASS
  - command: focused acceptance validation run 30092947208 job 89480131688
    result: PASS
blockers:
  - No accepted 24-hour multi-source liquid20-v1 package exists on the intended non-restricted always-on staging host.
next_action: Execute the unchanged 24-hour liquid20-v1 runbook on the intended staging host and preserve its immutable pass or failure evidence.
```
