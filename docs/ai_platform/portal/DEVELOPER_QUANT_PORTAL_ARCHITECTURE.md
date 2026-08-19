# Developer Quant Portal Architecture

Status: **owner-accepted current Portal product architecture**  
Owner product decision date: `2026-08-15`  
Related product Issue: `#1555`  
Applies to: **the entire current Portal product**  
Runtime/deployment overlay: **ADR-025**, accepted `2026-08-18`, Issue `#1604`  
Historical runtime overlay: ADR-024, superseded by ADR-025 for current target placement

## 1. Product identity

The current Portal is a **private, single-owner developer/quant/research platform** that continuously works with real public market data, simulation, datasets, experiments and local model development.

It is **not** currently a multi-tenant production trading control plane and it is **not** organized around capital-authority modes.

The current product goal is to let the owner:

- collect and inspect real public exchange data continuously;
- run WickHunter and other research/strategy runtimes against that data;
- record every decision, including `NO_TRADE`, with attributable context;
- simulate positions, lifecycle, PnL, fees, slippage and risk outcomes;
- grow versioned chronological datasets and labels from observed outcomes;
- train local challenger models on accumulated evidence;
- compare active/challenger/baseline models on the same evidence;
- deliberately select an active model without automatic promotion;
- inspect health, logs, data freshness, decisions, simulated positions and model/data drift from the Portal;
- survive restart of the Portal/runtime without losing authoritative developer state.

## 2. Current product vocabulary

The current Portal uses orthogonal developer concepts instead of `SHADOW | PAPER | LIVE` product modes.

### 2.1 Data source

```text
REALTIME_PUBLIC
REPLAY
```

- `REALTIME_PUBLIC` means current public market data from approved exchange/public providers.
- `REPLAY` means stored historical/replay evidence.
- The word `live` may remain only in historical file/process names during migration; new user-facing/current contracts should prefer `realtime_public`.

### 2.2 Runtime location and storage provider

ADR-025 defines current workload placement.

```text
runtime_location: LOCAL | SYNOLOGY
storage_provider: LOCAL | SYNOLOGY
```

- `LOCAL` runtime is developer compute for experiments, model training and bounded workflows.
- `SYNOLOGY` is the normal persistent application-compute location for the owner-facing Portal, persistent bots/simulation runtimes, long-lived collectors/workers and persistent WickHunter/inference where those services require continuous availability or durable state.
- `SYNOLOGY` is also the normal durable storage/evidence/backup provider.
- GitHub-hosted Actions is a **workload execution plane**, not a persistent runtime-location value: it handles stateless/disposable CI, test, build, scan and bounded jobs where compatible.
- A separate dedicated Linux runtime host is not required for current Portal completion.

These dimensions do not imply release maturity, trading authority or capital use.

### 2.3 Simulation

Simulation is a **normal integrated product capability**, not a separate operating authority mode.

A bot may continuously produce decisions from `REALTIME_PUBLIC` or `REPLAY` data. The simulator may materialize hypothetical positions and outcomes from those decisions. Observation and simulation are parts of one developer workflow.

There is no required `SHADOW -> PAPER` transition.

### 2.4 Model lifecycle

The current model lifecycle is intentionally simple:

```text
BASELINE | CHALLENGER | ACTIVE | ARCHIVED
```

Training may create a `CHALLENGER`. Training never automatically changes `ACTIVE`.

### 2.5 Real exchange execution

Real-money exchange execution is **not a current Portal capability**.

The current product has no need for a `LIVE` mode because there is no current real-capital execution path to select.

If real-money trading is wanted later, it requires a separate owner decision and a separate **Execution/Capital Gateway** programme. That future programme may introduce private trading credentials, capital/risk authority and stronger execution controls without forcing the current developer Portal to carry those concerns today.

## 3. Whole-Portal scope

These rules apply to all current Portal domains:

