from pathlib import Path


task_path = Path("docs/agents/tasks/FTAI-20260731-wickhunter-wh01-production-materialization-v1.md")
task = task_path.read_text(encoding="utf-8")
status_old = "## Status\n\n`validating`"
status_new = "## Status\n\n`completed`"
if task.count(status_old) != 1:
    raise SystemExit("task status anchor mismatch")
task = task.replace(status_old, status_new, 1)
terminal_heading = "## Terminal production materialization checkpoint"
if terminal_heading in task:
    raise SystemExit("terminal task checkpoint already exists")
task += """

## Terminal production materialization checkpoint

- canonical metric-binding repair PR #914 passed exact-head AI Platform CI `30692428808`, full Freqtrade CI `30692428826` including CI Gate, and security/zizmor `30692428833` on head `4d9077255753d626058161fa0a71094ed8bc9cd1`;
- PR #914 changed exactly the implementation, focused regression test and this task record, had zero review threads, and merged normally as `2091971608df3c33238c845f5f019a384b231580`;
- request-only PR #921 added exactly one workflow relative to that merged code SHA and closed without merge after terminal success;
- trusted-runner workflow `30693346424`, job `91351904433`, completed successfully on `freqtrade-synology-staging`;
- immutable dataset: `wickhunter-wh01-production-dataset-20260731-v3-2091971608df-eaccc5ec-8f5be573`;
- immutable root: `/var/lib/freqtrade-staging-state/wickhunter-production-datasets/wickhunter-wh01-production-dataset-20260731-v3-2091971608df-eaccc5ec-8f5be573`;
- dataset manifest SHA-256: `3b0a052d13c8d3684a9bf63712ee00d5a9c09343d14e628c6611a444024b2d51`;
- dataset manifest file SHA-256: `dfddc58ffc7e768d53883bea85dbb860cb0397f3d6995d600c2540530d274bae`;
- dataset request SHA-256: `fbeb64bd364e13c114e15865775fbd1df2c96160e5825f186152c8b611a3716e`;
- source binding SHA-256: `9d4f30c61a9810250ff8786cca69e916e4fe19d8cdfe5d20483150af0ed159bd`;
- materialization SHA-256: `ee4588d56918a79a690ffad965ab4e13014bfd79656880ad4c71bc728c468778`;
- split geometry SHA-256: `cb861e99fc7d2d9b9fd22aa86d4e890595d2765445c5a46b0d0911104ef7cc8b`;
- 154 immutable partitions and 919 rows were independently verified;
- decision range is `1785484861174..1785520559257`;
- ordered train/validation/test windows retain two explicit 30-minute embargo gaps and end before protected holdout `1785542400000`;
- `wh01_ready=true`, `wh01_blocker=null`, `protected_holdout_accessed=false`, `immutable_inputs_mutated=false`, `model_execution_authorized=false`, `replay_authorized=false`, `performance_research_authorized=false`, `execution_enabled=false`, `live_capital_authorized=false`, `trading_credentials_present=false`, `orders_submitted=0`;
- bounded metadata artifact `8816466252` has digest `sha256:816e5b11f9d3c3d3098509d0181b5aff11053cb461c77675ad108af7a0cb1c94` and expires on 2026-08-31;
- Portal runtime/observability is not claimed by this package: WH-08 remains separately gated by WH-07;
- WH-02 is unblocked only at its real accepted immutable dataset dependency and remains `not_started` until a separate governed replay package is opened.

```yaml
checkpoint_version: 6
updated_at: 2026-08-01T11:20:00+02:00
status: completed
implementation_merge: 2091971608df3c33238c845f5f019a384b231580
request_pr: "#921"
request_merged: false
workflow_run: 30693346424
workflow_job: 91351904433
dataset_id: wickhunter-wh01-production-dataset-20260731-v3-2091971608df-eaccc5ec-8f5be573
dataset_manifest_sha256: 3b0a052d13c8d3684a9bf63712ee00d5a9c09343d14e628c6611a444024b2d51
partition_count: 154
total_rows: 919
wh01_ready: true
wh01_blocker: null
protected_holdout_accessed: false
model_execution_authorized: false
replay_authorized: false
performance_research_authorized: false
execution_enabled: false
live_capital_authorized: false
trading_credentials_present: false
orders_submitted: 0
blockers: []
next_action: create a fresh WH-02 deterministic replay and event-label task from current develop, binding this exact immutable dataset without touching the protected final holdout
```
"""
task_path.write_text(task, encoding="utf-8")

program_path = Path("docs/agents/programs/FTAI_WICKHUNTER_LIQUIDATION_BOT_PROGRAM.md")
program = program_path.read_text(encoding="utf-8")
old = (
    "The first real paid bulk Tardis import remains owner/provider-access dependent. "
    "WH-01 provides the accepted-import builder but does not claim a real historical "
    "dataset was purchased, imported or accepted. WH-02 cannot consume or evaluate "
    "real history until such a package passes the unchanged historical acceptance contract."
)
new = (
    "The builder contract is now backed by the first real accepted immutable production "
    "dataset, materialized on the trusted runner by request-only PR #921 from merged code "
    "`2091971608df3c33238c845f5f019a384b231580`. Dataset "
    "`wickhunter-wh01-production-dataset-20260731-v3-2091971608df-eaccc5ec-8f5be573` "
    "contains 154 verified partitions and 919 rows with manifest "
    "`3b0a052d13c8d3684a9bf63712ee00d5a9c09343d14e628c6611a444024b2d51`. "
    "It retains explicit train/validation/test embargoes, excludes the protected holdout, "
    "and authorizes no replay, model execution, trading, orders or live capital. The WH-02 "
    "dataset dependency is therefore satisfied, while WH-02 itself remains not started and "
    "requires a separate governed package."
)
if program.count(old) != 1:
    raise SystemExit("program WH-01 boundary anchor mismatch")
program = program.replace(old, new, 1)
program_path.write_text(program, encoding="utf-8")
