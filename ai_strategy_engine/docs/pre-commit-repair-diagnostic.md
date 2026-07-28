# ASE-00 pre-commit repair diagnostic

- exit code: `1`

## Output
```text
[INFO] Initializing environment for local:python-rapidjson,jsonschema.
[INFO] Initializing environment for https://github.com/pre-commit/mirrors-mypy.
[INFO] Initializing environment for https://github.com/pre-commit/mirrors-mypy:types-cachetools==7.0.0.20260518,types-filelock==3.2.7,types-requests==2.33.0.20260518,types-tabulate==0.10.0.20260508,types-python-dateutil==2.9.0.20260518,scipy-stubs==1.17.1.5,SQLAlchemy==2.0.51.
[INFO] Initializing environment for https://github.com/charliermarsh/ruff-pre-commit.
[INFO] Initializing environment for https://github.com/pre-commit/pre-commit-hooks.
[INFO] Initializing environment for https://github.com/stefmolin/exif-stripper.
[INFO] Initializing environment for https://github.com/codespell-project/codespell.
[INFO] Initializing environment for https://github.com/codespell-project/codespell:tomli.
[INFO] Initializing environment for https://github.com/woodruffw/zizmor-pre-commit.
[INFO] Installing environment for local.
[INFO] Once installed this environment will be reused.
[INFO] This may take a few minutes...
[INFO] Installing environment for https://github.com/pre-commit/mirrors-mypy.
[INFO] Once installed this environment will be reused.
[INFO] This may take a few minutes...
[INFO] Installing environment for https://github.com/charliermarsh/ruff-pre-commit.
[INFO] Once installed this environment will be reused.
[INFO] This may take a few minutes...
[INFO] Installing environment for https://github.com/pre-commit/pre-commit-hooks.
[INFO] Once installed this environment will be reused.
[INFO] This may take a few minutes...
[INFO] Installing environment for https://github.com/stefmolin/exif-stripper.
[INFO] Once installed this environment will be reused.
[INFO] This may take a few minutes...
[INFO] Installing environment for https://github.com/codespell-project/codespell.
[INFO] Once installed this environment will be reused.
[INFO] This may take a few minutes...
[INFO] Installing environment for https://github.com/woodruffw/zizmor-pre-commit.
[INFO] Once installed this environment will be reused.
[INFO] This may take a few minutes...
extract-config-json-schema...............................................Passed
mypy.....................................................................Failed
- hook id: mypy
- exit code: 2

tests/freqai/conftest.py: error: Duplicate module named "conftest" (also at "tests/ai_platform_integration/conftest.py")
tests/freqai/conftest.py: note: See https://mypy.readthedocs.io/en/stable/running_mypy.html#mapping-file-paths-to-modules for more info
tests/freqai/conftest.py: note: Common resolutions include:
tests/freqai/conftest.py: note:     a) using `--exclude` to avoid checking one of them,
tests/freqai/conftest.py: note:     b) adding `__init__.py` somewhere,
tests/freqai/conftest.py: note:     c) using `--explicit-package-bases` or adjusting `MYPYPATH`
Found 1 error in 1 file (errors prevented further checking)

ruff (legacy alias)......................................................Failed
- hook id: ruff
- exit code: 1

I001 [*] Import block is un-sorted or un-formatted
  --> ai_platform/research/strategy_engine/ase00_adapter.py:1:1
   |
 1 | / from __future__ import annotations
 2 | |
 3 | | import math
 4 | | import os
 5 | | from collections.abc import Mapping, Sequence
 6 | | from dataclasses import dataclass
 7 | | from datetime import datetime, timedelta
 8 | | from pathlib import Path
 9 | | from typing import Literal, cast
10 | |
11 | | import pandas as pd
12 | | from pydantic import JsonValue
13 | |
14 | | from ai_platform.portal.contracts.risk import RiskDecisionOutcome
15 | | from ai_platform.portal.risk.schema import RiskEvaluationSnapshot, RiskPolicyLimits
16 | | from ai_platform.portal.risk.service import RiskService
17 | | from strategy_engine.domain.models import (
18 | |     Action,
19 | |     FeatureRecord,
20 | |     FeatureReference,
21 | |     Provenance,
22 | |     ShadowDecisionEvidence,
23 | |     Side,
24 | |     SignalEvent,
25 | |     StrategyDefinition,
26 | |     canonical_sha256,
27 | | )
28 | | from strategy_engine.dsl.evaluator import (
29 | |     DslEvaluationError,
30 | |     EvaluationSnapshot,
31 | |     StrategyEvaluator,
32 | | )
33 | | from strategy_engine.dsl.validator import StrategyValidationError, StrategyValidator
34 | | from strategy_engine.features.pivots import confirmed_pivots
35 | | from strategy_engine.features.records import make_confirmed_pivot_record, make_feature_record
36 | | from strategy_engine.features.squeeze import squeeze_features
37 | | from strategy_engine.features.supertrend import supertrend_features
38 | | from strategy_engine.registry import FeatureRegistry, SearchSpaceRegistry
39 | | from strategy_engine.validation.leakage import (
40 | |     LeakageContext,
41 | |     LeakageError,
42 | |     assert_features_available,
43 | | )
   | |_^
   |
help: Organize imports

Found 1 error.
[*] 1 fixable with the `--fix` option.

ruff format..............................................................Passed
fix end of files.........................................................Passed
mixed line ending........................................................Passed
debug statements (python)................................................Passed
check python ast.........................................................Passed
trim trailing whitespace.................................................Passed
strip EXIF metadata......................................................Passed
codespell................................................................Passed
zizmor...................................................................Passed
pre-commit hook(s) made changes.
If you are seeing this message in CI, reproduce locally with: `pre-commit run --all-files`.
To run `pre-commit` as part of git workflow, use `pre-commit install`.
All changes made by hooks:
diff --git a/.github/workflows/ai-strategy-engine.yml b/.github/workflows/ai-strategy-engine.yml
index a17401c75..d4c133c21 100644
--- a/.github/workflows/ai-strategy-engine.yml
+++ b/.github/workflows/ai-strategy-engine.yml
@@ -5,130 +5,220 @@ on:
     branches:
       - agent/ase-00-ai-strategy-engine-foundation
     paths:
+      - ai_strategy_engine/**
+      - ai_platform/research/strategy_engine/**
+      - tests/ai_platform_integration/conftest.py
+      - tests/ai_platform_integration/test_ase00_vertical_slice.py
       - .github/workflows/ai-strategy-engine.yml
   pull_request:
     branches:
       - develop
     paths:
+      - ai_strategy_engine/**
+      - ai_platform/research/strategy_engine/**
+      - tests/ai_platform_integration/conftest.py
+      - tests/ai_platform_integration/test_ase00_vertical_slice.py
       - .github/workflows/ai-strategy-engine.yml
+  workflow_dispatch:
 
 permissions:
-  contents: write
+  contents: read
+
+concurrency:
+  group: "${{ github.workflow }}-${{ github.ref }}"
+  cancel-in-progress: true
 
 jobs:
-  repair-pre-commit:
-    if: github.event_name == 'push' || github.event.pull_request.head.ref == 'agent/ase-00-ai-strategy-engine-foundation'
+  validate:
+    name: ASE-00 complete validation
     runs-on: ubuntu-24.04
-    timeout-minutes: 45
+    timeout-minutes: 30
     steps:
-      - name: Check out branch
+      - name: Check out exact source
         uses: actions/checkout@9c091bb21b7c1c1d1991bb908d89e4e9dddfe3e0 # v7.0.0
         with:
-          ref: agent/ase-00-ai-strategy-engine-foundation
           fetch-depth: 0
+          persist-credentials: false
 
       - name: Set up Python 3.12
         uses: actions/setup-python@ece7cb06caefa5fff74198d8649806c4678c61a1 # v6.3.0
         with:
           python-version: "3.12"
 
-      - name: Apply bounded findings and run exact pre-commit
-        id: repair
+      - name: Install development dependencies
+        working-directory: ai_strategy_engine
         run: |
-          cp .github/workflows/ai-strategy-engine.yml /tmp/diagnostic-workflow.yml
-          printf '%s\n' '"""Research-only modules."""' > ai_platform/research/__init__.py
-          : > ai_strategy_engine/src/strategy_engine/policies/__init__.py
-          : > ai_strategy_engine/src/strategy_engine/risk/__init__.py
-          python - <<'PY'
-          from pathlib import Path
+          python -m venv .venv
+          . .venv/bin/activate
+          python -m pip install --upgrade pip
+          pip install -e ".[dev]" "SQLAlchemy>=2.0.6" "fastapi>=0.115"
 
-          path = Path('pyproject.toml')
-          text = path.read_text(encoding='utf-8')
-          old = 'ignore-words-list = "coo,fo,strat,zar,selectin"'
-          new = 'ignore-words-list = "coo,fo,strat,zar,selectin,numer,parametr,losd,tekst"'
-          if text.count(old) != 1:
-              raise SystemExit('codespell configuration anchor mismatch')
-          path.write_text(text.replace(old, new, 1), encoding='utf-8')
-          PY
-          rm -f ai_strategy_engine/docs/pre-commit-diagnostic.md \
-            ai_strategy_engine/docs/pre-commit-repair-diagnostic.md
-          git show 627d0dc610d25859b13809aee147918d461f6619:.github/workflows/ai-strategy-engine.yml \
-            > .github/workflows/ai-strategy-engine.yml
-          python -m pip install --disable-pip-version-check pre-commit
-          set +e
-          pre-commit run --all-files --show-diff-on-failure > /tmp/pre-commit.txt 2>&1
-          status=$?
-          git diff --binary > /tmp/pre-commit.diff
-          set -e
-          if [[ "$status" -ne 0 ]]; then
-            git reset --hard HEAD
-            {
-              echo '# ASE-00 pre-commit repair diagnostic'
-              echo
-              echo "- exit code: \`$status\`"
-              echo
-              echo '## Output'
-              echo '```text'
-              cat /tmp/pre-commit.txt
-              echo '```'
-              echo
-              echo '## Proposed diff'
-              echo '```diff'
-              cat /tmp/pre-commit.diff
-              echo '```'
-            } > ai_strategy_engine/docs/pre-commit-repair-diagnostic.md
-            git config user.name "github-actions[bot]"
-            git config user.email "41898282+github-actions[bot]@users.noreply.github.com"
-            git add ai_strategy_engine/docs/pre-commit-repair-diagnostic.md
-            git commit -m "docs(ai-strategy): record remaining pre-commit finding"
-            git push origin HEAD:agent/ase-00-ai-strategy-engine-foundation
-            echo 'validated=false' >> "$GITHUB_OUTPUT"
-            exit 0
-          fi
-          cp /tmp/diagnostic-workflow.yml .github/workflows/ai-strategy-engine.yml
-          echo 'validated=true' >> "$GITHUB_OUTPUT"
-
-      - name: Validate exact AI Platform matrix
-        if: steps.repair.outputs.validated == 'true'
+      - name: Run package tests
+        working-directory: ai_strategy_engine
         run: |
