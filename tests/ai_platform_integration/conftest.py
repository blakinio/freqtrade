from __future__ import annotations

import sys
from pathlib import Path


REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
STRATEGY_ENGINE_SRC = REPOSITORY_ROOT / "ai_strategy_engine" / "src"
for import_root in (REPOSITORY_ROOT, STRATEGY_ENGINE_SRC):
    import_path = str(import_root)
    if import_path not in sys.path:
        sys.path.insert(0, import_path)
