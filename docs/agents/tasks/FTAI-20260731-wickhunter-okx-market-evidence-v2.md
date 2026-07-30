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
  - deploy/synology/wickhunter-market-evidence-v2/healthcheck.py
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
- explicit completed-candle, response-receipt and availability semantics;
- deterministic exact coverage, pagination, stale/conflict and gap refusal;
- credential, proxy, redirect, private endpoint, overwrite, traversal and symlink refusal;
- persistent no-overwrite OKX supplement lifecycle;
- verified immutable merge with the accepted two-source v1 package;
- source-package binding digest and full artifact checksums;
- Portal OKX status and instruments derived only from accepted v2 rows;
- hardened Synology daemon, image, Compose service and exact-one-file deployment trigger;
- backend normalization, persistence, merge and tamper tests;
- dedicated CI that compiles, tests, lints and validates the complete v1 and v2 path.

## Safety boundary

The v2 package intentionally remains `WH-01 BLOCKED` with `LIQUIDATION_ARCHIVE_NOT_BOUND`. Archive binding and dataset materialization belong to a separate focused package. No credentials, private/account/order endpoints, proxy routing, replay, training, performance research, execution, orders or live capital are authorized.

## Acceptance

- v1 request, package and PR #816 remain unchanged;
- exact-head repository CI passes;
- PR review threads are resolved;
- the mergeable implementation is merged normally;
- a separate exact-one-file request-only PR starts the prospective OKX capture before the frozen decision interval;
- request-only PR is never merged.

## Context checkpoint

```yaml
checkpoint_version: 1
updated_at: 2026-07-31T02:08:00+02:00
head: bf69b0e8b205cd4ba459f2fdb8e93f170e654716
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
  - deploy/synology/wickhunter-market-evidence-v2/healthcheck.py
  - tests/ai_platform_integration/test_wickhunter_production_market_evidence_v2.py
  - tests/ai_platform_integration/test_wickhunter_production_market_evidence_service_v2.py
  - docs/agents/tasks/FTAI-20260731-wickhunter-okx-market-evidence-v2.md
proven:
  - PR 816 and all v1 identities remain unchanged and two-source only.
  - Public OKX normalization requires live USDT-linear SWAP contracts and confirm equal to 1 candles.
  - A verified OKX supplement can be merged with a separately verified v1 package without mutating either input.
  - Portal OKX eligibility is derived from accepted v2 package rows and remains unavailable when those rows do not exist.
  - The combined package retains LIQUIDATION_ARCHIVE_NOT_BOUND until a separate binding is verified.
  - Synology deployment is exact-one-file, public-only, credential-free and persistent-container based.
  - Dedicated CI executes v2 normalization, persistence, merge, tamper and deployment checks.
derived:
  - The existing Bybit and Binance capture can remain the immutable base package while OKX is captured prospectively over the same frozen geometry.
unknown:
  - Terminal exact-head workflow conclusions for the latest PR head.
  - Terminal Synology artifact identities for the future request-only run.
conflicts: []
first_failure:
  marker: OKX_CANDLE_EVIDENCE_NOT_CONFIGURED
  evidence: Current develop Portal reader excludes OKX because no accepted three-source package exists.
rejected_hypotheses:
  - Mutate or reuse PR 816.
  - Treat OKX liquidation connectivity as candle evidence.
  - Clear Portal blockers before immutable evidence exists.
  - Add private endpoints, credentials, proxy routing or synthetic fallback.
  - Accept CI that triggers on v2 files but executes only the v1 test set.
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
  - deploy/synology/wickhunter-market-evidence-v2/healthcheck.py
  - tests/ai_platform_integration/test_wickhunter_production_market_evidence_v2.py
  - tests/ai_platform_integration/test_wickhunter_production_market_evidence_service_v2.py
  - docs/agents/tasks/FTAI-20260731-wickhunter-okx-market-evidence-v2.md
validation:
  - command: prior AI Platform test suite
    result: PASS
    evidence: 1007 passed and 71 skipped before exact-head dedicated v2 checks.
  - command: prior Portal Market Evidence typecheck, lint, build and browser flow
    result: PASS
    evidence: Dedicated Market Evidence workflow completed all Portal steps successfully on a prior head.
  - command: exact-head CI for PR 836
    result: NOT_RUN
    evidence: Latest exact-head rerun is pending after correcting checkpoint governance fields.
blockers:
  - Implementation PR must pass exact-head CI and merge before the request-only production trigger is opened.
next_action: Validate exact-head CI on PR 836, merge normally, then open the exact-one-file prospective v2 request PR before decision_start_ms 1785477600000.
```