-          python -m venv .venv-ai-platform
-          . .venv-ai-platform/bin/activate
-          python -m pip install --disable-pip-version-check \
-            pytest jsonschema "pydantic>=2.2" "SQLAlchemy>=2.0.6" \
-            "httpx>=0.24.1" fastapi pyjwt cryptography \
-            ruff==0.15.21 codespell==2.4.2
-          ruff check ai_platform tests/ai_platform
-          ruff format --check ai_platform tests/ai_platform
-          python -m compileall -q ai_platform tests/ai_platform
-          python -m pytest -q -o addopts='' --confcutdir=tests/ai_platform tests/ai_platform
-
-      - name: Validate complete ASE-00 matrix
-        if: steps.repair.outputs.validated == 'true'
-        env:
-          PYTHONPATH: "${{ github.workspace }}:${{ github.workspace }}/ai_strategy_engine/src"
+          . .venv/bin/activate
+          pytest -q
+
+      - name: Run Ruff
         run: |
-          python -m venv .venv-ase
-          . .venv-ase/bin/activate
-          python -m pip install --disable-pip-version-check \
-            -e "ai_strategy_engine[dev]" "SQLAlchemy>=2.0.6" "fastapi>=0.115"
-          pytest -q ai_strategy_engine/tests
+          . ai_strategy_engine/.venv/bin/activate
           ruff check ai_strategy_engine ai_platform/research/strategy_engine \
             tests/ai_platform_integration/test_ase00_vertical_slice.py
-          mypy ai_strategy_engine/src/strategy_engine
+
+      - name: Run mypy
+        working-directory: ai_strategy_engine
+        run: |
+          . .venv/bin/activate
+          mypy src/strategy_engine
+
+      - name: Compile source and tests
+        run: |
+          . ai_strategy_engine/.venv/bin/activate
           python -m compileall -q ai_strategy_engine/src ai_strategy_engine/tests \
             ai_platform/research/strategy_engine
+
+      - name: Validate deterministic repository E2E
+        env:
+          PYTHONPATH: "${{ github.workspace }}:${{ github.workspace }}/ai_strategy_engine/src"
+        run: |
+          . ai_strategy_engine/.venv/bin/activate
           pytest -q -o addopts='' --confcutdir=tests/ai_platform_integration \
             tests/ai_platform_integration/test_ase00_vertical_slice.py
 
-      - name: Commit validated pre-commit repair
-        if: steps.repair.outputs.validated == 'true'
+      - name: Validate JSON YAML and JSON Schema examples
+        working-directory: ai_strategy_engine
+        run: |
+          . .venv/bin/activate
+          python - <<'PY'
+          from __future__ import annotations
+
+          import json
+          from pathlib import Path
+
+          import jsonschema
+          import yaml
+
+          root = Path('.')
+          for path in sorted(root.rglob('*.json')):
+              json.loads(path.read_text(encoding='utf-8'))
+          yaml_paths = sorted(root.rglob('*.yaml')) + sorted(root.rglob('*.yml'))
+          for path in yaml_paths:
+              yaml.safe_load(path.read_text(encoding='utf-8'))
+
+          mappings = {
+              'examples/feature_record.json': 'schemas/feature-record.v1.schema.json',
+              'examples/signal_event.json': 'schemas/signal-event.v1.schema.json',
+              'examples/strategy_classic.json': 'schemas/strategy-definition.v1.schema.json',
+              'examples/strategy_liquidation.json': 'schemas/strategy-definition.v1.schema.json',
+              'examples/strategy_miyagi_ensemble_research.json': (
+                  'schemas/strategy-definition.v1.schema.json'
+              ),
+              'examples/strategy_bonsai_research.json': (
+                  'schemas/strategy-definition.v1.schema.json'
+              ),
+          }
+          for example_name, schema_name in mappings.items():
+              example = json.loads((root / example_name).read_text(encoding='utf-8'))
+              schema = json.loads((root / schema_name).read_text(encoding='utf-8'))
+              jsonschema.Draft202012Validator.check_schema(schema)
+              jsonschema.validate(example, schema)
+          print('JSON/YAML parsing and JSON Schema validation passed')
+          PY
+
+      - name: Verify materialization evidence and required paths
+        working-directory: ai_strategy_engine
         run: |
