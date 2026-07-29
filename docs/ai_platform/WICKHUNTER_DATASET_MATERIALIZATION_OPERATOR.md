# WickHunter WH-01 dataset materialization operator

## Purpose

This operator is the fail-closed boundary between an accepted immutable liquidation import and the existing WH-01 feature-dataset builder. It does not collect market data, create synthetic context, generate labels, replay strategies, fit models or authorize execution.

The operator has two commands:

```bash
python -m ai_platform.scripts.wickhunter_dataset_materialization preflight \
  --package-root /immutable/input-package \
  --request /immutable/input-package/request.json

python -m ai_platform.scripts.wickhunter_dataset_materialization materialize \
  --package-root /immutable/input-package \
  --request /immutable/input-package/request.json \
  --output-root /durable/no-overwrite/dataset
```

`preflight` returns exit code `0` only when every exact input exists and validates. Missing files produce a bounded `blocked` report and exit code `2`. Malformed, tampered or authority-bearing inputs produce an `error` report and exit code `1`.

## Immutable input package

The request schema is `wickhunter-dataset-materialization-request-v1`. It binds:

- one or more accepted-import relative roots;
- exact accepted `import_run_id` and selection SHA-256 identities;
- the exact market-context JSONL path and SHA-256;
- the exact universe-history JSONL path and SHA-256;
- dataset version and code SHA;
- burst, partition, history and freshness parameters;
- named split windows plus label horizon, purge-equivalent gap and embargo;
- the protected final holdout;
- explicit false values for credentials, trading, execution, model execution and live capital.

All paths are relative to one package root. Absolute paths, `..`, symlink traversal, duplicate accepted roots and output inside the immutable package are rejected.

## Market-context rows

Each line uses `wickhunter-market-context-row-v1`:

```json
{
  "schema_version": "wickhunter-market-context-row-v1",
  "snapshot": {
    "symbol": "BTCUSDT",
    "decision_timestamp_ms": 1785286800000,
    "decision_price": "118000",
    "completed_candle_close_ms": 1785286740000,
    "metrics": []
  },
  "snapshot_sha256": "..."
}
```

The nested snapshot is the canonical `MarketContextSnapshot`. The operator requires all nine WH-01 metrics, validates the canonical snapshot hash, rejects future availability and refuses completed-candle metrics reported before candle close. Rows must be unique and sorted by decision timestamp and symbol.

## Universe-history rows

Each line uses `wickhunter-universe-history-row-v1` and contains the canonical `DynamicUniverseSnapshot` plus its snapshot hash. Rows must be unique and sorted by selection time and identity. Only `wickhunter-dynamic-universe-v1` snapshots are accepted.

## Materialization and verification

When preflight is ready, the operator calls the existing unchanged `build_wickhunter_dataset()` with the validated accepted roots, market snapshots, universe history and split geometry.

The output is atomic and no-overwrite because the existing builder writes through a temporary root. The operator then independently verifies:

- manifest schema, identity and `model_execution_authorized = false`;
- every partition path, file SHA-256 and row count;
- every row SHA-256;
- total and earliest/latest decision timestamps;
- non-empty accepted source selections;
- universe-history identities against the manifest;
- manifest, sources and universe file hashes against the build result.

A successful report keeps model execution, trading and live capital authority false.

## Deliberate limitations

The operator does not produce the missing real market-context or historical universe evidence. It only validates exact immutable inputs and materializes them through WH-01. No production request or Synology workflow is included in this package. A later separately reviewed operational task must locate or produce accepted source evidence and must first run `preflight`.

WH-02 remains blocked until a real run produces a non-empty independently verified `wickhunter-dataset-manifest-v1`. Even then, labels, replay order, costs, latency, slippage, evaluation geometry and promotion remain separate WH-02 responsibilities.
