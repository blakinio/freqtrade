<!-- portal-status-authority: FEATURE_COMPLETENESS_LEDGER.json -->
# AI Trading Portal — Post-P12 Integration Backlog

## Historical planning record

The original dependency-ordered PI backlog remains preserved as dated planning and bounded
repository-acceptance evidence. It is no longer an active completeness-status authority because
terms such as `done`, `active` and `planned` combined different evidence layers.

Current PI and P-stage implementation status is defined only by the living exact-head ledger at
`tools/portal_audit/ledger/index.json`. The immutable
`docs/ai_platform/portal/FEATURE_COMPLETENESS_LEDGER.json` snapshot is historical compatibility
metadata, not current implementation authority.

Historical pre-ledger evidence is preserved exactly at:

```yaml
snapshot_sha: 4473dfc166d83fe5e0ffba4045c0dcd967626d68
blob_sha: 513dfa306a36c20f9afe601fdff26e3a2b63e522
```

## Durable decisions retained

- PI packages remain dependency-ordered and do not renumber P0–P14.
- Browser clients never address Freqtrade, exchanges, Vault or private data-plane services.
- Deterministic risk approval and transport acknowledgement are not execution proof.
- Repository component acceptance does not imply trusted runtime composition.
- Fixture/simulator evidence does not imply API-mode, deployment or protected-target acceptance.
- P11 remains owner-managed external infrastructure acceptance.
- P13 remains blocked until measured need exists.
- P14 remains separately owner-authorized and blocked.
- No integration package grants withdrawals or live-capital authority.

## Current work routing

Use the living exact-head ledger's PI records and linked open audit Issues. A package with a merged
bounded component may still be `PARTIAL` or `DISCONNECTED` in runtime composition and may require
`EXTERNAL_ACCEPTANCE_REQUIRED` for its real target.

The full pre-ledger package specifications, dependency graph, acceptance statements and merge
evidence remain recoverable from the exact historical blob above.
