# Clean-sheet technical architecture proposal

Status: proposal; does not supersede accepted ADR authority.

## Target split

```text
                          Next.js / TypeScript Portal
                                     |
                              same-origin API/BFF
                                     |
                        Rust platform/control services
                   _________|___________|____________
                  |                     |            |
             Market Data          Bot Runtime     Simulator
              / streams          supervision      event engine
                  |                     |            |
                  +---------------------+------------+
                                        |
                              durable event/data layer
                                        |
                         +--------------+--------------+
                         |                             |
                   Python ML/Research              AI Research
                 LightGBM / XGBoost /             Ollama/local LLM
                 PyTorch / tuning                  bounded context
                         |                             |
                         +--------------+--------------+
                                        |
                              model/dataset registry
                                        |
                        BASELINE/CHALLENGER/ACTIVE
```

## Rust responsibilities

Rust is the preferred clean-sheet core for components where long-lived concurrency, deterministic state machines, restart safety and resource efficiency matter:

- public exchange WebSocket ingestion and reconnection;
- normalization and event streaming;
- deterministic simulator / simulated order and position state;
- bot runtime host, supervision and recovery;
- event aggregation and durable runtime journaling boundaries;
- performance-sensitive replay/backtest kernels where profiling justifies it;
- a future separately-authorized Execution/Capital Gateway, if such a programme is ever approved.

Rust is not selected merely to maximize the percentage of Rust in the repository.

## Python responsibilities

Python remains the primary research/ML environment:

- feature engineering and exploratory analysis;
- dataset materialization and validation;
- LightGBM, XGBoost, scikit-learn;
- PyTorch where neural models are justified;
- hyperparameter tuning;
- training/evaluation orchestration;
- challenger creation and comparison logic where Python libraries provide leverage;
- research notebooks/scripts and offline tooling.

The heavy numerical work in these libraries is already native code; rewriting orchestration in Rust is not automatically a performance win.

## Ollama/local LLM responsibilities

Ollama is an optional research service, normally on the local training workstation:

- analyze backtests/experiments/logs;
- summarize model degradation and regime behaviour;
- propose hypotheses or experiment drafts;
- explain provenance-linked results.

The persistent trading/simulation runtime must remain healthy when Ollama or the local PC is offline. LLM output is advisory; it cannot silently promote a model or create capital/execution authority.

## Portal responsibilities

Next.js/TypeScript remains appropriate for the interactive UI. The browser talks only to the Portal same-origin boundary; it does not speak directly to Freqtrade, runtime supervisors, exchange APIs or model workers.

The UI consumes platform-owned contracts rather than Freqtrade schemas. This keeps the frontend stable while execution/research adapters are replaced behind the boundary.

## Persistent runtime placement

Under current ADR-025 authority:

- Synology is the normal persistent application/runtime/storage host;
- the local workstation is a permitted training/research node;
- GitHub-hosted Actions remains the stateless CI/build/test/scan/disposable-compute plane;
- GitHub Actions is not a 24/7 runtime.

A clean-sheet implementation may revisit service decomposition but must not silently change this accepted placement policy without a new architecture decision.

## First vertical slice

The first v2 implementation milestone should be deliberately small:

```text
public exchange WS
  -> normalized market event
  -> WickHunter/native strategy evaluation
  -> deterministic simulated execution
  -> durable decision/outcome record
  -> Portal Bot Detail + Decision Inspector
```

Acceptance for that slice should emphasize exact causal traceability, restart recovery and no dependency on the legacy Freqtrade UI/control surface.