- Portal web/UX;
- control plane/API;
- WickHunter integration;
- Liquid20 and market-data views/consumers;
- bot/runtime lifecycle;
- simulation and hypothetical position tracking;
- datasets and outcome labels;
- training, challengers, comparison and manual model activation;
- telemetry, logs and developer observability;
- persistence and restart recovery;
- Synology deployment/operations and durable storage/backup;
- GitHub-hosted CI/build/scan/disposable compute;
- CI, E2E and acceptance for Portal work.

A submodule must not reintroduce `SHADOW`, `PAPER` or `LIVE` as a current product authority model.

Historical records, old schema literals and compatibility fields may retain those names while migration is in progress, but they are not architecture authority for new work.

## 4. Target developer workflow

The canonical current workflow is:

```text
REALTIME_PUBLIC market + liquidation data
                |
                v
        feature/context build
                |
                v
       model/strategy decision
          |             |
      NO_TRADE        signal
          |             |
          +------> simulation
                     position/outcome
                          |
                          v
              chronological dataset/labels
                          |
                          v
                  local training
                          |
                          v
               CHALLENGER comparison
                          |
                          v
              deliberate ACTIVE selection
```

The same persistent runtime may record decisions and simulation results continuously. It does not need a mode rollout to begin or stop recording simulated outcomes.

## 5. Runtime architecture

### 5.1 Default principle

Use the **simplest persistent runtime architecture that safely supports the developer workflow**. For the current private platform, persistent application runtime and durable storage are intentionally co-located on Synology, while repository-wide stateless work is pushed to GitHub-hosted runners where practical.

The target topology is:

```text
GitHub repository / GitHub-hosted Actions / GHCR
        | CI, test, security, build, immutable image publication
        | disposable/stateless bounded jobs
        v
Synology persistent runtime
        | Portal / bots / collectors / WickHunter / supporting services
        v
Synology durable application state / datasets / evidence / backup
```

GitHub-hosted Actions runners are the default for stateless CI/build/validation. They are not long-lived application hosts.

Persistent Portal, Freqtrade simulation/bot runtimes, WickHunter/inference and workers/collectors that require continuous availability or durable state run on Synology. Their portable images should be built, scanned and published in GitHub-hosted workflows where practical and consumed by immutable digest.

Short-lived backtests, replay/data-processing jobs, packaging, scans and disposable containerized validation may execute on GitHub-hosted runners when their inputs, runtime, retention and resource requirements fit the Actions lifecycle.

Existing `RuntimeGeneration`, Runtime Supervisor, Gateway, reconciliation and isolation code may be reused where it provides concrete value, but those mechanisms are no longer universal completion prerequisites merely because they were part of a previous production-trading target architecture.

### 5.2 Persistent container and runner boundary

Persistent application containers run on Synology. GitHub Actions builds/publishes their images; it does not host those containers continuously.

Ordinary Portal/bot/application containers must not receive the container-engine socket merely because they share the NAS with Docker. Container-engine authority remains a narrow deployment/lifecycle boundary.

A Synology self-hosted GitHub runner may remain when target-specific operations genuinely require NAS access, but its normal scope is:

```text
runner_scope = disabled | deploy-only
```

It may perform bounded immutable-image pull, configuration validation, deployment update, health/restart/persistence checks and rollback. It must not be the normal repository-wide CI, dependency-build, unrestricted shell or model-training runner when GitHub-hosted execution is compatible.

### 5.3 State and durability

Co-locating current compute and storage on Synology does not remove persistence discipline.

- runtime/application state has explicit ownership;
- active databases use filesystem semantics appropriate to the deployed database/container package;
- datasets, models, evidence, reports and backups remain durable Synology responsibilities;
- important application state has a separate backup/recovery path rather than treating the active copy as its own backup;
- GitHub Actions artifacts and caches are disposable and are not the durable system of record.

### 5.4 What remains valuable

Retain proportionate properties such as:

