# WickHunter dataset builder

## Scope

WH-01 turns already accepted immutable historical liquidation imports into deterministic WickHunter feature partitions. It does not download provider data, approve a provider purchase, fit a model, execute replay, submit orders or authorize live capital.

The builder consumes the existing provider-neutral historical package created by `HistoricalLocalImporter`:

```text
manifest.json
acceptance.json
artifacts.json
events.jsonl
```

Each selected package must have:

- `acceptance.status = pass`;
- zero rejected records and at least one accepted record;
- a verified manifest identity;
- verified file hashes from `artifacts.json`;
- an accepted-event identity hash matching `events.jsonl`;
- an interval ending before the protected final holdout.

Rejected, incomplete, altered or duplicated packages fail closed.

## Availability-time normalization

Historical events retain their provider and source identities. `occurred_at_ms` remains the exchange/event time, while the historical `available_at_ms` becomes the canonical feature-side `received_at_ms`. A negative availability latency is rejected.

Feature rows use only evidence satisfying:

```text
event.available_at_ms <= decision_timestamp_ms
metric.available_at_ms <= decision_timestamp_ms
universe.selected_at_ms <= decision_timestamp_ms
history.available_at_ms <= decision_timestamp_ms
```

The latest universe snapshot available at the decision time is selected by a deterministic as-of rule. A symbol without an eligible decision is omitted rather than silently admitted.

## History and features

For each market decision snapshot the builder:

1. selects the declared split without touching the protected final holdout;
2. selects the latest available dynamic-universe snapshot;
3. constructs historical event and burst distributions strictly before the current burst window;
4. constructs source health state from the latest source-labelled available event;
5. calls the same pure `build_liquidation_features` function used by the WH-00 vertical slice;
6. binds every feature row to accepted import selections, provider IDs, import run IDs, market context and universe snapshot hashes.

No label, model score or trade outcome is produced in WH-01.

## Split geometry

`DatasetSplitGeometry` declares ordered named windows, a label horizon, an embargo and the protected holdout start. Adjacent windows must be separated by at least the greater of the label horizon and embargo. Random splitting is not supported.

Calling the classifier at or after the protected holdout start raises an error. The protected final holdout therefore cannot be materialized accidentally by this builder.

## Atomic output

A build writes to a temporary sibling directory and atomically publishes the final root only after every row and hash is complete. Existing output roots are never overwritten.

```text
<dataset-root>/
  manifest.json
  sources.json
  universe/history.jsonl
  features/
    split=<name>/
      symbol=<symbol>/
        part-<bucket-start-ms>.jsonl
```

Every row has a canonical `row_sha256`. Every partition records its SHA-256, row count and decision-time range. The manifest binds:

- dataset request and split geometry hashes;
- exact code SHA;
- accepted source selections and immutable import identities;
- dynamic-universe snapshot hashes;
- partition identities and counts;
- total decision-time range;
- `model_execution_authorized = false`.

## Current evidence boundary

The repository contains historical contracts and a deterministic local Tardis importer, but the first paid bulk Tardis import remains dependent on owner/provider access. WH-01 therefore proves the builder contract with deterministic synthetic accepted-import fixtures. It does not claim that a real bulk historical WickHunter dataset has already been selected or generated.

WH-02 replay may begin only after a real import package passes the unchanged historical acceptance contract and is selected through this builder without protected-holdout access.
