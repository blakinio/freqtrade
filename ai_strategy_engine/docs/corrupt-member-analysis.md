# ASE-00 corrupted-member analysis

- archive sha256: `e8a8f6f6aeba3c2bb9eb95e96355bb478e2a70cd9f1ebb4aa62a3d511cb601db`
- archive bytes: `62601`
- target: `examples/signal_event.json`
- expected CRC32: `798330cd`
- uncompressed size: `1016`
- compressed size: `515`
- compression method: `8`
- flag bits: `0`
- header offset: `4951`
- timestamp: `(2026, 7, 28, 6, 53, 42)`
- local header signature: `04034b50`
- local CRC32 field: `798330cd`
- data start: `5035`
- raw compressed sha256: `0e4ca73868869e85dcb9e9493f86d8ecf6553283f7df3c875935c602492e75a8`
- raw compressed hex: `7d53616f9b3010fdde5f11e5736126d9da2a1f97642d5b1a324ad5add364397021d68ccd6c9326abfadf7736b066533b849078efddf1eef9783c190c8686979209ca8be1643024dd15bcf0e8ae6878eacbac6616ca435728f8cf8617cc7225030d3bd0868960f7afd6e1a87005514842d2d1876aad8403df67d337b737b36ce21e2d6979051bcd2af0455557c10bff2e942c5b84e5b66b0cd2826e41f4212d751d1c3122a3b3809c07a38b8c441342f0be6f750558c82d1494d957846174d18bd98e71c1d602fea31e47bd1af635d7605ed646cf168c6a74ee6df66105204b2ea1a573253738b3f412129e471ed5c08c9234570518c4bf2186e822fe4c17c9f292ded3abf8f2ca374038b1e92c4d56749a2c3fc4e9f57cd61337b7ab5592667495265fe2eb38fbda138be46e9ed2bb78fa89a6f38ff3691627cb2152dffdc737c06ca3811ac96ab3556ebec7b6ce9d0a3d5a08fa0bb971f8b66bab38cdb74c96e0f16014461d517063198e48ada2a6a96ba52de6a6fdc4e3d3bef70368fac0f31f54bbe69e3c1b21f9e45dd55ae1a1b336a8ce8fcbe778f54a6e03b365fd9868921dd3eeddc05f927e560d257ad4af2c727bdca071df70eddaff0281a0c1207a41855eba9f4d3642fcf10d7bc81b1f56ad04cf0fcfee1b033417cae07aae990bc3ea06fa6e6c4f056e8bcc0fb4722b10bd23e4883382d735c3a4d7b5677d4e274fbf01`
- raw decompression: `success`
- actual uncompressed bytes: `1016`
- actual CRC32: `d56d2b2b`
- actual sha256: `6c33d10575d4d5dd599c762d946fb29512d1fbb5e6788bdf0128945fa6bbdea9`

## Decompressed target content
```text
{
  "signal_id": "00000000-0000-0000-0000-000000000001",
  "strategy_id": "liquidation-reversal-v1",
  "strategy_version": "1.0.0",
  "symbol": "BTC/USDT:USDT",
  "timeframe": "1m",
  "side": "long",
  "action": "enter",
  "event_time": "2026-07-28T01:00:00Z",
  "detected_at": "2026-07-28T01:00:00.180Z",
  "available_at": "2026-07-28T01:00:00.310Z",
  "expires_at": "2026-07-28T01:01:00Z",
  "source": "strategy-engine",
  "confidence": 0.71,
  "reason_codes": [
    "LIQ_LONG_Z_HIGH",
    "OtRDROP_CONFIRMED",
    "SUPPORT_PROXIMITY",
    "LOWER_WICK_REJECTION"
  ],
  "feature_snapshot": {
    "long_liquidation_z": 3.4,
    "oi_change_z": -2.1,
    "distance_to_support_atr": 0.3,
    "lower_wick_ratio": 0.62
  },
  "provenance": {
    "code_version": "git-sha",
    "data_version": "dataset-sha",
    "feature_registry_version": "1.0.0",
    "experiment_id": "exp-uuid",
    "model_id": null
  },
  "execution_policy": {
    "use_closed_bar": true,
    "max_latency_ms": 1500,
    "max_slippage_bps": 12
  }
}
```

## Decompressed target repr
```text
b'{\n  "signal_id": "00000000-0000-0000-0000-000000000001",\n  "strategy_id": "liquidation-reversal-v1",\n  "strategy_version": "1.0.0",\n  "symbol": "BTC/USDT:USDT",\n  "timeframe": "1m",\n  "side": "long",\n  "action": "enter",\n  "event_time": "2026-07-28T01:00:00Z",\n  "detected_at": "2026-07-28T01:00:00.180Z",\n  "available_at": "2026-07-28T01:00:00.310Z",\n  "expires_at": "2026-07-28T01:01:00Z",\n  "source": "strategy-engine",\n  "confidence": 0.71,\n  "reason_codes": [\n    "LIQ_LONG_Z_HIGH",\n    "OtRDROP_CONFIRMED",\n    "SUPPORT_PROXIMITY",\n    "LOWER_WICK_REJECTION"\n  ],\n  "feature_snapshot": {\n    "long_liquidation_z": 3.4,\n    "oi_change_z": -2.1,\n    "distance_to_support_atr": 0.3,\n    "lower_wick_ratio": 0.62\n  },\n  "provenance": {\n    "code_version": "git-sha",\n    "data_version": "dataset-sha",\n    "feature_registry_version": "1.0.0",\n    "experiment_id": "exp-uuid",\n    "model_id": null\n  },\n  "execution_policy": {\n    "use_closed_bar": true,\n    "max_latency_ms": 1500,\n    "max_slippage_bps": 12\n  }\n}'
```