- exact code/model/config identity for reproducibility;
- restart-safe durable state;
- bounded retries and truthful health;
- no unnecessary public runtime API exposure;
- no unnecessary Docker socket inside application containers;
- non-root/no-new-privileges/read-only mounts where practical;
- bounded resource usage where the host supports it without elaborate certification;
- clear process ownership and cleanup for temporary resources;
- explicit backup/recovery boundaries for durable state;
- a narrowly scoped Synology deployment runner (`deploy-only` or disabled) instead of using the NAS as a general CI worker.

### 5.5 What is no longer a default requirement

The current Portal does **not** require, as a universal product gate:

- a separate dedicated Linux application host;
- physical service cutover away from Synology;
- per-runtime production-grade host capability certification;
- mandatory effective CPU/PID attestation before a developer bot may run;
- mandatory stop-then-replace rollout solely to change a simulated/observational mode;
- generation-local exchange trading credentials;
- capital-authority safety epochs;
- protected-target acceptance for ordinary developer functionality;
- enterprise-style release promotion as proof that a developer runtime is usable.

A stronger mechanism may still be used when a concrete present risk or implementation need justifies it.

## 6. Freqtrade role

Freqtrade remains an internal engine/tool where useful, but the Portal product is not defined by Freqtrade execution semantics.

- Browser code must not receive private internal engine credentials/endpoints.
- Existing simulation/dry-run capabilities may be reused.
- Native research runtimes such as WickHunter may coexist with Freqtrade-backed simulation where appropriate.
- No current Portal flow requires private exchange trading credentials.

## 7. Data and research rules

The following remain important because they protect research quality rather than capital authority:

- decision-time evidence and later outcome evidence stay separately attributable;
- no-lookahead rules remain mandatory;
- dataset/model/config identities remain versioned;
- immutable or append-only chronological evidence is preferred for research datasets;
- test/protected holdout data must not be iteratively consumed for selection where an existing research package marks it protected;
- challenger training is separate from active-model selection;
- negative/`NO_TRADE` observations are first-class learning evidence;
- real public data source freshness and provenance remain explicit.

## 8. Proportionate security baseline

The Portal remains private and authenticated, but security must be proportional to the current product.

KEEP:

- authentication for the owner-facing Portal;
- no secrets committed to repository or rendered to the browser;
- no unnecessary privileged containers or Docker socket exposure;
- server-side validation for mutations;
- durable state and recoverable backup appropriate to a private developer system;
- versioned model/config/dataset identities;
- explicit manual model activation;
- dependency/security updates and ordinary CI;
- bounded external I/O and truthful error states;
- repository-wide CI/build offloaded to GitHub-hosted runners by default so the Synology runtime/storage host is not also a broad CI shell.

DO NOT make current MVP completion depend on enterprise controls that exist only for hypothetical future multi-user/private-capital operation.

## 9. Portal information architecture priority

The current Portal should prioritize usable developer surfaces:

1. **Dashboard** — source health, event counts, running runtimes, active models, current alerts.
2. **WickHunter / Bots** — decisions, `NO_TRADE`, confidence, reasons, signals, simulated positions, PnL and drawdown.
3. **Market Data** — liquidation/market feeds, source health/freshness and history.
4. **Datasets** — observations, labels, date coverage, feature/schema identity and quality.
5. **Models** — baseline/challenger/active models, training actions and comparisons.
6. **Experiments** — replay, backtest, comparison and diagnostics.
7. **System** — runtime/container/process state, logs, storage and restart controls.

Other surfaces are retained only when they materially support this workflow.

## 10. Completion definition

A Portal capability is complete when the owner can use the real developer workflow end to end.

For the first current-platform vertical slice, completion means:

1. real public exchange/liquidation data is continuously collected;
2. a bot/runtime consumes the canonical data and records attributable decisions;
3. simulated positions/outcomes are materialized where applicable;
4. observations/outcomes grow a durable versioned dataset;
5. local training can produce a challenger from that accumulated dataset;
6. Portal comparison shows active vs challenger/baseline evidence;
7. active-model selection is deliberate and does not auto-promote;
8. the Portal and persistent Synology runtime survive restart with correct durable state;
9. the owner can inspect the above through the actual Portal without fixture fallback.

