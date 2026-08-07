<!-- portal-status-authority: FEATURE_COMPLETENESS_LEDGER.json -->
# AI Trading Portal — UI Delivery Status

## Authority

The active per-surface status matrix is maintained in
`docs/ai_platform/portal/FEATURE_COMPLETENESS_LEDGER.json` and rendered in
`docs/ai_platform/portal/FEATURE_COMPLETENESS_LEDGER.md`.

This file no longer declares a separate `integrated`/`partially integrated` status vocabulary.
Those terms were too coarse because they combined route presence, repository components, trusted
runtime composition, fixture browser evidence, deployment validation and real target acceptance.

Historical pre-ledger evidence is preserved exactly at:

```yaml
snapshot_sha: 4473dfc166d83fe5e0ffba4045c0dcd967626d68
blob_sha: 722f7b121e2a0997c4e3be51c1cffe899d79d6ad
```

## Required interpretation

For every route, consult all five ledger dimensions independently:

- `repository_component`;
- `runtime_composition`;
- `api_mode_e2e`;
- `deployment_package`;
- `protected_target_acceptance`.

A rendered route or green fixture test does not imply a real backend producer, durable product
workflow, selected runtime provider, API-mode browser journey, deployable artifact or accepted
protected target.

## UI closure rule

A user-facing module may be reported `COMPLETE` only when its declared vertical slice is complete,
its linked audit Issues are terminal, exact-head required CI is green and the evidence type is
explicit. Unavailable, stale, denied, conflict, fixture and external-acceptance states must remain
truthful and distinct.

No UI status grants production deployment, trading execution, withdrawals or live capital.