## Per-member validation
- `schemas/signal-event.v1.schema.json`: ok crc=53ab6487
- `schemas/feature-record.v1.schema.json`: ok crc=e5f5d94f
- `schemas/strategy-definition.v1.schema.json`: ok crc=a2dc22e3
- `examples/strategy_classic.json`: ok crc=cb3510ac
- `examples/strategy_miyagi_ensemble_research.json`: ok crc=fdee1240
- `examples/strategy_bonsai_research.json`: ok crc=4f0bdb62
- `examples/signal_event.json`: FAIL BadZipFile: Bad CRC-32 for file 'examples/signal_event.json'
- `examples/strategy_liquidation.json`: ok crc=678d5cbb
- `Makefile`: ok crc=fe90bc54
- `configs/search_spaces.v1.yaml`: ok crc=299585cc
- `configs/miyagi_parameter_map.v1.yaml`: ok crc=04cf292a
- `configs/feature_registry.v1.yaml`: ok crc=f88cb38f
- `ARCHITECTURE.md`: ok crc=5f06e533
- `README.md`: ok crc=d1d76390
- `docs/AI_ADAPTATION_POLICY.md`: ok crc=e4727692
- `docs/STRATEGY_DSL.md`: ok crc=22dc6629
- `docs/FEATURE_REGISTRY_V1.md`: ok crc=0f660cc5
- `docs/TIMESTAMP_SEMANTICS.md`: ok crc=b9b6608c
- `docs/MIYAGI_PARAMETER_MAP.md`: ok crc=b8427356
- `docs/TECHNICAL_AUDIT.md`: ok crc=0a53deed
- `docs/VALIDATION_AND_ACCEPTANCE.md`: ok crc=07a336fe
- `docs/DECISIONS.md`: ok crc=bacaf804
- `docs/LICENSE_BOUNDARIES.md`: ok crc=5173a3cb
- `docs/IMPLEMENTATION_CHECKPOINT.md`: ok crc=5fc74b55
- `src/strategy_engine/dsl/validator.py`: ok crc=512f3bae
- `src/strategy_engine/dsl/__init__.py`: ok crc=00000000
- `src/strategy_engine/risk/position_management.py`: ok crc=ac794d8a
- `src/strategy_engine/risk/__init__.py`: ok crc=32d70693
- `src/strategy_engine/domain/models.py`: ok crc=ed6ac644
- `src/strategy_engine/domain/__init__.py`: ok crc=00000000
- `src/strategy_engine/api/contracts.py`: ok crc=d4475225
- `src/strategy_engine/api/__init__.py`: ok crc=00000000
- `src/strategy_engine/policies/signals.py`: ok crc=38a33da5
- `src/strategy_engine/policies/__init__.py`: ok crc=32d70693
- `src/strategy_engine/features/pivots.py`: ok crc=f3a73e17
- `src/strategy_engine/features/base.py`: ok crc=f1e5e47a
- `src/strategy_engine/features/trend.py`: ok crc=e43b7532
- `src/strategy_engine/features/macd.py`: ok crc=b2eea577
- `src/strategy_engine/features/volume.py`: ok crc=f54c364c
- `src/strategy_engine/features/candles.py`: ok crc=435c2c43
- `src/strategy_engine/features/momentum.py`: FAIL BadZipFile: Bad CRC-32 for file 'src/strategy_engine/features/momentum.py'
- `src/strategy_engine/features/range_filter.py`: ok crc=952cb50f
- `src/strategy_engine/features/squeeze.py`: ok crc=af83c327
- `src/strategy_engine/features/common.py`: ok crc=21b9ef59
- `src/strategy_engine/features/supertrend.py`: ok crc=fc663572
- `src/strategy_engine/features/market_structure.py`: ok crc=68e604ce
- `src/strategy_engine/features/__init__.py`: ok crc=00000000
- `src/strategy_engine/validation/leakage.py`: ok crc=afdf0a5d
- `src/strategy_engine/validation/__init__.py`: ok crc=00000000
- `src/strategy_engine/__init__.py`: ok crc=dce6f0a3
- `tests/e2e/test_examples_validate.py`: ok crc=1618c128
- `tests/e2e/test_pipeline_contract.py`: ok crc=1f38c4f6
- `tests/unit/test_momentum.py`: ok crc=a6411330
- `tests/unit/test_trend.py`: ok crc=4deec693
- `tests/unit/test_volume.py`: ok crc=777bc1f8
- `tests/unit/test_position_management.py`: ok crc=dcfaabb3
- `tests/unit/test_signal_policies.py`: ok crc=40b47c9b
- `tests/unit/test_pivots.py`: ok crc=c14491ce
- `tests/unit/test_squeeze.py`: FAIL error: Error -3 while decompressing data: invalid distance too far back
- `tests/unit/test_range_filter.py`: ok crc=e957315d
- `tests/unit/test_models.py`: ok crc=0975e02f
- `tests/unit/test_macd.py`: ok crc=3a685dd7
- `sources/README.md`: ok crc=9c22e0a7
- `TASKS.md`: ok crc=2b6bbbbb
- `AGENT_MASTER_PROMPT.md`: ok crc=f1c2d0d9
- `.gitignore`: ok crc=d78e8211
- `pyproject.toml`: ok crc=d04abc4c
