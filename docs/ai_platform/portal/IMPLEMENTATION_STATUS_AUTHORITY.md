# AI Trading Portal — Implementation Status Authority

Status: `accepted candidate pending merge`

Machine-readable contract: `tools/portal_audit/ledger/status_authority.json`

## Purpose

The Portal has several legitimate status-bearing artifacts created at different stages of the programme. They do not have equal authority and must not be combined into an optimistic completion claim.

This contract separates architecture truth, current implementation truth, work ownership and historical/derived roll-ups.

## Authority hierarchy

### 1. Architecture and document authority

`ARCHITECTURE_REGISTRY.yaml`, together with the accepted ADRs it references, is authoritative for architecture decisions, document lifecycle and architecture findings.

It is **not** the current implementation-completeness inventory. An accepted target architecture does not prove that its runtime, browser, deployment or protected-target path is implemented.

### 2. Current implementation authority

`tools/portal_audit/ledger/index.json` and its referenced `tools/portal_audit/ledger/*` sections are the sole current exact-head implementation inventory for the Portal.

The inventory is authoritative only when its deterministic validation passes for the exact repository head being claimed. Its required contract is:

```yaml
schema_version: portal-completeness-ledger-v2
mode: living_exact_head_gate
status_authority: tools/portal_audit/ledger/status_authority.json
```

Inventory drift, composition drift or an invalid status contract must fail closed rather than falling back to an older status document.

The reserved `portal-current-status-authority` marker is the machine-discoverable human roll-up pointer to this authority. It must occur exactly once in the documentation tree, in `UI_DELIVERY_STATUS.md`, and must point to `tools/portal_audit/ledger/index.json`. Explicit prose claims that something is the current implementation/status authority are restricted to this contract and that validated UI roll-up; the CI guard discovers such claims across the documentation tree rather than trusting only paths declared by the sidecar.

### 3. Historical and derived status surfaces

`docs/ai_platform/portal/FEATURE_COMPLETENESS_LEDGER.json` is the historical #1101 snapshot at:

```yaml
as_of_sha: b39b29c3e831ba491aa3376e5de86a8c09e2b537
git_blob_sha: 4893b73ef020621529612192ff942fef79fb3cfc
```

The Git blob identity is pinned by the CI guard from the file bytes themselves, so changing the historical snapshot while retaining or jointly editing its embedded metadata fails closed.

Its embedded `status_authority: true` field and the legacy `portal-status-authority` document markers are retained **only as compatibility metadata for the completed #1101 snapshot and its validator**. They do not confer current implementation authority after adoption of the living exact-head ledger.

`FEATURE_COMPLETENESS_LEDGER.md`, `UI_DELIVERY_STATUS.md`, README/roadmap/backlog/next-work documents and programme tables are historical evidence, validated roll-ups, work-ownership views or dependency plans as classified by `status_authority.json`. They may summarize authoritative evidence but may not override it.

### 4. GitHub Issues and Pull Requests

GitHub Issues are work-ownership and acceptance units. Open/closed state is important lifecycle evidence, but it is not standalone implementation truth.

A closed Issue does not by itself prove current runtime composition, API-mode E2E, deployment acceptance or protected-target acceptance. A Pull Request, review or green CI run likewise proves only the scope its evidence actually exercises.

## Roll-up rules

- Current implementation claims must derive from the living exact-head ledger and its exact-head validation.
- Architecture status must derive from the architecture registry and accepted ADRs, not from implementation roll-ups.
- A historical/roll-up document may never become a second current implementation authority merely by containing words such as `COMPLETE`, `integrated`, `done` or `status_authority`.
- Fixture, repository-component, runtime-composition, API-mode E2E, deployment-package and protected-target evidence remain distinct dimensions.
- Missing, stale, disconnected, partial, fixture-only, external-acceptance and blocked states must remain explicit.
- No generated or historical roll-up may upgrade a lower evidence dimension into a higher one.

## CI enforcement

`tests/ci/test_portal_status_authority.py` validates the authority graph without network access. It rejects, among other things:

- a missing or redirected current implementation authority;
- a living ledger whose schema/mode no longer matches the authority contract;
- a duplicate reserved current-authority marker or an unclassified explicit current-authority claim in the documentation tree;
- any additional documentation JSON object carrying top-level `status_authority: true` outside the pinned #1101 snapshot;
- a missing or duplicate legacy-surface classification;
- any rewrite of the #1101 snapshot by checking both its fixed `as_of_sha` and independently computed Git blob SHA;
- an implicit second current implementation authority;
- loss of the explicit compatibility-only treatment of the old `status_authority: true` flag;
- loss of the current-authority declaration from the UI status roll-up;
- any structured authority grant for LIVE, real capital, withdrawals, private trading credentials, model/strategy promotion, protected-environment mutation or production deployment.

The existing #1101 compatibility validator remains valid for its historical snapshot. This contract supersedes only its claim to be the *current* status authority; it does not rewrite its evidence.

## Safety boundary

The machine-readable contract carries explicit `false` authority grants for LIVE trading, real capital, withdrawals, private trading credentials, model/strategy promotion, protected-environment mutation and production deployment. Human prose cannot override those structured fields.

PAPER remains the only currently authorized operational trading mode. SHADOW remains optional and purpose-bound. LIVE remains unreachable/fail-closed until a separate explicit owner-approved architecture and implementation programme changes that authority.
