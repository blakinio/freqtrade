---
task_id: FTAI-20260728-market-data-binance-spot-instrument-shadow-acceptance-v1
status: validating
branch: fix/binance-spot-instrument-shadow-acceptance-runtime-v2
base_branch: develop
created: 2026-07-28
updated: 2026-07-29
related_pr: "#690"
owned_paths:
  - ai_platform/market_data/binance-spot-instrument-shadow-acceptance-policy-v1.json
  - ai_platform/market_data/binance_spot_instrument_acceptance.py
  - .github/workflows/ai-platform-binance-spot-instrument-shadow-acceptance-v2.yml
  - tools/market_data/binance_spot_instrument_acceptance_v2_preflight.py
  - tests/ai_platform_integration/test_market_data_binance_spot_instrument_acceptance_v2.py
  - docs/ai_platform/market_data/BINANCE_SPOT_INSTRUMENT_SHADOW_ACCEPTANCE_V2.md
  - docs/agents/tasks/FTAI-20260728-market-data-binance-spot-instrument-shadow-acceptance-v1.md
required_reads:
  - AGENTS.md
  - docs/agents/CONTEXT_HANDOFF.md
  - docs/ai_platform/market_data/BINANCE_SPOT_INSTRUMENT_SHADOW_ACCEPTANCE.md
  - docs/ai_platform/market_data/BINANCE_SPOT_INSTRUMENT_SHADOW_ACCEPTANCE_V2.md
search_first:
  - current status of PR 690 and exact-head CI
  - current changed-file scope and review threads for PR 690
optional_reads:
  - docs/ai_platform/LIQUIDATION_OKX_SHADOW_ACCEPTANCE_EXECUTION.md
---

# Binance Spot instrument shadow acceptance v1

## Context checkpoint

```yaml
checkpoint_version: 1
updated_at: 2026-07-29T15:46:00+02:00
head: 43205555c187af08a8d624191dbf44fce9543013
branch: fix/binance-spot-instrument-shadow-acceptance-runtime-v2
pr: "#690"
status: validating
context_routes:
  - Binance Spot public instrument-catalog acceptance
  - Synology self-hosted staging runner
  - credential-free deterministic evidence
owned_paths:
  - .github/workflows/ai-platform-binance-spot-instrument-shadow-acceptance-v2.yml
  - tools/market_data/binance_spot_instrument_acceptance_v2_preflight.py
  - tests/ai_platform_integration/test_market_data_binance_spot_instrument_acceptance_v2.py
  - docs/ai_platform/market_data/BINANCE_SPOT_INSTRUMENT_SHADOW_ACCEPTANCE_V2.md
  - docs/agents/tasks/FTAI-20260728-market-data-binance-spot-instrument-shadow-acceptance-v1.md
proven:
  - Original acceptance implementation remains merged as aeb858ebe5266742c257aa7b45b5cffd11c4b5ba with unchanged policy, transport, parser, thresholds, durable evidence and independent evaluator.
  - Replacement no-network proof workflow 30455561706 job 90588120948 completed success on exact runner freqtrade-synology-staging.
  - Consumed v1 trigger workflow 30456309522 failed before network because its isolated runtime lacked jsonschema; no observation or acceptance package was created and PR 687 was closed without merge.
  - PR 690 contains no request file and cannot trigger a Binance acceptance run.
  - The v2 workflow watches only ai_platform/market_data/run-requests/binance-spot-instrument-shadow-acceptance-20260729-v2.json on the opened event.
  - The v2 workflow retains exact runner, protected environment, durable root, public URL, 24-hour 97-slot schedule, zero retries, independent evaluation, bounded artifact upload and production-disabled zero-order boundary.
  - The v2 workflow installs and verifies jsonschema 4.26.0 before importing the acceptance package.
  - A standard-library-only preflight binds the new request_id and run_id, validates runner and storage identity, performs atomic durable I/O and rejects an existing run directory.
  - Focused tests cover exact-one-file routing, consumed-v1 exclusion, dependency ordering, bounded metadata upload, exact v2 identity, durable preflight and runner refusal.
  - The new request identity is binance-spot-instrument-shadow-acceptance-20260729-v2 with run identity binance-spot-instrument-shadow-acceptance-20260729-v2-r1.
derived:
  - The repair changes only workflow runtime and trigger identity; it does not change source-quality acceptance semantics.
  - A separate exact-merged-head no-network proof is still required before the v2 request may be created.
unknown:
  - Terminal exact-head CI and review outcome of PR 690.
  - Terminal outcome of the later no-network v2 proof.
  - Outcome of any later real v2 24-hour acceptance window.
conflicts: []
first_failure:
  marker: none
  evidence: No current PR 690 terminal failure is recorded; the historical v1 missing-jsonschema failure is preserved above.
rejected_hypotheses:
  - Modify or rerun the consumed v1 workflow and request identity.
  - Add the v2 canonical request to the runtime-repair PR.
  - Change the frozen policy, parser, thresholds or production-disabled boundary to repair an environment dependency.
  - Create the v2 trigger before exact-merged-head no-network proof success.
changed_paths:
  - .github/workflows/ai-platform-binance-spot-instrument-shadow-acceptance-v2.yml
  - tools/market_data/binance_spot_instrument_acceptance_v2_preflight.py
  - tests/ai_platform_integration/test_market_data_binance_spot_instrument_acceptance_v2.py
  - docs/ai_platform/market_data/BINANCE_SPOT_INSTRUMENT_SHADOW_ACCEPTANCE_V2.md
  - docs/agents/tasks/FTAI-20260728-market-data-binance-spot-instrument-shadow-acceptance-v1.md
validation:
  - command: GitHub compare develop...fix/binance-spot-instrument-shadow-acceptance-runtime-v2
    result: PASS
    evidence: Four pre-checkpoint commits add only the v2 workflow, preflight guard, focused tests and runtime-v2 documentation; no request file exists.
  - command: GitHub PR 690 metadata inspection
    result: PASS
    evidence: Open against develop with no canonical request and no authorization for a Binance network run.
blockers:
  - PR 690 requires exact-head CI, security validation and review-thread closure before merge.
  - Exact merged runtime v2 requires a separate no-network proof on freqtrade-synology-staging before any trigger.
next_action: Complete exact-head CI and guarded merge of PR 690 without adding a request file; then create a separate exact-one-workflow no-network proof against the merged repair and close that proof PR without merge before considering the v2 24-hour trigger.
```
