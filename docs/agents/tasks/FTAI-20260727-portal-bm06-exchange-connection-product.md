---
task_id: FTAI-20260727-portal-bm06-exchange-connection-product
status: review
owner: OpenAI Codex
created_at: 2026-07-27
updated_at: 2026-07-27
branch: feat/portal-bm06-exchange-connection-product
base_branch: develop
related_pr: 480
scope:
  - ai_platform/portal/exchange_connections/**
  - tests/ai_platform/portal/exchange_connections/**
  - docs/agents/tasks/FTAI-20260727-portal-bm06-exchange-connection-product.md
out_of_scope:
  - secret-provider selection or implementation
  - API key, secret, passphrase or token storage and retrieval
  - private exchange or live-trading endpoint calls
  - shared API registration, migrations, BFF or infrastructure changes
  - PI-07 or PI-08 implementation
  - live capital
---

# BM-06 Exchange Connection Product

## Objective

Implement the bounded portal product layer for exchange connections on top of the merged BM-00 contracts while preserving strict tenant isolation and secret-free boundaries.

## Preconditions

- BM-00 PR #440 is merged into the current `develop` history.
- BM-00 required checks were green before implementation started.
- The implementation branch is based on `develop` commit `0e2a6428a7ca29e7c2fdc4ac34be85bb5f5ac0c0`.

## Delivered

- Account and optional subaccount metadata validation.
- Version-bound exchange capability product profiles.
- Supported markets, symbols, precision, order types and exchange functions.
- Tenant-scoped in-memory product repository with cross-tenant denial.
- Opaque credential-reference inspection port for future PI-07 integration.
- Verification request/result state machine with idempotent request handling.
- Explicit availability, trading-permission and withdrawal-permission states.
- Product states for stale, unavailable, revoked and rotation-required connections.
- Rejection of withdrawal-enabled evidence without creating a permission observation.

## Security boundaries

- Credential references remain opaque BM-00 `CredentialReference` values.
- Product models forbid undeclared secret-bearing fields through strict contract validation.
- No secret provider is selected or implemented.
- No API key, secret, passphrase, token, private endpoint or resolved secret-store path is stored or fetched.
- No private exchange or live-trading endpoint is called.
- No shared API registration, migration, BFF or infrastructure path is changed.
- PI-07, PI-08 and live capital remain out of scope.

## Focused tests

- Secret-bearing fields are excluded from product models and serialization.
- Cross-tenant reads are denied and tenant listings remain isolated.
- Invalid capability combinations are rejected.
- Verified connections transition to stale after the configured maximum age.
- Withdrawal-enabled probes fail verification and do not produce permission observations.

## Validation checkpoint

- Validated implementation head: `9fb139e1fdeb2dffc66145119a34d40ef5789b38`.
- AI Platform CI run #2165: passed, including compile, five focused tests, Ruff, Ruff format and Codespell.
- GitHub Actions Security Analysis run #2493: passed.
- Full PR acceptance remains governed by the required checks on the current PR head.
- Diff against the recorded base contains only the eight allowed files.

## Pull request

- PR: #480
- URL: https://github.com/blakinio/freqtrade/pull/480
- State at checkpoint: open, non-draft and mergeable.

## Blockers

None.

next_action: Review and merge PR #480 after all required checks on the current head are green.
