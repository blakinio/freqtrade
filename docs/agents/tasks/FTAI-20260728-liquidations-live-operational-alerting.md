---
task_id: FTAI-20260728-liquidations-live-operational-alerting
status: completed
branch: develop
base_branch: develop
created: 2026-07-28
updated: 2026-07-29
related_pr: 734
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
updated_at: 2026-07-29T19:07:13Z
head: d7fc27211e5e6391704d5db732fb7f72d267e6e6
branch: develop
pr: 734
status: completed
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
  - "Trusted run 30470845965 completed all control-plane, watchdog and Synology health jobs successfully and published liquidations-live-health=success with no collector-or-portal alerts."
  - "Repository Issues were enabled and the API channel was verified by creating and closing technical issue #728."
  - "PR #734 exact head 3df671d7cc0a5d1567889d474e8a41027fbf4cba passed Freqtrade CI 30481850336 including Documentation build and CI Gate, plus zizmor 30481852814, then merged as d7fc27211e5e6391704d5db732fb7f72d267e6e6."
  - "Run 30482051923 exercised the live fail-closed path while freqtrade-staging was occupied: the watchdog updated exact-title issue #729 with LIQUIDATIONS_HEALTH_RUNNER_UNAVAILABLE."
  - "After the runner became available, the trusted health job in run 30482051923 completed successfully, posted the recovery comment as github-actions[bot], closed issue #729 and published liquidations-live-health=success."
  - "The merge commit d7fc27211e5e6391704d5db732fb7f72d267e6e6 finished with both liquidations-live-synology=success and liquidations-live-health=success."
derived:
  - "The monitor observes collector data without giving the runner a writable host-data mount, mounting the Docker socket into a helper or modifying accepted evidence."
  - "Healthy checks publish terminal success and retain no artifact; unhealthy or unavailable-runner checks publish failure, retain bounded evidence where available and reconcile one exact-title GitHub alert."
  - "The complete alert lifecycle is now proven against the repository setting and workflow token: create/update on failure, recovery comment and automatic close on health."
unknown: []
conflicts: []
first_failure:
  marker: GITHUB_ISSUES_DISABLED
  status: resolved
  evidence: "Issues were enabled; issue #728 proved API availability and run 30482051923 proved workflow-token update and close permissions through issue #729."
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
  - command: "GitHub Issues API verification #728"
    result: PASS
    evidence: "The repository accepted creation and immediate closure of a technical verification issue after Issues were enabled."
  - command: "PR #734 exact-head CI"
    result: PASS
    evidence: "Freqtrade CI 30481850336 and zizmor 30481852814 succeeded on 3df671d7cc0a5d1567889d474e8a41027fbf4cba."
  - command: "Operational alert lifecycle run 30482051923"
    result: PASS
    evidence: "The watchdog updated issue #729 during runner unavailability; the later healthy job posted a recovery comment, closed the issue and published liquidations-live-health=success."
  - command: "Merge commit d7fc27211e5e6391704d5db732fb7f72d267e6e6 statuses"
    result: PASS
    evidence: "liquidations-live-synology and liquidations-live-health both published success."
blockers: []
follow_up:
  - "Consider narrowing the Liquidations Live Synology path filter so Markdown-only runbook changes under deploy/synology/liquid20 do not request a deployment."
next_action: null
```
