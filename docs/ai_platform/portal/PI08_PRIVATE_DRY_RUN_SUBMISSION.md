# PI-08 Private Dry-Run Approved Execution Submission

## Purpose

PI-08 activates one private, server-side submission path for an already risk-approved execution intent. It does not create approval authority, does not expose Freqtrade to the browser, and does not authorize live capital.

The path is intentionally split into durable phases:

```text
ApprovedExecutionIntent
  -> exact tenant/bot/config/runtime binding
  -> current runtime + healthy + kill switch off
  -> durable idempotent reservation
  -> PI-07 five-minute credential lease
  -> private TLS show_config dry-run proof
  -> private forceenter request
  -> acknowledgement or ambiguity
  -> PI-01 authoritative order reconciliation
```

An HTTP response is never execution proof. Only matching, current, complete and synchronized runtime evidence can complete reconciliation.

## Security invariants

- `ExecutionMode.DRY_RUN` is mandatory and `Environment.PRODUCTION` is rejected by contract.
- The approved intent, authoritative runtime state and execution binding must match exactly for tenant, bot, configuration revision, runtime identity, runtime revision, environment and correlation.
- Approval must be unexpired.
- Runtime evidence must be current, health must be `HEALTHY`, and the kill switch must be inactive.
- The credential lease must match the exact tenant, exchange connection, opaque credential reference, exchange and runtime.
- Runtime credentials exist only inside the bounded PI-07 lease callback and are cleared when the lease closes.
- Runtime targets require HTTPS, a private hostname/address and an explicit CA file. Redirects, proxy environment variables, embedded credentials and public endpoints are rejected.
- `/api/v1/show_config` must independently report `dry_run=true` and `force_entry_enable=true` before submission.
- Browser-facing contracts contain no credential values, private endpoint, Vault path or runtime authentication data.

## Idempotency and ambiguity

The service writes a `CREATED` attempt before any network request. Tenant-scoped uniqueness is enforced for:

- idempotency key;
- command ID;
- approved execution-intent ID.

An exact replay returns the stored receipt without a second runtime request. A conflicting replay fails closed. A timeout, network failure, retryable server response, oversized body or malformed success response after submission is recorded as `AMBIGUOUS`; it is not automatically retried.

## Acknowledgement and reconciliation

A valid Freqtrade response creates an `ACKNOWLEDGED` attempt with `execution_proven=false` and a pending reconciliation record. The opaque runtime request reference is retained, but the raw response and credentials are not persisted.

Reconciliation succeeds only when PI-01 provides exactly one order that:

- has the expected execution-intent attribution;
- belongs to the exact tenant, bot and runtime;
- was observed no earlier than the attempt;
- comes from a current, complete and synchronized runtime read.

No match remains pending, duplicate matches become a conflict, and a governed timeout becomes failed reconciliation.

## Composition

`PrivateSubmissionExecutionAdapter` is additive. It delegates lifecycle and read operations to the existing private execution adapter and replaces only `submit_approved_intent` when trusted server composition explicitly injects the PI-08 submitter. The default `FreqtradeExecutionAdapter` remains fail-closed with `ORDER_SUBMISSION_NOT_IMPLEMENTED`.

## Deployment boundary

Repository tests prove contracts, persistence, redaction, transport policy and deterministic reconciliation behavior. They do not prove a real Synology Vault/Freqtrade deployment. Target acceptance requires owner-managed TLS material, private routing, credentials, Vault initialization and dry-run runtime evidence.

## Non-goals

- position, order, DCA, TP/SL or grid command activation; those belong to BM-07;
- public or browser-addressable Freqtrade APIs;
- production credentials, withdrawals, live-small or P14;
- treating an acknowledgement as an executed order;
- claiming repository CI as real target-environment acceptance.
