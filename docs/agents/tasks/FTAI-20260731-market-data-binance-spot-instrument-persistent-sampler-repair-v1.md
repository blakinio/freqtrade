---
task_id: FTAI-20260731-market-data-binance-spot-instrument-persistent-sampler-repair-v1
status: validating
branch: fix/binance-v3-persistent-sampler-20260731
base_branch: develop
created: 2026-07-31
updated: 2026-07-31
parent_task: FTAI-20260728-market-data-binance-spot-instrument-shadow-acceptance-v1
owned_paths:
  - ai_platform/market_data/binance_spot_instrument_acceptance_daemon.py
  - deploy/synology/binance-spot-instrument-acceptance/Dockerfile
  - deploy/synology/binance-spot-instrument-acceptance/compose.yaml
  - deploy/synology/binance-spot-instrument-acceptance/healthcheck.py
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
updated_at: 2026-07-31T21:50:00+02:00
head: 6c43481187d8e74c2e80aeebc178aabff1bbb75c
branch: fix/binance-v3-persistent-sampler-20260731
pr: null
status: validating
proven:
  - The immutable run binance-spot-instrument-shadow-acceptance-20260729-v3-r1 remains active and had 24 of 97 samples at 2026-07-31T21:19:13.991121+02:00.
  - GitHub emitted only 26 scheduled runs versus approximately 545 expected, with schedule gaps up to 12510 seconds.
  - One scheduled job waited approximately 7 hours 52 minutes for the shared runner and three pending runs were cancelled before job creation.
  - Existing incremental sampling uses a Linux file lock, enforces at least 900 seconds after the last completed observation and performs one attempt without retry.
  - The repository already uses a hardened persistent Synology container to solve the same scheduler and runner-occupancy failure class for WickHunter.
derived:
  - A local persistent loop can safely call the existing due-sample function because state locking and due-time enforcement remain authoritative.
  - A separate exact-one-file operational request is required after implementation merge to deploy the container without merging the request.
unknown:
  - Exact sample index when the deployment request reaches the trusted runner.
  - Terminal accepted, rejected or inconclusive outcome.
conflicts: []
first_failure:
  marker: BINANCE_ACCEPTANCE_SCHEDULER_CADENCE_UNRELIABLE
  evidence: Sparse GitHub schedule emission plus prolonged shared-runner contention cannot provide the required cadence.
rejected_hypotheses:
  - Restart or replace the immutable v3 acceptance run.
  - Shorten the required 900-second interval.
  - Retry missed or failed Binance observations.
  - Enable production, execution or order authority.
changed_paths:
  - ai_platform/market_data/binance_spot_instrument_acceptance_daemon.py
  - deploy/synology/binance-spot-instrument-acceptance/Dockerfile
  - deploy/synology/binance-spot-instrument-acceptance/compose.yaml
  - deploy/synology/binance-spot-instrument-acceptance/healthcheck.py
  - .github/workflows/ai-platform-binance-spot-instrument-persistent-sampler-deploy.yml
  - tests/ai_platform_integration/test_market_data_binance_spot_instrument_acceptance_daemon.py
  - docs/agents/tasks/FTAI-20260731-market-data-binance-spot-instrument-persistent-sampler-repair-v1.md
validation:
  - command: Python syntax compilation of daemon, healthcheck and focused tests
    result: PASS
    evidence: All authored Python files compile before repository CI.
blockers:
  - Implementation PR must pass exact-head CI before the operational deployment request is created.
next_action: Open the implementation PR, obtain green exact-head CI, merge it normally, then create one exact-file operational request PR that deploys the persistent sampler against the unchanged active v3 run and closes without merge after verified sample advancement.
```
