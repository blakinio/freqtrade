# ASE-00 validation report

## Last complete post-merge validation

- workflow: `AI Strategy Engine`
- run ID: `30364326953`
- job ID: `90291563081`
- validated commit: `378bd45ec4706ca61af08f093f838c60e7da750a`
- conclusion: `success`

## Passed checks

| Check | Result |
|---|---|
| package tests | passed |
| Ruff | passed |
| mypy | passed |
| compileall | passed |
| deterministic repository E2E | 12 scenarios passed |
| JSON and YAML parsing | passed |
| JSON Schema example validation | passed |
| materialization evidence and required paths | passed |
| secret scan | passed |
| prohibited `eval` and `exec` scan | passed |
| proprietary runtime reference scan | passed |
| Browser-to-Freqtrade boundary scan | passed |
| direct execution import scan | passed |

## Validated behavior

The repository E2E suite covers:

- complete synthetic shadow flow using the existing Portal Risk Core;
- exact duplicate idempotency;
- delayed event accepted only before decision time;
- out-of-order normalization;
- future feature rejection;
- unconfirmed pivot rejection;
- unconfirmed HTF rejection;
- preservation of Risk Core rejection;
- deterministic restart and replay;
- missing liquidation data rejection;
- conflicting duplicate rejection;
- absence of execution and Freqtrade dependencies in the adapter.

## Exact-head policy

This report replaces historical intermediate failure logs. The permanent workflow `.github/workflows/ai-strategy-engine.yml` reruns the complete matrix after any Strategy Engine, adapter, E2E or workflow change. The exact final cleanup HEAD and workflow run are recorded in draft PR #584 without modifying the validated implementation afterward.
