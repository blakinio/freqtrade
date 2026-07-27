---
task_id: FTAI-20260727-portal-bm00-shared-bot-management-contracts
status: active
branch: feat/portal-bm00-shared-contracts
base_branch: develop
created: 2026-07-27
updated: 2026-07-27
related_pr: null
owned_paths:
  - ai_platform/portal/contracts/bot_management/**
  - tests/ai_platform/portal/contracts/bot_management/**
  - docs/agents/tasks/FTAI-20260727-portal-bm00-shared-bot-management-contracts.md
  - docs/agents/prompts/PORTAL_BOT_MANAGEMENT_AGENT_PROMPTS.md
required_reads:
  - AGENTS.md
  - docs/agents/CONTEXT_HANDOFF.md
  - docs/agents/programs/FTAI_AI_TRADING_PORTAL_PROGRAM.md
  - docs/ai_platform/portal/README.md
  - docs/ai_platform/portal/SYSTEM_ARCHITECTURE.md
  - docs/ai_platform/portal/SECURITY_ARCHITECTURE.md
  - docs/ai_platform/portal/BOT_MANAGEMENT_PRODUCT_ARCHITECTURE.md
  - docs/ai_platform/portal/BOT_MANAGEMENT_AGENT_PLAN.md
  - docs/ai_platform/portal/POST_P12_INTEGRATION_BACKLOG.md
  - ai_platform/portal/contracts/common.py
  - ai_platform/portal/contracts/environment.py
  - ai_platform/portal/contracts/identity.py
  - ai_platform/portal/contracts/bots.py
search_first:
  - current develop and open pull requests
  - overlapping contract or identity ownership
  - current contract conventions and tests
---

# BM-00 — Shared bot-management contracts

## Goal

Freeze the versioned, secret-free and fail-closed contracts required for complete dry-run bot creation and management before downstream backend, web, credential or execution agents work in parallel.

BM-00 is a contract-only package. It creates no API route, database table, migration, BFF route, runtime command, exchange connection, credential lookup or order submission.

## Entry state

- PR #438 merged the canonical bot-management architecture and agent ownership plan.
- Existing portal contracts use frozen Pydantic `ContractModel` records with `extra="forbid"`, deterministic canonical JSON and explicit tenant/environment context.
- PI-07 credential brokering and PI-08 private dry-run submission remain separately gated and are not activated by BM-00.
- P11 remains a separate external Cloudflare acceptance gate.
- P14/live capital remains blocked.

## Deliverables

Create the additive package:

```text
ai_platform/portal/contracts/bot_management/
  __init__.py
  capabilities.py
  pagination.py
  templates.py
  compatibility.py
  configuration.py
  policies.py
  commands.py
  exchange_connections.py
  signals.py
  execution.py
```

Create focused tests under:

```text
tests/ai_platform/portal/contracts/bot_management/
```

The exact number of test files may follow repository conventions, but ownership must remain inside the declared test directory.

## Required contract families

### 1. Capabilities

Freeze capability identifiers for at least:

- template/catalog read;
- bot create and revise;
- lifecycle start, pause, stop and retire;
- position close, partial close and close-all;
- order cancel, cancel-all and replace;
- signal endpoint and signal-rule management;
- exchange connection create, verify, rotate and revoke;
- grid configuration;
- command and reconciliation read;
- kill-switch use;
- privileged policy management.

These are vocabulary contracts only. BM-00 must not grant them to roles or change authorization behavior.

### 2. Pagination and filtering

Freeze bounded list-query contracts with:

- deterministic stable ordering;
- opaque cursor or bounded page semantics;
- explicit maximum page size;
- tenant scope supplied by trusted context, never by an untrusted browser field;
- optional bot, environment, state and time-range filters where applicable;
- no unbounded export or list request.

### 3. Template and compatibility records

Define versioned records for:

- `BotTemplateVersion`;
- supported strategy/model/exchange/market/mode declarations;
- required and optional policy families;
- `BotCompatibilityDecision`;
- deterministic compatibility status and reason codes;
- exact evidence/version references used by the decision.

A compatibility decision must not silently coerce an unsupported configuration into a supported one.

### 4. Configuration and policy records

Define immutable versioned records for:

- market and pair policy;
- entry policy;
- position-sizing policy;
- DCA policy;
- exit policy including take-profit, multiple take-profit, stop-loss, break-even and trailing declarations;
- signal policy;
- grid policy;
- runtime policy;
- complete normalized bot-management configuration referencing exact policy versions.

Requirements:

- use `Decimal`, not binary floating-point, for prices, percentages, allocations and quantities;
- reject negative, zero or contradictory values where invalid;
- reject duplicate pairs, levels and identifiers;
- preserve deterministic ordering;
- make unsupported optional behavior explicit rather than inventing defaults;
- permit only `simulated` or `dry_run` execution modes;
- contain no exchange secret, passphrase, token, private endpoint or resolved secret-store path.

### 5. Command records

Define versioned records for:

- bot lifecycle commands;
- position commands;
- order commands;
- command target and exact immutable revision binding;
- idempotency key;
- actor, tenant, environment and correlation context;
- command state;
- accepted, rejected, blocked and pending-reconciliation outcomes;
- deterministic reason codes;
- required step-up or confirmation metadata without storing credentials.

The contract must distinguish command acceptance from authoritative execution success.

### 6. Exchange connection product records

Define secret-free metadata contracts for:

- exchange capability profile;
- connection metadata;
- verification request/result;
- permission observations such as trading enabled and withdrawals disabled;
- market type and account/subaccount metadata;
- rotation and revocation status;
- opaque credential reference only.

No contract may serialize API keys, secrets, passphrases, browser-readable tokens or provider-internal secret paths.

### 7. Signal records

Define contracts for:

- endpoint metadata;
- versioned signal schema;
- supported command vocabulary;
- authentication mode declaration;
- replay/idempotency envelope;
- signal validation result;
- signal-to-command mapping result;
- advisory-only versus execution-authorized classification.

BM-00 must not create an endpoint or accept a real webhook.

### 8. Execution and reconciliation records

Define contracts for:

- execution attempt;
- runtime acknowledgement;
- ambiguous response;
- reconciliation state and record;
- authoritative runtime identity and configuration revision binding;
- order, position and trade evidence references;
- terminal states and reason codes.

An `EXECUTED` or equivalent successful terminal result must require authoritative reconciliation evidence. An HTTP acknowledgement alone cannot construct a proven success state.

## Contract rules

1. Reuse `ContractModel`, `NonEmptyStr`, `UtcDateTime`, `CorrelationContext`, `Environment` and `ExecutionMode` where applicable.
2. Use frozen records and `extra="forbid"` through existing contract conventions.
3. Prefer tuples and immutable nested contracts over mutable mappings.
4. Use explicit `StrEnum` values and stable machine-readable reason codes.
5. Keep identifiers opaque and non-secret.
6. Require tenant and actor attribution for state-changing commands.
7. Require exact bot/config/runtime attribution where execution is involved.
8. Keep AI/model confidence separate from execution authority.
9. Do not redefine existing `BotInstance`, `BotSpec`, risk or identity semantics silently.
10. Any necessary change outside owned paths requires a separate contract-change handoff; do not edit downstream modules opportunistically.

## Non-negotiable boundaries

- no changes to `control_plane`, `web`, `execution`, `risk`, migrations or deployment;
- no Authentik, Cloudflare, Synology or external account mutation;
- no secret-store provider selection;
- no exchange credential or trading API call;
- no Freqtrade command or runtime mutation;
- no order submission, even in dry-run;
- no live-capital mode or P14 work;
- no copied WickHunter code, assets, schemas or proprietary behavior;
- no changes to frozen AI thresholds, protected holdout or completed research evidence.

## Acceptance criteria

1. Every delivered model is versioned, frozen and rejects unknown fields.
2. Canonical serialization is deterministic.
3. Invalid DCA, exit, grid, sizing and market-policy combinations fail closed.
4. Compatibility decisions contain stable reason codes and exact evidence references.
5. Commands cannot be created without tenant, actor, target, environment, immutable revision and idempotency context.
6. Accepted commands remain distinct from reconciled execution success.
7. Proven execution success cannot be constructed without authoritative reconciliation evidence.
8. Exchange and signal contracts serialize no secrets or private endpoints.
9. Pagination is bounded and deterministic.
10. Contract tests include cross-tenant attribution mismatch, duplicate identifiers, invalid decimals, stale/revision mismatch states and secret-exclusion assertions.
11. Existing portal contract tests continue to pass.
12. The PR changes only declared owned paths unless a separately documented contract-change gate is opened.

## Validation

Run narrow validation first:

```text
python -m compileall ai_platform/portal/contracts/bot_management
pytest -q tests/ai_platform/portal/contracts/bot_management
```

Then run repository-required formatting, typing, contract/security and CI gates according to `AGENTS.md` and live workflow scope.

The PR description must list:

- exact contract families delivered;
- exact reason-code and state-machine boundaries;
- secret-exclusion evidence;
- changed paths;
- narrow and full validation evidence;
- explicit statement that no API, persistence, runtime or live-capital behavior was activated.

## Context checkpoint

```yaml
checkpoint_version: 1
updated_at: 2026-07-27T10:30:00+02:00
head: null
branch: feat/portal-bm00-shared-contracts
pr: null
status: active
proven:
  - PR 438 merged the bot-management product architecture and multi-agent ownership plan.
  - Existing portal contracts provide frozen strict Pydantic contract conventions.
  - BM-00 is the mandatory serial contract package before feature agents may implement against the new schemas.
derived:
  - Downstream BM-01 through BM-06 and BMW feature work must not start implementation against invented local schemas.
unknown:
  - Exact final model decomposition and names until the contract agent inspects all current contracts and tests.
conflicts: []
first_failure:
  marker: null
  evidence: null
rejected_hypotheses:
  - Implement API routes, migrations or web forms as part of BM-00.
  - Select a secret provider or implement PI-07.
  - Implement Freqtrade submission or PI-08.
  - Copy third-party WickHunter contracts or behavior.
changed_paths:
  - docs/agents/tasks/FTAI-20260727-portal-bm00-shared-bot-management-contracts.md
  - docs/agents/prompts/PORTAL_BOT_MANAGEMENT_AGENT_PROMPTS.md
validation: []
blockers: []
next_action: Implement and test the BM-00 contract package only on this branch, then open or update its draft PR with exact-head validation evidence.
```

next_action: Implement and test the BM-00 contract package only on `feat/portal-bm00-shared-contracts`, then open or update its draft PR with exact-head validation evidence.
