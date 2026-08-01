# WickHunter Paper Validation v1

## Scope

WH-09 turns the merged WH-07 runtime and WH-08 read model into immutable shadow/paper
activation and evidence packages. It does not promote a model or parameter set automatically and
never grants credentials, order submission, execution or live-capital authority.

The default policy requires a real observation window of at least 24 hours, at least 96 distinct
snapshots and no gap longer than 30 minutes. These thresholds are contract defaults and must not
be shortened to manufacture a terminal program result.

## Activation package

`build_paper_run_request` freezes:

- run creation time and exact observation window;
- bot identity and `shadow` or `paper` mode;
- candidate model and parameter versions and hashes;
- dataset and exact Git code identity;
- explicit rollback model and parameter identities;
- WH-07 snapshot schema and WH-08 consumer version;
- the self-hashed validation policy;
- all zero-authority fields.

`publish_paper_run_request` creates one no-overwrite activation directory containing the policy,
request, self-hashed activation manifest and complete checksum index. The run ID is derived from
all immutable request fields. Reusing or overwriting an activation directory is refused.

Activation is request-only. It does not start an exchange connection, place an order or imply that
the observation window has completed.

## Evidence inputs

Evidence evaluation accepts only exact request-bound values:

- ordered `PortalObservabilitySnapshot` records from WH-07;
- accepted `ReplayShadowParityEvidence` for every simulated-allowed decision;
- explicit read-only exercises for stale-source, model-drift, circuit-breaker and restart recovery.

Each observation binds the snapshot hash, generation, bot/mode, model, parameter, dataset and code
identities, source freshness, decisions, risk rejections, positions, PnL, equity, drawdown, drift
and circuit-breaker state. Any identity mismatch, duplicate snapshot, non-monotonic timestamp,
out-of-window record or unsafe authority is rejected.

## Terminal policy

A report is `ready_for_owner_review` only when all policy gates pass:

- minimum real duration and snapshot count;
- bounded maximum gap;
- minimum fresh-source ratio;
- candidate, allowed and risk-rejected decision evidence;
- drawdown within policy;
- replay/shadow parity for every allowed decision;
- all mandatory safety exercises passed and recovered.

Otherwise the report remains `incomplete` with deterministic blocker codes. An incomplete report
cannot produce an eligible promotion candidate.

## Candidate review boundary

The candidate package contains the exact candidate and rollback model/parameter identities. It is
only an owner-review package. It always records:

```text
owner_decision_required=true
automatic_promotion_enabled=false
trading_credentials_present=false
execution_enabled=false
orders_submitted=0
live_capital_authorized=false
```

No WH-09 result authorizes live deployment or capital.

## Publication and verification

`publish_paper_validation_package` writes one atomic no-overwrite directory containing:

- policy and immutable request;
- canonical observation, parity and safety-exercise JSONL;
- report and candidate-review package;
- self-hashed manifest;
- complete SHA-256 checksum index.

`verify_paper_validation_package` independently checks the exact file set, regular-file boundary,
all checksums, manifest self-hash, run/report/review identities and zero-authority fields. Any
mutation is rejected.

## Program closure rule

Merging the WH-09 implementation proves only that the activation and evidence machinery is ready.
The WickHunter rollout must remain `waiting` after activation until the actual immutable window
has elapsed and terminal evidence has been independently verified. Chat history, synthetic tests
or a shortened policy are not evidence of a sustained production shadow/paper run.
