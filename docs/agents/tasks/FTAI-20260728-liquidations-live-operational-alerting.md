---
task_id: FTAI-20260728-liquidations-live-operational-alerting
status: blocked
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
  - ai_platform/scripts/liquidation_portal_health.py
  - ai_platform/scripts/liquidation_live_operational_health.py
  - tests/ai_platform_integration/test_liquidation_live_health.py
  - tests/ai_platform_integration/test_liquidation_portal_health.py
---

# FTAI-20260728-liquidations-live-operational-alerting

Provide autonomous fail-closed monitoring for both the completed Synology Liquid20 collector and the production portal read path without modifying collector data, accepted historical evidence, production authentication or trading state.

## Context checkpoint

```yaml
checkpoint_version: 1
updated_at: 2026-07-29T16:31:00Z
head: 182a54d175f63b08e7c481e82bb0b35d8e75771f
branch: develop
pr: 717
status: blocked
context_routes:
  - docs/agents/tasks/FTAI-20260728-liquidations-live-operational-alerting.md
  - .github/workflows/liquidations-live-operational-health.yml
  - ai_platform/scripts/liquidation_live_health.py
  - ai_platform/scripts/liquidation_portal_health.py
  - ai_platform/scripts/liquidation_live_operational_health.py
  - deploy/synology/liquid20/LIVE_STREAM.md
  - tests/ai_platform_integration/test_liquidation_live_health.py
  - tests/ai_platform_integration/test_liquidation_portal_health.py
owned_paths:
  - .github/workflows/liquidations-live-operational-health.yml
  - ai_platform/scripts/liquidation_live_health.py
  - ai_platform/scripts/liquidation_portal_health.py
  - ai_platform/scripts/liquidation_live_operational_health.py
  - deploy/synology/liquid20/LIVE_STREAM.md
  - tests/ai_platform_integration/test_liquidation_live_health.py
  - tests/ai_platform_integration/test_liquidation_portal_health.py
  - docs/agents/tasks/FTAI-20260728-liquidations-live-operational-alerting.md
proven:
  - "PR #578 merged the recurring five-minute collector monitor, fail-closed workflow result, failure-only evidence retention and deduplicated GitHub Issue lifecycle."
  - "PR #594 merged the production portal read-path proof while preserving exact SESSION_MISSING authentication, read-only Liquid20 data and isolated candidate security boundaries."
  - "PR #689 registered Liquidations Live Health under .github/workflows/liquidations-live-operational-health.yml on the default develop branch."
  - "PR #702 merged the GitHub-hosted pending status publisher and bounded freqtrade-staging assignment watchdog, so runner unavailability publishes terminal failure independently of Synology."
  - "PR #710 merged pinned Python 3.13 setup for freqtrade-staging and resilient best-effort Issue reconciliation as develop commit 833f0be980a8c7fedc42fa9d1265d4833e041bb4."
  - "Exact PR #710 head 98516a1f3d885cb0fc03d801633c96c6cd223ece passed Freqtrade CI 30466181375 and zizmor 30466181388."
  - "PR #717 merged read-only collector-container observation of live state and disk capacity as develop commit 182a54d175f63b08e7c481e82bb0b35d8e75771f."
  - "Exact PR #717 head 673165ada1be097b58dbef033edafc0ff4bd22c3 passed AI Platform CI 30469427788, Freqtrade CI 30469428405 and zizmor 30469427983."
  - "Trusted production run 30470845965 completed the control-plane publisher, runner watchdog and Synology collector-and-portal health job successfully."
  - "Run 30470845965 reported healthy collector state, collector-container data observation, 23.076 percent disk usage, connected Binance USDM and Bybit Linear sources, portal LIVE mode, production page 200 and protected health 401 SESSION_MISSING."
  - "Develop commit 182a54d175f63b08e7c481e82bb0b35d8e75771f has terminal liquidations-live-health status success targeting run 30470845965."
  - "Healthy run 30470845965 produced no alerts and skipped failure-only evidence upload."
derived:
  - "The monitor is autonomous on push, workflow_dispatch and a five-minute schedule, with the trusted collector and portal check confined to freqtrade-staging."
  - "The classic commit status is the authoritative fail-closed signal even when the optional GitHub Issue channel is unavailable."
  - "No unattended production portal session, writable Liquid20 mount, Docker socket mount or trading-state mutation is required."
unknown: []
conflicts: []
first_failure:
  marker: GITHUB_ISSUES_DISABLED
  evidence: "Production watchdog run 30461651652 received HTTP 410 while reconciling the operational alert, and PR #717 records that GitHub Issues are disabled for this repository."
rejected_hypotheses:
  - "Store or fabricate a real production portal session."
  - "Enable fixture identity in production or weaken exact 401 SESSION_MISSING authentication."
  - "Mount Liquid20 writable, expose the Docker socket or restart production as part of monitoring."
  - "Upload artifacts for healthy five-minute checks."
  - "Treat an absent self-hosted job as healthy or wait indefinitely for freqtrade-staging."
changed_paths:
  - .github/workflows/liquidations-live-operational-health.yml
  - ai_platform/scripts/liquidation_live_health.py
  - ai_platform/scripts/liquidation_portal_health.py
  - ai_platform/scripts/liquidation_live_operational_health.py
  - deploy/synology/liquid20/LIVE_STREAM.md
  - tests/ai_platform_integration/test_liquidation_live_health.py
  - tests/ai_platform_integration/test_liquidation_portal_health.py
  - docs/agents/tasks/FTAI-20260728-liquidations-live-operational-alerting.md
validation:
  - command: "PR #710 exact-head repository and workflow-security validation"
    result: PASS
    evidence: "Freqtrade CI 30466181375 and zizmor 30466181388 succeeded on 98516a1f3d885cb0fc03d801633c96c6cd223ece."
  - command: "PR #717 exact-head platform, repository and workflow-security validation"
    result: PASS
    evidence: "AI Platform CI 30469427788, Freqtrade CI 30469428405 and zizmor 30469427983 succeeded on 673165ada1be097b58dbef033edafc0ff4bd22c3."
  - command: "Liquidations Live Health production run 30470845965"
    result: PASS
    evidence: "Control-plane status publication, freqtrade-staging assignment watchdog, Python setup, collector-and-portal check, summary, final status and healthy-result enforcement all succeeded."
  - command: "Combined health report from run 30470845965"
    result: PASS
    evidence: "Report schema version 2 returned healthy true with no alerts; collector, data observation, disk, sources, portal and safety checks were healthy."
  - command: "Classic commit status on develop 182a54d175f63b08e7c481e82bb0b35d8e75771f"
    result: PASS
    evidence: "liquidations-live-health is terminal success and targets run 30470845965."
blockers:
  - "GitHub Issues are disabled for blakinio/freqtrade, so unhealthy runs cannot create, update or close the optional deduplicated operational Issue until that repository setting is enabled; fail-closed commit status publication remains operational."
next_action: "Enable GitHub Issues in the blakinio/freqtrade repository settings; no code or Synology change is required, and the next unhealthy run will use the already-tested deduplicated Issue lifecycle while commit status remains authoritative."
```
