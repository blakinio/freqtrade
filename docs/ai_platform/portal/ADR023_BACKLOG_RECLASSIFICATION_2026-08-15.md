# ADR-023 Portal/WickHunter backlog reclassification — 2026-08-15

```yaml
cutover_issue: 1560
successor_mvp_issue: 1561
repository: blakinio/freqtrade
classification_base: 1f62ff29f4a2a25c929218bd3b69bf19257f3055
governing_decision: ADR-023
classification_values:
  - KEEP_NOW
  - SIMPLIFY
  - DEFER
  - OBSOLETE
```

## Purpose

This is the canonical one-time cutover ledger for open Portal/WickHunter work that existed when ADR-023 replaced the former PAPER-first, multi-tenant and production-trading target.

The classification answers whether the **open work item** remains a current product priority. It does not erase already merged implementation or historical evidence. Useful code from an `OBSOLETE` or `DEFER` work item may be reused later when it directly supports the Developer Quant Portal.

Definitions:

- `KEEP_NOW` — directly required by the current owner-facing Developer Quant MVP.
- `SIMPLIFY` — the capability is currently useful, but former mode/enterprise/protected-target ceremony must be removed and acceptance rewritten around the current workflow.
- `DEFER` — useful or prudent later, but not a blocker for the first complete current workflow.
- `OBSOLETE` — the open work item exists primarily because of superseded SHADOW/PAPER/LIVE, private-trading, multi-tenant or production-certification assumptions.

Current product acceptance is Issue #1561:

`REALTIME_PUBLIC -> WickHunter decisions incl NO_TRADE -> simulation/outcomes -> durable dataset -> LOCAL challenger training -> active/challenger comparison -> deliberate owner activation -> restart-safe Portal observation`

## Former 50-Issue Portal remediation inventory

Six audit items were already terminal before this cutover and are preserved as historical completed work: `#1101`, `#1116`, `#1122`, `#1124`, `#1126`, `#1127`. They are not reopened by ADR-023.

The remaining open inventory is reclassified as follows.

