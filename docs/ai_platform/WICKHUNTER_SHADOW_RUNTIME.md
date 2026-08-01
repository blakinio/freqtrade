# WickHunter Shadow Runtime v1

## Scope

WH-07 provides a continuous, deterministic and read-only shadow/paper runtime around the
accepted WickHunter contracts. It consumes caller-supplied current evidence and never imports
an exchange client, private endpoint, credential provider or order adapter.

The runtime reuses the existing pure decision seam:

```text
ShadowDecisionRequest
  -> evaluate_shadow_decision
  -> candidate
  -> advisory score
  -> WickHunterTradeIntent
  -> deterministic local RiskDecision
  -> simulated position only
```

`BotMode.LIVE_BLOCKED` is structurally refused. Every observability snapshot records
`read_only=true`, `trading_credentials_present=false`, `order_adapter_present=false`,
`orders_submitted=0` and `live_capital_authorized=false`.

## Runtime inputs

A `ShadowRuntimeTick` binds:

- one monotonic observation timestamp;
- one current `DynamicUniverseSnapshot`;
- zero or more `ShadowDecisionRequest` values using that exact universe and bot identity;
- sorted mark prices;
- sorted liquidation source states;
- model and data drift state;
- validation and retraining state labels.

All network acquisition, catalog refresh and source collection remain outside WH-07. This keeps
the runtime provider-neutral and lets trusted deployment code supply already accepted,
decision-time-safe evidence.

## Fail-closed behavior

New decisions are not evaluated when any required dependency is unsafe. Circuit-breaker reasons
include:

- future or stale universe snapshots;
- insufficient fresh liquidation sources;
- individual unhealthy, missing or stale sources;
- model or data drift that is not healthy;
- maximum simulated drawdown reached.

Existing simulated positions continue to receive mark updates while new entries are blocked.
Ticks must be strictly increasing, and one tick cannot mix dataset, code, model or parameter
identities.

## Simulation

A locally allowed intent creates a deterministic simulated position. Quantity is derived from the
configured simulated equity and the larger of base or bounded DCA total risk, multiplied by the
requested leverage. TP and SL prices come directly from the accepted intent. Marks close long or
short positions deterministically at the frozen TP/SL level and update realized PnL, unrealized
PnL, equity, peak equity and drawdown.

No fee or slippage convention is recomputed in the runtime. Replay policy identity is verified
through `verify_replay_shadow_parity`, which requires the exact dataset hash, source code SHA,
symbol, side, decision timestamp, TP and SL policy from the accepted WH-02 label. The label must
also prove that credentials, execution, orders and live-capital authority are absent.

## Persistence and restart

`ShadowRuntimeStore` writes the canonical restart state and the latest read-only Portal snapshot
atomically per file with `fsync` and `os.replace`. The state file includes the canonical state
SHA-256, while `portal-observability-snapshot.json` is the stable WH-08 input. Load rejects
malformed content, schema mismatch, symlinks and any integrity mismatch. Runtime identity and
policy must match before restart.

The persisted state contains only bounded simulation state and identities:

- generation and last observation;
- universe identity;
- open and closed simulated positions;
- realized PnL, peak equity and drawdown;
- bounded recent decision IDs;
- model, parameter, dataset and code identities.

## Portal producer contract

`PortalObservabilitySnapshot` is the stable WH-07 producer contract for WH-08. It is a frozen,
read-only value containing:

- bot mode and health;
- current dynamic universe;
- per-source freshness;
- model, parameter, dataset and code identities;
- latest candidate/risk summaries;
- simulated positions, realized/unrealized PnL, equity and drawdown;
- retraining, validation and drift state;
- circuit-breaker state and reasons;
- persistence generation and runtime state hash;
- explicit zero-authority fields.

WH-08 may render this snapshot but must not mutate it or add trade controls.
