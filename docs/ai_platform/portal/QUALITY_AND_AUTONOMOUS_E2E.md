# AI Trading Portal — Quality and Autonomous E2E Architecture

## 1. Objective

Build a full-platform validation system that behaves like a real user, traverses real product and security boundaries, exercises Freqtrade through the supported portal path, validates AI/risk/trade-intelligence behavior, and produces enough evidence for an autonomous agent to diagnose and safely propose repairs.

The test system must find integration failures that unit tests cannot see without turning self-healing into test weakening.

## 2. Testing pyramid and gates

```text
                    Full production-like E2E
                 Security / chaos / visual E2E
              AI learning-loop scenario validation
             Integration and component contract tests
          Unit / property / schema / deterministic tests
```

Fast, deterministic tests run first. Full E2E is a promotion gate, not a substitute for lower-level coverage.

## 3. Test classes

### Unit

- pure domain logic;
- risk rules;
- state transitions;
- serializers/contracts;
- diagnosis classifiers;
- feature helpers where applicable.

### Contract

- portal API schemas;
- event schemas;
- Freqtrade adapter contract;
- model registry contracts;
- exchange simulator protocol;
- webhook schemas.

### Integration

- PostgreSQL persistence;
- outbox/event delivery;
- object storage;
- secret reference flow with test secrets;
- orchestrator -> runtime adapter;
- Freqtrade test runtime lifecycle;
- analytics reconciliation.

### Full E2E

Real browser + deployed platform + isolated test tenant + simulated exchange/market.

### Security E2E

Identity, tenant, RBAC, Cloudflare-protected ingress, secret and network boundaries.

### AI Scenario E2E

Deterministic model/data fixtures proving inference, risk, execution and learning-loop contracts.

### Visual E2E

Screenshot/layout acceptance for key surfaces and responsive breakpoints.

### Chaos/recovery

Exchange disconnects, partial fills, event delays, runtime restarts, stale model/data, unavailable dependencies and reconciliation.

## 4. Canonical critical journey

```text
Open browser
  -> authenticate
  -> complete MFA when scenario requires
  -> create/select test exchange connection
  -> create AI bot from approved test strategy/model
  -> configure deterministic risk policy
  -> deploy/start bot
  -> wait for explicit runtime readiness
  -> inject deterministic market scenario
  -> observe prediction
  -> observe risk decision
  -> execute simulated order through Freqtrade
  -> close trade
  -> reconcile trade into portal
  -> calculate analytics/PNL
  -> run post-trade analysis
  -> display AI insight
  -> stop bot
  -> verify audit trail
  -> logout
```

The test must not replace readiness with arbitrary sleeps. It waits on explicit health/state conditions with bounded timeouts and useful failure evidence.

## 5. Exchange and market simulator

E2E must not require real capital.

The simulator provides deterministic scenario control:

```text
balances
market prices
OHLCV stream
spread
liquidity
latency
order acceptance/rejection
full fill
partial fill
slippage
rate limiting
connection loss/recovery
insufficient balance
liquidation-like events for authorized futures tests
```

A scenario is versioned and reproducible:

```text
ScenarioManifest
  scenario_id
  version
  initial_balances
  market_timeline
  exchange_faults
  expected_invariants
  random_seed
```

No test depends on uncontrolled live-market outcomes.

## 6. Browser automation

Use Playwright-compatible browser automation as the default product E2E approach.

Test matrix:

### Pull request critical gate

- Chromium desktop;
- critical journeys only;
- deterministic exchange simulator;
- targeted visual assertions.

### Staging gate

- Chromium;
- Firefox;
- WebKit;
- desktop/tablet/mobile representative viewports;
- critical and major user journeys;
- security boundaries;
- visual regression.

### Nightly / scheduled

- full scenario library;
- longer-running bot lifecycle tests;
- chaos/recovery;
- AI learning-loop tests;
- autonomous diagnosis dry-run;
- accessibility and expanded visual sweep.

Cross-browser failures remain real failures unless a documented product support policy excludes the platform.

## 7. Production-like security path

Staging E2E should traverse:

```text
Test browser/agent
      |
      v
Cloudflare edge
      |
      v
Access policy where surface is privileged
      |
      v
Cloudflare Tunnel
      |
      v
Staging portal
```

Do not create hidden `/bypass-security-for-tests` production code paths.

Machine automation receives dedicated test identity/service credentials scoped to staging and rotated separately from human identities.

Exchange execution remains simulated unless a separately declared testnet/sandbox scenario is explicitly allowed.

## 8. AI deterministic test strategy

PR CI does not retrain expensive production models.

Use small deterministic fixtures:

```text
known DatasetVersion fixture
known FeatureSchemaVersion
known tiny ModelVersion artifact
known market scenario
known prediction range / eligibility outcome
known RiskDecision
known simulated TradeOutcome
```

Assertions focus on contracts and invariants rather than reproducing stochastic training metrics.

Full training is exercised in dedicated training-pipeline smoke/scheduled jobs.

## 9. AI learning-loop E2E

Canonical safe self-improvement test:

