# Temporary Branch Policy

Status: ACTIVE
Owner decision date: 2026-08-09

## Current rule

`develop` is the single canonical integration trunk for the entire Quant Platform until the repository owner explicitly introduces a separate production/release branch model.

All repository work must be delivered through short-lived task branches and pull requests targeting `develop`.

Do not use `main`, `production`, `quant-platform`, or programme-specific long-lived branches as an intermediate integration stage while this policy is active.

The eventual separation of development and production branches is intentionally deferred until the platform is closer to production readiness and requires a new explicit owner decision plus governance update.

This policy governs Git integration only. It does not authorize production deployment, live trading, live capital, protected-environment mutations, secrets, credentials, model promotion, or bypassing CI, review, audit, E2E, or merge gates.
