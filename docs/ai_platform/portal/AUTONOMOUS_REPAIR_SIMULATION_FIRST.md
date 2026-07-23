# Autonomous Diagnosis and Bounded Repair — Simulation-First Mode

## Purpose

P12 begins with deterministic simulated/local/CI evidence while real P11 Cloudflare infrastructure is intentionally deferred. This mode exercises diagnosis and repair governance without claiming that production-like staging has passed.

## Input boundary

The first implementation consumes P10 `ScenarioFailureEvidence`:

```text
scenario_id
correlation_id
stage
reason_code
```

The caller must separately state whether the failure was reproduced. A captured failure is not automatically treated as reproducible merely because evidence exists.

## Diagnosis

`SimulationFirstRepairService.diagnose()` produces an immutable `DiagnosisRecord` with:

- first failure stage and reason;
- deterministic classification as product defect, test defect, environment defect, dependency outage or flaky/ambiguous;
- likely layer;
- explicit confidence;
- reproducibility state;
- simulation-only evidence label and optional evidence references.

Unknown failures stay ambiguous rather than being forced into a product-defect classification.

## Repair proposal

A proposal contains:

- bounded task ID;
- isolated `agent/...` branch name derived from task identity and correlation ID;
- regression-test paths;
- proposed changed paths;
- explicit validation commands;
- PR evidence summary;
- fail-closed safety flags.

The service produces metadata only. It does not create Git branches, push commits, merge PRs, deploy environments or retrieve secrets by itself. Repository-capable agents may execute an allowed plan only under their separately declared task ownership and normal branch/CI/PR governance.

## Fail-closed policy

A repair is rejected when any of these conditions is true:

- the failure has not been reproduced;
- no regression test accompanies the proposed repair;
- a regression-test path is not part of the proposed changed paths;
- a changed path escapes declared task ownership or uses parent-path traversal;
- no validation command is declared;
- the proposal weakens a mandatory safety assertion;
- the proposal deploys production;
- the proposal requires production secrets;
- the proposal enables live capital;
- the proposal claims that simulated evidence proves real P11 Cloudflare acceptance.

## Relationship to P10

P10 already preserves the first deterministic scenario failure with a correlation ID. P12 consumes that evidence instead of replacing it, silently retrying it or rewriting the first failure marker.

A typical simulation-first flow is:

```text
P10 deterministic scenario failure
  -> preserve first ScenarioFailureEvidence
  -> reproduce with the same deterministic fixture
  -> P12 diagnosis
  -> bounded repair plan
  -> fail-closed policy evaluation
  -> regression test first
  -> isolated repair branch
  -> targeted validation
  -> required CI
  -> PR with evidence
```

## Relationship to real P11 staging

Simulation-first P12 is not a substitute for real production-like staging validation.

It cannot prove:

- Cloudflare Tunnel connectivity;
- authoritative/proxied DNS behavior;
- real Access policy enforcement;
- real WAF or rate limiting;
- real origin firewall denial;
- real direct-Freqtrade public denial.

Those claims require the deferred owner-approved `Portal Staging External E2E` run. Until that real run passes, P11 remains externally blocked even if P12 simulation-first work is complete.

## Safety invariants

- no production deployment authority;
- no production exchange-secret access;
- no live-capital enablement;
- no hidden test security bypass;
- no repair outside declared ownership;
- no assertion weakening merely to make CI green;
- no simulated evidence presented as real Cloudflare acceptance;
- negative or ambiguous diagnosis evidence remains durable.
