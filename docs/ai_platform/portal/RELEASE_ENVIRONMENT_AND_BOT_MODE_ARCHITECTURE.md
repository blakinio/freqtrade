# Release, Environment and Bot Operating-Mode Architecture

Status: `accepted target architecture`

Owner acceptance: `2026-08-10`

Binding decision: `ADR-021`

Issue: `#1438`

## Purpose

The Quant Platform must not encode source-control state, deployment environment and trading authority as one concept. They are independent control dimensions with different owners, evidence and safety consequences.

This document defines the binding detailed architecture for ADR-021. It is architecture/governance authority only; implementation and deployed-target state still require exact repository and environment evidence.

## 1. Three orthogonal dimensions

### 1.1 Deployment environment

Canonical values:

```text
dev
staging
production
```

Environment answers **where** a release is running and which state, identity, secrets, network and protected-environment policies apply.

- `dev` is local/developer/ephemeral development and test execution.
- `staging` is the production-like acceptance environment. It uses isolated staging state and credentials and is the normal protected target for release-candidate validation.
- `production` is the operational production environment. It has independent durable state, identity, secrets, ingress and rollback evidence.

Environment does not grant bot trading authority.

### 1.2 Bot operating mode

Canonical values:

```text
SHADOW
PAPER
LIVE
```

Mode answers **what execution authority a bot generation has**.

- `SHADOW` observes real/current market inputs and produces decisions/evidence without submitted exchange orders or live capital.
- `PAPER` uses approved simulation/paper execution and remains zero-live-capital authority.
- `LIVE` is real exchange execution and is unavailable/fail-closed until a separate explicit live-capital, credential, execution and risk-acceptance package authorizes it.

A production deployment may run `SHADOW` or `PAPER`. `environment=production` never implies `mode=LIVE`.

Operating mode is immutable generation material under ADR-020 and the canonical bot lifecycle contracts. A mode change is a new/apply rollout, not an in-place mutation of a running generation.

### 1.3 Release channel

Canonical values:

```text
candidate
stable
```

Release channel answers **what promotion state an immutable platform artifact has**.

- `candidate` is eligible for staging/acceptance but is not production-approved merely because tests passed.
- `stable` is an explicitly promoted immutable release derived through the protected release path from `main`.

Release channel does not grant live trading authority.

## 2. Git branch model

### `develop` — integration branch

`develop` remains the controlled Quant Platform integration branch and the primary convergence point for ordinary product, fix, architecture, audit, CI and infrastructure work.

It also remains the natural synchronization boundary for upstream `freqtrade/freqtrade:develop`. Upstream synchronization must remain reviewable and must not give upstream commits direct production authority.

`develop` is not a deployment environment and must not be described as “the staging branch”.

### `main` — release branch

`main` is the canonical release branch after the migration defined below is completed.

Its invariants are:

- it receives reviewed release-promotion changes rather than ordinary feature integration;
- every accepted head is releaseable;
- stable release tags/artifacts originate from an exact `main` commit;
- production deployment consumes an immutable approved artifact identity, not the moving `main` ref;
- direct feature development on `main` is prohibited.

`main` is not itself production. Production is a protected deployment environment that consumes approved artifacts originating from `main`.

### Short-lived branches

Normal work uses bounded short-lived branches, for example:

```text
feature/*
fix/*
audit/*
arch/*
docs/*
ops/*
```

They integrate through PRs and are deleted after terminal merge/closeout unless durable evidence requires a documented exception.

## 3. Promotion flow

The target flow is:

```text
freqtrade/freqtrade:develop
          |
          v
blakinio/freqtrade:develop
          |
          | CI / review / integration evidence
          v
immutable candidate artifact
          |
          v
STAGING acceptance
          |
          | explicit release promotion PR
          v
        main
          |
          v
stable tag + immutable artifact identity
          |
          | protected production authorization
          v
PRODUCTION
```

The preferred supply-chain rule is **build once, promote the same digest**. When technically feasible, the exact artifact proven in staging is promoted to stable/production without rebuilding it. If a rebuild is unavoidable, it is a new artifact and must repeat the required provenance and acceptance gates.

Branch advancement is not deployment authorization. A merge to `main` does not by itself mutate production.

## 4. Deployment identity and provenance

Every staging or production deployment must be attributable to immutable evidence sufficient for rollback and audit. At minimum, where the artifact type supports it:

```text
source_commit_sha
release_tag_or_release_id
artifact_or_image_digest
configuration/generation identity
protected environment
deployment request/approval identity
```

Moving references such as `develop`, `main`, `latest` or an unpinned image tag are not sufficient production provenance.

## 5. Environment isolation

`staging` and `production` are separate security domains.

They must not silently share:

- authoritative PostgreSQL state;
- session/cookie trust domains where that would cross environment authority;
- exchange/private trading credentials;
- Vault/KMS secret paths;
- bot runtime writable state;
- RuntimeGeneration authority;
- protected deployment approvals.

Test fixtures and fixture identity remain prohibited in protected staging/production paths where the existing Portal architecture already requires real API/identity mode.

Promotion is artifact promotion, not database/state promotion. Any data migration between environments requires its own explicit migration/restore authority and evidence.

## 6. Bot-mode safety across environments

Valid examples include:

```text
environment=staging     release=candidate mode=SHADOW
environment=staging     release=candidate mode=PAPER
environment=production  release=stable    mode=SHADOW
environment=production  release=stable    mode=PAPER
```

`environment=production release=stable mode=LIVE` is structurally representable but remains unauthorized until a separate accepted LIVE lifecycle package exists. Current behavior must therefore remain fail-closed for LIVE.

No environment/release promotion may implicitly promote a bot from SHADOW to PAPER or LIVE. Bot-mode promotion follows its own immutable generation and eligibility policy.

## 7. Terminology rule

New architecture, task, PR and operational evidence should identify the relevant axes explicitly instead of combining them into ambiguous phrases.

Prefer:

```text
production environment + stable release + SHADOW mode
staging environment + candidate release + PAPER mode
```

Avoid using phrases such as “production bot”, “test branch” or “production research/shadow runtime” when they obscure which dimension is meant.

Historical evidence is immutable audit history and does not need mass rewriting. When interpreting older terms, record the mapped environment/mode/release tuple when it can be established from exact evidence; otherwise preserve the historical wording without inventing a mapping.

## 8. Repository migration from the temporary single-trunk policy

ADR-021 supersedes the temporary branch-policy decision recorded on 2026-08-09, but the physical repository migration is staged to avoid creating an unprotected or misleading release branch.

Migration order:

1. merge ADR-021, this architecture document, the registry update and governance routing into the currently authoritative `develop` branch;
2. create `main` from the exact accepted migration base;
3. configure `main` rules/protection and required release gates before using it as release authority;
4. update workflow triggers, release automation, branch references and deployment policies to understand the two-branch model;
5. verify `develop -> main` promotion and immutable artifact provenance without deploying live capital;
6. change the repository default branch to `main` only after agents, CI and operational tooling resolve the model correctly;
7. preserve `develop` as the integration/upstream-sync branch.

Until steps 2-6 are verified, documentation may describe `main` as the accepted target release branch while exact repository metadata continues to prove whether the physical migration is complete. Agents must never claim the migration is implemented solely from this decision.

## 9. Hotfix policy

Do not introduce full ceremonial GitFlow by default.

A production-critical hotfix may use a narrowly authorized release repair path, but it must:

- start from the exact affected stable release/main state;
- pass the required focused and release gates;
- produce a new immutable stable artifact;
- reconcile the semantic fix back into `develop` so the integration branch cannot regress it;
- preserve audit/rollback provenance.

## 10. Relationship to other accepted decisions

- ADR-019 remains authoritative for architecture registry and exact implementation evidence.
- ADR-020 remains authoritative for RuntimeGeneration, Runtime Supervisor, Gateway and execution isolation. ADR-021 adds release/environment semantics and does not weaken ADR-020.
- Existing SHADOW/PAPER lifecycle work remains mode authority; ADR-021 prevents deployment environment from being mistaken for that authority.
- ADR-018 remains the target production portal hostname. A production hostname does not itself prove an active production deployment.

## 11. Non-authority statement

Acceptance of ADR-021 does **not** authorize:

- a production deployment;
- mutation of a protected Synology target;
- production secrets or exchange credentials;
- model promotion;
- PAPER or LIVE promotion for a bot that is not independently eligible;
- real order submission, withdrawals or live capital;
- bypass of CI, review, audit, E2E, branch protection or deployment approval.

Those remain separate lifecycle/operational decisions with exact evidence requirements.