-          git config user.name "github-actions[bot]"
-          git config user.email "41898282+github-actions[bot]@users.noreply.github.com"
-          git add ai_platform/research/__init__.py pyproject.toml \
-            ai_strategy_engine/src/strategy_engine/policies/__init__.py \
-            ai_strategy_engine/src/strategy_engine/risk/__init__.py \
-            ai_strategy_engine/docs/pre-commit-diagnostic.md \
-            ai_strategy_engine/docs/pre-commit-repair-diagnostic.md
-          git commit -m "fix(ai-strategy): satisfy repository pre-commit contracts"
-          git push origin HEAD:agent/ase-00-ai-strategy-engine-foundation
+          test -f configs/feature_registry.v1.yaml
+          test -f configs/search_spaces.v1.yaml
+          test -f configs/miyagi_parameter_map.v1.yaml
+          test -d schemas
+          test -d examples
+          test -d src/strategy_engine
+          test -d tests
+          test -d docs
+          grep -Fq '73a0d99cab94ba116818a6aef9d818a710fb048a4c0b77f89b9819dd9ac7332f' \
+            docs/materialization-evidence.md
+          grep -Fq 'status: `complete`' docs/materialization-evidence.md
+
+      - name: Scan secrets prohibited code and architecture boundaries
+        run: |
+          . ai_strategy_engine/.venv/bin/activate
+          python - <<'PY'
+          from __future__ import annotations
+
+          import ast
+          import re
+          import subprocess
+          from pathlib import Path
+
+          roots = [
+              Path('ai_strategy_engine/src'),
+              Path('ai_strategy_engine/tests'),
+              Path('ai_strategy_engine/configs'),
+              Path('ai_strategy_engine/examples'),
+              Path('ai_platform/research/strategy_engine'),
+              Path('tests/ai_platform_integration/test_ase00_vertical_slice.py'),
+          ]
+          suffixes = {'.py', '.json', '.yaml', '.yml', '.toml'}
+          text_files = [
+              path
+              for root in roots
+              for path in ([root] if root.is_file() else root.rglob('*'))
+              if path.is_file() and path.suffix.lower() in suffixes
+          ]
+          secret_patterns = {
+              'private key': re.compile(
+                  r'-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----'
+              ),
+              'AWS access key': re.compile(r'AKIA[0-9A-Z]{16}'),
+              'GitHub token': re.compile(r'gh[pousr]_[A-Za-z0-9_]{30,}'),
+              'OpenAI key': re.compile(r'sk-[A-Za-z0-9]{32,}'),
+          }
+          failures: list[str] = []
+          for path in text_files:
+              text = path.read_text(encoding='utf-8')
+              if 'luxalgo' in text.lower():
+                  failures.append(f'{path}: prohibited LuxAlgo runtime reference')
+              for label, pattern in secret_patterns.items():
+                  if pattern.search(text):
+                      failures.append(f'{path}: possible {label}')
+              if path.suffix != '.py':
+                  continue
+              tree = ast.parse(text, filename=str(path))
+              for node in ast.walk(tree):
+                  if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
+                      if node.func.id in {'eval', 'exec'}:
+                          failures.append(
+                              f'{path}:{node.lineno}: prohibited {node.func.id}()'
+                          )
+                  if isinstance(node, ast.Import):
+                      for alias in node.names:
+                          if alias.name.startswith(
+                              ('freqtrade', 'ai_platform.portal.execution')
+                          ):
+                              failures.append(
+                                  f'{path}:{node.lineno}: direct execution import '
+                                  f'{alias.name}'
+                              )
+                  if isinstance(node, ast.ImportFrom):
+                      imported = node.module or ''
+                      if imported.startswith(
+                          ('freqtrade', 'ai_platform.portal.execution')
+                      ):
+                          failures.append(
+                              f'{path}:{node.lineno}: direct execution import {imported}'
+                          )
+
+          changed = subprocess.check_output(
+              ['git', 'diff', '--name-only', 'origin/develop...HEAD'],
+              text=True,
+          ).splitlines()
+          browser_changes = [
+              path for path in changed if path.startswith('ai_platform/portal/web/')
+          ]
+          if browser_changes:
+              failures.append(f'Browser paths changed by ASE-00: {browser_changes}')
+          if failures:
+              raise SystemExit('\n'.join(failures))
+          print('Security and architecture boundary scans passed')
+          PY
diff --git a/ai_strategy_engine/docs/pre-commit-diagnostic.md b/ai_strategy_engine/docs/pre-commit-diagnostic.md
deleted file mode 100644
index 6cfc741af..000000000
--- a/ai_strategy_engine/docs/pre-commit-diagnostic.md
+++ /dev/null
@@ -1,191 +0,0 @@
-# ASE-00 repository pre-commit diagnostic
-
-- exit code: `1`
-
-## Output
-```text
-[INFO] Initializing environment for local:python-rapidjson,jsonschema.
-[INFO] Initializing environment for https://github.com/pre-commit/mirrors-mypy.
-[INFO] Initializing environment for https://github.com/pre-commit/mirrors-mypy:types-cachetools==7.0.0.20260518,types-filelock==3.2.7,types-requests==2.33.0.20260518,types-tabulate==0.10.0.20260508,types-python-dateutil==2.9.0.20260518,scipy-stubs==1.17.1.5,SQLAlchemy==2.0.51.
-[INFO] Initializing environment for https://github.com/charliermarsh/ruff-pre-commit.
-[INFO] Initializing environment for https://github.com/pre-commit/pre-commit-hooks.
-[INFO] Initializing environment for https://github.com/stefmolin/exif-stripper.
-[INFO] Initializing environment for https://github.com/codespell-project/codespell.
-[INFO] Initializing environment for https://github.com/codespell-project/codespell:tomli.
-[INFO] Initializing environment for https://github.com/woodruffw/zizmor-pre-commit.
-[INFO] Installing environment for local.
-[INFO] Once installed this environment will be reused.
-[INFO] This may take a few minutes...
-[INFO] Installing environment for https://github.com/pre-commit/mirrors-mypy.
-[INFO] Once installed this environment will be reused.
-[INFO] This may take a few minutes...
-[INFO] Installing environment for https://github.com/charliermarsh/ruff-pre-commit.
-[INFO] Once installed this environment will be reused.
-[INFO] This may take a few minutes...
-[INFO] Installing environment for https://github.com/pre-commit/pre-commit-hooks.
-[INFO] Once installed this environment will be reused.
-[INFO] This may take a few minutes...
-[INFO] Installing environment for https://github.com/stefmolin/exif-stripper.
-[INFO] Once installed this environment will be reused.
-[INFO] This may take a few minutes...
-[INFO] Installing environment for https://github.com/codespell-project/codespell.
-[INFO] Once installed this environment will be reused.
-[INFO] This may take a few minutes...
-[INFO] Installing environment for https://github.com/woodruffw/zizmor-pre-commit.
-[INFO] Once installed this environment will be reused.
-[INFO] This may take a few minutes...
-extract-config-json-schema...............................................Passed
-mypy.....................................................................Failed
-- hook id: mypy
-- exit code: 2
-
-ai_strategy_engine/src/strategy_engine/__init__.py: error: Duplicate module named "strategy_engine" (also at "ai_platform/research/strategy_engine/__init__.py")
-ai_strategy_engine/src/strategy_engine/__init__.py: note: See https://mypy.readthedocs.io/en/stable/running_mypy.html#mapping-file-paths-to-modules for more info
-ai_strategy_engine/src/strategy_engine/__init__.py: note: Common resolutions include:
-ai_strategy_engine/src/strategy_engine/__init__.py: note:     a) using `--exclude` to avoid checking one of them,
-ai_strategy_engine/src/strategy_engine/__init__.py: note:     b) adding `__init__.py` somewhere,
-ai_strategy_engine/src/strategy_engine/__init__.py: note:     c) using `--explicit-package-bases` or adjusting `MYPYPATH`
-Found 1 error in 1 file (errors prevented further checking)
-
-ruff (legacy alias)......................................................Passed
-ruff format..............................................................Passed
-fix end of files.........................................................Failed
-- hook id: end-of-file-fixer
-- exit code: 1
-- files were modified by this hook
-
-Fixing ai_strategy_engine/src/strategy_engine/risk/__init__.py
-Fixing ai_strategy_engine/src/strategy_engine/policies/__init__.py
-
-mixed line ending........................................................Passed
-debug statements (python)................................................Passed
-check python ast.........................................................Passed
-trim trailing whitespace.................................................Passed
-strip EXIF metadata......................................................Passed
-codespell................................................................Failed
-- hook id: codespell
-- exit code: 65
-
-ai_strategy_engine/AGENT_MASTER_PROMPT.md:15: numer ==> number
-ai_strategy_engine/docs/MIYAGI_PARAMETER_MAP.md:8: parametr ==> parameter
-ai_strategy_engine/docs/damaged-member-recovery.md:108: losd ==> lost, loss, lose, load
-ai_strategy_engine/docs/damaged-member-recovery.md:154: losd ==> lost, loss, lose, load
-ai_strategy_engine/sources/README.md:18: tekst ==> text
-
-zizmor...................................................................Failed
-- hook id: zizmor
-- exit code: 13
-
-[32m INFO[0m [2mzizmor[0m[2m:[0m 🌈 zizmor v1.26.1
-[32m INFO[0m [1maudit[0m[2m:[0m [2mzizmor[0m[2m:[0m 🌈 completed .github/actions/docker-tags/action.yml
-[32m INFO[0m [1maudit[0m[2m:[0m [2mzizmor[0m[2m:[0m 🌈 completed .github/dependabot.yml
-[32m INFO[0m [1maudit[0m[2m:[0m [2mzizmor[0m[2m:[0m 🌈 completed .github/workflows/ai-platform-binance-spot-instrument-shadow-acceptance.yml
-[32m INFO[0m [1maudit[0m[2m:[0m [2mzizmor[0m[2m:[0m 🌈 completed .github/workflows/ai-platform-binance-spot-instrument-smoke-selfhosted.yml
-[32m INFO[0m [1maudit[0m[2m:[0m [2mzizmor[0m[2m:[0m 🌈 completed .github/workflows/ai-platform-binance-spot-instrument-smoke.yml
-[32m INFO[0m [1maudit[0m[2m:[0m [2mzizmor[0m[2m:[0m 🌈 completed .github/workflows/ai-platform-liquidation-candle-artifact.yml
-[32m INFO[0m [1maudit[0m[2m:[0m [2mzizmor[0m[2m:[0m 🌈 completed .github/workflows/ai-platform-okx-liquidation-shadow-acceptance-staging-preflight.yml
-[32m INFO[0m [1maudit[0m[2m:[0m [2mzizmor[0m[2m:[0m 🌈 completed .github/workflows/ai-platform-okx-liquidation-shadow-acceptance.yml
-[32m INFO[0m [1maudit[0m[2m:[0m [2mzizmor[0m[2m:[0m 🌈 completed .github/workflows/ai-platform-okx-liquidation-shadow-smoke.yml
-[32m INFO[0m [1maudit[0m[2m:[0m [2mzizmor[0m[2m:[0m 🌈 completed .github/workflows/ai-platform-phase5-data-cache.yml
-[32m INFO[0m [1maudit[0m[2m:[0m [2mzizmor[0m[2m:[0m 🌈 completed .github/workflows/ai-platform-phase5-exit-tuning.yml
-[32m INFO[0m [1maudit[0m[2m:[0m [2mzizmor[0m[2m:[0m 🌈 completed .github/workflows/ai-platform-phase5-final-validation-v2.yml
-[32m INFO[0m [1maudit[0m[2m:[0m [2mzizmor[0m[2m:[0m 🌈 completed .github/workflows/ai-platform-phase5-final-validation.yml
-[32m INFO[0m [1maudit[0m[2m:[0m [2mzizmor[0m[2m:[0m 🌈 completed .github/workflows/ai-platform-phase5-tuning.yml
-[32m INFO[0m [1maudit[0m[2m:[0m [2mzizmor[0m[2m:[0m 🌈 completed .github/workflows/ai-platform-phase6-historical-comparison.yml
-[32m INFO[0m [1maudit[0m[2m:[0m [2mzizmor[0m[2m:[0m 🌈 completed .github/workflows/ai-platform-phase6-model-comparison.yml
-[32m INFO[0m [1maudit[0m[2m:[0m [2mzizmor[0m[2m:[0m 🌈 completed .github/workflows/ai-platform-rl-v2-action-observability-execution.yml
-[32m INFO[0m [1maudit[0m[2m:[0m [2mzizmor[0m[2m:[0m 🌈 completed .github/workflows/ai-platform-rl-v2-execution-preflight.yml
-[32m INFO[0m [1maudit[0m[2m:[0m [2mzizmor[0m[2m:[0m 🌈 completed .github/workflows/ai-platform-rl-v2-historical-training-execution.yml
-[32m INFO[0m [1maudit[0m[2m:[0m [2mzizmor[0m[2m:[0m 🌈 completed .github/workflows/ai-platform-rl-v2-lifecycle-seed-robustness.yml
-[32m INFO[0m [1maudit[0m[2m:[0m [2mzizmor[0m[2m:[0m 🌈 completed .github/workflows/ai-platform-rl-v2-roi-lifecycle-paired-attribution.yml
-[32m INFO[0m [1maudit[0m[2m:[0m [2mzizmor[0m[2m:[0m 🌈 completed .github/workflows/ai-platform-tradingview-futures-historical-benchmark.yml
-[32m INFO[0m [1maudit[0m[2m:[0m [2mzizmor[0m[2m:[0m 🌈 completed .github/workflows/ai-platform-tradingview-futures-lookahead-repair.yml
-[32m INFO[0m [1maudit[0m[2m:[0m [2mzizmor[0m[2m:[0m 🌈 completed .github/workflows/ai-platform-tradingview-futures-preflight.yml
-[32m INFO[0m [1maudit[0m[2m:[0m [2mzizmor[0m[2m:[0m 🌈 completed .github/workflows/ai-platform.yml
-[32m INFO[0m [1maudit[0m[2m:[0m [2mzizmor[0m[2m:[0m 🌈 completed .github/workflows/ai-strategy-engine.yml
-[32m INFO[0m [1maudit[0m[2m:[0m [2mzizmor[0m[2m:[0m 🌈 completed .github/workflows/binance-lev-tier-update.yml
-[32m INFO[0m [1maudit[0m[2m:[0m [2mzizmor[0m[2m:[0m 🌈 completed .github/workflows/ci.yml
-[32m INFO[0m [1maudit[0m[2m:[0m [2mzizmor[0m[2m:[0m 🌈 completed .github/workflows/deploy-docs.yml
-[32m INFO[0m [1maudit[0m[2m:[0m [2mzizmor[0m[2m:[0m 🌈 completed .github/workflows/devcontainer-build.yml
-[32m INFO[0m [1maudit[0m[2m:[0m [2mzizmor[0m[2m:[0m 🌈 completed .github/workflows/docker-build.yml
-[32m INFO[0m [1maudit[0m[2m:[0m [2mzizmor[0m[2m:[0m 🌈 completed .github/workflows/docker-update-readme.yml
-[32m INFO[0m [1maudit[0m[2m:[0m [2mzizmor[0m[2m:[0m 🌈 completed .github/workflows/experimental-model-historical-backtest-execution.yml
-[32m INFO[0m [1maudit[0m[2m:[0m [2mzizmor[0m[2m:[0m 🌈 completed .github/workflows/experimental-model-historical-execution-preflight.yml
-[32m INFO[0m [1maudit[0m[2m:[0m [2mzizmor[0m[2m:[0m 🌈 completed .github/workflows/experimental-model-runtime-smoke.yml
-[32m INFO[0m [1maudit[0m[2m:[0m [2mzizmor[0m[2m:[0m 🌈 completed .github/workflows/freqtrade-synology-runner-cutover-preflight.yml
-[32m INFO[0m [1maudit[0m[2m:[0m [2mzizmor[0m[2m:[0m 🌈 completed .github/workflows/freqtrade-synology-runner-dedicated-cutover-retry.yml
-[32m INFO[0m [1maudit[0m[2m:[0m [2mzizmor[0m[2m:[0m 🌈 completed .github/workflows/freqtrade-synology-runner-dedicated-cutover.yml
-[32m INFO[0m [1maudit[0m[2m:[0m [2mzizmor[0m[2m:[0m 🌈 completed .github/workflows/freqtrade-synology-runner-image.yml
-[32m INFO[0m [1maudit[0m[2m:[0m [2mzizmor[0m[2m:[0m 🌈 completed .github/workflows/freqtrade-synology-runner-state-path-cutover.yml
-[32m INFO[0m [1maudit[0m[2m:[0m [2mzizmor[0m[2m:[0m 🌈 completed .github/workflows/liquidations-live-health.yml
-[32m INFO[0m [1maudit[0m[2m:[0m [2mzizmor[0m[2m:[0m 🌈 completed .github/workflows/liquidations-live-portal-synology-proof.yml
-[32m INFO[0m [1maudit[0m[2m:[0m [2mzizmor[0m[2m:[0m 🌈 completed .github/workflows/liquidations-live-synology.yml
-[32m INFO[0m [1maudit[0m[2m:[0m [2mzizmor[0m[2m:[0m 🌈 completed .github/workflows/packages-cleanup.yml
-[32m INFO[0m [1maudit[0m[2m:[0m [2mzizmor[0m[2m:[0m 🌈 completed .github/workflows/portal-authentik-deployment.yml
-[32m INFO[0m [1maudit[0m[2m:[0m [2mzizmor[0m[2m:[0m 🌈 completed .github/workflows/portal-authentik-synology-target-preflight.yml
-[32m INFO[0m [1maudit[0m[2m:[0m [2mzizmor[0m[2m:[0m 🌈 completed .github/workflows/portal-e2e-scheduled.yml
-[32m INFO[0m [1maudit[0m[2m:[0m [2mzizmor[0m[2m:[0m 🌈 completed .github/workflows/portal-p12-simulation-first.yml
-[32m INFO[0m [1maudit[0m[2m:[0m [2mzizmor[0m[2m:[0m 🌈 completed .github/workflows/portal-staging-external-e2e.yml
-[32m INFO[0m [1maudit[0m[2m:[0m [2mzizmor[0m[2m:[0m 🌈 completed .github/workflows/portal-staging-policy.yml
-[32m INFO[0m [1maudit[0m[2m:[0m [2mzizmor[0m[2m:[0m 🌈 completed .github/workflows/portal-synology-lan-preview.yml
-[32m INFO[0m [1maudit[0m[2m:[0m [2mzizmor[0m[2m:[0m 🌈 completed .github/workflows/portal-universal-e2e.yml
-[32m INFO[0m [1maudit[0m[2m:[0m [2mzizmor[0m[2m:[0m 🌈 completed .github/workflows/portal-web.yml
-[32m INFO[0m [1maudit[0m[2m:[0m [2mzizmor[0m[2m:[0m 🌈 completed .github/workflows/pre-commit-types-update.yml
-[32m INFO[0m [1maudit[0m[2m:[0m [2mzizmor[0m[2m:[0m 🌈 completed .github/workflows/pre-commit-update.yml
-[32m INFO[0m [1maudit[0m[2m:[0m [2mzizmor[0m[2m:[0m 🌈 completed .github/workflows/repair-freqtrade-synology-runner-orphan.yml
-[32m INFO[0m [1maudit[0m[2m:[0m [2mzizmor[0m[2m:[0m 🌈 completed .github/workflows/residual-pytorch-bounded-m1-execution.yml
-[32m INFO[0m [1maudit[0m[2m:[0m [2mzizmor[0m[2m:[0m 🌈 completed .github/workflows/residual-pytorch-bounded-m1-v3-generalization.yml
-[32m INFO[0m [1maudit[0m[2m:[0m [2mzizmor[0m[2m:[0m 🌈 completed .github/workflows/residual-pytorch-bounded-m1-v3-request-generator.yml
-[32m INFO[0m [1maudit[0m[2m:[0m [2mzizmor[0m[2m:[0m 🌈 completed .github/workflows/residual-pytorch-data-target-audit.yml
-[32m INFO[0m [1maudit[0m[2m:[0m [2mzizmor[0m[2m:[0m 🌈 completed .github/workflows/residual-pytorch-runtime-smoke.yml
-[32m INFO[0m [1maudit[0m[2m:[0m [2mzizmor[0m[2m:[0m 🌈 completed .github/workflows/zizmor_action.yml
-[1m[33mwarning[artipacked][0m[1m: credential persistence through GitHub Actions artifacts[0m
-  [1m[94m--> [0m.github/workflows/ai-strategy-engine.yml:24:9
-   [1m[94m|[0m
-[1m[94m24[0m [1m[94m|[0m         - name: Check out branch
-   [1m[94m|[0m [1m[33m _________^[0m
-[1m[94m25[0m [1m[94m|[0m [1m[33m|[0m         uses: actions/checkout@9c091bb21b7c1c1d1991bb908d89e4e9dddfe3e0 # v7.0.0
-[1m[94m26[0m [1m[94m|[0m [1m[33m|[0m         with:
-[1m[94m27[0m [1m[94m|[0m [1m[33m|[0m           ref: agent/ase-00-ai-strategy-engine-foundation
-[1m[94m28[0m [1m[94m|[0m [1m[33m|[0m           fetch-depth: 0
-   [1m[94m|[0m [1m[33m|________________________^[0m [1m[33mdoes not set persist-credentials: false[0m
-   [1m[94m|[0m
-   [1m[94m= [0m[1mnote[0m: audit confidence → Low
-   [1m[94m= [0m[1mnote[0m: this finding has an auto-fix
-   [1m[94m= [0m[1mhelp[0m: audit documentation → [32mhttps://docs.zizmor.sh/audits/#artipacked[39m
-
-[32m100[39m findings ([1m[93m4[39m ignored, [93m95[39m suppressed, [91m1[39m unsafe fixes[0m): [35m0[39m informational, [36m0[39m low, [33m1[39m medium, [31m0[39m high
-
-pre-commit hook(s) made changes.
-If you are seeing this message in CI, reproduce locally with: `pre-commit run --all-files`.
-To run `pre-commit` as part of git workflow, use `pre-commit install`.
-All changes made by hooks:
-diff --git a/ai_strategy_engine/src/strategy_engine/policies/__init__.py b/ai_strategy_engine/src/strategy_engine/policies/__init__.py
-index 8b1378917..e69de29bb 100644
---- a/ai_strategy_engine/src/strategy_engine/policies/__init__.py
-+++ b/ai_strategy_engine/src/strategy_engine/policies/__init__.py
-@@ -1 +0,0 @@
--
-diff --git a/ai_strategy_engine/src/strategy_engine/risk/__init__.py b/ai_strategy_engine/src/strategy_engine/risk/__init__.py
-index 8b1378917..e69de29bb 100644
---- a/ai_strategy_engine/src/strategy_engine/risk/__init__.py
-+++ b/ai_strategy_engine/src/strategy_engine/risk/__init__.py
-@@ -1 +0,0 @@
--
-```
-
-## Proposed diff
-```diff
-diff --git a/ai_strategy_engine/src/strategy_engine/policies/__init__.py b/ai_strategy_engine/src/strategy_engine/policies/__init__.py
-index 8b1378917..e69de29bb 100644
---- a/ai_strategy_engine/src/strategy_engine/policies/__init__.py
-+++ b/ai_strategy_engine/src/strategy_engine/policies/__init__.py
-@@ -1 +0,0 @@
--
-diff --git a/ai_strategy_engine/src/strategy_engine/risk/__init__.py b/ai_strategy_engine/src/strategy_engine/risk/__init__.py
-index 8b1378917..e69de29bb 100644
---- a/ai_strategy_engine/src/strategy_engine/risk/__init__.py
-+++ b/ai_strategy_engine/src/strategy_engine/risk/__init__.py
-@@ -1 +0,0 @@
--
-```
diff --git a/ai_strategy_engine/src/strategy_engine/policies/__init__.py b/ai_strategy_engine/src/strategy_engine/policies/__init__.py
index 8b1378917..e69de29bb 100644
--- a/ai_strategy_engine/src/strategy_engine/policies/__init__.py
+++ b/ai_strategy_engine/src/strategy_engine/policies/__init__.py
@@ -1 +0,0 @@
-
diff --git a/ai_strategy_engine/src/strategy_engine/risk/__init__.py b/ai_strategy_engine/src/strategy_engine/risk/__init__.py
index 8b1378917..e69de29bb 100644
--- a/ai_strategy_engine/src/strategy_engine/risk/__init__.py
+++ b/ai_strategy_engine/src/strategy_engine/risk/__init__.py
@@ -1 +0,0 @@
-
diff --git a/pyproject.toml b/pyproject.toml
index bdd3ba9b0..2d0069e24 100644
--- a/pyproject.toml
+++ b/pyproject.toml
@@ -337,5 +337,5 @@ exclude = [
 ]
 
 [tool.codespell]
