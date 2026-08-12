<!-- portal-status-authority: FEATURE_COMPLETENESS_LEDGER.json -->
# AI Trading Portal — Next Work and Repair Plan

## Authority

Current work selection is derived from:

1. live GitHub Issue, claim, ownership, PR and required-CI state;
2. the living exact-head implementation ledger at `tools/portal_audit/ledger/index.json`;
3. repository governance under `docs/agents/`.

The immutable `docs/ai_platform/portal/FEATURE_COMPLETENESS_LEDGER.json` snapshot is retained only as
historical compatibility metadata and is not current implementation authority. This document does
not maintain a second static completion snapshot.

Historical pre-ledger evidence is preserved exactly at:

```yaml
snapshot_sha: 4473dfc166d83fe5e0ffba4045c0dcd967626d68
blob_sha: 9e8b5862aa2d611d40e7ec64e045603bc93331e0
```

## Autonomous repair routing

- Select only normalized `programme:audit-repair` work that is ready, unclaimed and non-overlapping.
- Claim the Issue before mutation and record exact owned/shared/forbidden paths.
- Do not manufacture parallelism or duplicate an existing branch/PR.
- Preserve one atomic repair vehicle per coherent finding.
- Require focused validation, exact-head required CI, fresh independent audit, review-thread
  reconciliation and truthful task archival before merge/closeout.
- Keep fixture/API-mode/deployment/protected-target evidence separate.
- Keep P11 external infrastructure and P14 live-capital work blocked unless explicitly authorized.

## Current priority model

Priority is determined by the live queue and dependencies, not by stale prose. Security and
high-severity runtime-composition findings precede convenience work when they are ready and
non-conflicting. Owner/provider-gated work remains `BLOCKED` or
`EXTERNAL_ACCEPTANCE_REQUIRED`; agents must not simulate acceptance.

## Completion invariant

A task is not complete because code exists or a PR opened. It becomes terminal only after its
declared vertical slice, tests, exact-head CI, audit, documentation, PR hygiene, merge, archive and
ownership release are complete.

No autonomous continuation authorizes protected infrastructure mutation, credentials, withdrawals
or live capital.