| Issue | Former scope | ADR-023 class | Current disposition |
|---|---|---|---|
| #1085 | Strategy Catalog producer/API | DEFER | Catalog breadth is not needed for the first owner workflow; retain existing strategy/model identity mechanisms. |
| #1086 | PI-08 private dry-run submission composition | OBSOLETE | Private execution/credential submission is outside the current product. Do not continue this work item. |
| #1087 | Localization boundary | DEFER | Keep current usable language; localization is not an MVP blocker. |
| #1089 | Authenticated API-mode deployment | SIMPLIFY | Keep real API-mode persistent Developer Portal and real-data composition; drop production-trading/protected-acceptance ceremony not tied to a concrete current risk. |
| #1090 | Durable Create Bot materialization | KEEP_NOW | Durable bot definition and restart-safe state directly support the MVP. |
| #1091 | BM-07 private command activation | SIMPLIFY | Retain only developer lifecycle start/stop/restart/apply semantics; remove private-order activation requirements. |
| #1092 | PI-01 runtime collection/reconciliation | SIMPLIFY | Retain runtime state/health and restart reconciliation needed by persistent SYNOLOGY bot operation; do not require the former private-runtime architecture universally. |
| #1093 | PI-02 valuation | SIMPLIFY | Reframe around simulated positions, PnL, fees/slippage and drawdown. |
| #1094 | PI-04 observability | KEEP_NOW | Runtime/data/model health and evidence are directly visible owner requirements. |
| #1095 | Signed Signal control | DEFER | Not required for single-owner simulation workflow. |
| #1096 | Grid policy persistence/UI | DEFER | Strategy/product breadth after the primary WickHunter workflow. |
| #1097 | Exchange connection lifecycle/private credential verification | OBSOLETE | Private trading credentials are outside current product; public market-source configuration belongs to current data collectors instead. |
| #1098 | Real API-mode browser E2E | SIMPLIFY | Keep real browser/API E2E for #1561; remove production-trading/protected-target framing. |
| #1099 | Desired-state outbox activation | SIMPLIFY | Keep durable lifecycle/restart intent where needed; do not require universal enterprise outbox/RuntimeGeneration ceremony. |
| #1100 | PI-07 Vault credential broker | OBSOLETE | Private order credentials are outside current product. Preserve code/history only. |
| #1102 | AI/learning/model lifecycle | KEEP_NOW | Reframe around durable datasets, LOCAL challenger training, comparison and explicit owner activation. |
| #1103 | Administration workflows | DEFER | Enterprise/admin breadth is not needed for the single-owner MVP. |
| #1104 | Notification channels/rules | DEFER | Useful later; health remains visible in Portal first. |
| #1107 | Pagination/retention | SIMPLIFY | Add bounded pagination/retention only on growing decision/outcome/dataset surfaces as required; no enterprise-wide retention programme. |
| #1108 | Correlation/causation propagation | DEFER | Preserve existing IDs where present; broad cross-plane programme is not an MVP blocker. |
| #1109 | Generated contracts/error envelope | DEFER | Use stable current API contracts; whole-platform generation is not required for the first workflow. |
| #1110 | BFF bounded transport | KEEP_NOW | Real browser/API journey requires bounded server-side transport. |
| #1111 | Canonical append-only audit | SIMPLIFY | Keep attributable owner/model activation and important mutations; enterprise compliance audit is not a universal gate. |
| #1112 | Transactional outbox/domain events | SIMPLIFY | Use only where a current asynchronous consumer/restart requirement materially needs it. |
| #1113 | Idempotency/optimistic concurrency | SIMPLIFY | Keep it on material current mutations such as activation/training/lifecycle; no blanket framework-first programme. |
| #1114 | Browser security headers | SIMPLIFY | Keep sensible browser/cache/security headers; remove separate protected-production certification campaign. |
| #1115 | Inbound request limits | KEEP_NOW | Proportionate input bounds remain a current safety requirement. |
| #1117 | Capability-aware UI | DEFER | Single-owner Portal does not need enterprise capability matrices for MVP. |
| #1118 | Tenant selection/switching | OBSOLETE | Current Portal is single-owner; tenant switching is not a current product feature. |
| #1119 | Freshness-aware operational updates | KEEP_NOW | Real public market-data freshness and bot health are core acceptance. |
| #1120 | Hierarchical platform/tenant/exchange/bot kill switch | OBSOLETE | The enterprise hierarchy is superseded. Simple bot stop/pause/restart remains part of current lifecycle work. |
| #1121 | Session inventory/revocation | DEFER | Basic authentication remains; advanced session administration is not MVP-blocking. |
| #1123 | Partial upstream failure isolation | KEEP_NOW | Binance/Bybit/OKX and runtime partial failures must not corrupt the current workflow. |
| #1128 | OIDC flow quotas/cleanup | DEFER | Current single-owner login must remain usable, but this hardening programme is not a workflow blocker absent a proven defect. |
| #1129 | Bounded semantic fields | DEFER | Retain existing bounded inputs; broad semantic-field programme can wait. |
| #1130 | OIDC response/algorithm/rotation bounds | DEFER | Preserve current secure login; further provider hardening is not MVP-blocking absent a proven defect. |
| #1132 | Back-channel logout replay protection | DEFER | Not required for the owner workflow; re-open only if current identity behavior proves it necessary. |
| #1134 | Tenant workload budgets | OBSOLETE | Per-tenant workload admission is not a current single-owner requirement. Host/resource bounds may remain where operationally useful. |
| #1135 | Identity key rotation | DEFER | Operational hardening later unless current key handling presents a concrete defect. |
| #1136 | Clock-skew/monotonic evidence | KEEP_NOW | Realtime public data, delayed outcomes and restart ordering require truthful source/event time. |
| #1137 | Atomic OIDC state claim protected acceptance | SIMPLIFY | Repository implementation already merged. Drop the old special protected concurrency campaign as a universal gate; require ordinary current login/browser smoke and close if no live defect remains. |
| #1139 | Backup/restore/DR | SIMPLIFY | Keep practical backup/restore for Portal DB, datasets and models; defer enterprise DR ceremony. |
| #1140 | Full accessibility/responsive acceptance | DEFER | Maintain baseline accessibility on changed surfaces; whole-product acceptance is not the MVP blocker. |
| #1142 | Session touch write amplification | DEFER | Performance optimization after owner workflow is operational. |

## Additional open Portal/WickHunter/PAPER work

