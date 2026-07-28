# ASE-00 current state

## Scope and architectural boundary

ASE-00 is an additive research/shadow package. It must integrate with the existing portal architecture and must not introduce a second portal, bot manager, risk engine, execution service, liquidation data layer, WickHunter implementation, or public Freqtrade endpoint.

The existing repository already implements the required authority chain:

```text
Browser
  -> same-origin Portal BFF route handlers
  -> Portal Control Plane
  -> deterministic Portal Risk Core
  -> private ExecutionAdapter
  -> isolated dry-run Freqtrade runtime
```

The browser-facing code must never import or instantiate the Freqtrade execution adapter and must never receive exchange or Freqtrade credentials.

## Portal BFF/API and browser boundary

The browser application is the Next.js package under `ai_platform/portal/web/`.

Confirmed BFF and session paths include:

- `ai_platform/portal/web/proxy.ts`
- `ai_platform/portal/web/lib/client-fetch.ts`
- `ai_platform/portal/web/lib/identity.ts`
- `ai_platform/portal/web/lib/portal-api.ts`
- `ai_platform/portal/web/app/api/identity/login/route.ts`
- `ai_platform/portal/web/app/api/identity/callback/route.ts`
- `ai_platform/portal/web/app/api/identity/session/route.ts`
- `ai_platform/portal/web/app/api/identity/logout/route.ts`
- `ai_platform/portal/web/app/api/identity/logout-all/route.ts`
- `ai_platform/portal/web/app/api/bots/route.ts`
- `ai_platform/portal/web/app/api/bots/[botId]/desired-state/route.ts`
- `ai_platform/portal/web/app/api/bots/[botId]/revisions/route.ts`
- `ai_platform/portal/web/app/api/terminal/route.ts`
- `ai_platform/portal/web/app/api/signals/route.ts`

The corresponding browser E2E coverage is under:

- `ai_platform/portal/web/e2e/identity-session.spec.ts`
- `ai_platform/portal/web/e2e/bot-operations.spec.ts`
- `ai_platform/portal/web/e2e/liquidations.spec.ts`
- `ai_platform/portal/web/e2e/shell.spec.ts`

ASE-00 must expose future read/advisory surfaces through these same-origin BFF conventions, not through Freqtrade.

## Control Plane

The canonical Portal Control Plane is implemented under:

- `ai_platform/portal/control_plane/api.py`
- `ai_platform/portal/control_plane/context.py`
- `ai_platform/portal/control_plane/database.py`
- `ai_platform/portal/control_plane/models.py`
- `ai_platform/portal/control_plane/repository.py`
- `ai_platform/portal/control_plane/service.py`
- `ai_platform/portal/control_plane/migrations/0001_control_plane.sql`

Focused tests are under:

- `tests/ai_platform/portal/control_plane/test_api.py`
- `tests/ai_platform/portal/control_plane/test_migration.py`
- `tests/ai_platform/portal/control_plane/test_service.py`

ASE-00 must deliver research decisions to a Control Plane-owned integration seam. It must not add a parallel HTTP authority or trust browser-supplied identity, tenant, risk, dataset, code, or configuration evidence.

## Canonical shared contracts

The existing versioned immutable portal contracts are under `ai_platform/portal/contracts/`.

Relevant files are:

- `ai_platform/portal/contracts/common.py`
- `ai_platform/portal/contracts/events.py`
- `ai_platform/portal/contracts/payloads.py`
- `ai_platform/portal/contracts/models.py`
- `ai_platform/portal/contracts/risk.py`
- `ai_platform/portal/contracts/execution.py`
- `ai_platform/portal/contracts/audit.py`
- `ai_platform/portal/contracts/environment.py`

`ai_platform/portal/contracts/common.py` supplies frozen, extra-forbid Pydantic contracts, UTC timestamp normalization, SHA-256 types, and canonical sorted JSON. ASE-00 domain records should reuse or adapt to these conventions instead of creating incompatible serialization rules.

`ai_platform/portal/contracts/risk.py` is the canonical execution-authority chain:

```text
TradeIntent
  -> RiskDecision
  -> ApprovedExecutionIntent | RejectedExecutionIntent
```

`ai_platform/portal/contracts/execution.py` defines the private `ExecutionAdapter` protocol. Its submission method accepts only `ApprovedExecutionIntent`.

## Trading terminal

The existing terminal flow is implemented by:

- `ai_platform/portal/risk/terminal.py`
- `ai_platform/portal/control_plane/api.py`
- `ai_platform/portal/web/app/api/terminal/route.ts`
- `ai_platform/portal/web/app/terminal/page.tsx`
- `ai_platform/portal/web/components/terminal-form.tsx`

Tests include:

- `tests/ai_platform/portal/risk/test_terminal.py`
- `tests/ai_platform/portal/control_plane/test_api.py`
- `ai_platform/portal/web/e2e/shell.spec.ts`

ASE-00 shadow decisions must not bypass this server-owned risk-gated pattern.

## Bot management

Shared bot-management contracts already exist under `ai_platform/portal/contracts/bot_management/`:

- `capabilities.py`
- `commands.py`
- `compatibility.py`
- `configuration.py`
- `exchange_connections.py`
- `execution.py`
- `pagination.py`
- `policies.py`
- `signals.py`
- `templates.py`

Catalog compatibility is implemented under:

- `ai_platform/portal/bot_catalog/schema.py`
- `ai_platform/portal/bot_catalog/repository.py`
- `ai_platform/portal/bot_catalog/compatibility.py`
- `ai_platform/portal/bot_catalog/service.py`

