<!-- portal-status-authority: FEATURE_COMPLETENESS_LEDGER.json -->
<!-- portal-current-status-authority: tools/portal_audit/ledger/index.json -->
# AI Trading Portal — UI Delivery Status

## Authority

Current implementation status is derived from the living exact-head inventory at
`tools/portal_audit/ledger/index.json`, under
`tools/portal_audit/ledger/status_authority.json`.

`docs/ai_platform/portal/FEATURE_COMPLETENESS_LEDGER.json` and its rendered
`docs/ai_platform/portal/FEATURE_COMPLETENESS_LEDGER.md` are the completed #1101 historical
snapshot/roll-up. The first HTML marker in this file is retained for the legacy #1101 validator and
does not make that snapshot the current implementation authority.

The full authority hierarchy and supersession rules are documented in
`docs/ai_platform/portal/IMPLEMENTATION_STATUS_AUTHORITY.md`.

This file does not declare a separate `integrated`/`partially integrated` status vocabulary.
Those terms were too coarse because they combined route presence, repository components, trusted
runtime composition, fixture browser evidence, deployment validation and real target acceptance.

Historical pre-ledger evidence is preserved exactly at:

```yaml
snapshot_sha: 4473dfc166d83fe5e0ffba4045c0dcd967626d68
blob_sha: 722f7b121e2a0997c4e3be51c1cffe899d79d6ad
```

## Required interpretation

For every route, preserve the five completeness dimensions independently:

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

GitHub Issue state is work-ownership/acceptance evidence, not standalone implementation truth.
No UI or status artifact grants production deployment, trading execution, withdrawals, private
trading credentials or live capital.
