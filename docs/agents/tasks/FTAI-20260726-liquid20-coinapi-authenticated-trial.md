---
task_id: FTAI-20260726-liquid20-coinapi-authenticated-trial
status: in_progress
branch: feat/liquid20-coinapi-authenticated-trial
base_branch: develop
created: 2026-07-26
updated: 2026-07-26
related_pr: "#352"
owned_paths:
  - docs/ai_platform/LIQUID20_COINAPI_AUTHENTICATED_TRIAL.md
  - ai_platform/research/liquidations/historical/liquid20-coinapi-authenticated-trial-v1.json
  - ai_platform/research/liquidations/historical/coinapi-authenticated-trial-v1.schema.json
  - tests/ai_platform_integration/test_liquidation_historical_coinapi_authenticated_trial.py
  - docs/agents/tasks/FTAI-20260726-liquid20-coinapi-authenticated-trial.md
required_reads:
  - AGENTS.md
  - docs/agents/CONTEXT_HANDOFF.md
  - docs/ai_platform/LIQUID20_HISTORICAL_PROVIDER_PREFLIGHT.md
  - docs/ai_platform/LIQUID20_COINAPI_PROVIDER_PREFLIGHT.md
search_first:
  - current develop HEAD, PR 352 and exact-head CI
  - exact authenticated CoinAPI workflow evidence
optional_reads: []
---

# Liquid20 CoinAPI Authenticated Trial

## Goal

Use the owner-provisioned `COINAPI_KEY` GitHub Actions secret for a bounded, non-secret
authenticated check of exact Bybit and Binance Futures liquidation coverage and account
access, without purchase, raw-data retention, importer work, training, backtesting, live
collector changes, Synology mutation, protected-holdout access or execution.

## Result

The secret was present and masked, but the CoinAPI free account returned HTTP `403` for all
exact-symbol metadata and metric-listing requests. A one-request quota probe reported
`Insufficient Usage Credits or Subscription`, organization monetary quota `0 $`, and current
usage `0 $`. Exact symbol, metric and historical coverage therefore remain unverified with
this account.

This does not reopen the prior event-level decision. CoinAPI remains rejected as a Tardis
event-level replacement and is only a conditional aggregate-feature candidate.

## Context checkpoint

```yaml
checkpoint_version: 1
updated_at: 2026-07-26T10:23:00Z
head: 898ef311aa13e407116ad9abc6c4693e30dd17b4
branch: feat/liquid20-coinapi-authenticated-trial
pr: "#352"
status: in_progress
context_routes:
  - docs/ai_platform/LIQUID20_COINAPI_AUTHENTICATED_TRIAL.md
  - ai_platform/research/liquidations/historical/liquid20-coinapi-authenticated-trial-v1.json
  - docs/ai_platform/LIQUID20_COINAPI_PROVIDER_PREFLIGHT.md
owned_paths:
  - docs/ai_platform/LIQUID20_COINAPI_AUTHENTICATED_TRIAL.md
  - ai_platform/research/liquidations/historical/liquid20-coinapi-authenticated-trial-v1.json
  - ai_platform/research/liquidations/historical/coinapi-authenticated-trial-v1.schema.json
  - tests/ai_platform_integration/test_liquidation_historical_coinapi_authenticated_trial.py
  - docs/agents/tasks/FTAI-20260726-liquid20-coinapi-authenticated-trial.md
proven:
  - GitHub Actions secret COINAPI_KEY was present and masked during the authenticated trial.
  - Coverage probe run 30197961324 job 89782783001 made 8 bounded requests across four exact targets.
  - Every exact-symbol metadata and exact-symbol liquidation metric-listing request returned HTTP 403.
  - Quota probe run 30198031682 job 89782989299 returned QuotaKey BA, Insufficient Usage Credits or Subscription, Organization Limit, QuotaValue 0 $, and current usage 0 $.
  - Temporary authenticated workflow and script were removed from the durable change set at implementation head 898ef311aa13e407116ad9abc6c4693e30dd17b4.
  - No raw market records, market values, private key value, paid history, importer, training, backtest, collector change, Synology mutation or protected-holdout access occurred.
derived:
  - The free account is not usable for the Liquid20 CoinAPI trial.
  - Exact target metric and historical coverage cannot be verified without credited or paid access.
  - Paying solely to evaluate CoinAPI as an event-level Tardis replacement is not recommended because the documented event-provenance mismatch remains.
  - CoinAPI may only be considered later for aggregate completed-interval features under a separate owner-approved scope.
unknown:
  - Exact target metric and historical availability under a credited or paid CoinAPI account.
  - Exact CoinAPI price, license, retention and redistribution terms for an optional aggregate-feature scope.
conflicts: []
first_failure:
  marker: coinapi-zero-usage-credit-organization-limit
  evidence: Authenticated CoinAPI REST requests returned HTTP 403 and a monetary organization quota value of zero.
rejected_hypotheses:
  - Treat the free account as providing 100 usable market-data requests per day.
  - Infer exact symbol or historical coverage from exchange-level metadata tables.
  - Purchase CoinAPI to replace Tardis event-level replay.
  - Log, commit or otherwise expose the CoinAPI secret.
changed_paths:
  - docs/ai_platform/LIQUID20_COINAPI_AUTHENTICATED_TRIAL.md
  - ai_platform/research/liquidations/historical/liquid20-coinapi-authenticated-trial-v1.json
  - ai_platform/research/liquidations/historical/coinapi-authenticated-trial-v1.schema.json
  - tests/ai_platform_integration/test_liquidation_historical_coinapi_authenticated_trial.py
  - docs/agents/tasks/FTAI-20260726-liquid20-coinapi-authenticated-trial.md
validation:
  - command: GitHub Actions authenticated coverage probe
    result: PASS
    evidence: Run 30197961324 job 89782783001 completed successfully and emitted only sanitized summaries.
  - command: GitHub Actions exact quota probe
    result: PASS
    evidence: Run 30198031682 job 89782989299 completed successfully and froze the non-secret quota metadata.
  - command: Durable exact-head repository validation
    result: PENDING
    evidence: Run after the temporary workflow and script were removed.
blockers: []
next_action: Validate the durable evidence on the exact PR head and merge PR 352 if CI and review are clean.
```
