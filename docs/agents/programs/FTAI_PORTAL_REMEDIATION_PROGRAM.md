# AI Trading Portal Remediation Programme — superseded

```yaml
programme_id: FTAI-20260803-portal-remediation
repository: blakinio/freqtrade
programme_lane: freqtrade-portal
status: superseded
superseded_by: ADR-023
superseded_at_develop: 1f62ff29f4a2a25c929218bd3b69bf19257f3055
cutover_issue: 1560
successor_mvp_issue: 1561
historical_programme_blob: f349d7e03b37881a928532d9bad139d32bbb4e94
autonomous_dispatch_enabled: false
live_capital_authorized: false
withdrawals_enabled: false
```

## Authority change

This file was the canonical coordinator for the former 50-Issue PAPER-first/multi-tenant/production-like Portal remediation programme. The owner replaced that current product model for the **entire Portal** through ADR-023, merged by PR #1558 at `develop@1f62ff29f4a2a25c929218bd3b69bf19257f3055`.

The programme is therefore terminally superseded. It MUST NOT dispatch Issue #1132, resume the old S0/F1/R2/P3/D4 dependency graph, wait for old protected-production acceptance gates, or treat all 50 historical audit findings as prerequisites for the current Developer Quant Portal.

The full prior programme, including its 50-Issue inventory, dependency graph, accepted remediation and evidence, remains preserved in Git history at blob `f349d7e03b37881a928532d9bad139d32bbb4e94`. Already merged fixes remain valid current code unless separately changed; this cutover does not revert them.

## Current routing

Use instead:

- current programme: `docs/agents/programs/FTAI_AI_TRADING_PORTAL_PROGRAM.md`
- governing product decision: `docs/ai_platform/portal/ADR-023_DEVELOPER_QUANT_PORTAL.md`
- canonical cutover ledger: `docs/ai_platform/portal/ADR023_BACKLOG_RECLASSIFICATION_2026-08-15.md`
- cutover Issue: #1560
- current P1 owner workflow: #1561

Every formerly open remediation item is now exactly one of `KEEP_NOW | SIMPLIFY | DEFER | OBSOLETE`. Do not infer priority from this historical programme.

## Historical completed remediation

Before supersession, Issues #1101, #1116, #1122, #1124, #1126 and #1127 were terminally completed, and repository implementation for #1137 had merged through PR #1154. These facts remain historical/current implementation evidence. ADR-023 changes the product target and remaining acceptance requirements; it does not falsify completed work.

## Current completion rule

The current Portal is judged by the real owner-facing workflow:

`REALTIME_PUBLIC -> WickHunter decisions incl NO_TRADE -> simulated positions/outcomes -> durable dataset growth -> LOCAL challenger training -> active/challenger comparison -> deliberate owner activation -> restart-safe Portal observation`

Real-money exchange execution, private order credentials, withdrawals and capital authority are outside the current product.
