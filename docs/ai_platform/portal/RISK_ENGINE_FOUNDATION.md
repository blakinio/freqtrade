# AI Trading Portal — Risk Engine Foundation

## Scope

P7.1 introduces deterministic risk approval authority under `ai_platform/portal/risk/`. It does not submit orders and it does not add a browser execution path.

The authority chain is:

```text
manual/AI source
    |
    v
TradeIntent
    |
    v
Deterministic RiskService
    |                     |
    v                     v
ApprovedExecutionIntent   RejectedExecutionIntent
    |                     |
    | future P7.2/P3      +--> durable audit / reason evidence
    v
ExecutionAdapter.submit_approved_intent(...)
```

The current P3 `FreqtradeExecutionAdapter.submit_approved_intent` remains fail-closed with `ORDER_SUBMISSION_NOT_IMPLEMENTED`. P7.1 does not change or bypass that boundary.

## Immutable policy identity

A P7 risk policy consists of the canonical P1 `RiskPolicyVersion` plus immutable `RiskPolicyLimits`. The service computes the canonical policy hash from the serialized limits and rejects duplicate `(tenant_id, risk_policy_version_id)` identity rather than updating limits in place.

P7.1 registers policies as `PROMOTED` because the slice owns only active deterministic evaluation policy, not a draft/promotion workflow. Future policy changes require a new immutable version identity.

## Deterministic inputs

The caller supplies a `RiskEvaluationSnapshot` containing already-normalized decision-time facts:

- intent notional;
- projected gross exposure;
- projected open-position count;
- current daily loss;
- current drawdown;
- runtime health.

Projected values are explicit inputs. The risk engine does not infer hidden portfolio effects or silently query Freqtrade.

## Gate order and reason codes

Evaluation order is stable:

1. tenant/environment kill switch;
2. maximum order notional;
3. maximum projected gross exposure;
4. maximum projected open positions;
5. maximum daily loss;
6. maximum drawdown;
7. runtime health.

Machine-readable rejection codes are stable and attributable:

- `KILL_SWITCH_ACTIVE`;
- `ORDER_NOTIONAL_LIMIT_EXCEEDED`;
- `GROSS_EXPOSURE_LIMIT_EXCEEDED`;
- `OPEN_POSITION_LIMIT_EXCEEDED`;
- `DAILY_LOSS_LIMIT_EXCEEDED`;
- `DRAWDOWN_LIMIT_EXCEEDED`;
- `RUNTIME_UNHEALTHY`.

A fully passing evaluation uses `RISK_APPROVED` as the required non-empty canonical decision reason.

Every decision also contains ordered `RiskLimitEvaluation` evidence with configured value, observed value and pass/fail state.

## Kill switch

Kill-switch state is scoped by tenant and environment. Activation and release require canonical `risk.manage` permission and write canonical audit evidence. An active switch always rejects new approval authority before execution submission can be considered.

The kill switch blocks new approvals; it does not directly manipulate runtime containers. Runtime emergency behavior remains an explicit execution/orchestration concern.

## Permissions

- risk policy registration/read and kill-switch mutation/read: `risk.manage`;
- manual trade-intent evaluation: `trade.manual_execute`.

Tenant identity comes from trusted `RequestContext`; the P7.1 service does not accept a caller-selected tenant parameter.

## Transaction and evidence model

For each evaluated manual intent, one database transaction persists:

- canonical `TradeIntent`;
- canonical `RiskDecision`;
- canonical `trade.manual_intent` audit event;
- `trade_intent.created` outbox event;
- `risk.approved` or `risk.rejected` outbox event.

An outbox persistence failure rolls back the intent, decision and audit evidence together. The module reuses the P2 canonical audit/outbox tables rather than creating a second event system.

## Security boundaries

P7.1 intentionally does not:

- import or call `FreqtradeExecutionAdapter`;
- submit an order;
- query an exchange directly;
- expose a terminal HTTP route;
- change P1 contracts;
- modify P2/P3/P6 owned paths;
- enable live capital.

Only a canonical `ApprovedExecutionIntent` can be eligible for the future execution submission boundary. A rejected result is a separate contract type and cannot satisfy `ExecutionAdapter.submit_approved_intent`.

## P7.2 dependency

P7.2 may add the terminal API/UI only after P7.1 is merged and live repository state is revalidated. The integration must resolve the bot's immutable pinned risk-policy version and normalized decision snapshot server-side before invoking P7.1. It must remain fail-closed while P3 order submission is unsupported.
