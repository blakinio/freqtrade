# BM-07 Position and Order Command Activation

## Purpose

BM-07 connects already-authorized BM-03 position and order command intents to the private dry-run execution boundary delivered by PI-07 and PI-08. It does not add new browser authority and does not authorize live capital.

The activation sequence is:

```text
trusted command context + immutable command
  -> BM-03 authorization, revision, freshness and kill-switch decision
  -> durable PENDING_RECONCILIATION reservation
  -> PI-07 runtime credential lease
  -> private TLS dry-run verification
  -> bounded Freqtrade command
  -> secret-free acknowledgement or ambiguity
  -> authoritative PI-01 reconciliation
```

The pending-reconciliation transition is written before any runtime call. Replaying the same command therefore returns the existing attempt reference and never repeats the private mutation blindly.

## Activated command mapping

| Product command | Private runtime operation | Exposure behavior |
|---|---|---|
| `CLOSE_POSITION` | `POST /api/v1/forceexit` for the exact source trade | reduces exposure |
| `PARTIAL_CLOSE` | `POST /api/v1/forceexit` with a bounded amount | reduces exposure |
| `CLOSE_ALL` | `POST /api/v1/forceexit` with `tradeid=all` | reduces exposure |
| `FORCE_TAKE_PROFIT` | exact-position force exit | reduces exposure |
| `CANCEL_ORDER` | `DELETE /api/v1/trades/{tradeid}/open-order` | does not increase exposure |
| `CANCEL_ALL_ORDERS` | deterministic, sorted cancellation of current authoritative orders | does not increase exposure |
| quantity-only `REPLACE_ORDER` | cancel current order, then submit the exact risk-approved PI-08 replacement | increase path is re-risked |
| DCA/grid entry | PI-08 approved-execution submission | increases exposure only after risk approval |

Price-changing replacement is rejected because Freqtrade does not provide a native, atomic replacement operation at this boundary. Cancel-then-recreate with a browser-selected price would create an unsafe partial-success path and is not represented as atomic replacement.

## Evidence requirements

Every non-bulk position or order command must carry one exact authoritative evidence record with:

- tenant, bot and runtime scope;
- source position/order identity and revision;
- exact source trade identity used by the private runtime adapter;
- market side, amount and observation time.

Cross-tenant, cross-bot, cross-runtime, duplicate, missing or stale evidence fails closed. BM-03 independently verifies command capability, actor, environment, immutable config/runtime revision, current runtime freshness and kill-switch policy.

## Runtime and credential safety

- Targets reuse the PI-08 `PrivateRuntimeTarget`: HTTPS only, private address/name, explicit CA, no embedded credentials.
- Transport disables redirects and proxy-environment routing and uses bounded timeout/body limits.
- PI-07 leases are exact-tenant, exact-connection, exact-exchange and exact-runtime, and are cleared after use.
- Runtime dry-run configuration is independently checked before every mutation.
- Acknowledgements contain only opaque request references, hashes and timestamps. They never contain credentials, endpoints or raw responses.
- `execution_proven` is always false until authoritative reconciliation.

## Replay and ambiguity

A command is persisted as `PENDING_RECONCILIATION` before network I/O. The deterministic attempt reference is bound to the exact command serialization.

- An exact retry returns `REPLAY_PENDING` and performs no second mutation.
- Timeout, retryable server failure, malformed body or unknown partial outcome is `AMBIGUOUS`.
- Explicit runtime rejection is `REJECTED` but remains linked to the durable attempt.
- Neither acknowledgement nor ambiguity is execution proof.

## DCA, grid and replacement

BM-07 does not create a second exposure-increasing transport. DCA, grid entries and the new side of a quantity-only replacement delegate to PI-08, preserving risk approval, PI-07 credential scope, idempotency and authoritative reconciliation.

## Non-goals

- no browser-to-Freqtrade path;
- no public runtime endpoint;
- no live or production execution mode;
- no withdrawals;
- no automatic strategy/model promotion;
- no claim that repository CI proves real Synology/Vault/Freqtrade target acceptance;
- no price-changing or atomic exchange-order replacement where the runtime lacks that capability.
