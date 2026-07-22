# AI Trading Portal — Execution Adapter

## Scope

P3 implements the first concrete private execution boundary behind the P1 `ExecutionAdapter` protocol. It provides deterministic runtime identity, isolated per-bot workspaces, dry-run-only configuration enforcement, a Docker CLI runtime driver and explicit lifecycle/health mapping.

P3 does not expose Freqtrade to browser-facing code, does not publish runtime ports, does not retrieve exchange credentials, does not enable live capital and does not implement order submission or portfolio/trade queries.

Canonical implementation path:

```text
ai_platform/portal/execution/
```

## One bot to one runtime

Runtime identity is deterministic from the tuple:

```text
(tenant_id, bot_id)
```

The external runtime identifier is a SHA-256-derived opaque value. Tenant and bot values are not placed directly into Docker labels.

Each runtime receives one isolated workspace:

```text
<workspace-root>/<runtime-id>/
  config.json
  runtime-manifest.json
```

`runtime-manifest.json` stores only private operational metadata needed to verify tenant/bot identity, immutable config revision, image/strategy identity, configuration hash, correlation context and the latest machine-readable driver error code. It stores no exchange credential values.

## Artifact resolver boundary

`RuntimeArtifactResolver` is injected into `FreqtradeExecutionAdapter` and resolves a `BotInstance` to:

- a Freqtrade runtime image;
- a strategy name;
- a non-secret base configuration.

P3 intentionally does not choose the final artifact registry, deployment controller or exchange-connection metadata provider. Those remain replaceable integration decisions.

The resolver cannot bypass P3 safety policy. Before a runtime configuration is written, P3:

1. rejects credential-bearing configuration fields;
2. requires non-secret `exchange.name` metadata;
3. forces `dry_run = true`;
4. forces `api_server.enabled = false`;
5. forces `telegram.enabled = false`;
6. pins the pair whitelist, timeframe, stake currency and dry-run wallet from the immutable `BotSpec`.

P3 accepts only `ExecutionMode.DRY_RUN`. `simulated` belongs to the P10a exchange simulator and live-capital execution is not represented by the P1/P3 contract.

## Immutable runtime revision

A provisioned runtime record pins:

- `tenant_id` and `bot_id`;
- deterministic `runtime_id`;
- `config_revision`;
- runtime image;
- strategy name;
- SHA-256 of canonical runtime configuration.

Provisioning the same bot/revision is idempotent when those identities remain unchanged.

Changing config revision, image, strategy identity or generated runtime configuration is rejected. P3 does not silently mutate a provisioned immutable revision. A later orchestration work package must define explicit teardown/recreate or replacement-runtime semantics.

## Private Docker boundary

`DockerCliRuntimeDriver` uses argument-array subprocess execution and never invokes a shell.

Provisioning creates a container with:

- deterministic private runtime name;
- private correlation/request labels;
- hashed tenant/bot labels;
- one bind mount for the bot-specific workspace;
- no `-p`, `--publish` or `--publish-all` option;
- fixed Freqtrade config path inside `/freqtrade/user_data`.

The driver implements private lifecycle operations using Docker create/start/unpause/pause/stop/inspect. No public Freqtrade REST or WebSocket route is introduced.

## Desired runtime lifecycle

P3 maps driver state to the P1 observed-state vocabulary:

| Driver state | Observed state |
| --- | --- |
| missing | `ERROR` |
| created | `CREATED` |
| restarting | `STARTING` |
| running | `RUNNING` |
| paused | `PAUSED` |
| exited/dead | `STOPPED` |

Start, pause and stop operations are idempotent at the driver boundary. A pause request against a non-running created/stopped runtime does not fabricate a `PAUSED` state.

## Health and deterministic failures

Driver failures carry machine-readable reason codes such as:

```text
DOCKER_CREATE_FAILED
DOCKER_START_FAILED
DOCKER_PAUSE_FAILED
DOCKER_STOP_FAILED
DOCKER_INSPECT_FAILED
DOCKER_STATE_UNKNOWN
RUNTIME_MISSING
```

A lifecycle driver failure returns `RuntimeStatus(observed_state=ERROR)` and persists the reason code in the private runtime manifest. `get_health()` reports the persisted failure as `UNHEALTHY` until a successful lifecycle/status observation clears it.

Healthy-state mapping is:

- running: `HEALTHY`;
- created/starting/paused/stopped: `DEGRADED` with an explicit reason code;
- missing or driver failure: `UNHEALTHY`.

## Correlation

Provisioning propagates P1 correlation identity into private Docker labels and the runtime manifest:

```text
request_id
correlation_id
causation_id
```

Raw tenant and bot identifiers are represented in Docker labels only as short SHA-256-derived hashes. The private manifest retains authoritative tenant/bot identity for server-side isolation checks.

## Fail-closed trading boundary

P3 deliberately does not pretend that trade/portfolio integration exists.

The following protocol methods raise `UnsupportedExecutionOperationError`:

- `submit_approved_intent`;
- `get_open_positions`;
- `get_orders`;
- `get_trades`.

This is safer than returning fabricated empty results or bypassing the deterministic risk-approved execution boundary. A later bounded task must implement a private risk-approved transport before these operations can become functional.

## Security invariants preserved

- no upstream `freqtrade/` core modification;
- no public Freqtrade REST/WebSocket port;
- no browser-facing Freqtrade credential path;
- no raw exchange credential persistence;
- no production-secret retrieval;
- no withdrawal capability;
- no live-capital execution mode;
- no model-to-execution bypass;
- no protected-holdout evaluation or Phase 6 changes;
- frozen thresholds `0.006/-0.009` and authoritative `selected_model = null` remain untouched.
