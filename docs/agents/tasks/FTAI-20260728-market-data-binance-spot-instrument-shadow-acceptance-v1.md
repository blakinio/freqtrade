---
task_id: FTAI-20260728-market-data-binance-spot-instrument-shadow-acceptance-v1
status: validating
branch: trigger/binance-v3-shadow-acceptance-20260729
base_branch: develop
created: 2026-07-28
updated: 2026-07-31
related_pr: "#738"
required_reads:
  - AGENTS.md
  - docs/agents/CONTEXT_HANDOFF.md
  - docs/ai_platform/market_data/BINANCE_SPOT_INSTRUMENT_SHADOW_ACCEPTANCE_V3.md
search_first:
  - workflow 30482434626 and initializer job 90679668485
  - cadence diagnostic workflow 30647694832 and job 91213062987
  - persistent sampler implementation PR 882 and deployment workflow 30662088662
---

# Binance Spot instrument shadow acceptance v1

## Context checkpoint

```yaml
checkpoint_version: 1
updated_at: 2026-07-31T22:22:00+02:00
head: 72cdd4613bba59a02aa3ab7cac3c29774929b5d5
branch: trigger/binance-v3-shadow-acceptance-20260729
pr: "#738"
status: validating
proven:
  - Exact-one-file trigger PR 738 initialized immutable run binance-spot-instrument-shadow-acceptance-20260729-v3-r1 and was closed without merge.
  - Read-only cadence diagnostic workflow 30647694832 job 91213062987 proved sparse GitHub schedule emission, shared-runner contention and pre-job concurrency cancellations.
  - Persistent sampler repair PR 882 passed AI Platform CI 30660990277, Freqtrade CI 30660989969 and workflow-security run 30660990016 at exact head 7892c6c026783614a6ecf1188b1167de93636d8e.
  - PR 882 merged to develop as b735a6c8cd3b5ac8340c61a0171aa1cde947a9b7.
  - Exact-one-file deployment request PR 885 at head 15e84526dc4206221747b05c589eba1c9bcab911 was consumed and closed without merge.
  - Deployment workflow 30662088662 job 91260465852 completed success on freqtrade-synology-staging.
  - Deployment artifact 8805675828 has digest sha256:07db6cb4ca51f4c88a5df97488cd9fe4377c7a9d8a12d5c179de0a9cbcce4c60.
  - Hardened container binance-v3-acceptance-sampler was healthy and advanced the same immutable run from sample index 24 to 25.
  - Deployment initialized no new run, reset or deleted no state, enabled no production or execution authority and submitted zero orders.
derived:
  - The cadence blocker is repaired by a persistent Synology loop that uses the existing file lock, enforced 900-second due time and single-attempt sampler while releasing the GitHub runner.
  - The old GitHub schedule may remain as a lock-protected fallback, but terminal progress no longer depends on its best-effort emissions or shared-runner availability.
unknown:
  - Terminal accepted, rejected or inconclusive outcome and exact completion time.
conflicts: []
first_failure:
  marker: BINANCE_ACCEPTANCE_SCHEDULER_CADENCE_UNRELIABLE
  evidence: Best-effort GitHub cron and a shared runner could not provide the required cadence; persistent local sampling is now deployed and verified.
rejected_hypotheses:
  - Restart, replace or reuse the immutable v3 acceptance run or its consumed identities.
  - Shorten the required 900-second interval or retry failed observations.
  - Enable production source access, execution, orders or live capital before terminal evaluation.
changed_paths:
  - ai_platform/market_data/binance_spot_instrument_acceptance_daemon.py
  - deploy/synology/binance-spot-instrument-acceptance/Dockerfile
  - deploy/synology/binance-spot-instrument-acceptance/compose.yaml
  - deploy/synology/binance-spot-instrument-acceptance/binance_acceptance_healthcheck.py
  - .github/workflows/ai-platform-binance-spot-instrument-persistent-sampler-deploy.yml
  - tests/ai_platform_integration/test_market_data_binance_spot_instrument_acceptance_daemon.py
  - docs/agents/tasks/FTAI-20260728-market-data-binance-spot-instrument-shadow-acceptance-v1.md
  - docs/agents/tasks/FTAI-20260731-market-data-binance-spot-instrument-persistent-sampler-repair-v1.md
validation:
  - command: Exact-head implementation CI for PR 882
    result: PASS
    evidence: AI Platform, full Freqtrade matrix and CI Gate, pre-commit, documentation and zizmor all succeeded.
  - command: Deployment workflow 30662088662 job 91260465852
    result: PASS
    evidence: Container health and real sample advancement 24 to 25 were proven in artifact 8805675828.
  - command: GitHub PR 885 terminal state
    result: PASS
    evidence: Exact-one-file operational request closed without merge after one successful deployment attempt.
blockers:
  - Seventy-two observations remained at deployment verification before terminal evaluation could occur.
next_action: Observe the deployed persistent sampler through completion of the same immutable 97-observation run, then verify and record the bounded terminal artifact identity and accepted, rejected or inconclusive outcome without rerun, retry, reopening PR 738 or reusing consumed identities.
```
