# WickHunter portal Risk Engine integration

## Scope

WH-06 defines the fail-closed seam between strategy-owned WickHunter evidence and the existing canonical portal risk contracts. The implementation is intentionally contained under `ai_platform/wickhunter/` and consumes portal contracts without modifying portal, bot-management, execution or database paths.

The authority chain is:

```text
WickHunterTradeIntent
  -> strategy-owned WickHunter risk allow/reject
  -> conservative portal TradeIntent + RiskEvaluationSnapshot mapping
  -> canonical portal risk authority result
  -> immutable request/result evidence bundle
```

A local WickHunter rejection is terminal. It cannot be converted into a portal request and can never be overridden by a later authority.

## Canonical portal seam

The bridge consumes the existing versioned portal contracts:

- `ai_platform.portal.contracts.risk.TradeIntent`;
- `ai_platform.portal.risk.schema.RiskEvaluationSnapshot`;
- `ai_platform.portal.contracts.risk.ApprovedExecutionIntent`;
- `ai_platform.portal.contracts.risk.RejectedExecutionIntent`.

It does not call `ExecutionAdapter.submit_approved_intent`, the manual trade service, a browser route, Freqtrade, an exchange or a credential broker.

## Mapping rules

`build_portal_risk_request` requires:

- a WickHunter intent already allowed by the pure strategy-owned Risk Engine;
- exact equality between the local and portal risk-policy version identities;
- a portal snapshot observed no later than the local risk evaluation;
- a non-production environment compatible with the WickHunter mode;
- positive account equity and decimal-safe exposure inputs.

The portal amount is conservative. Planned notional uses the larger of base risk and total bounded DCA risk, multiplied by account equity and requested leverage. The canonical base amount is that notional divided by the decision price.

Projected gross exposure and open positions include the new intent. Daily loss, drawdown and runtime health retain their trusted snapshot values.

## Environment policy

Allowed mappings are deliberately narrow:

| WickHunter mode | Allowed portal environment |
| --- | --- |
| `research` | `research`, `test` |
| `shadow` | `test`, `staging` |
| `paper` | `staging` |
| `live_blocked` | none |

`production` is rejected structurally.

## Identity and validation

Portal UUID identities and correlation context are deterministic UUIDv5 values derived from immutable WickHunter identities. A returned portal result is accepted only when tenant, TradeIntent, policy version, intent identity, correlation identity and wrapper/outcome semantics match the prepared request.

Any mismatch fails closed with `PortalRiskEvidenceMismatchError`.

## Deterministic persistence

`persist_portal_risk_evidence` writes an atomic no-overwrite directory named by the request SHA-256:

```text
<output-root>/<request-sha256>/
  request.json
  result.json       # only after a terminal portal result
  manifest.json
```

The manifest binds exact file hashes and records:

```json
{
  "order_submission_performed": false,
  "execution_adapter_called": false,
  "live_capital_authorized": false
}
```

A prepared request may be persisted before a result. Reusing the same final identity is rejected rather than overwritten.

## Explicit non-capabilities

WH-06 does not:

- activate the portal manual-intent flow;
- create an API/BFF endpoint;
- register or mutate portal risk policies;
- change bot-management contracts;
- resolve exchange credentials;
- call an execution or order adapter;
- authorize production or live capital;
- claim replay, strategy, model or profitability evidence.

A future runtime package may invoke the reviewed portal authority through a separately owned adapter, but it must preserve this request/result validation and deterministic evidence contract.
