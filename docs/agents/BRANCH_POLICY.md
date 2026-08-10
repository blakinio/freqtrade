# Quant Platform Branch and Release Policy

Status: ACCEPTED TARGET / MIGRATION REQUIRED
Owner decision date: 2026-08-10
Binding decision: ADR-021
Issue: #1438

## Core rule

Source-control branches, deployment environments and bot operating modes are independent dimensions.

- `develop` is the controlled integration branch.
- `main` is the accepted target release branch.
- `dev`, `staging` and `production` are deployment environments, not branch aliases.
- `SHADOW`, `PAPER` and `LIVE` are bot operating modes, not environment aliases.
- `candidate` and `stable` are release channels.

The detailed contract is `docs/ai_platform/portal/RELEASE_ENVIRONMENT_AND_BOT_MODE_ARCHITECTURE.md`.

## Integration routing

Until exact repository evidence proves the physical `main` migration and its required protection/CI are complete, all ordinary task, feature, fix, audit, documentation, migration, runtime, portal, WickHunter, CI and infrastructure PRs continue to target `develop`.

After the migration is complete:

- ordinary work still integrates through `develop`;
- upstream `freqtrade/freqtrade:develop` synchronization converges through `develop`;
- stable release promotion uses a dedicated reviewed `develop -> main` release PR;
- direct ordinary feature integration into `main` is prohibited.

## Release and deployment separation

A branch tip is never deployment authorization.

- candidate artifacts are immutable and are validated in staging;
- stable artifacts originate from exact accepted `main` commits after release promotion;
- staging/production deployments use exact commit/tag/artifact or image-digest provenance;
- prefer build-once/promote-the-same-digest rather than rebuilding between staging and production;
- production deployment requires its own protected authorization and is not triggered merely by merging to `main`.

`develop` must not be described as “the staging branch” and `main` must not be described as “the production environment”.

## Bot-mode separation

`environment=production` does not imply `mode=LIVE`.

Production may operate stable `SHADOW` or `PAPER` generations. `LIVE` remains fail-closed until a separate explicit live-capital, credentials, execution and risk-acceptance package authorizes it.

No branch/release/environment promotion implicitly changes a bot's operating mode.

## Physical `main` migration gate

ADR-021 supersedes the 2026-08-09 temporary single-trunk architecture decision, but documentation does not fabricate implementation state.

Before `main` becomes operational release authority, the repository must have exact evidence that:

1. ADR-021/governance is merged to `develop`;
2. `main` is created from the accepted migration base;
3. required rules/protection and release gates are configured;
4. workflows and automation understand the two-branch model;
5. `develop -> main` promotion and immutable artifact provenance are verified;
6. changing the repository default branch cannot break agent, CI, upstream-sync or deployment routing.

Only then may repository default-branch migration to `main` be claimed complete.

## Short-lived branches

Use bounded short-lived task branches such as `feature/*`, `fix/*`, `audit/*`, `arch/*`, `docs/*` or `ops/*`. Delete them after terminal merge/closeout unless a documented evidence requirement justifies retention.

## Hotfixes

Do not adopt full ceremonial GitFlow by default. A production-critical stable hotfix must remain narrowly authorized, produce a new immutable stable artifact and reconcile the semantic fix back to `develop`.

## Safety boundary

This policy changes Git/release architecture only. It does not authorize production deployment, protected-environment mutation, live trading, live capital, secrets, credentials, PAPER/LIVE promotion, model promotion or bypassing CI, review, audit, E2E, branch protection or deployment gates.
