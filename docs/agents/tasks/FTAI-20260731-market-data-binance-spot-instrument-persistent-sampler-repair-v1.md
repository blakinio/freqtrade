---
task_id: FTAI-20260731-market-data-binance-spot-instrument-persistent-sampler-repair-v1
status: completed
branch: fix/binance-v3-persistent-sampler-20260731
base_branch: develop
created: 2026-07-31
updated: 2026-07-31
parent_task: FTAI-20260728-market-data-binance-spot-instrument-shadow-acceptance-v1
owned_paths:
  - ai_platform/market_data/binance_spot_instrument_acceptance_daemon.py
  - deploy/synology/binance-spot-instrument-acceptance/Dockerfile
  - deploy/synology/binance-spot-instrument-acceptance/compose.yaml
  - deploy/synology/binance-spot-instrument-acceptance/binance_acceptance_healthcheck.py
  - .github/workflows/ai-platform-binance-spot-instrument-persistent-sampler-deploy.yml
  - tests/ai_platform_integration/test_market_data_binance_spot_instrument_acceptance_daemon.py
  - docs/agents/tasks/FTAI-20260731-market-data-binance-spot-instrument-persistent-sampler-repair-v1.md
---

# Binance v3 persistent sampler cadence repair

## Goal

Replace dependence on best-effort GitHub cron and the shared self-hosted runner with a hardened persistent Synology sampler that advances the existing immutable Binance v3 acceptance run at its enforced 900-second cadence.

## Safety boundary

The repair must not initialize a new acceptance run, reset or delete durable state, reuse PR 738 identities, submit orders, enable production source access, authorize execution, replay, model training, strategy research or live capital.

## Context checkpoint

```yaml
checkpoint_version: 1
updated_at: 2026-07-31T22:22:00+02:00
head: b735a6c8cd3b5ac8340c61a0171aa1cde947a9b7
branch: fix/binance-v3-persistent-sampler-20260731
pr: "#882"
status: completed
proven:
  - PR 882 implemented a persistent Synology sampler that reuses the existing locked, due-time-enforced and single-attempt incremental sampling function.
  - The container is non-root, read-only, drops all capabilities, exposes no ports and keeps production, execution and order authority disabled.
  - Exact-head AI Platform CI 30660990277, Freqtrade CI 30660989969 and workflow-security run 30660990016 completed success.
  - PR 882 merged to develop as b735a6c8cd3b5ac8340c61a0171aa1cde947a9b7.
  - Exact-one-file deployment request PR 885 at head 15e84526dc4206221747b05c589eba1c9bcab911 was closed without merge.
  - Deployment workflow 30662088662 job 91260465852 completed success on freqtrade-synology-staging.
  - Deployment artifact 8805675828 has digest sha256:07db6cb4ca51f4c88a5df97488cd9fe4377c7a9d8a12d5c179de0a9cbcce4c60.
  - Container binance-v3-acceptance-sampler was healthy and advanced immutable run binance-spot-instrument-shadow-acceptance-20260729-v3-r1 from sample index 24 to 25.
  - No new run was initialized, no durable state was reset or deleted and zero orders were submitted.
derived:
  - The cadence repair is deployed and no longer depends on GitHub schedule emission or availability of the shared runner for each sample.
  - Existing file locking makes any residual scheduled workflow a serialized fallback rather than the primary cadence source.
unknown:
  - Terminal outcome of the parent 97-observation acceptance run.
conflicts: []
first_failure:
  marker: BINANCE_ACCEPTANCE_SCHEDULER_CADENCE_UNRELIABLE
  evidence: Sparse GitHub schedule emission and shared-runner contention were replaced by a verified persistent local sampler.
rejected_hypotheses:
  - Restart or replace the immutable acceptance run.
  - Shorten the 900-second interval or add observation retries.
  - Enable production, execution, orders or live capital.
changed_paths:
  - ai_platform/market_data/binance_spot_instrument_acceptance_daemon.py
  - deploy/synology/binance-spot-instrument-acceptance/Dockerfile
  - deploy/synology/binance-spot-instrument-acceptance/compose.yaml
  - deploy/synology/binance-spot-instrument-acceptance/binance_acceptance_healthcheck.py
  - .github/workflows/ai-platform-binance-spot-instrument-persistent-sampler-deploy.yml
  - tests/ai_platform_integration/test_market_data_binance_spot_instrument_acceptance_daemon.py
  - docs/agents/tasks/FTAI-20260731-market-data-binance-spot-instrument-persistent-sampler-repair-v1.md
validation:
  - command: Exact-head implementation CI for 7892c6c026783614a6ecf1188b1167de93636d8e
    result: PASS
    evidence: AI Platform tests and lint, full Freqtrade matrix and CI Gate, pre-commit, documentation and zizmor succeeded.
  - command: Deployment workflow 30662088662 job 91260465852
    result: PASS
    evidence: Artifact 8805675828 proves healthy deployment and real sample advancement 24 to 25.
  - command: GitHub PR 885 terminal state
    result: PASS
    evidence: Operational request closed without merge after its one authorized deployment attempt.
blockers: []
next_action: Continue the parent acceptance task from its deployed persistent sampler and record the terminal artifact and outcome when the immutable run completes.
```
