# ADR-023 Portal/WickHunter backlog cutover — completed

```yaml
task_id: FTAI-20260815-portal-adr023-backlog-cutover-1560
status: completed
related_issue: 1560
cutover_pr: 1564
cutover_merge_sha: ff4979f5c14b0d584d11eaff4260a65423abf3aa
closeout_pr: pending
result: ADR_023_BACKLOG_CUTOVER_COMPLETE
successor_product_issue: 1561
next_action: none
```

ADR-023 is now the current product authority for the entire Portal. The former PAPER-first / SHADOW-PAPER-LIVE / multi-tenant / production-certification work graph was reclassified through the canonical `KEEP_NOW | SIMPLIFY | DEFER | OBSOLETE` ledger; obsolete legacy work and request-only PRs were made terminal while reusable real-data/runtime/simulation/model components were preserved.

Programme parent #1211 now names **Developer Quant Portal** and routes the sole current P1 owner-facing product journey to Issue #1561:

`REALTIME_PUBLIC -> WickHunter decisions incl NO_TRADE -> simulation/outcomes -> durable dataset -> LOCAL challenger training -> ACTIVE/CHALLENGER comparison -> deliberate owner activation -> restart-safe Portal observation`

Useful Market Evidence host-mount repair #1553 merged before the cutover. PR #1564 merged the cutover to `develop` as `ff4979f5c14b0d584d11eaff4260a65423abf3aa` with its product/browser/core checks green. A legacy completeness-audit Issue-state check is retained only for pre-ADR-023 authority and is not a current Portal delivery blocker when `ARCHITECTURE_REGISTRY.yaml` proves ADR-023 is the active product overlay.

No real exchange orders, private trading credentials, withdrawals or capital authority were introduced by this task.
