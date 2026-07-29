# ASE-00 bundle forensics

- expected ZIP SHA-256: `73a0d99cab94ba116818a6aef9d818a710fb048a4c0b77f89b9819dd9ac7332f`
- inspected branch head: `acc30b21f22ab2681a05ef26609f8fc51f1ced80`
- inspected develop: `e79f4f1358a67304eab8667f165a9d94723103ce`

## Current parts
- `ai_strategy_engine/bootstrap/strategy_engine_source.zip.b64.part01`: bytes=12000, blob_sha=`d360223da4077ad773deccd3df1367a7e26330d9`, sha256=`64a5ed6d348c601f564c20304d48561462f982b189227816b9a1cd06dc7ea4e1`
- `ai_strategy_engine/bootstrap/strategy_engine_source.zip.b64.part02a`: bytes=6000, blob_sha=`2d30581a92418b60814360df46ab400e373ff87a`, sha256=`4251508e825ad6f690a406d8c4e38f5352d626eed214fd5dafc9ba0bc0f61395`
- `ai_strategy_engine/bootstrap/strategy_engine_source.zip.b64.part02b`: bytes=6000, blob_sha=`0c236c5885bcaa5ea9d7df88817beeeb98d4b0f1`, sha256=`ee018327d5bfcf4ec9a87d290ed6b3329413ecd7d352e893d5dbe943793e2db3`
- `ai_strategy_engine/bootstrap/strategy_engine_source.zip.b64.part03a`: bytes=6000, blob_sha=`7e3f3d929f78f14f44fb04f2be9a0e460151dd1e`, sha256=`da2aa7672e6a446cbea533078fc5b48553a6a59652f1d4e376220ef7e8aaba68`
- `ai_strategy_engine/bootstrap/strategy_engine_source.zip.b64.part03b`: bytes=18000, blob_sha=`42c361aace41e4b226d92e3a0847aabf420e695f`, sha256=`9aa05012fa6d38a15001a71c9db4a3f805d4fe08ccd89565d286f70397638a4b`
- `ai_strategy_engine/bootstrap/strategy_engine_source.zip.b64.part04`: bytes=18000, blob_sha=`1024d6c40bd7181f5c185d6c0c0a8b1b60467793`, sha256=`a5e6b0c8f1aa86450c71636867bf360d706d467a1a424cd86a546dcf210c48b3`
- `ai_strategy_engine/bootstrap/strategy_engine_source.zip.b64.part05`: bytes=17468, blob_sha=`674ffd6cf3a69427af2ac93497ef1f404aea489a`, sha256=`ebb510d23054c3b9bce86ab04ceda7328717730d177029f75aefe8131bf58fa1`

- current reconstructed ZIP SHA-256: `e8a8f6f6aeba3c2bb9eb95e96355bb478e2a70cd9f1ebb4aa62a3d511cb601db`
- reconstructed bytes: `62601`
- ZIP readable: `true`
- ZIP member count: `84`
- ZIP test failure: `examples/signal_event.json`

## Current ZIP members
```text
schemas/
schemas/signal-event.v1.schema.json
schemas/feature-record.v1.schema.json
schemas/strategy-definition.v1.schema.json
examples/
examples/strategy_classic.json
examples/strategy_miyagi_ensemble_research.json
examples/strategy_bonsai_research.json
examples/signal_event.json
examples/strategy_liquidation.json
Makefile
configs/
configs/search_spaces.v1.yaml
configs/miyagi_parameter_map.v1.yaml
configs/feature_registry.v1.yaml
ARCHITECTURE.md
README.md
docs/
docs/AI_ADAPTATION_POLICY.md
docs/STRATEGY_DSL.md
docs/FEATURE_REGISTRY_V1.md
docs/TIMESTAMP_SEMANTICS.md
docs/MIYAGI_PARAMETER_MAP.md
docs/TECHNICAL_AUDIT.md
docs/VALIDATION_AND_ACCEPTANCE.md
docs/DECISIONS.md
docs/LICENSE_BOUNDARIES.md
docs/IMPLEMENTATION_CHECKPOINT.md
src/
src/strategy_engine/
src/strategy_engine/dsl/
src/strategy_engine/dsl/validator.py
src/strategy_engine/dsl/__init__.py
src/strategy_engine/risk/
src/strategy_engine/risk/position_management.py
src/strategy_engine/risk/__init__.py
src/strategy_engine/domain/
src/strategy_engine/domain/models.py
src/strategy_engine/domain/__init__.py
src/strategy_engine/api/
src/strategy_engine/api/contracts.py
src/strategy_engine/api/__init__.py
src/strategy_engine/policies/
src/strategy_engine/policies/signals.py
src/strategy_engine/policies/__init__.py
src/strategy_engine/features/
src/strategy_engine/features/pivots.py
src/strategy_engine/features/base.py
src/strategy_engine/features/trend.py
src/strategy_engine/features/macd.py
src/strategy_engine/features/volume.py
src/strategy_engine/features/candles.py
src/strategy_engine/features/momentum.py
src/strategy_engine/features/range_filter.py
src/strategy_engine/features/squeeze.py
src/strategy_engine/features/common.py
src/strategy_engine/features/supertrend.py
src/strategy_engine/features/market_structure.py
src/strategy_engine/features/__init__.py
src/strategy_engine/validation/
src/strategy_engine/validation/leakage.py
src/strategy_engine/validation/__init__.py
src/strategy_engine/__init__.py
tests/
tests/e2e/
tests/e2e/test_examples_validate.py
tests/e2e/test_pipeline_contract.py
tests/unit/
tests/unit/test_momentum.py
tests/unit/test_trend.py
tests/unit/test_volume.py
tests/unit/test_position_management.py
tests/unit/test_signal_policies.py
tests/unit/test_pivots.py
tests/unit/test_squeeze.py
tests/unit/test_range_filter.py
tests/unit/test_models.py
tests/unit/test_macd.py
sources/
sources/README.md
TASKS.md
AGENT_MASTER_PROMPT.md
.gitignore
pyproject.toml
```

