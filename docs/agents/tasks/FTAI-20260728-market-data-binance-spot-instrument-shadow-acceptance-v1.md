---
task_id: FTAI-20260728-market-data-binance-spot-instrument-shadow-acceptance-v1
status: completed
branch: trigger/binance-v3-shadow-acceptance-20260729
base_branch: develop
created: 2026-07-28
updated: 2026-08-01
related_pr: "#738"
required_reads:
  - AGENTS.md
  - docs/agents/CONTEXT_HANDOFF.md
  - docs/ai_platform/market_data/BINANCE_SPOT_INSTRUMENT_SHADOW_ACCEPTANCE_V3.md
search_first:
  - workflow 30482434626 and initializer job 90679668485
  - cadence diagnostic workflow 30647694832 and job 91213062987
  - persistent sampler implementation PR 882 and deployment workflow 30662088662
  - terminal observer workflow 30716415603 and job 91412606538
---

# Binance Spot instrument shadow acceptance v1

## Context checkpoint

```yaml
checkpoint_version: 1
updated_at: 2026-08-01T22:13:00+02:00
head: 72cdd4613bba59a02aa3ab7cac3c29774929b5d5
branch: trigger/binance-v3-shadow-acceptance-20260729
pr: "#738"
status: completed
proven:
  - Exact-one-file trigger PR 738 initialized immutable run binance-spot-instrument-shadow-acceptance-20260729-v3-r1 and was closed without merge.
  - Read-only cadence diagnostic workflow 30647694832 job 91213062987 proved sparse GitHub schedule emission, shared-runner contention and pre-job concurrency cancellations.
  - Persistent sampler repair PR 882 passed exact-head AI Platform CI 30660990277, Freqtrade CI 30660989969 and workflow-security run 30660990016, then merged to develop as b735a6c8cd3b5ac8340c61a0171aa1cde947a9b7.
  - Exact-one-file deployment request PR 885 was consumed and closed without merge after deployment workflow 30662088662 job 91260465852 completed success.
  - Deployment artifact 8805675828 has digest sha256:07db6cb4ca51f4c88a5df97488cd9fe4377c7a9d8a12d5c179de0a9cbcce4c60.
  - Hardened container binance-v3-acceptance-sampler advanced the unchanged immutable run with the enforced 900-second interval, file locking and one attempt per observation.
  - Exact-one-file terminal observer PR 966 at head af6d44db0a85e5c6e55264eb5165952edd94b2c9 was closed without merge after read-only workflow 30716415603 job 91412606538 completed success.
  - Terminal observer artifact 8823464359 has digest sha256:ee707fc119857ef58183d576eecf6ab0eb5960ac5e1ad79eae7a383aa03bcf83.
  - The immutable run completed all 97 of 97 observations at 2026-08-01T16:38:38.547630+02:00 with 97 successful samples, zero failed samples and availability ratio 1.0.
  - Independent terminal evaluation returned outcome accepted and every frozen gate passed.
  - Observed duration was 242618.547629444 seconds, exceeding the required 86400-second minimum.
  - Instrument count remained between 3669 and 3670, active instrument count between 1371 and 1380, and maximum consecutive catalog count change ratio was 0.0002725538293813028 against the 0.02 maximum.
  - Maximum response duration was 2792.085707 ms against the 15000 ms maximum and maximum response size was 6649842 bytes against the 16777216-byte maximum.
  - Terminal summary, manifest, report and checksum index are present and bounded by the observer evidence.
  - Observer SHA-256 values are summary c6d93d729536ccf76bb80fdf56bfbccb87f68a61266360b32d80f9fbbfbddf68, manifest 608b9b7853c0cce5b8aeda5b930b4264666a4587acb14cc9b5245ec9e9838278, report b909f466185e9585978ef3f2c3f3e4efb9ee4cedca1d4bc2b4ef624512a3617a and checksum index 3bb4903d4b6e1c5109fe61f3ddfbc40fc947ef2d0bf875997118672e91bb9d0c.
  - The accepted result keeps source_acceptance=false, production_source_enabled=false and orders_submitted=0.
derived:
  - The scheduler cadence defect was repaired without restarting, replacing or mutating the immutable acceptance identity.
  - The public Binance Spot instrument-catalog source passed the frozen shadow acceptance contract.
  - Accepted authorizes only a later separately reviewed integration proposal; it does not enable a production collector, source acceptance flag, execution, orders, trading authority or live capital.
unknown: []
conflicts: []
first_failure:
  marker: BINANCE_ACCEPTANCE_SCHEDULER_CADENCE_UNRELIABLE
  evidence: Best-effort GitHub cron and a shared runner could not provide the required cadence; the persistent local sampler repaired this and completed the same immutable run.
rejected_hypotheses:
  - Restart, replace or reuse the immutable v3 acceptance run or its consumed identities.
  - Shorten the required 900-second interval or retry failed observations.
  - Treat accepted as production enablement or trading authority.
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
    evidence: Container health and real sample advancement were proven in artifact 8805675828.
  - command: Terminal observer workflow 30716415603 job 91412606538
    result: PASS
    evidence: Artifact 8823464359 independently captured completed state, all four terminal files and accepted outcome without mutation or a Binance request.
  - command: GitHub PR 966 terminal state
    result: PASS
    evidence: Exact-one-file observer PR closed without merge after evidence capture.
blockers: []
next_action: Prepare a separately reviewed proposal for integrating the accepted public Binance Spot instrument-catalog source while preserving production, execution, order and live-capital authority as disabled until explicitly approved.
```