ASE-00 strategy/risk policy output must map to these immutable policies and capability decisions. It must not create a second bot configuration or lifecycle model.

## Deterministic Risk Core

The canonical deterministic Portal Risk Core is under:

- `ai_platform/portal/risk/schema.py`
- `ai_platform/portal/risk/models.py`
- `ai_platform/portal/risk/repository.py`
- `ai_platform/portal/risk/service.py`
- `ai_platform/portal/risk/database.py`
- `ai_platform/portal/risk/migrations/0001_risk_core.sql`

Tests are under:

- `tests/ai_platform/portal/risk/test_risk_core_service.py`
- `tests/ai_platform/portal/risk/test_risk_core_migration.py`

ASE-00 may prepare a conservative `TradeIntent` and a trusted risk snapshot adapter, but only this Risk Core may approve or reject execution.

## Private Freqtrade execution adapter

The existing private runtime boundary is under:

- `ai_platform/portal/execution/adapter.py`
- `ai_platform/portal/execution/config.py`
- `ai_platform/portal/execution/driver.py`
- `ai_platform/portal/execution/runtime.py`
- `ai_platform/portal/execution/workspace.py`
- `ai_platform/portal/execution/errors.py`

Tests are under `tests/ai_platform/portal/execution/`.

The concrete adapter is dry-run-only and keeps order submission fail-closed. ASE-00 must not call Docker, Freqtrade, an exchange, or `ExecutionAdapter.submit_approved_intent` in its vertical slice.

## WickHunter

The existing liquidation strategy vertical slice is under `ai_platform/wickhunter/`:

- `canonical.py`
- `contracts.py`
- `features.py`
- `parameters.py`
- `risk.py`
- `scoring.py`
- `shadow.py`
- `strategy.py`
- `universe.py`
- `dataset.py`

Tests are:

- `tests/ai_platform_integration/test_wickhunter_vertical_slice.py`
- `tests/ai_platform_integration/test_wickhunter_dataset_builder.py`

WickHunter already provides source-labelled liquidation aggregates, availability-time checks, deterministic candidate/scoring/risk/shadow evidence, canonical hashes, duplicate-safe identities, and a dataset builder. ASE-00 must consume accepted WickHunter/liquidation evidence through an adapter or synthetic fixture and must not duplicate this package.

## Liquidation ingestion and accepted datasets

Historical liquidation import and acceptance are implemented under:

- `ai_platform/research/liquidations/historical/acceptance.py`
- `ai_platform/research/liquidations/historical/importer.py`
- `ai_platform/research/liquidations/historical/providers/tardis.py`

The focused test is:

- `tests/ai_platform_integration/test_liquidation_history_tardis_importer.py`

The live read-only portal proof is implemented by:

- `.github/workflows/liquidations-live-portal-synology-proof.yml`
- `deploy/synology/portal/prove-liquidations-live.sh`
- `tests/ai_platform/portal/deployment/test_liquidations_live_portal_synology_proof.py`

ASE-00 does not own provider acquisition, historical acceptance, live collection, or portal-mounted liquidation storage.

## Deterministic simulator

The existing no-capital simulator is under:

- `ai_platform/portal/simulator/schema.py`
- `ai_platform/portal/simulator/exchange.py`
- `ai_platform/portal/simulator/runner.py`

Evidence and tests include:

- `tests/ai_platform/portal/simulator/scenarios/profitable.json`
- `tests/ai_platform/portal/simulator/test_universal_scenario.py`
- `tests/ai_platform/portal/simulator/test_visual_baseline.py`
- `tests/ai_platform/portal/simulator/visual_acceptance_baseline.json`
- `.github/workflows/portal-universal-e2e.yml`

ASE-00 may reuse deterministic hashing and replay conventions. It must not add a second exchange simulator in this package.

## Existing timestamp and availability conventions

Confirmed existing conventions include:

- timezone-aware UTC contracts in `ai_platform/portal/contracts/common.py`;
- event and correlation contracts in `ai_platform/portal/contracts/events.py`;
- `available_at_ms` and decision-time fail-closed validation in `ai_platform/wickhunter/contracts.py`;
- provider/source/event/availability-time preservation in `ai_platform/wickhunter/dataset.py` and `ai_platform/research/liquidations/historical/`.

ASE-00 canonical feature and signal records must preserve `event_time`, `detected_at`, and `available_at` and enforce `available_at <= decision_time`.

## Checkpoint and evidence standards

The repository records bounded packages under:

- `docs/agents/programs/`
- `docs/agents/tasks/`
- `docs/agents/prompts/`
- `docs/ai_platform/`

Existing checkpoints record exact branch/head/base, owned paths, commands, test outcomes, hashes, proved/unproved behavior, blockers, rollback, and one dependency-ordered next action. ASE-00 should follow that format and keep PR #584 as draft until exact-head CI is green.

## Current ASE-00 bootstrap state

The bootstrap materializer is `ai_strategy_engine/materialize_starter.py`.

Current forensic evidence is recorded in:

- `ai_strategy_engine/docs/materialization-evidence.md`
- `ai_strategy_engine/docs/bundle-forensics.md`

At the time of this document, the stored parts reconstruct a readable ZIP with SHA-256 `e8a8f6f6aeba3c2bb9eb95e96355bb478e2a70cd9f1ebb4aa62a3d511cb601db`, not the required `73a0d99cab94ba116818a6aef9d818a710fb048a4c0b77f89b9819dd9ac7332f`. The exact required archive has not yet been proven recoverable from reachable Git history. Materialization is therefore not complete.