Digest-heavy evidence packages, protected-environment ceremony or exact-current whole-monorepo proofs are supporting evidence only when they address a concrete current risk; they are not substitutes for this user outcome.

## 11. Backlog migration

Every open Portal/WickHunter item must be classified from current live state as exactly one of:

```text
KEEP_NOW
SIMPLIFY
DEFER
OBSOLETE
```

### KEEP_NOW
Directly required for the canonical developer workflow, reliability or proportional safety.

### SIMPLIFY
Useful capability whose current enterprise/production design is unnecessarily heavy for the private developer Portal.

### DEFER
Potentially useful later but not a blocker for current developer usefulness.

### OBSOLETE
Exists only because of a superseded multi-tenant/SHADOW-PAPER-LIVE/private-capital or dedicated-Linux-cutover target.

Reclassification must inspect exact current code, open PRs/issues and already implemented components before removing anything. Useful implementation should be reused rather than deleted merely because its original justification changed.

## 12. Supersession and historical evidence

ADR-023 supersedes conflicting **current Portal product** assumptions in ADR-003, ADR-004, ADR-005, ADR-013, ADR-014, ADR-016, ADR-017, ADR-020, ADR-021 and ADR-022 as specified by ADR-023.

ADR-025 supersedes the conflicting current-target parts of ADR-024 that required persistent application compute to migrate away from Synology onto a separate dedicated Linux host. The current target runtime location is again `LOCAL | SYNOLOGY`.

ADR-025 deliberately retains ADR-024's GitHub-hosted build-plane direction: stateless CI/build/validation should use GitHub-hosted runners by default where compatible; persistent application runtime must not be misrepresented as GitHub Actions hosting; privileged self-hosted runner access remains narrow.

Historical evidence is not rewritten. Old runs, Issues, PRs and artifacts remain valid records of what was tested or decided at the time.

This architecture does not authorize real exchange execution. Real-money execution remains absent from the current Portal rather than represented as a blocked mode.

## 13. Immediate migration order

1. Keep ADR-023 product semantics and apply the ADR-025 runtime/CI placement overlay.
2. Preserve and complete the GitHub-hosted build-plane work from PR #1609/#1610: build/scan/publish portable images on GitHub-hosted Linux, consume immutable identities on Synology.
3. Stop work whose only objective is provisioning or cutting over to a separate dedicated Linux host.
4. Move remaining repository-wide stateless CI/test/build/scan/disposable jobs off general-purpose Synology self-hosted execution when GitHub-hosted execution is compatible.
5. Keep persistent Portal, bot/simulation, required collector/worker and supporting containers on Synology with explicit restart/persistence/backup behavior.
6. Narrow retained Synology self-hosted runner responsibilities toward `deploy-only` or disable them when target access is not needed.
7. Remove or compatibility-wrap `SHADOW/PAPER/LIVE` assumptions from current Portal UI/API/runtime contracts in dependency order.
8. Implement the smallest complete developer workflow from realtime public data through simulation, dataset growth, local challenger training and Portal observation.
9. Simplify deployment/CI gates around actual developer risks rather than hypothetical future capital authority.
10. Keep `deploy/runtime/**` as an optional portability reference only; a future separate-compute migration requires a new explicit owner decision.

## 14. Non-goals of this architecture change

This document does not claim every remaining CI runner/workload has already been migrated. Exact workflow and runner evidence determines implementation state.

It does not authorize:

- private exchange trading credentials;
- real-money order submission;
- withdrawals;
- automatic model promotion;
- capital allocation;
- a future multi-user commercial product;
- treating GitHub Actions as a 24/7 persistent application host;
- broadening Synology self-hosted runner authority;
- destructive cleanup of current Synology services merely because their build path moved to GitHub.

A future decision may revisit separate compute if scale, reliability, performance or isolation requirements justify it, but such a migration is not part of current Portal completion.
