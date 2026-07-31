---
task_id: FTAI-20260731-wickhunter-okx-market-evidence-v2
status: in_progress
branch: agent/wickhunter-okx-market-evidence-v2
base_branch: develop
created: 2026-07-31
updated: 2026-07-31
related_pr: 836
depends_on:
  - FTAI-20260731-wickhunter-market-evidence-recovery-v1
  - merged production Market Evidence v1 implementation
  - merged public OKX Liquid20 source implementation
owned_paths:
  - .github/workflows/ai-platform-wickhunter-market-evidence-ci.yml
  - .github/workflows/ai-platform-wickhunter-production-market-evidence-v2.yml
  - ai_platform/wickhunter/production-market-evidence-contract-v2.json
  - ai_platform/wickhunter/production_market_evidence_v2.py
  - ai_platform/wickhunter/production_market_evidence_service_v2.py
  - ai_platform/wickhunter/production_market_evidence_daemon_v2.py
  - ai_platform/wickhunter/policies/wickhunter-production-market-evidence-wh01-policy-v2.json
  - ai_platform/wickhunter/ruff.toml
  - ai_platform/portal/web/lib/market-evidence/contracts.ts
  - ai_platform/portal/web/lib/market-evidence/reader-v2.ts
  - ai_platform/portal/web/lib/market-evidence/index.ts
  - deploy/synology/wickhunter-market-evidence-v2/Dockerfile
  - deploy/synology/wickhunter-market-evidence-v2/compose.yaml
  - deploy/synology/wickhunter-market-evidence-v2/healthcheck_v2.py
  - tests/ai_platform_integration/test_wickhunter_production_market_evidence_v2.py
  - tests/ai_platform_integration/test_wickhunter_production_market_evidence_service_v2.py
  - docs/agents/tasks/FTAI-20260731-wickhunter-okx-market-evidence-v2.md
required_reads:
  - AGENTS.md
  - docs/agents/CONTEXT_HANDOFF.md
  - docs/agents/tasks/FTAI-20260731-wickhunter-market-evidence-recovery-v1.md
  - docs/ai_platform/WICKHUNTER_PRODUCTION_MARKET_EVIDENCE.md
  - docs/ai_platform/portal/MARKET_EVIDENCE_READ_MODEL.md
---

# WickHunter OKX Market Evidence v2

## Goal

Add a backward-compatible three-source Market Evidence path for `bybit-linear`, `binance-usdm` and `okx-swap` without changing or reusing the immutable v1 request in PR #816.

## Implemented scope

- versioned v2 request and evidence contract;
- public-only OKX SWAP instrument, ticker and completed 5m candle normalization;
- exact coverage, pagination, stale/conflict, gap, credential, proxy, redirect, private endpoint, overwrite, traversal and symlink refusal;
- persistent immutable OKX supplement and verified merge with the two-source v1 package;
- Portal OKX status derived only from accepted v2 rows;
- hardened Synology daemon, image, Compose service and exact-one-file deployment trigger;
- focused backend, tamper, Portal and deployment CI.

## Safety boundary

The v2 package intentionally remains `WH-01 BLOCKED` with `LIQUIDATION_ARCHIVE_NOT_BOUND`. Archive binding and materialization are a separate package. Credentials, private/account/order endpoints, proxy routing, replay, training, performance research, execution, orders and live capital remain forbidden.

## Context checkpoint

