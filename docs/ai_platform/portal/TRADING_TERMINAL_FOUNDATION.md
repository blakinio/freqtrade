# Trading Terminal Foundation

## Boundary

P7.2 exposes manual trading as intent, never as direct browser execution.

```text
Browser
  -> same-origin Next.js BFF
  -> Portal `/v1/terminal/intents`
  -> tenant-scoped BotSpec lookup
  -> server-side trusted RiskEvaluationSnapshot provider
  -> deterministic P7 RiskService
  -> ApprovedExecutionIntent only
  -> private execution submitter boundary
```

The browser may submit only `bot_id`, `pair`, `side` and `amount`. It cannot supply exposure, loss, drawdown, runtime-health or risk-policy facts.

## Immutable policy resolution

The terminal resolves `risk_policy_version` and `environment` from the current immutable `BotSpec`. Pair selection must belong to the bot's immutable pair universe.

## Fail-closed execution

Rejected risk decisions never invoke the execution submitter. Approved decisions may reach only an injected `ApprovedIntentSubmitter` boundary. The default submitter preserves the existing P3 behavior and returns `ORDER_SUBMISSION_NOT_IMPLEMENTED`, surfaced as terminal state `BLOCKED` rather than pretending an order was executed.

## Trusted snapshot provider

The default provider is unavailable and raises `RISK_SNAPSHOT_UNAVAILABLE`. A deployment or deterministic simulator must inject a provider backed by trusted server-side runtime/position/PNL state. Browser payloads are explicitly rejected if they contain undeclared snapshot fields.

## Web surface

`/terminal` renders the risk-gated intent form. `/api/terminal` is a same-origin BFF route that validates the narrow intent payload and forwards only the existing authenticated cookie to the private portal API.

## Safety invariants

- no browser-to-Freqtrade or browser-to-exchange path;
- no manual intent bypasses deterministic risk evaluation;
- rejected intent cannot reach execution;
- missing trusted snapshot data fails closed;
- current P3 order submission remains unsupported until a separately coordinated execution implementation exists;
- no live-capital authorization is introduced.
