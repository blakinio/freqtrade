---
task_id: FTAI-20260728-liquidations-live-operational-alerting
status: validating
branch: develop
base_branch: develop
created: 2026-07-28
updated: 2026-07-29
related_pr: 717
required_reads:
  - docs/agents/tasks/FTAI-20260727-liquidations-live-stream-repair.md
  - docs/agents/tasks/FTAI-20260727-liquidations-live-portal-synology-proof.md
  - deploy/synology/liquid20/LIVE_STREAM.md
search_first:
  - .github/workflows/liquidations-live-operational-health.yml
  - ai_platform/scripts/liquidation_live_health.py
  - ai_platform/scripts/liquidation_operational_health.py
  - ai_platform/scripts/liquidation_portal_health.py
  - tests/ai_platform_integration/test_liquidation_live_health.py
  - tests/ai_platform_integration/test_liquidation_operational_health.py
  - tests/ai_platform_integration/test_liquidation_portal_health.py
---

# FTAI-20260728-liquidations-live-operational-alerting

Provide autonomous fail-closed monitoring for both the completed Synology Liquid20 collector and the production portal read path without modifying collector data, accepted historical evidence, production authentication or trading state.

## Context checkpoint

```yaml
checkpoint_version: 1
updated_at: 2026-07-29T16:32:00Z
head: 182a54d175f63b08e7c481e82bb0b35d8e75771f
branch: develop
pr: 717
status: validating
context_routes:
  - docs/agents/tasks/FTAI-20260728-liquidations-live-operational-alerting.md
  - .github/workflows/liquidations-live-operational-health.yml
  - ai_platform/scripts/liquidation_live_health.py
  - ai_platform/scripts/liquidation_operational_health.py
  - ai_platform/scripts/liquidation_portal_health.py
  - deploy/synology/liquid20/LIVE_STREAM.md
  - tests/ai_platform_integration/test_liquidation_live_health.py
  - tests/ai_platform_integration/test_liquidation_operational_health.py
  - tests/ai_platform_integration/test_liquidation_portal_health.py
owned_paths:
  - .github/workflows/liquidations-live-operational-health.yml
  - ai_platform/scripts/liquidation_portal_health.py
  - ai_platform/scripts/liquidation_operational_health.py
  - deploy/synology/liquid20/LIVE_STREAM.md
  - tests/ai_platform_integration/test_liquidation_live_health.py
  - tests/ai_platform_integration/test_liquidation_operational_health.py
  - tests/ai_platform_integration/test_liquidation_portal_health.py
  - docs/agents/tasks/FTAI-20260728-liquidations-live-operational-alerting.md
proven:
  - "PR #594 merged the combined collector and portal monitor, exact production authentication boundary, isolated exact-image protected API proof, deduplicated alert lifecycle and failure-only evidence retention."
  - "PR #689 registered Liquidations Live Health on develop with push, five-minute schedule and workflow_dispatch triggers."
  - "PR #710 exact head 98516a1f3d885cb0fc03d801633c96c6cd223ece passed Freqtrade CI 30466181375 and zizmor 30466181388, then merged as 833f0be980a8c7fedc42fa9d1265d4833e041bb4."
  - "Run 30467670280 proved the freqtrade-synology-staging runner and pinned Python runtime worked; portal proof was LIVE with production page 200, protected API 401 SESSION_MISSING and healthy connected Bybit/Binance sources."
  - "PR #717 changed collector state and disk observation to a read-only Python process inside liquid20-live after validating the exact /volume1/docker/freqtrade-liquidations/data bind mount."
  - "PR #717 exact head 673165ada1be097b58dbef033edafc0ff4bd22c3 passed AI Platform CI 30469427788, Freqtrade CI 30469428405 including Python 3.11-3.14, coverage, distributions and CI Gate, plus zizmor 30469427983 with zero review threads."
  - "PR #717 merged with expected-head protection as 182a54d175f63b08e7c481e82bb0b35d8e75771f."
  - "Trusted run 30470845965 completed all control-plane, watchdog and Synology health jobs successfully and published liquidations-live-health=success on 182a54d175f63b08e7c481e82bb0b35d8e75771f."
  - "Run 30470845965 reported no alerts, active healthy collector state, healthy validated container observation, 23.076 percent disk use with 2.95 TB free, portal LIVE, production page 200, protected API 401 SESSION_MISSING, and healthy connected Binance/Bybit sources."
derived:
  - "The monitor now observes collector data without giving the runner a writable host-data mount, restarting production, mounting the Docker socket into a helper or modifying accepted evidence."
  - "Healthy five-minute checks publish terminal commit status and retain no artifact; unhealthy checks remain fail-closed and retain bounded evidence."
unknown:
  - "Whether the workflow can create or update the exact-title GitHub alert issue during a real failure while repository Issues remain disabled."
conflicts: []
first_failure:
  marker: GITHUB_ISSUES_DISABLED
  evidence: "Run 30467670280 received GitHub Issues API HTTP 410 with 'Issues has been disabled in this repository'; the available connector cannot change that repository setting."
rejected_hypotheses:
  - "Store or fabricate a real production portal session."
  - "Enable fixture identity in the production portal or weaken SESSION_MISSING."
  - "Mount Liquid20 writable, restart production or alter accepted evidence as part of monitoring."
  - "Treat a healthy portal proof alone as sufficient without collector state and disk evidence."
changed_paths:
  - .github/workflows/liquidations-live-operational-health.yml
  - ai_platform/scripts/liquidation_portal_health.py
  - ai_platform/scripts/liquidation_operational_health.py
  - deploy/synology/liquid20/LIVE_STREAM.md
  - tests/ai_platform_integration/test_liquidation_live_health.py
  - tests/ai_platform_integration/test_liquidation_operational_health.py
  - tests/ai_platform_integration/test_liquidation_portal_health.py
  - docs/agents/tasks/FTAI-20260728-liquidations-live-operational-alerting.md
validation:
  - command: "PR #710 exact-head CI"
    result: PASS
    evidence: "Freqtrade CI 30466181375 and zizmor 30466181388 succeeded on 98516a1f3d885cb0fc03d801633c96c6cd223ece."
  - command: "PR #717 exact-head CI"
    result: PASS
    evidence: "AI Platform CI 30469427788, Freqtrade CI 30469428405 and zizmor 30469427983 succeeded on 673165ada1be097b58dbef033edafc0ff4bd22c3."
  - command: "Liquidations Live Health 30470845965"
    result: PASS
    evidence: "All jobs succeeded and liquidations-live-health published success with zero collector-or-portal alerts."
blockers:
  - marker: GITHUB_ISSUES_DISABLED
    evidence: "The monitor is operational and healthy, but its deduplicated GitHub Issue alert channel cannot be exercised until Issues are enabled for blakinio/freqtrade."
next_action: "Enable GitHub Issues for blakinio/freqtrade, then verify the next Liquidations Live Health failure can reconcile the exact-title alert issue without changing collector or portal production state to force a failure."
```