```yaml
checkpoint_version: 1
updated_at: 2026-07-31T01:47:00+02:00
head: d07f9cd49128e9345256fdd8c4d593c7d33be12a
branch: agent/wickhunter-okx-market-evidence-v2
pr: 836
status: validating
context_routes:
  - AGENTS.md
  - docs/agents/CONTEXT_HANDOFF.md
  - docs/agents/tasks/FTAI-20260731-wickhunter-market-evidence-recovery-v1.md
  - docs/agents/tasks/FTAI-20260731-wickhunter-okx-market-evidence-v2.md
owned_paths:
  - .github/workflows/ai-platform-wickhunter-market-evidence-ci.yml
  - .github/workflows/ai-platform-wickhunter-production-market-evidence-v2.yml
  - ai_platform/wickhunter/production-market-evidence-contract-v2.json
  - ai_platform/wickhunter/production_market_evidence_v2.py
  - ai_platform/wickhunter/production_market_evidence_service_v2.py
  - ai_platform/wickhunter/production_market_evidence_daemon_v2.py
  - ai_platform/wickhunter/policies/wickhunter-production-market-evidence-wh01-policy-v2.json
  - ai_platform/wickhunter/ruff.toml
  - ai_platform/portal/web/lib/market-evidence/contracts.ts
  - ai_platform/portal/web/lib/market-evidence/reader-v2.ts
  - ai_platform/portal/web/lib/market-evidence/index.ts
  - deploy/synology/wickhunter-market-evidence-v2/Dockerfile
  - deploy/synology/wickhunter-market-evidence-v2/compose.yaml
  - deploy/synology/wickhunter-market-evidence-v2/healthcheck_v2.py
  - tests/ai_platform_integration/test_wickhunter_production_market_evidence_v2.py
  - tests/ai_platform_integration/test_wickhunter_production_market_evidence_service_v2.py
  - docs/agents/tasks/FTAI-20260731-wickhunter-okx-market-evidence-v2.md
proven:
  - PR 816 and all v1 identities remain unchanged and two-source only.
  - OKX evidence requires verified public instruments, tickers and confirm equal to 1 candles.
  - The combined package keeps LIQUIDATION_ARCHIVE_NOT_BOUND until a separate binding is verified.
  - Portal OKX availability is derived from accepted v2 rows and remains unavailable without them.
  - The duplicate v1 and v2 healthcheck module name was removed by assigning the v2 file a unique module name.
derived:
  - The accepted Bybit and Binance package can remain the immutable base while OKX is captured prospectively over matching geometry.
unknown:
  - Exact-head terminal workflow conclusions after the healthcheck correction.
  - Terminal Synology artifact identities for the future request-only run.
conflicts: []
first_failure:
  marker: OKX_CANDLE_EVIDENCE_NOT_CONFIGURED
  evidence: develop has no accepted three-source package and therefore truthfully excludes OKX.
rejected_hypotheses:
  - Mutate or reuse PR 816.
  - Treat OKX liquidation connectivity as candle evidence.
  - Clear Portal blockers before immutable evidence exists.
  - Add credentials, private endpoints, proxy routing or synthetic fallback.
changed_paths:
  - .github/workflows/ai-platform-wickhunter-market-evidence-ci.yml
  - .github/workflows/ai-platform-wickhunter-production-market-evidence-v2.yml
  - ai_platform/wickhunter/production-market-evidence-contract-v2.json
  - ai_platform/wickhunter/production_market_evidence_v2.py
  - ai_platform/wickhunter/production_market_evidence_service_v2.py
  - ai_platform/wickhunter/production_market_evidence_daemon_v2.py
  - ai_platform/wickhunter/policies/wickhunter-production-market-evidence-wh01-policy-v2.json
  - ai_platform/wickhunter/ruff.toml
  - ai_platform/portal/web/lib/market-evidence/contracts.ts
  - ai_platform/portal/web/lib/market-evidence/reader-v2.ts
  - ai_platform/portal/web/lib/market-evidence/index.ts
  - deploy/synology/wickhunter-market-evidence-v2/Dockerfile
  - deploy/synology/wickhunter-market-evidence-v2/compose.yaml
  - deploy/synology/wickhunter-market-evidence-v2/healthcheck_v2.py
  - tests/ai_platform_integration/test_wickhunter_production_market_evidence_v2.py
  - tests/ai_platform_integration/test_wickhunter_production_market_evidence_service_v2.py
  - docs/agents/tasks/FTAI-20260731-wickhunter-okx-market-evidence-v2.md
validation:
  - command: dedicated Market Evidence CI before healthcheck rename
    result: PASS
    evidence: backend, Portal and deployment jobs passed on head 38d8bc0dd4d1465de015fd2dfa402231aa73fa0e.
  - command: exact-head CI after healthcheck rename
    result: NOT_RUN
    evidence: workflows are pending for the latest branch head.
blockers:
  - PR 836 must pass exact-head CI and merge before the request-only production trigger opens.
next_action: Validate exact-head CI on PR 836, merge normally, then open the exact-one-file prospective v2 request PR before decision_start_ms 1785477600000.
```
