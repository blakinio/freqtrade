---
task_id: FTAI-20260726-residual-pytorch-bounded-m1-execution
status: completed
branch: run/residual-pytorch-bounded-m1-execution-v10
base_branch: develop
created: 2026-07-26
updated: 2026-07-27
related_pr: 517
owned_paths:
  - docs/agents/tasks/FTAI-20260726-residual-pytorch-bounded-m1-execution.md
required_reads:
  - AGENTS.md
  - docs/agents/CONTEXT_HANDOFF.md
search_first:
  - versioned successor task ownership
---

# Residual PyTorch P3 bounded M1 execution — retired v1

V1 built and exercised the fail-closed historical-development path for the frozen LightGBM, seeded MLP and residual MLP comparison. It is retired because its frozen `%-volume-change = volume.pct_change()` definition generated infinity when the prior Kraken candle volume was zero.

The versioned successor is `docs/agents/tasks/FTAI-20260727-residual-pytorch-bounded-m1-v2-remediation.md`. V1 must not be modified or rerun.

## Context checkpoint

```yaml
checkpoint_version: 1
updated_at: 2026-07-27T21:30:00Z
head: d88cf99ea2453b00d4314d804a73ff0eb04bad3d
branch: run/residual-pytorch-bounded-m1-execution-v10
pr: 517
status: ready
context_routes:
  - docs/agents/CONTEXT_HANDOFF.md
  - docs/agents/tasks/FTAI-20260727-residual-pytorch-bounded-m1-v2-remediation.md
owned_paths:
  - docs/agents/tasks/FTAI-20260726-residual-pytorch-bounded-m1-execution.md
proven:
  - Guarded run 30299203871 passed exact request validation, both pre-May Kraken data jobs and combined pre-fit coverage verification.
  - Artifact 8667673779 with digest sha256:f02fa4e18350c4feb745ca80c105be1c4245f6a79af18d9a6359b8c0bf346575 preserved the exact first failure.
  - BTC/USDT and ETH/USDT each raised Expanded feature %-volume-change_gen_*_15m contains infinity.
  - The matrix audit failed closed, all three comparator executions were skipped, and no consumed May-June historical OOS or protected final holdout was used.
  - PR 517 was closed without merge and terminal evidence was merged through PR 534 as 351567d57760305b992fb1e441205dc32890dc2a.
derived:
  - Repeating the unchanged v1 request would reproduce the same invalid matrix and is not authorized.
unknown: []
conflicts: []
first_failure:
  marker: EXPANDED_VOLUME_CHANGE_INFINITY
  evidence: runtime/backtest.log in artifact 8667673779 records both pair-level exceptions.
rejected_hypotheses:
  - Data coverage failed; all coverage gates passed.
  - A comparator model failed; no comparator was started.
changed_paths:
  - docs/agents/tasks/FTAI-20260726-residual-pytorch-bounded-m1-execution.md
validation:
  - command: run 30299203871 and artifact 8667673779 inspection
    result: FAIL
    evidence: Exact non-finite feature was identified before model execution.
blockers: []
next_action: Continue only through docs/agents/tasks/FTAI-20260727-residual-pytorch-bounded-m1-v2-remediation.md; v1 is retired and must not be rerun.
```
