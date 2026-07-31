---
task_id: FTAI-20260728-market-data-binance-spot-instrument-shadow-acceptance-v1
status: validating
branch: trigger/binance-v3-shadow-acceptance-20260729
base_branch: develop
created: 2026-07-28
updated: 2026-07-31
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
  - observer workflow 30645984529 and job 91207351730
  - scheduled AI Platform Binance Spot Instrument Shadow Acceptance V3 runs
optional_reads:
  - docs/ai_platform/market_data/BINANCE_SPOT_INSTRUMENT_SHADOW_ACCEPTANCE_V2.md
---

# Binance Spot instrument shadow acceptance v1

## Context checkpoint

```yaml
checkpoint_version: 1
updated_at: 2026-07-31T18:12:00+02:00
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
  - PR 738 was closed without merge after successful initialization and the frozen identities were not reused.
  - Consumed v2 PR 699, workflow 30459738848 and v2 request/run identities remain forbidden from rerun or reuse.
  - Read-only observer PR 871 at head 35e6995638b9b20ba3b658e6ec6eedce1443c441 changed exactly one temporary workflow file and was closed without merge.
  - Observer workflow 30645984529 job 91207351730 completed success without a Binance request or durable-state mutation.
  - Observer artifact 8799420811 has digest sha256:bb9a1d18897890c5dce4484ac9eb95672e350e5d2a3146e5b6529f2e904ca333.
  - Durable run binance-spot-instrument-shadow-acceptance-20260729-v3-r1 remained active with 21 completed sample reports, next_sample_index 21 and expected_sample_count 97.
  - The window started at 2026-07-29T21:15:00+02:00 and the latest completed sample was recorded at 2026-07-31T16:36:52.657754+02:00.
  - Terminal summary, manifest, report and checksum files were absent; source_acceptance=false, production_source_enabled=false and orders_submitted=0.
derived:
  - The canonical real v3 attempt is alive but substantially behind the nominal 15-minute observation cadence.
  - Initializer or observer success is not Binance source acceptance and authorizes no production, execution, research, replay, orders or live capital.
unknown:
  - Cause of the missed scheduled sampling opportunities and future effective sampling cadence.
  - Terminal accepted, rejected or inconclusive outcome and completion time of the 97-observation window.
conflicts: []
first_failure:
  marker: BINANCE_ACCEPTANCE_RUNNER_MONOPOLIZATION
  evidence: Runtime v2 held the single self-hosted runner inside one 24-hour job and was cancelled before terminal evaluation; runtime v3 removes that architecture, but current v3 scheduled sampling is progressing slower than nominal.
rejected_hypotheses:
  - Treat initializer success, no-network proof or observer success as real source acceptance.
  - Treat the stale repository checkpoint as proof that the durable run stopped.
  - Rerun, reopen or reuse consumed v2 or v3 trigger identities.
  - Merge the exact-one-file trigger or observer PR.
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
  - command: Read-only observer workflow 30645984529 job 91207351730
    result: PASS
    evidence: Bounded artifact 8799420811 independently recorded active durable state at 21 of 97 samples with no terminal files and all production/order authority false.
  - command: GitHub PR 871 terminal state
    result: PASS
    evidence: Exact-one-file temporary observer closed without merge after evidence capture.
blockers:
  - Seventy-six scheduled observations remain and the cause of the slower-than-nominal cadence is not yet proven.
next_action: Re-observe the same immutable durable v3 run after scheduled sampling advances, without rerun, retry, reopening PR 738 or reusing its identities; when state becomes completed, verify and record the bounded terminal artifact identity and accepted, rejected or inconclusive outcome.
```
