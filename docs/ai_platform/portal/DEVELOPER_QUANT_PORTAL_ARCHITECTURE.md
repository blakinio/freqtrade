# Developer Quant Portal Architecture

Status: **owner-accepted current Portal product architecture**  
Owner decision date: `2026-08-15`  
Related Issue: `#1555`  
Applies to: **the entire current Portal product**  
Runtime/deployment overlay: **ADR-024**, accepted `2026-08-18`, Issue `#1603`

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

ADR-024 separates application compute from durable storage.

```text
runtime_location: LOCAL | DEDICATED_LINUX
storage_provider: LOCAL | SYNOLOGY
```

- `LOCAL` runtime is developer compute for experiments, model training and bounded workflows.
- `DEDICATED_LINUX` is the target persistent application-compute location for Portal, collectors, WickHunter/inference, Freqtrade simulation and ordinary long-lived workers.
- `SYNOLOGY` is the target durable storage/evidence/backup provider, not the target application-compute location.
- Existing Synology-hosted services remain valid transitional implementation state until each service is migrated and its replacement is proven.

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
- dedicated-Linux deployment/operations and Synology durable storage/backup;
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

The same runtime may record decisions and simulation results continuously. It does not need a mode rollout to begin or stop recording simulated outcomes.

## 5. Runtime architecture

### 5.1 Default principle

Use the **simplest persistent runtime architecture that safely supports the developer workflow**, with application compute separated from durable storage.

The target topology is:

```text
GitHub repository / GitHub-hosted Actions
        | CI, build, security, immutable artifact publication
        v
Dedicated Linux runtime host
        | narrow durable-storage boundary
        v
Synology durable storage / evidence / backup
```

GitHub-hosted Actions runners are the default for stateless CI/build/validation, not for long-lived application services. Persistent Portal, collectors, WickHunter/inference, Freqtrade simulation and ordinary workers target a dedicated Linux host. Synology provides durable storage and backup while existing Synology compute remains transitional current state during migration.

Active transactional databases must not be placed on a network filesystem merely to centralize storage. They may run locally on the dedicated runtime and back up or replicate to Synology under an explicit recovery contract.

Existing `RuntimeGeneration`, Runtime Supervisor, Gateway, reconciliation and isolation code may be reused where it provides concrete value, but those mechanisms are no longer universal completion prerequisites merely because they were part of the previous production-trading target architecture.

### 5.2 What remains valuable

Retain proportionate properties such as:

- exact code/model/config identity for reproducibility;
- restart-safe durable state;
- bounded retries and truthful health;
- no unnecessary public runtime API exposure;
- no unnecessary Docker socket inside application containers;
- non-root/no-new-privileges/read-only mounts where practical;
- bounded resource usage where the host supports it without elaborate certification;
- clear process ownership and cleanup for temporary resources;
- explicit separation of runtime-local transactional state from Synology-backed durable datasets/evidence/backups;
- a narrowly scoped deployment runner (`deploy-only` or disabled) instead of privileged runtime/storage hosts serving as general CI workers.

### 5.3 What is no longer a default requirement

The current Portal does **not** require, as a universal product gate:

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
- bounded external I/O and truthful error states.

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
8. the Portal and persistent runtime survive restart with correct durable state;
9. the owner can inspect the above through the actual Portal without fixture fallback.

Digest-heavy evidence packages, protected-environment ceremony or exact-current whole-monorepo proofs are supporting evidence only when they address a concrete current risk; they are not substitutes for this user outcome.

## 11. Backlog migration

After this architecture is merged, every open Portal/WickHunter item must be reclassified from current live state as exactly one of:

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
Exists only because of the superseded multi-tenant/SHADOW-PAPER-LIVE/private-capital product model.

Reclassification must inspect exact current code, open PRs/issues and already implemented components before removing anything. Useful implementation should be reused rather than deleted merely because its original justification changed.

## 12. Supersession and historical evidence

This architecture supersedes conflicting **current Portal product** assumptions in ADR-003, ADR-004, ADR-005, ADR-013, ADR-014, ADR-016, ADR-017, ADR-020, ADR-021 and ADR-022 as specified by ADR-023.

ADR-024 additionally supersedes conflicting current-target statements that make Synology the normal persistent application-compute location. The target runtime location is `LOCAL | DEDICATED_LINUX`; Synology remains the durable storage/evidence/backup provider and transitional compute only until service-level migration is proven.

It does not rewrite historical evidence. Old runs, Issues, PRs and artifacts remain valid records of what was tested at the time.

It also does not authorize real exchange execution. Real-money execution remains absent from the current Portal rather than represented as a blocked mode.

## 13. Immediate migration order

1. Keep ADR-023 product semantics and apply the ADR-024 runtime/deployment overlay.
2. Use `deploy/runtime/**` as the generic host/storage contract while preserving `deploy/synology/**` as transitional current-state packages.
3. Reclassify open Portal/WickHunter Issues/PRs as `KEEP_NOW | SIMPLIFY | DEFER | OBSOLETE`, including Synology-as-compute assumptions that now require portability reconciliation.
4. Remove or compatibility-wrap `SHADOW/PAPER/LIVE` assumptions from current Portal UI/API/runtime contracts in dependency order.
5. Implement the smallest complete developer workflow from realtime public data through simulation, dataset growth, local challenger training and Portal observation.
6. Migrate persistent service groups to a verified dedicated Linux host in the order defined by ADR-024/Issue #1604, proving state, restart and rollback per service.
7. Keep Synology as durable storage/evidence/backup and validate recovery after compute cutover.
8. Simplify deployment/CI gates around actual developer risks rather than hypothetical future capital authority.
9. Archive superseded plans only after exact references and useful implementation have been migrated.

## 14. Non-goals of this architecture change

This document does not claim the code or physical runtime migration is already complete. It changes the governing current product architecture and migration target.

It does not authorize:

- private exchange trading credentials;
- real-money order submission;
- withdrawals;
- automatic model promotion;
- capital allocation;
- a future multi-user commercial product;
- physical deployment to an unverified dedicated Linux host;
- destructive cleanup of existing Synology services merely because they are transitional.

Those concerns require separate future owner decisions or task-specific deployment authority if they ever become desired product scope.
