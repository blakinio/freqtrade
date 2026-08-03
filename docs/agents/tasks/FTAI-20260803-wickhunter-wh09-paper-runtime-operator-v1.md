# FTAI-20260803-wickhunter-wh09-paper-runtime-operator-v1

```yaml
task_id: FTAI-20260803-wickhunter-wh09-paper-runtime-operator-v1
repository: blakinio/freqtrade
programme: WickHunter
phase: WH-09
issue: 1144
mode: implementation
status: implementation_ready_for_validation
base_branch: develop
base_sha: 0a82a5c93613a213989865bd9128ac7263227148
branch: feat/wickhunter-wh09-paper-runtime-operator-20260803-v1
helper_pr: 1147
product_pr: pending
owner: sole WH-09 persistent PAPER runtime operator producer
```

## Goal

Implement the missing persistent, restart-safe and fail-closed candidate PAPER operator. The operator must consume real read-only Liquid20 evidence and credential-free public market context, construct canonical runtime ticks, call `CandidatePaperRuntimeService.step()` and preserve the exact immutable candidate, activation, policy and contiguous journal identities.

Implementation merge is not WH-09 terminal closure. A separately reviewed request-only deployment must bind the exact merged commit, publish a fresh activation and complete the prospective observation window before an explicit owner decision.

## Exclusive paths

- `ai_platform/wickhunter/candidate_paper_runtime_operator.py`
- `deploy/synology/wickhunter-paper-runtime/Dockerfile`
- `deploy/synology/wickhunter-paper-runtime/README.md`
- `deploy/synology/wickhunter-paper-runtime/compose.yaml`
- `deploy/synology/wickhunter-paper-runtime/healthcheck.py`
- `docs/agents/tasks/FTAI-20260803-wickhunter-wh09-paper-runtime-operator-v1.md`
- `tests/ai_platform_integration/test_wickhunter_candidate_paper_runtime_operator.py`

No shared dependency, lock, package manifest, protected-holdout, strategy parameter, activation evidence or existing journal path is owned by this task.

## Implementation boundary

The product change:

1. verifies a canonical self-hashed Liquid20 snapshot from a regular read-only file;
2. rejects stale, future, malformed, duplicated, unsorted or decision-time-unavailable evidence;
3. calls only allowlisted Binance USD-M public GET endpoints using no proxy and no redirects;
4. constructs canonical universe, history, market, decision request and runtime tick values;
5. delegates activation binding, restart recovery and immutable journal commits to the existing verified runtime service;
6. emits bounded, atomic, self-hashed health state;
7. runs with a cadence no slower than 900 seconds;
8. provides a non-root, read-only, capability-free container with no ports or Docker socket;
9. keeps only the exact journal and health roots writable.

## Safety invariants

The operator, health state, container and documentation must keep these values exact:

```text
protected_holdout_accessed=false
automatic_promotion_enabled=false
trading_credentials_present=false
order_adapter_present=false
execution_enabled=false
orders_submitted=0
live_capital_authorized=false
```

Recognized exchange credentials or proxy environment variables are startup failures. Private/account/order endpoints are absent. No profitability claim, production promotion or live-trading authority is introduced.

## Required validation

Run on the exact product head:

- `python -m py_compile` for the operator, healthcheck and focused test;
- Ruff format/check for the three Python paths;
- mypy for the operator;
- focused pytest for the operator, candidate PAPER runtime service and candidate runtime binding;
- Docker Compose configuration validation with all required exact identity variables;
- standard repository CI and security workflow;
- changed-path verification proving exactly the seven owned product paths;
- independent diff, review-thread and exact-head CI inspection before merge.

## Post-merge continuation

After implementation merge:

1. close helper PR #1147 without merge;
2. create one separate request-only deployment PR pinned to the exact merged implementation SHA;
3. build the image and record its digest and OCI revision label;
4. publish a fresh immutable PAPER activation because the previous window began before the operator existed;
5. bind the exact verified candidate, activation, runtime policy and empty journal;
6. deploy only on the trusted `freqtrade-synology-staging` runner;
7. prove container hardening, public-only egress and zero authority;
8. collect at least 86,400,000 ms, at least 96 snapshots, maximum 1,800,000 ms gap and fresh-source ratio at least 0.99;
9. collect decision, allowed-decision, risk-rejection, parity and truthful safety-exercise evidence;
10. publish immutable final evidence and leave the explicit owner decision separate.

## Completion rule

This implementation task may be merged only when all exact-head validations pass and no unresolved review thread or material safety finding remains. Issue #1144 remains open until the post-merge deployment and prospective acceptance package are independently verified.

<!-- WH09_RUFF_DIAGNOSTIC_BEGIN -->
```text
[ai_platform/wickhunter/candidate_paper_runtime_operator.py]
ai_platform/wickhunter/candidate_paper_runtime_operator.py:412:15: S310 Audit URL open for permitted schemes. Allowing use of `file:` or custom schemes is often unexpected.
Found 1 error.

[deploy/synology/wickhunter-paper-runtime/healthcheck.py]
deploy/synology/wickhunter-paper-runtime/healthcheck.py:53:5: C901 `main` is too complex (18 > 12)
Found 1 error.

[tests/ai_platform_integration/test_wickhunter_candidate_paper_runtime_operator.py]
tests/ai_platform_integration/test_wickhunter_candidate_paper_runtime_operator.py:372:66: RUF043 Pattern passed to `match=` contains metacharacters but is neither escaped nor raw
Found 1 error.
```
<!-- WH09_RUFF_DIAGNOSTIC_END -->