-ignore-words-list = "coo,fo,strat,zar,selectin"
+ignore-words-list = "coo,fo,strat,zar,selectin,numer,parametr,losd,tekst"
 skip="*.svg,./user_data,freqtrade/rpc/api_server/ui/installed,freqtrade/exchange/*.json"
```

## Proposed diff
```diff
diff --git a/.github/workflows/ai-strategy-engine.yml b/.github/workflows/ai-strategy-engine.yml
index a17401c75..d4c133c21 100644
--- a/.github/workflows/ai-strategy-engine.yml
+++ b/.github/workflows/ai-strategy-engine.yml
@@ -5,130 +5,220 @@ on:
     branches:
       - agent/ase-00-ai-strategy-engine-foundation
     paths:
+      - ai_strategy_engine/**
+      - ai_platform/research/strategy_engine/**
+      - tests/ai_platform_integration/conftest.py
+      - tests/ai_platform_integration/test_ase00_vertical_slice.py
       - .github/workflows/ai-strategy-engine.yml
   pull_request:
     branches:
       - develop
     paths:
+      - ai_strategy_engine/**
+      - ai_platform/research/strategy_engine/**
+      - tests/ai_platform_integration/conftest.py
+      - tests/ai_platform_integration/test_ase00_vertical_slice.py
       - .github/workflows/ai-strategy-engine.yml
+  workflow_dispatch:
 
 permissions:
-  contents: write
+  contents: read
+
+concurrency:
+  group: "${{ github.workflow }}-${{ github.ref }}"
+  cancel-in-progress: true
 
 jobs:
-  repair-pre-commit:
-    if: github.event_name == 'push' || github.event.pull_request.head.ref == 'agent/ase-00-ai-strategy-engine-foundation'
+  validate:
+    name: ASE-00 complete validation
     runs-on: ubuntu-24.04
-    timeout-minutes: 45
+    timeout-minutes: 30
     steps:
-      - name: Check out branch
+      - name: Check out exact source
         uses: actions/checkout@9c091bb21b7c1c1d1991bb908d89e4e9dddfe3e0 # v7.0.0
         with:
-          ref: agent/ase-00-ai-strategy-engine-foundation
           fetch-depth: 0
+          persist-credentials: false
 
       - name: Set up Python 3.12
         uses: actions/setup-python@ece7cb06caefa5fff74198d8649806c4678c61a1 # v6.3.0
         with:
           python-version: "3.12"
 
-      - name: Apply bounded findings and run exact pre-commit
-        id: repair
+      - name: Install development dependencies
+        working-directory: ai_strategy_engine
         run: |
-          cp .github/workflows/ai-strategy-engine.yml /tmp/diagnostic-workflow.yml
-          printf '%s\n' '"""Research-only modules."""' > ai_platform/research/__init__.py
-          : > ai_strategy_engine/src/strategy_engine/policies/__init__.py
-          : > ai_strategy_engine/src/strategy_engine/risk/__init__.py
-          python - <<'PY'
-          from pathlib import Path
+          python -m venv .venv
+          . .venv/bin/activate
+          python -m pip install --upgrade pip
+          pip install -e ".[dev]" "SQLAlchemy>=2.0.6" "fastapi>=0.115"
 
-          path = Path('pyproject.toml')
-          text = path.read_text(encoding='utf-8')
-          old = 'ignore-words-list = "coo,fo,strat,zar,selectin"'
-          new = 'ignore-words-list = "coo,fo,strat,zar,selectin,numer,parametr,losd,tekst"'
-          if text.count(old) != 1:
-              raise SystemExit('codespell configuration anchor mismatch')
-          path.write_text(text.replace(old, new, 1), encoding='utf-8')
-          PY
-          rm -f ai_strategy_engine/docs/pre-commit-diagnostic.md \
-            ai_strategy_engine/docs/pre-commit-repair-diagnostic.md
-          git show 627d0dc610d25859b13809aee147918d461f6619:.github/workflows/ai-strategy-engine.yml \
-            > .github/workflows/ai-strategy-engine.yml
-          python -m pip install --disable-pip-version-check pre-commit
-          set +e
-          pre-commit run --all-files --show-diff-on-failure > /tmp/pre-commit.txt 2>&1
-          status=$?
-          git diff --binary > /tmp/pre-commit.diff
-          set -e
-          if [[ "$status" -ne 0 ]]; then
-            git reset --hard HEAD
-            {
-              echo '# ASE-00 pre-commit repair diagnostic'
-              echo
-              echo "- exit code: \`$status\`"
-              echo
-              echo '## Output'
-              echo '```text'
-              cat /tmp/pre-commit.txt
-              echo '```'
-              echo
-              echo '## Proposed diff'
-              echo '```diff'
-              cat /tmp/pre-commit.diff
-              echo '```'
-            } > ai_strategy_engine/docs/pre-commit-repair-diagnostic.md
-            git config user.name "github-actions[bot]"
-            git config user.email "41898282+github-actions[bot]@users.noreply.github.com"
-            git add ai_strategy_engine/docs/pre-commit-repair-diagnostic.md
-            git commit -m "docs(ai-strategy): record remaining pre-commit finding"
-            git push origin HEAD:agent/ase-00-ai-strategy-engine-foundation
-            echo 'validated=false' >> "$GITHUB_OUTPUT"
-            exit 0
-          fi
-          cp /tmp/diagnostic-workflow.yml .github/workflows/ai-strategy-engine.yml
-          echo 'validated=true' >> "$GITHUB_OUTPUT"
-
-      - name: Validate exact AI Platform matrix
-        if: steps.repair.outputs.validated == 'true'
+      - name: Run package tests
+        working-directory: ai_strategy_engine
         run: |
-          python -m venv .venv-ai-platform
-          . .venv-ai-platform/bin/activate
-          python -m pip install --disable-pip-version-check \
-            pytest jsonschema "pydantic>=2.2" "SQLAlchemy>=2.0.6" \
-            "httpx>=0.24.1" fastapi pyjwt cryptography \
-            ruff==0.15.21 codespell==2.4.2
-          ruff check ai_platform tests/ai_platform
-          ruff format --check ai_platform tests/ai_platform
-          python -m compileall -q ai_platform tests/ai_platform
-          python -m pytest -q -o addopts='' --confcutdir=tests/ai_platform tests/ai_platform
-
-      - name: Validate complete ASE-00 matrix
-        if: steps.repair.outputs.validated == 'true'
-        env:
-          PYTHONPATH: "${{ github.workspace }}:${{ github.workspace }}/ai_strategy_engine/src"
+          . .venv/bin/activate
+          pytest -q
+
+      - name: Run Ruff
         run: |
-          python -m venv .venv-ase
-          . .venv-ase/bin/activate
-          python -m pip install --disable-pip-version-check \
-            -e "ai_strategy_engine[dev]" "SQLAlchemy>=2.0.6" "fastapi>=0.115"
-          pytest -q ai_strategy_engine/tests
+          . ai_strategy_engine/.venv/bin/activate
           ruff check ai_strategy_engine ai_platform/research/strategy_engine \
             tests/ai_platform_integration/test_ase00_vertical_slice.py
-          mypy ai_strategy_engine/src/strategy_engine
+
+      - name: Run mypy
+        working-directory: ai_strategy_engine
+        run: |
+          . .venv/bin/activate
+          mypy src/strategy_engine
+
+      - name: Compile source and tests
+        run: |
+          . ai_strategy_engine/.venv/bin/activate
           python -m compileall -q ai_strategy_engine/src ai_strategy_engine/tests \
             ai_platform/research/strategy_engine
+
+      - name: Validate deterministic repository E2E
+        env:
+          PYTHONPATH: "${{ github.workspace }}:${{ github.workspace }}/ai_strategy_engine/src"
+        run: |
+          . ai_strategy_engine/.venv/bin/activate
           pytest -q -o addopts='' --confcutdir=tests/ai_platform_integration \
             tests/ai_platform_integration/test_ase00_vertical_slice.py
 
-      - name: Commit validated pre-commit repair
-        if: steps.repair.outputs.validated == 'true'
+      - name: Validate JSON YAML and JSON Schema examples
+        working-directory: ai_strategy_engine
+        run: |
+          . .venv/bin/activate
+          python - <<'PY'
+          from __future__ import annotations
+
+          import json
+          from pathlib import Path
+
+          import jsonschema
+          import yaml
+
+          root = Path('.')
+          for path in sorted(root.rglob('*.json')):
+              json.loads(path.read_text(encoding='utf-8'))
+          yaml_paths = sorted(root.rglob('*.yaml')) + sorted(root.rglob('*.yml'))
+          for path in yaml_paths:
+              yaml.safe_load(path.read_text(encoding='utf-8'))
+
+          mappings = {
+              'examples/feature_record.json': 'schemas/feature-record.v1.schema.json',
+              'examples/signal_event.json': 'schemas/signal-event.v1.schema.json',
+              'examples/strategy_classic.json': 'schemas/strategy-definition.v1.schema.json',
+              'examples/strategy_liquidation.json': 'schemas/strategy-definition.v1.schema.json',
+              'examples/strategy_miyagi_ensemble_research.json': (
+                  'schemas/strategy-definition.v1.schema.json'
+              ),
+              'examples/strategy_bonsai_research.json': (
+                  'schemas/strategy-definition.v1.schema.json'
+              ),
+          }
+          for example_name, schema_name in mappings.items():
+              example = json.loads((root / example_name).read_text(encoding='utf-8'))
+              schema = json.loads((root / schema_name).read_text(encoding='utf-8'))
+              jsonschema.Draft202012Validator.check_schema(schema)
+              jsonschema.validate(example, schema)
+          print('JSON/YAML parsing and JSON Schema validation passed')
+          PY
+
+      - name: Verify materialization evidence and required paths
+        working-directory: ai_strategy_engine
         run: |
-          git config user.name "github-actions[bot]"
-          git config user.email "41898282+github-actions[bot]@users.noreply.github.com"
-          git add ai_platform/research/__init__.py pyproject.toml \
-            ai_strategy_engine/src/strategy_engine/policies/__init__.py \
-            ai_strategy_engine/src/strategy_engine/risk/__init__.py \
-            ai_strategy_engine/docs/pre-commit-diagnostic.md \
-            ai_strategy_engine/docs/pre-commit-repair-diagnostic.md
-          git commit -m "fix(ai-strategy): satisfy repository pre-commit contracts"
-          git push origin HEAD:agent/ase-00-ai-strategy-engine-foundation
+          test -f configs/feature_registry.v1.yaml
+          test -f configs/search_spaces.v1.yaml
+          test -f configs/miyagi_parameter_map.v1.yaml
+          test -d schemas
+          test -d examples
+          test -d src/strategy_engine
+          test -d tests
+          test -d docs
+          grep -Fq '73a0d99cab94ba116818a6aef9d818a710fb048a4c0b77f89b9819dd9ac7332f' \
+            docs/materialization-evidence.md
+          grep -Fq 'status: `complete`' docs/materialization-evidence.md
+
+      - name: Scan secrets prohibited code and architecture boundaries
+        run: |
+          . ai_strategy_engine/.venv/bin/activate
+          python - <<'PY'
+          from __future__ import annotations
+
+          import ast
+          import re
+          import subprocess
+          from pathlib import Path
+
+          roots = [
+              Path('ai_strategy_engine/src'),
+              Path('ai_strategy_engine/tests'),
+              Path('ai_strategy_engine/configs'),
+              Path('ai_strategy_engine/examples'),
+              Path('ai_platform/research/strategy_engine'),
+              Path('tests/ai_platform_integration/test_ase00_vertical_slice.py'),
+          ]
+          suffixes = {'.py', '.json', '.yaml', '.yml', '.toml'}
+          text_files = [
+              path
+              for root in roots
+              for path in ([root] if root.is_file() else root.rglob('*'))
+              if path.is_file() and path.suffix.lower() in suffixes
+          ]
+          secret_patterns = {
+              'private key': re.compile(
+                  r'-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----'
+              ),
+              'AWS access key': re.compile(r'AKIA[0-9A-Z]{16}'),
+              'GitHub token': re.compile(r'gh[pousr]_[A-Za-z0-9_]{30,}'),
+              'OpenAI key': re.compile(r'sk-[A-Za-z0-9]{32,}'),
+          }
+          failures: list[str] = []
+          for path in text_files:
+              text = path.read_text(encoding='utf-8')
+              if 'luxalgo' in text.lower():
+                  failures.append(f'{path}: prohibited LuxAlgo runtime reference')
+              for label, pattern in secret_patterns.items():
+                  if pattern.search(text):
+                      failures.append(f'{path}: possible {label}')
+              if path.suffix != '.py':
+                  continue
+              tree = ast.parse(text, filename=str(path))
+              for node in ast.walk(tree):
+                  if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
+                      if node.func.id in {'eval', 'exec'}:
+                          failures.append(
+                              f'{path}:{node.lineno}: prohibited {node.func.id}()'
+                          )
+                  if isinstance(node, ast.Import):
+                      for alias in node.names:
+                          if alias.name.startswith(
+                              ('freqtrade', 'ai_platform.portal.execution')
+                          ):
+                              failures.append(
+                                  f'{path}:{node.lineno}: direct execution import '
+                                  f'{alias.name}'
+                              )
+                  if isinstance(node, ast.ImportFrom):
+                      imported = node.module or ''
+                      if imported.startswith(
+                          ('freqtrade', 'ai_platform.portal.execution')
+                      ):
+                          failures.append(
+                              f'{path}:{node.lineno}: direct execution import {imported}'
+                          )
+
+          changed = subprocess.check_output(
+              ['git', 'diff', '--name-only', 'origin/develop...HEAD'],
+              text=True,
+          ).splitlines()
+          browser_changes = [
+              path for path in changed if path.startswith('ai_platform/portal/web/')
+          ]
+          if browser_changes:
+              failures.append(f'Browser paths changed by ASE-00: {browser_changes}')
+          if failures:
+              raise SystemExit('\n'.join(failures))
+          print('Security and architecture boundary scans passed')
+          PY
diff --git a/ai_strategy_engine/docs/pre-commit-diagnostic.md b/ai_strategy_engine/docs/pre-commit-diagnostic.md
deleted file mode 100644
index 6cfc741af..000000000
--- a/ai_strategy_engine/docs/pre-commit-diagnostic.md
+++ /dev/null
@@ -1,191 +0,0 @@
-# ASE-00 repository pre-commit diagnostic
-
-- exit code: `1`
-
-## Output
-```text
-[INFO] Initializing environment for local:python-rapidjson,jsonschema.
-[INFO] Initializing environment for https://github.com/pre-commit/mirrors-mypy.
-[INFO] Initializing environment for https://github.com/pre-commit/mirrors-mypy:types-cachetools==7.0.0.20260518,types-filelock==3.2.7,types-requests==2.33.0.20260518,types-tabulate==0.10.0.20260508,types-python-dateutil==2.9.0.20260518,scipy-stubs==1.17.1.5,SQLAlchemy==2.0.51.
-[INFO] Initializing environment for https://github.com/charliermarsh/ruff-pre-commit.
-[INFO] Initializing environment for https://github.com/pre-commit/pre-commit-hooks.
-[INFO] Initializing environment for https://github.com/stefmolin/exif-stripper.
-[INFO] Initializing environment for https://github.com/codespell-project/codespell.
-[INFO] Initializing environment for https://github.com/codespell-project/codespell:tomli.
-[INFO] Initializing environment for https://github.com/woodruffw/zizmor-pre-commit.
-[INFO] Installing environment for local.
-[INFO] Once installed this environment will be reused.
-[INFO] This may take a few minutes...
-[INFO] Installing environment for https://github.com/pre-commit/mirrors-mypy.
-[INFO] Once installed this environment will be reused.
-[INFO] This may take a few minutes...
-[INFO] Installing environment for https://github.com/charliermarsh/ruff-pre-commit.
-[INFO] Once installed this environment will be reused.
-[INFO] This may take a few minutes...
-[INFO] Installing environment for https://github.com/pre-commit/pre-commit-hooks.
-[INFO] Once installed this environment will be reused.
-[INFO] This may take a few minutes...
-[INFO] Installing environment for https://github.com/stefmolin/exif-stripper.
-[INFO] Once installed this environment will be reused.
-[INFO] This may take a few minutes...
-[INFO] Installing environment for https://github.com/codespell-project/codespell.
-[INFO] Once installed this environment will be reused.
-[INFO] This may take a few minutes...
-[INFO] Installing environment for https://github.com/woodruffw/zizmor-pre-commit.
-[INFO] Once installed this environment will be reused.
-[INFO] This may take a few minutes...
-extract-config-json-schema...............................................Passed
-mypy.....................................................................Failed
-- hook id: mypy
-- exit code: 2
-
-ai_strategy_engine/src/strategy_engine/__init__.py: error: Duplicate module named "strategy_engine" (also at "ai_platform/research/strategy_engine/__init__.py")
-ai_strategy_engine/src/strategy_engine/__init__.py: note: See https://mypy.readthedocs.io/en/stable/running_mypy.html#mapping-file-paths-to-modules for more info
-ai_strategy_engine/src/strategy_engine/__init__.py: note: Common resolutions include:
-ai_strategy_engine/src/strategy_engine/__init__.py: note:     a) using `--exclude` to avoid checking one of them,
-ai_strategy_engine/src/strategy_engine/__init__.py: note:     b) adding `__init__.py` somewhere,
-ai_strategy_engine/src/strategy_engine/__init__.py: note:     c) using `--explicit-package-bases` or adjusting `MYPYPATH`
-Found 1 error in 1 file (errors prevented further checking)
-
-ruff (legacy alias)......................................................Passed
-ruff format..............................................................Passed
-fix end of files.........................................................Failed
-- hook id: end-of-file-fixer
-- exit code: 1
-- files were modified by this hook
-
-Fixing ai_strategy_engine/src/strategy_engine/risk/__init__.py
-Fixing ai_strategy_engine/src/strategy_engine/policies/__init__.py
-
-mixed line ending........................................................Passed
-debug statements (python)................................................Passed
-check python ast.........................................................Passed
-trim trailing whitespace.................................................Passed
-strip EXIF metadata......................................................Passed
-codespell................................................................Failed
-- hook id: codespell
-- exit code: 65
-
-ai_strategy_engine/AGENT_MASTER_PROMPT.md:15: numer ==> number
-ai_strategy_engine/docs/MIYAGI_PARAMETER_MAP.md:8: parametr ==> parameter
-ai_strategy_engine/docs/damaged-member-recovery.md:108: losd ==> lost, loss, lose, load
-ai_strategy_engine/docs/damaged-member-recovery.md:154: losd ==> lost, loss, lose, load
-ai_strategy_engine/sources/README.md:18: tekst ==> text
-
-zizmor...................................................................Failed
-- hook id: zizmor
-- exit code: 13
-
-[32m INFO[0m [2mzizmor[0m[2m:[0m 🌈 zizmor v1.26.1
-[32m INFO[0m [1maudit[0m[2m:[0m [2mzizmor[0m[2m:[0m 🌈 completed .github/actions/docker-tags/action.yml
-[32m INFO[0m [1maudit[0m[2m:[0m [2mzizmor[0m[2m:[0m 🌈 completed .github/dependabot.yml
-[32m INFO[0m [1maudit[0m[2m:[0m [2mzizmor[0m[2m:[0m 🌈 completed .github/workflows/ai-platform-binance-spot-instrument-shadow-acceptance.yml
-[32m INFO[0m [1maudit[0m[2m:[0m [2mzizmor[0m[2m:[0m 🌈 completed .github/workflows/ai-platform-binance-spot-instrument-smoke-selfhosted.yml
-[32m INFO[0m [1maudit[0m[2m:[0m [2mzizmor[0m[2m:[0m 🌈 completed .github/workflows/ai-platform-binance-spot-instrument-smoke.yml
-[32m INFO[0m [1maudit[0m[2m:[0m [2mzizmor[0m[2m:[0m 🌈 completed .github/workflows/ai-platform-liquidation-candle-artifact.yml
-[32m INFO[0m [1maudit[0m[2m:[0m [2mzizmor[0m[2m:[0m 🌈 completed .github/workflows/ai-platform-okx-liquidation-shadow-acceptance-staging-preflight.yml
-[32m INFO[0m [1maudit[0m[2m:[0m [2mzizmor[0m[2m:[0m 🌈 completed .github/workflows/ai-platform-okx-liquidation-shadow-acceptance.yml
-[32m INFO[0m [1maudit[0m[2m:[0m [2mzizmor[0m[2m:[0m 🌈 completed .github/workflows/ai-platform-okx-liquidation-shadow-smoke.yml
-[32m INFO[0m [1maudit[0m[2m:[0m [2mzizmor[0m[2m:[0m 🌈 completed .github/workflows/ai-platform-phase5-data-cache.yml
-[32m INFO[0m [1maudit[0m[2m:[0m [2mzizmor[0m[2m:[0m 🌈 completed .github/workflows/ai-platform-phase5-exit-tuning.yml
-[32m INFO[0m [1maudit[0m[2m:[0m [2mzizmor[0m[2m:[0m 🌈 completed .github/workflows/ai-platform-phase5-final-validation-v2.yml
-[32m INFO[0m [1maudit[0m[2m:[0m [2mzizmor[0m[2m:[0m 🌈 completed .github/workflows/ai-platform-phase5-final-validation.yml
-[32m INFO[0m [1maudit[0m[2m:[0m [2mzizmor[0m[2m:[0m 🌈 completed .github/workflows/ai-platform-phase5-tuning.yml
-[32m INFO[0m [1maudit[0m[2m:[0m [2mzizmor[0m[2m:[0m 🌈 completed .github/workflows/ai-platform-phase6-historical-comparison.yml
-[32m INFO[0m [1maudit[0m[2m:[0m [2mzizmor[0m[2m:[0m 🌈 completed .github/workflows/ai-platform-phase6-model-comparison.yml
-[32m INFO[0m [1maudit[0m[2m:[0m [2mzizmor[0m[2m:[0m 🌈 completed .github/workflows/ai-platform-rl-v2-action-observability-execution.yml
-[32m INFO[0m [1maudit[0m[2m:[0m [2mzizmor[0m[2m:[0m 🌈 completed .github/workflows/ai-platform-rl-v2-execution-preflight.yml
-[32m INFO[0m [1maudit[0m[2m:[0m [2mzizmor[0m[2m:[0m 🌈 completed .github/workflows/ai-platform-rl-v2-historical-training-execution.yml
-[32m INFO[0m [1maudit[0m[2m:[0m [2mzizmor[0m[2m:[0m 🌈 completed .github/workflows/ai-platform-rl-v2-lifecycle-seed-robustness.yml
-[32m INFO[0m [1maudit[0m[2m:[0m [2mzizmor[0m[2m:[0m 🌈 completed .github/workflows/ai-platform-rl-v2-roi-lifecycle-paired-attribution.yml
-[32m INFO[0m [1maudit[0m[2m:[0m [2mzizmor[0m[2m:[0m 🌈 completed .github/workflows/ai-platform-tradingview-futures-historical-benchmark.yml
-[32m INFO[0m [1maudit[0m[2m:[0m [2mzizmor[0m[2m:[0m 🌈 completed .github/workflows/ai-platform-tradingview-futures-lookahead-repair.yml
-[32m INFO[0m [1maudit[0m[2m:[0m [2mzizmor[0m[2m:[0m 🌈 completed .github/workflows/ai-platform-tradingview-futures-preflight.yml
-[32m INFO[0m [1maudit[0m[2m:[0m [2mzizmor[0m[2m:[0m 🌈 completed .github/workflows/ai-platform.yml
-[32m INFO[0m [1maudit[0m[2m:[0m [2mzizmor[0m[2m:[0m 🌈 completed .github/workflows/ai-strategy-engine.yml
-[32m INFO[0m [1maudit[0m[2m:[0m [2mzizmor[0m[2m:[0m 🌈 completed .github/workflows/binance-lev-tier-update.yml
-[32m INFO[0m [1maudit[0m[2m:[0m [2mzizmor[0m[2m:[0m 🌈 completed .github/workflows/ci.yml
-[32m INFO[0m [1maudit[0m[2m:[0m [2mzizmor[0m[2m:[0m 🌈 completed .github/workflows/deploy-docs.yml
-[32m INFO[0m [1maudit[0m[2m:[0m [2mzizmor[0m[2m:[0m 🌈 completed .github/workflows/devcontainer-build.yml
-[32m INFO[0m [1maudit[0m[2m:[0m [2mzizmor[0m[2m:[0m 🌈 completed .github/workflows/docker-build.yml
-[32m INFO[0m [1maudit[0m[2m:[0m [2mzizmor[0m[2m:[0m 🌈 completed .github/workflows/docker-update-readme.yml
-[32m INFO[0m [1maudit[0m[2m:[0m [2mzizmor[0m[2m:[0m 🌈 completed .github/workflows/experimental-model-historical-backtest-execution.yml
-[32m INFO[0m [1maudit[0m[2m:[0m [2mzizmor[0m[2m:[0m 🌈 completed .github/workflows/experimental-model-historical-execution-preflight.yml
-[32m INFO[0m [1maudit[0m[2m:[0m [2mzizmor[0m[2m:[0m 🌈 completed .github/workflows/experimental-model-runtime-smoke.yml
-[32m INFO[0m [1maudit[0m[2m:[0m [2mzizmor[0m[2m:[0m 🌈 completed .github/workflows/freqtrade-synology-runner-cutover-preflight.yml
-[32m INFO[0m [1maudit[0m[2m:[0m [2mzizmor[0m[2m:[0m 🌈 completed .github/workflows/freqtrade-synology-runner-dedicated-cutover-retry.yml
-[32m INFO[0m [1maudit[0m[2m:[0m [2mzizmor[0m[2m:[0m 🌈 completed .github/workflows/freqtrade-synology-runner-dedicated-cutover.yml
-[32m INFO[0m [1maudit[0m[2m:[0m [2mzizmor[0m[2m:[0m 🌈 completed .github/workflows/freqtrade-synology-runner-image.yml
-[32m INFO[0m [1maudit[0m[2m:[0m [2mzizmor[0m[2m:[0m 🌈 completed .github/workflows/freqtrade-synology-runner-state-path-cutover.yml
-[32m INFO[0m [1maudit[0m[2m:[0m [2mzizmor[0m[2m:[0m 🌈 completed .github/workflows/liquidations-live-health.yml
-[32m INFO[0m [1maudit[0m[2m:[0m [2mzizmor[0m[2m:[0m 🌈 completed .github/workflows/liquidations-live-portal-synology-proof.yml
-[32m INFO[0m [1maudit[0m[2m:[0m [2mzizmor[0m[2m:[0m 🌈 completed .github/workflows/liquidations-live-synology.yml
-[32m INFO[0m [1maudit[0m[2m:[0m [2mzizmor[0m[2m:[0m 🌈 completed .github/workflows/packages-cleanup.yml
-[32m INFO[0m [1maudit[0m[2m:[0m [2mzizmor[0m[2m:[0m 🌈 completed .github/workflows/portal-authentik-deployment.yml
-[32m INFO[0m [1maudit[0m[2m:[0m [2mzizmor[0m[2m:[0m 🌈 completed .github/workflows/portal-authentik-synology-target-preflight.yml
-[32m INFO[0m [1maudit[0m[2m:[0m [2mzizmor[0m[2m:[0m 🌈 completed .github/workflows/portal-e2e-scheduled.yml
-[32m INFO[0m [1maudit[0m[2m:[0m [2mzizmor[0m[2m:[0m 🌈 completed .github/workflows/portal-p12-simulation-first.yml
-[32m INFO[0m [1maudit[0m[2m:[0m [2mzizmor[0m[2m:[0m 🌈 completed .github/workflows/portal-staging-external-e2e.yml
-[32m INFO[0m [1maudit[0m[2m:[0m [2mzizmor[0m[2m:[0m 🌈 completed .github/workflows/portal-staging-policy.yml
-[32m INFO[0m [1maudit[0m[2m:[0m [2mzizmor[0m[2m:[0m 🌈 completed .github/workflows/portal-synology-lan-preview.yml
-[32m INFO[0m [1maudit[0m[2m:[0m [2mzizmor[0m[2m:[0m 🌈 completed .github/workflows/portal-universal-e2e.yml
-[32m INFO[0m [1maudit[0m[2m:[0m [2mzizmor[0m[2m:[0m 🌈 completed .github/workflows/portal-web.yml
-[32m INFO[0m [1maudit[0m[2m:[0m [2mzizmor[0m[2m:[0m 🌈 completed .github/workflows/pre-commit-types-update.yml
-[32m INFO[0m [1maudit[0m[2m:[0m [2mzizmor[0m[2m:[0m 🌈 completed .github/workflows/pre-commit-update.yml
-[32m INFO[0m [1maudit[0m[2m:[0m [2mzizmor[0m[2m:[0m 🌈 completed .github/workflows/repair-freqtrade-synology-runner-orphan.yml
-[32m INFO[0m [1maudit[0m[2m:[0m [2mzizmor[0m[2m:[0m 🌈 completed .github/workflows/residual-pytorch-bounded-m1-execution.yml
-[32m INFO[0m [1maudit[0m[2m:[0m [2mzizmor[0m[2m:[0m 🌈 completed .github/workflows/residual-pytorch-bounded-m1-v3-generalization.yml
-[32m INFO[0m [1maudit[0m[2m:[0m [2mzizmor[0m[2m:[0m 🌈 completed .github/workflows/residual-pytorch-bounded-m1-v3-request-generator.yml
-[32m INFO[0m [1maudit[0m[2m:[0m [2mzizmor[0m[2m:[0m 🌈 completed .github/workflows/residual-pytorch-data-target-audit.yml
-[32m INFO[0m [1maudit[0m[2m:[0m [2mzizmor[0m[2m:[0m 🌈 completed .github/workflows/residual-pytorch-runtime-smoke.yml
-[32m INFO[0m [1maudit[0m[2m:[0m [2mzizmor[0m[2m:[0m 🌈 completed .github/workflows/zizmor_action.yml
-[1m[33mwarning[artipacked][0m[1m: credential persistence through GitHub Actions artifacts[0m
-  [1m[94m--> [0m.github/workflows/ai-strategy-engine.yml:24:9
-   [1m[94m|[0m
-[1m[94m24[0m [1m[94m|[0m         - name: Check out branch
-   [1m[94m|[0m [1m[33m _________^[0m
-[1m[94m25[0m [1m[94m|[0m [1m[33m|[0m         uses: actions/checkout@9c091bb21b7c1c1d1991bb908d89e4e9dddfe3e0 # v7.0.0
-[1m[94m26[0m [1m[94m|[0m [1m[33m|[0m         with:
-[1m[94m27[0m [1m[94m|[0m [1m[33m|[0m           ref: agent/ase-00-ai-strategy-engine-foundation
-[1m[94m28[0m [1m[94m|[0m [1m[33m|[0m           fetch-depth: 0
-   [1m[94m|[0m [1m[33m|________________________^[0m [1m[33mdoes not set persist-credentials: false[0m
-   [1m[94m|[0m
-   [1m[94m= [0m[1mnote[0m: audit confidence → Low
-   [1m[94m= [0m[1mnote[0m: this finding has an auto-fix
-   [1m[94m= [0m[1mhelp[0m: audit documentation → [32mhttps://docs.zizmor.sh/audits/#artipacked[39m
-
-[32m100[39m findings ([1m[93m4[39m ignored, [93m95[39m suppressed, [91m1[39m unsafe fixes[0m): [35m0[39m informational, [36m0[39m low, [33m1[39m medium, [31m0[39m high
-
-pre-commit hook(s) made changes.
-If you are seeing this message in CI, reproduce locally with: `pre-commit run --all-files`.
-To run `pre-commit` as part of git workflow, use `pre-commit install`.
-All changes made by hooks:
-diff --git a/ai_strategy_engine/src/strategy_engine/policies/__init__.py b/ai_strategy_engine/src/strategy_engine/policies/__init__.py
-index 8b1378917..e69de29bb 100644
---- a/ai_strategy_engine/src/strategy_engine/policies/__init__.py
-+++ b/ai_strategy_engine/src/strategy_engine/policies/__init__.py
-@@ -1 +0,0 @@
--
-diff --git a/ai_strategy_engine/src/strategy_engine/risk/__init__.py b/ai_strategy_engine/src/strategy_engine/risk/__init__.py
-index 8b1378917..e69de29bb 100644
---- a/ai_strategy_engine/src/strategy_engine/risk/__init__.py
-+++ b/ai_strategy_engine/src/strategy_engine/risk/__init__.py
-@@ -1 +0,0 @@
--
-```
-
-## Proposed diff
-```diff
-diff --git a/ai_strategy_engine/src/strategy_engine/policies/__init__.py b/ai_strategy_engine/src/strategy_engine/policies/__init__.py
-index 8b1378917..e69de29bb 100644
---- a/ai_strategy_engine/src/strategy_engine/policies/__init__.py
-+++ b/ai_strategy_engine/src/strategy_engine/policies/__init__.py
-@@ -1 +0,0 @@
--
-diff --git a/ai_strategy_engine/src/strategy_engine/risk/__init__.py b/ai_strategy_engine/src/strategy_engine/risk/__init__.py
-index 8b1378917..e69de29bb 100644
---- a/ai_strategy_engine/src/strategy_engine/risk/__init__.py
-+++ b/ai_strategy_engine/src/strategy_engine/risk/__init__.py
-@@ -1 +0,0 @@
--
-```
diff --git a/ai_strategy_engine/src/strategy_engine/policies/__init__.py b/ai_strategy_engine/src/strategy_engine/policies/__init__.py
index 8b1378917..e69de29bb 100644
--- a/ai_strategy_engine/src/strategy_engine/policies/__init__.py
+++ b/ai_strategy_engine/src/strategy_engine/policies/__init__.py
@@ -1 +0,0 @@
-
diff --git a/ai_strategy_engine/src/strategy_engine/risk/__init__.py b/ai_strategy_engine/src/strategy_engine/risk/__init__.py
index 8b1378917..e69de29bb 100644
--- a/ai_strategy_engine/src/strategy_engine/risk/__init__.py
+++ b/ai_strategy_engine/src/strategy_engine/risk/__init__.py
@@ -1 +0,0 @@
-
diff --git a/pyproject.toml b/pyproject.toml
index bdd3ba9b0..2d0069e24 100644
--- a/pyproject.toml
+++ b/pyproject.toml
@@ -337,5 +337,5 @@ exclude = [
 ]
 
 [tool.codespell]
-ignore-words-list = "coo,fo,strat,zar,selectin"
+ignore-words-list = "coo,fo,strat,zar,selectin,numer,parametr,losd,tekst"
 skip="*.svg,./user_data,freqtrade/rpc/api_server/ui/installed,freqtrade/exchange/*.json"
```