```text
start bot with immutable test ModelVersion A
  -> execute deterministic sequence of trades
  -> include deliberately poor/anomalous scenario
  -> close trades
  -> Post-Trade Intelligence classifies evidence
  -> generate bounded Insight/Hypothesis
  -> create Experiment proposal
  -> run authorized test training job
  -> register Candidate ModelVersion B
  -> execute validation gates
  -> assert ModelVersion A is still active
```

Critical invariant:

> Creating a better or worse candidate must not silently replace the running production/dry-run model.

Separate promotion tests verify that only explicitly authorized lifecycle transitions can change assignment.

## 10. Trade-intelligence quality tests

Use scenario fixtures with expected diagnosis boundaries.

Example:

```text
Scenario: abrupt volatility regime change after valid entry
Expected:
  - analyzer may flag MARKET_REGIME_CHANGE
  - analyzer must not claim entry was certainly wrong solely because PNL < 0
  - user insight must link evidence
  - no production strategy/model mutation
```

Example:

```text
Scenario: exchange returns large slippage with stable model signal
Expected:
  - execution/slippage diagnosis prioritized
  - model blamed only if independent evidence supports it
```

LLM-based synthesis tests validate structure, evidence references and forbidden claims. Deterministic classifiers remain independently testable.

## 11. Security E2E scenarios

Required baseline:

```text
anonymous -> protected API denied
expired session -> denied
revoked session -> denied
invalid MFA -> denied
CSRF attempt -> denied
User A -> User B bot -> denied
viewer -> start bot -> denied
trader -> promote model -> denied
model_reviewer -> read exchange secret -> denied
browser -> Freqtrade -> unreachable
authorized portal adapter -> Freqtrade -> reachable
research worker -> production exchange secret -> denied
invalid webhook signature -> denied
replayed webhook -> denied
invalid model hash -> runtime load denied
kill switch -> new exposure denied
```

Security test results are first-class CI evidence.

## 12. Visual/UX acceptance

Key surfaces:

```text
Dashboard
PNL Reporting
Open Deals
Trading Terminal
Create Bot
View Bots
Signal Wizard
Strategy Catalog / Marketplace
Grid Bots
Logs
Subscription / Usage
AI Intelligence
Trade Analysis
Model Health
Experiments
Profile
Notifications
Admin
```

Validate:

- desktop;
- tablet;
- mobile;
- loading states;
- empty states;
- errors;
- denied states;
- degraded runtime/data states;
- long content/overflow;
- keyboard/focus behavior on critical paths.

Functional success does not imply visual acceptance.

## 13. Failure evidence bundle

Every E2E failure produces a bounded evidence bundle:

```text
scenario manifest
step timeline
screenshots
video when enabled
Playwright trace
DOM snapshot at failure
browser console
network request summary
portal API structured logs
correlation_id
backend trace links/exports
orchestrator events
Freqtrade runtime logs for test runtime
simulator timeline
relevant model/risk/config identifiers
```

Secrets are redacted before artifact publication.

## 14. Autonomous diagnosis agent

Failure workflow:

```text
E2E failure
   |
   v
Evidence collector
   |
   v
Diagnosis agent
   |
   +--> identify first failure marker
   +--> classify likely layer
   +--> reproduce with narrow test
   +--> inspect owned code/contracts
   |
   v
Diagnosis record
```

The agent must distinguish:

- product defect;
- test defect;
- environment defect;
- dependency outage;
- flaky/ambiguous evidence.

Uncertainty is explicit.

## 15. Controlled autonomous repair

Allowed repair pipeline:

```text
confirmed reproducible defect
  -> create regression test
  -> create isolated task branch
  -> implement minimal fix in owned paths
  -> run targeted validation
  -> run required broad gates
  -> create PR with evidence
```

Forbidden shortcuts:

- modify production directly;
- remove an assertion only because it fails;
- replace readiness with larger arbitrary sleep;
- skip security test to make CI green;
- update screenshot baseline without explaining intentional visual change;
- ignore tenant/authorization failures;
- self-merge a high-risk change outside configured governance.

## 16. Self-healing test policy

A test locator may be repaired automatically only when the semantic user contract remains proven.

Example allowed:

- stable accessible role/name identifies the same button after an implementation-only selector change.

Example not allowed:

- expected `Create Bot` capability disappears and agent simply deletes the assertion.

The repair system optimizes for product correctness, not green dashboards.

## 17. Flake policy

Retries collect evidence; they do not erase the first failure.

Track:

- first-attempt pass rate;
- retry pass rate;
- scenario-specific flake rate;
- infrastructure vs product classification.

A chronically flaky critical test is a defect in the quality system and receives its own bounded task.

## 18. CI gates

Suggested merge gates for portal implementation:

```text
format/lint/type
unit
contract
integration
security static analysis
build
critical Chromium E2E
critical AI scenario E2E
critical tenant/RBAC E2E
```

Broader cross-browser/visual/chaos may run on staging/nightly until runtime cost permits stronger merge gating.

## 19. Autonomous quality invariants

1. Agents can propose fixes, not silently patch production.
2. Every repair starts from reproducible evidence.
3. Regression tests precede or accompany defect fixes.
4. First failure evidence is preserved.
5. Test code cannot weaken a product safety contract merely to pass.
6. E2E uses simulated capital by default.
7. Real security ingress is tested in production-like staging.
8. Model self-improvement tests prove that candidate creation is not automatic promotion.
