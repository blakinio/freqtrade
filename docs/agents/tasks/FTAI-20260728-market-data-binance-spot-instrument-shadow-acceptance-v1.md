---
task_id: FTAI-20260728-market-data-binance-spot-instrument-shadow-acceptance-v1
status: validating
branch: trigger/binance-v3-shadow-acceptance-20260729
base_branch: develop
created: 2026-07-28
updated: 2026-07-29
related_pr: "#738"
owned_paths:
  - ai_platform/market_data/binance-spot-instrument-shadow-acceptance-policy-v1.json
  - ai_platform/market_data/binance_spot_instrument_acceptance.py
  - ai_platform/market_data/binance_spot_instrument_acceptance_incremental.py
  - .github/workflows/ai-platform-binance-spot-instrument-shadow-acceptance-v3.yml
  - tests/ai_platform_integration/test_market_data_binance_spot_instrument_acceptance_v3.py
  - docs/ai_platform/market_data/BINANCE_SPOT_INSTRUMENT_SHADOW_ACCEPTANCE_V3.md
  - docs/agents/tasks/FTAI-20260728-market-data-binance-spot-instrument-shadow-acceptance-v1.md
required_reads:
  - AGENTS.md
  - docs/agents/CONTEXT_HANDOFF.md
  - docs/ai_platform/market_data/BINANCE_SPOT_INSTRUMENT_SHADOW_ACCEPTANCE_V3.md
search_first:
  - workflow 30482434626 and initializer job 90679668485
  - scheduled AI Platform Binance Spot Instrument Shadow Acceptance V3 runs
optional_reads:
  - docs/ai_platform/market_data/BINANCE_SPOT_INSTRUMENT_SHADOW_ACCEPTANCE_V2.md
---

# Binance Spot instrument shadow acceptance v1

## Context checkpoint

```yaml
checkpoint_version: 1
updated_at: 2026-07-29T21:10:00+02:00
head: 72cdd4613bba59a02aa3ab7cac3c29774929b5d5
branch: trigger/binance-v3-shadow-acceptance-20260729
pr: "#738"
status: validating
context_routes:
  - Binance Spot public instrument-catalog acceptance
  - Synology self-hosted staging runner
  - credential-free deterministic evidence
owned_paths:
  - ai_platform/market_data/binance-spot-instrument-shadow-acceptance-policy-v1.json
  - ai_platform/market_data/binance_spot_instrument_acceptance.py
  - ai_platform/market_data/binance_spot_instrument_acceptance_incremental.py
  - .github/workflows/ai-platform-binance-spot-instrument-shadow-acceptance-v3.yml
  - tests/ai_platform_integration/test_market_data_binance_spot_instrument_acceptance_v3.py
  - docs/ai_platform/market_data/BINANCE_SPOT_INSTRUMENT_SHADOW_ACCEPTANCE_V3.md
  - docs/agents/tasks/FTAI-20260728-market-data-binance-spot-instrument-shadow-acceptance-v1.md
proven:
  - Runtime v3 repair PR 711 merged as 3d3c5d2c5806e2d23c86d2fc53cb01322d85a147.
  - Runtime v3 uses a five-minute due check, ten-minute initializer, five-minute sampler and at most one observation per sampler job.
  - The frozen v3 request and run identities were added by exact-one-file trigger PR 738 at head 72cdd4613bba59a02aa3ab7cac3c29774929b5d5.
  - AI Platform CI 30482435217, Freqtrade CI 30482435287 and workflow-security run 30482435054 passed on the exact trigger head.
  - Workflow 30482434626 initializer job 90679668485 completed success on freqtrade-synology-staging.
  - Exact-one-file scope, approved runner and durable root, credential and proxy refusal, isolated dependency installation and durable incremental-state initialization all passed.
  - PR 738 was closed without merge after successful initialization and the frozen identities were not reused.
  - The PR-event sampler was skipped as designed; scheduled short-lived sampler jobs now own the real 97-observation window.
  - Consumed v2 PR 699, workflow 30459738848 and v2 request/run identities remain forbidden from rerun or reuse.
derived:
  - The canonical real v3 acceptance attempt is active in durable Synology state without holding the runner for 24 hours.
  - Initializer success is not Binance source acceptance and does not enable production, execution, research, models, replay, orders or live capital.
unknown:
  - Number and outcomes of scheduled real Binance observations completed after initialization.
  - Terminal accepted, rejected or inconclusive outcome of the complete 97-observation window.
conflicts: []
first_failure:
  marker: BINANCE_ACCEPTANCE_RUNNER_MONOPOLIZATION
  evidence: Runtime v2 held the single self-hosted runner inside one 24-hour job and was cancelled before terminal evaluation; runtime v3 removes that architecture.
rejected_hypotheses:
  - Treat initializer success or the v3 no-network proof as real source acceptance.
  - Rerun, reopen or reuse consumed v2 or v3 trigger identities.
  - Merge the exact-one-file trigger PR.
  - Enable source_acceptance, production_source_enabled, orders or live capital before terminal evaluation.
changed_paths:
  - ai_platform/market_data/binance_spot_instrument_acceptance_incremental.py
  - .github/workflows/ai-platform-binance-spot-instrument-shadow-acceptance-v3.yml
  - tests/ai_platform_integration/test_market_data_binance_spot_instrument_acceptance_v3.py
  - docs/ai_platform/market_data/BINANCE_SPOT_INSTRUMENT_SHADOW_ACCEPTANCE_V3.md
  - docs/agents/tasks/FTAI-20260728-market-data-binance-spot-instrument-shadow-acceptance-v1.md
validation:
  - command: GitHub workflow 30482434626 initializer job 90679668485
    result: PASS
    evidence: Exact trigger commit initialized durable incremental state on freqtrade-synology-staging with all scope and safety checks successful.
  - command: GitHub PR 738 terminal state
    result: PASS
    evidence: Closed without merge after initializer success; request and run identities remain consumed and non-reusable.
  - command: Trigger exact-head repository workflows
    result: PASS
    evidence: AI Platform CI 30482435217, Freqtrade CI 30482435287 and zizmor 30482435054 succeeded on 72cdd4613bba59a02aa3ab7cac3c29774929b5d5.
blockers:
  - The real acceptance window requires 97 scheduled observations at least 900 seconds apart before independent terminal evaluation.
next_action: Observe scheduled short-lived Binance acceptance v3 sampler jobs through the single terminal evaluation, without rerun, retry, reopening PR 738 or reusing its request/run identities; then record the bounded artifact identity and accepted, rejected or inconclusive outcome.
```
