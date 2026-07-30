# ASE-03 paper/shadow integration

ASE-03 integrates the existing deterministic ASE shadow slice, Portal Risk Core, and private Freqtrade Execution Adapter without adding order submission or live-capital authority.

## Flow

```text
accepted point-in-time events
→ independent simulator evidence
→ independent shadow evidence
→ exact semantic parity gate
→ existing deterministic Risk Core outcome
→ shadow admission (no runtime)
  or
→ private Freqtrade DRY_RUN provisioning/start
→ append-only admission evidence
→ explicit rollback/stop evidence
```

## Simulator parity

The integration compares decision identity, input hashes, feature records, signal semantics, risk outcome, and the no-order boundary. Any mismatch rejects admission before the private runtime is touched.

## Risk approval

The controller consumes `ShadowDecisionEvidence` produced through the existing `Ase00ShadowEngine`, which already evaluates the canonical Portal Risk Core. Paper admission requires:

- matching simulator and shadow evidence;
- `risk_outcome=approved`;
- a concrete signal;
- `no_order_submitted=true` in both evidence records.

A rejected or missing signal cannot provision a runtime.

## Paper boundary

Paper mode uses the already merged `FreqtradeExecutionAdapter` and only calls:

- `provision_bot`;
- `start_bot`;
- `get_health`;
- `stop_bot` during rollback or fail-closed cleanup.

The bot must use `ExecutionMode.DRY_RUN` in `TEST` or `STAGING`. `PRODUCTION`, simulated mode, scope mismatch, unhealthy runtime, adapter failure, and parity failure are rejected.

`submit_approved_intent` is never called. The existing adapter continues to raise `ORDER_SUBMISSION_NOT_IMPLEMENTED` for that operation.

## Audit and rollback

The local integration store persists immutable simulator and shadow evidence by canonical hash and appends admission/rollback records to JSONL. Records contain exact strategy, parity, risk, runtime, reason-code, evidence-reference, idempotency, and source-admission hashes.

Rollback never deletes evidence. Shadow rollback is an audited no-op. Paper rollback stops the private dry-run runtime and records whether `STOPPED` was authoritatively observed.

## Non-goals

ASE-03 does not implement PI-08, submit orders, expose Freqtrade publicly, resolve exchange credentials, enable production/live mode, promote a strategy, consume the protected holdout, or modify upstream Freqtrade core.
