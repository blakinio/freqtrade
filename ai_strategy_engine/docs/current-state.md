# ASE-00 current state

## Status

ASE-00 is a completed additive research/shadow package. The source tree is fully materialized and the deterministic synthetic vertical slice is implemented.

Required source ZIP SHA-256:

```text
73a0d99cab94ba116818a6aef9d818a710fb048a4c0b77f89b9819dd9ac7332f
```

Latest `develop` SHA merged at this checkpoint:

```text
66e119db9a009cef6a51303a0f054012362fc98b
```

The branch is synchronized with `develop` by a normal merge and has not been force-pushed.

## Architectural boundary

The repository authority chain remains:

```text
Browser
→ same-origin Portal BFF/API
→ Portal Control Plane
→ Strategy Engine / AI Research
→ deterministic Portal Risk Core
→ private ExecutionAdapter
→ isolated private Freqtrade runtime
```

ASE-00 does not change browser routes, expose Freqtrade, own exchange credentials, submit approved intents, or create a second portal, bot manager, Risk Core, execution service, liquidation collector, WickHunter implementation or simulator.

## Implemented vertical slice

```text
accepted synthetic market and liquidation events
→ deterministic normalization and idempotency checks
→ point-in-time feature records
→ Strategy DSL validation and evaluation
→ Leakage Guard
→ existing Portal Risk Core decision
→ deterministic shadow evidence
```

The adapter is implemented at:

- `ai_platform/research/strategy_engine/ase00_adapter.py`

It reuses:

- `ai_platform/portal/risk/service.py` for deterministic risk authority;
- canonical Portal risk contracts and snapshots;
- the materialized Strategy Engine domain, registry, DSL and leakage contracts.

## Feature and signal behavior

The synthetic vertical slice produces canonical records for:

- `squeeze_ratio.v1`, including state, duration, release timing and momentum values;
- `supertrend_direction.v1`, including the canonical DSL `direction` alias and flip event;
- `confirmed_pivot.v1`, available only after right-bar confirmation and detection-event confirmation;
- `liquidation_notional_z.v1`, preserving source, timestamps and provenance.

Signals and evidence include deterministic identities, data/code/configuration hashes, complete lineage and explicit shadow-only provenance.

## Fail-closed behavior

The implementation rejects or normalizes the tested cases:

- missing market or liquidation data;
- conflicting duplicate events;
- duplicate market timestamps;
- future features;
- unconfirmed pivots;
- unclosed or unconfirmed HTF features;
- mismatched data, code or configuration hashes;
- incomplete lineage or future-shift provenance;
- reused final holdout evidence;
- Risk Core policy rejection.

Exact duplicates are idempotent, delayed events are accepted only when available before the decision, out-of-order input is normalized deterministically, and restart/replay produces byte-identical evidence.

## Safety state

- research/shadow only;
- no live-order path;
- `no_order_submitted = true`;
- no direct Strategy Engine dependency on Portal execution or Freqtrade modules;
- no direct Browser-to-Freqtrade path;
- no runtime vendor-specific proprietary indicator reference;
- no `eval` or `exec`;
- secret and architecture-boundary scans enforced in CI.

## Validation state

Full post-merge run `30364326953` passed on commit `378bd45ec4706ca61af08f093f838c60e7da750a`:

- package tests;
- Ruff;
- mypy;
- compileall;
- all 12 deterministic repository E2E scenarios;
- JSON/YAML parsing and JSON Schema examples;
- materialization evidence and required paths;
- secret, prohibited-code and architecture-boundary scans.

The permanent read-only workflow is:

- `.github/workflows/ai-strategy-engine.yml`

The final exact-head run after documentation cleanup is recorded in draft PR #584.

## Remaining scope

No further ASE-00 implementation work is required. Review and merge are separate repository-governance actions. Any new strategy research, UI surface, accepted dataset integration or execution-approved flow must be delivered as a separate bounded package and preserve the authority boundary above.
