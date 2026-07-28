from __future__ import annotations

import sys
from pathlib import Path


REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
STRATEGY_ENGINE_SRC = REPOSITORY_ROOT / "ai_strategy_engine" / "src"
if str(STRATEGY_ENGINE_SRC) not in sys.path:
    sys.path.insert(0, str(STRATEGY_ENGINE_SRC))