| Issue | Former/current scope | ADR-023 class | Current disposition |
|---|---|---|---|
| #1144 | Persistent WH09 PAPER runtime operator | OBSOLETE | The old PAPER acceptance/window issue is superseded by #1561. Preserve and reuse the already-built persistent research runtime, Liquid20 input, journal/outcome and restart code. |
| #1211 | AI Trading Portal programme parent | KEEP_NOW | Reframe the programme parent as Developer Quant Portal and point it to ADR-023, #1560 and #1561. |
| #1305 | Protected public-origin HSTS/security-header acceptance campaign | OBSOLETE | Parent #1114 remains SIMPLIFY for sensible browser security; the separate protected-production acceptance campaign is no longer a current product gate. |
| #1396 | SHADOW/PAPER/LIVE runtime-mode lifecycle | OBSOLETE | Product modes were explicitly removed by ADR-023. Fold useful simulation/runtime behavior into #1561 without mode transition ceremony. |
| #1491 | G7 portfolio risk / virtual capital producer | DEFER | Useful for richer portfolio simulation later; not needed before one end-to-end WickHunter simulation workflow exists. |
| #1492 | PaperExecutionProfile producer | SIMPLIFY | The useful concept becomes simulation assumptions/profile (fees, slippage, latency, fill limitations) under #1561; the disconnected PAPER producer is not a standalone deliverable. |
| #1493 | PAPER G3 Runtime Gateway producer | DEFER | Specialized boundary may be reused if the current Freqtrade path needs it; it is no longer a universal prerequisite. |
| #1499 | PAPER Evidence Workbench eligibility producer | DEFER | Evidence comparison may be useful later; PAPER eligibility engine is not current product authority. |
| #1560 | ADR-023 backlog cutover | KEEP_NOW | This cutover ledger/programme retirement task closes the old work graph. |
| #1561 | Developer Quant MVP vertical slice | KEEP_NOW | Sole current P1 product journey after cutover. |

## Open Pull Request disposition at cutover

Dependency-update PRs `#1314` and `#1336` are ordinary maintenance and are outside this product cutover.

| PR | Related work | ADR-023 disposition |
|---|---|---|
| #1448 | continuous PAPER programme governance | CLOSE_OBSOLETE — governance exists solely to continue the superseded PAPER programme. |
| #1451 | stacked repair for #1448 | CLOSE_OBSOLETE — parent programme is superseded. |
| #1478 | stale repair child after #1470 already merged | CLOSE_SUPERSEDED — parent #1470 is merged; this child must not remain open. |
| #1494 | #1491 portfolio-risk partial producer | CLOSE_DEFERRED — preserve branch/code for later reuse; do not merge a disconnected producer now. |
| #1495 | #1492 PaperExecutionProfile producer | CLOSE_SUPERSEDED — preserve code as a source for a future SimulationExecutionProfile integrated directly into #1561. |
| #1497 | #1493 Runtime Gateway partial producer | CLOSE_DEFERRED — specialized code may be reused later; do not merge in isolation. |
| #1498 | dependency-independent G4 reconciliation producer | CLOSE_SUPERSEDED — old G4/PAPER coordination shape is not the current delivery graph; reuse concepts only inside an actual current consumer. |
| #1500 | #1499 Evidence Workbench partial producer | CLOSE_DEFERRED — preserve code, no standalone PAPER eligibility producer now. |
| #1511 | PAPER G0 archive housekeeping | CLOSE_OBSOLETE — stale programme lifecycle cleanup is no longer worth merging. Historical merged evidence remains available. |
| #1546 | request-only #1396 PAPER proof | CLOSE_OBSOLETE — request contract says close without merge; #1396 itself is obsolete under ADR-023. |
| #1549 | request-only #1089 protected acceptance | CLOSE_SUPERSEDED — must never merge; old protected acceptance ceremony is superseded by simplified #1089/#1561 validation. |
| #1553 | Market Evidence Synology host-mount repair | KEEP_AND_REFRAME — real public evidence is directly useful. Resolve its live review findings and rewrite acceptance around the Developer Portal data path before merge. |

## Programme cutover

The old `FTAI-20260803-portal-remediation` 50-Issue coordinator is terminally superseded by ADR-023. It must not autonomously dispatch `#1132` or continue its S0/F1/R2/P3/D4 wave graph.

Historical audit PR #1082 and all already merged remediation remain valid evidence. The open issues above now follow this classification ledger and the current programme `docs/agents/programs/FTAI_AI_TRADING_PORTAL_PROGRAM.md`.

## Execution priority after cutover

1. Make old coordinator and obsolete request/producer PRs terminal.
2. Reframe/finish the useful real-data mount repair #1553 if still required by the current environment.
3. Execute #1561 as one vertical product programme; prefer integrating existing code over creating new producers.
4. Only after the #1561 owner journey works, reconsider `DEFER` items from measured need.
