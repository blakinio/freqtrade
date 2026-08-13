<!-- portal-status-authority: FEATURE_COMPLETENESS_LEDGER.json -->
# AI Trading Portal Program

## Status authority

Current implementation completeness is defined by the living exact-head inventory at
`tools/portal_audit/ledger/index.json`, subject to its deterministic exact-head validation and
`tools/portal_audit/ledger/status_authority.json`.

The `portal-status-authority` marker above is retained only as compatibility metadata for the
historical #1101 feature-completeness snapshot. `FEATURE_COMPLETENESS_LEDGER.json` and its Markdown
projection remain dated evidence; neither is the current implementation authority.

Architecture statements in this README remain active. Any completion wording from the pre-living-ledger
version is historical evidence only and cannot override the living exact-head inventory.

Historical pre-ledger evidence is preserved exactly at:

```yaml
snapshot_sha: 4473dfc166d83fe5e0ffba4045c0dcd967626d68
blob_sha: dfd5c7ffe252f6666c3bf3a53d3ee55c58b7bf3d
```

## Purpose

The AI Trading Portal is the private, tenant-scoped control and evidence plane for the Quant
Platform. It combines bot configuration, deterministic risk decisions, runtime evidence, AI/model
lifecycle evidence and operations views without making Freqtrade, exchanges, Vault or other private
providers browser-addressable.

## Non-negotiable boundaries

- Browser traffic terminates at the Portal/Next.js same-origin boundary.
- Private runtimes, credential stores, databases and provider endpoints remain server-side.
- Deterministic risk approval is necessary but is not execution proof.
- Transport acknowledgement is never authoritative execution proof.
- Fixture, simulator and repository evidence remain visibly distinct from API-mode, deployment and
  protected-target acceptance.
- New trading configuration remains dry-run/non-live unless a separately authorized programme says
  otherwise.
- No documentation or software completion grants withdrawals or live-capital authority.

## Completeness model

Every package and user-facing module is recorded across five independent dimensions:

1. repository component;
2. trusted runtime composition;
3. API-mode browser E2E;
4. deployment package;
5. protected-target acceptance.

Use only the approved statuses in the living exact-head inventory for current claims. Historical
snapshots may preserve their dated vocabulary. Do not use `done`, `integrated`, `ready`,
`production-ready` or similar prose as active completeness authority.

## Canonical architecture and programme documents

- `SYSTEM_ARCHITECTURE.md`
- `SECURITY_ARCHITECTURE.md`
- `DATA_AND_OBSERVABILITY_ARCHITECTURE.md`
- `AI_ML_LEARNING_ARCHITECTURE.md`
- `BOT_MANAGEMENT_PRODUCT_ARCHITECTURE.md`
- `UI_INFORMATION_ARCHITECTURE.md`
- `E2E_TEST_ARCHITECTURE.md`
- `QUALITY_AND_AUTONOMOUS_E2E.md`
- `docs/agents/programs/FTAI_AI_TRADING_PORTAL_PROGRAM.md`

Historical roadmaps and status narratives remain linked for architectural context, but current work
selection and closure claims must be derived from the living exact-head inventory plus live GitHub
Issue/PR/CI state.

## Validation

```bash
python tools/agents/check_portal_completeness_ledger.py
pytest -q tests/tools/test_check_portal_completeness_ledger.py
pytest -q tests/ci/test_portal_status_authority.py
```
