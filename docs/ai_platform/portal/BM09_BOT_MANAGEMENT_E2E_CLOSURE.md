# BM-09 bot-management E2E closure

## Scope

BM-09 closes the repository-side bot-management delivery sequence with one explicit scenario matrix and one critical browser journey over the already integrated BM-00 through BM-08, BMW and PI-07/PI-08 packages.

The closure remains dry-run-only. It does not turn fixture evidence into real target acceptance, publish Freqtrade endpoints, authorize production credentials, enable withdrawals or start P11/P14.

## Repository acceptance

The versioned scenario matrix is stored at:

```text
ai_platform/portal/e2e/scenarios/bot_management_closure.json
```

It maps every required family to existing authoritative narrow tests or browser journeys:

- bot creation, revision conflict and lifecycle intent;
- signal authentication and replay;
- approved and rejected risk commands;
- private dry-run submission and ambiguous reconciliation;
- position and order management;
- grid configuration and runtime gating;
- cross-tenant denial;
- session revocation and step-up;
- unavailable and stale source behavior.

The matrix is validated as repository evidence. Each reference must exist, each required family must occur exactly once and the matrix must preserve the external-target and live-capital gates.

## Browser closure

The BM-09 critical Playwright journey traverses:

```text
dashboard -> bot fleet -> bot detail -> exchange connections -> signals -> grid
```

It verifies explicit test/dry-run presentation, authoritative evidence surfaces, fail-closed unavailable providers and the absence of browser traffic to private Freqtrade mutation routes or secret references.

A lifecycle replay assertion separately proves that accepted and persisted command intent is not execution proof.

## CI gate

`Portal Universal E2E` now runs both:

- the deterministic universal simulator and BM-09 scenario-matrix validation;
- the critical Chromium journey, including the BM-09 browser closure.

The normal AI Platform, Portal Web, Freqtrade and workflow-security gates remain required on the exact pull-request head.

## Evidence boundary

A green BM-09 repository bundle proves deterministic repository integration and browser/BFF safety only. The following remain external or separately governed:

- real Authentik/Synology identity acceptance;
- real Vault initialization and private Freqtrade target acceptance;
- real Cloudflare protected staging under P11;
- live-small readiness or any capital authorization under P14.
