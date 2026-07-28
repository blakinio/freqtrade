# ASE-00 materialization evidence

- status: `incomplete`
- develop SHA merged in runner: `e79f4f1358a67304eab8667f165a9d94723103ce`
- branch head before runner merge: `86a4b01d371d881b6f97a86fdbe033399c8dc3ce`
- materializer exit code: `1`
- expected source ZIP SHA-256: `73a0d99cab94ba116818a6aef9d818a710fb048a4c0b77f89b9819dd9ac7332f`
- materialized source tree hash: `294d679467af22ed837e90ddae1a9e8d5c0b3652102bcb1f7d125cb4d3945b31`
- command: `python ai_strategy_engine/materialize_starter.py`
- update method: non-force merge preserving both parent histories

## Missing required paths
- `ai_strategy_engine/configs/feature_registry.v1.yaml`
- `ai_strategy_engine/configs/search_spaces.v1.yaml`
- `ai_strategy_engine/configs/miyagi_parameter_map.v1.yaml`
- `ai_strategy_engine/schemas`
- `ai_strategy_engine/examples`
- `ai_strategy_engine/src/strategy_engine`

## Materializer output
```text
archive checksum mismatch: e8a8f6f6aeba3c2bb9eb95e96355bb478e2a70cd9f1ebb4aa62a3d511cb601db
```

## Materialized file inventory
```text
ai_strategy_engine/AGENT_MASTER_PROMPT.md
ai_strategy_engine/ARCHITECTURE.md
ai_strategy_engine/ARCHIVE_MANIFEST.md
ai_strategy_engine/README.md
ai_strategy_engine/TASKS.md
ai_strategy_engine/bootstrap/strategy_engine_source.zip.b64.part01
ai_strategy_engine/bootstrap/strategy_engine_source.zip.b64.part02a
ai_strategy_engine/bootstrap/strategy_engine_source.zip.b64.part02b
ai_strategy_engine/bootstrap/strategy_engine_source.zip.b64.part03a
ai_strategy_engine/bootstrap/strategy_engine_source.zip.b64.part03b
ai_strategy_engine/bootstrap/strategy_engine_source.zip.b64.part04
ai_strategy_engine/bootstrap/strategy_engine_source.zip.b64.part05
ai_strategy_engine/docs/AI_ADAPTATION_POLICY.md
ai_strategy_engine/docs/IMPLEMENTATION_CHECKPOINT.md
ai_strategy_engine/docs/MIYAGI_PARAMETER_MAP.md
ai_strategy_engine/docs/TECHNICAL_AUDIT.md
ai_strategy_engine/materialize_starter.py
ai_strategy_engine/tests/e2e/test_examples_validate.py
ai_strategy_engine/tests/e2e/test_pipeline_contract.py
ai_strategy_engine/tests/unit/test_macd.py
ai_strategy_engine/tests/unit/test_models.py
ai_strategy_engine/tests/unit/test_momentum.py
ai_strategy_engine/tests/unit/test_pivots.py
ai_strategy_engine/tests/unit/test_position_management.py
ai_strategy_engine/tests/unit/test_range_filter.py
ai_strategy_engine/tests/unit/test_signal_policies.py
ai_strategy_engine/tests/unit/test_squeeze.py
ai_strategy_engine/tests/unit/test_trend.py
ai_strategy_engine/tests/unit/test_volume.py
```