## Historical candidate commits
- `3982c8fa60194a228abe5e87f8b1f5aeedeac09f`: parts=5, digest=`6b7a54ab1ec387390fe5a93e8ada03c93b1c2950b3696b753940349ba931493a`, bytes=45000
- `78185932aef785f960d65a21a958b78af1dfb536`: parts=3, digest=`d46fa7670c7dde43213b94e0fcac6e529145250c0edac05766fcae209cf6ae3c`, bytes=18000
- `991f5eda1df21284732c90f67956d8f45f276ee9`: parts=7, digest=`e8a8f6f6aeba3c2bb9eb95e96355bb478e2a70cd9f1ebb4aa62a3d511cb601db`, bytes=62601
- `a5d38176f373543b99e376f43cc2cb4d91b09970`: parts=7, digest=`e8a8f6f6aeba3c2bb9eb95e96355bb478e2a70cd9f1ebb4aa62a3d511cb601db`, bytes=62601
- `bb20405108220587b0f66e5de3f6e2280d0ffdb9`: parts=2, digest=`e996121cde8df763888bcfec5b719c9d63fa8f0d7ef8fabc094acbcc47f40d76`, bytes=13500
- `c489ef6af793482dd76edfddd11e011cd7613dce`: parts=6, digest=`ee2d68c378ad184cfcfd7c3d3c02dc13eaa6d22bc72ba30b82e476a53c9e26f1`, bytes=58101
- `e29c132a44f7ef90ba494ada5c86491076e5bcbc`: parts=1, digest=`e44869e969fa40f0e53d83bbd306b065973d0c7bfa9c60fdbd3ca994f3f8df5f`, bytes=9000
- `ff47e0d19dacf6c34904c2e87f0d5cd9a970b8e7`: parts=4, digest=`2ed4dea860e315b7bad89bd2b8d24cc9aab11419a64c4c0c0e1b25cfa1c5d7cf`, bytes=31500

## Digest summary
- `2ed4dea860e315b7bad89bd2b8d24cc9aab11419a64c4c0c0e1b25cfa1c5d7cf`: 1 commit(s)
- `6b7a54ab1ec387390fe5a93e8ada03c93b1c2950b3696b753940349ba931493a`: 1 commit(s)
- `d46fa7670c7dde43213b94e0fcac6e529145250c0edac05766fcae209cf6ae3c`: 1 commit(s)
- `e44869e969fa40f0e53d83bbd306b065973d0c7bfa9c60fdbd3ca994f3f8df5f`: 1 commit(s)
- `e8a8f6f6aeba3c2bb9eb95e96355bb478e2a70cd9f1ebb4aa62a3d511cb601db`: 2 commit(s)
- `e996121cde8df763888bcfec5b719c9d63fa8f0d7ef8fabc094acbcc47f40d76`: 1 commit(s)
- `ee2d68c378ad184cfcfd7c3d3c02dc13eaa6d22bc72ba30b82e476a53c9e26f1`: 1 commit(s)

## Materialized-path history
```text
991f5eda1df21284732c90f67956d8f45f276ee9 2026-07-28T10:23:23+02:00 test(ai-strategy): materialize reference contract suite
A	ai_strategy_engine/tests/e2e/test_examples_validate.py
A	ai_strategy_engine/tests/e2e/test_pipeline_contract.py
A	ai_strategy_engine/tests/unit/test_macd.py
A	ai_strategy_engine/tests/unit/test_models.py
A	ai_strategy_engine/tests/unit/test_momentum.py
A	ai_strategy_engine/tests/unit/test_pivots.py
A	ai_strategy_engine/tests/unit/test_position_management.py
A	ai_strategy_engine/tests/unit/test_range_filter.py
A	ai_strategy_engine/tests/unit/test_signal_policies.py
A	ai_strategy_engine/tests/unit/test_squeeze.py
A	ai_strategy_engine/tests/unit/test_trend.py
A	ai_strategy_engine/tests/unit/test_volume.py
```

## Reachable relevant objects
```text
d360223da4077ad773deccd3df1367a7e26330d9 ai_strategy_engine/bootstrap/strategy_engine_source.zip.b64.part01
2d30581a92418b60814360df46ab400e373ff87a ai_strategy_engine/bootstrap/strategy_engine_source.zip.b64.part02a
0c236c5885bcaa5ea9d7df88817beeeb98d4b0f1 ai_strategy_engine/bootstrap/strategy_engine_source.zip.b64.part02b
7e3f3d929f78f14f44fb04f2be9a0e460151dd1e ai_strategy_engine/bootstrap/strategy_engine_source.zip.b64.part03a
42c361aace41e4b226d92e3a0847aabf420e695f ai_strategy_engine/bootstrap/strategy_engine_source.zip.b64.part03b
1024d6c40bd7181f5c185d6c0c0a8b1b60467793 ai_strategy_engine/bootstrap/strategy_engine_source.zip.b64.part04
674ffd6cf3a69427af2ac93497ef1f404aea489a ai_strategy_engine/bootstrap/strategy_engine_source.zip.b64.part05
```

## Recovery
- exact expected bundle was not found in reachable Git history.
