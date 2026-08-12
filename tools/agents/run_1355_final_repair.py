from __future__ import annotations

from pathlib import Path

source_path = Path("tools/agents/apply_1355_final_repair.py")
source = source_path.read_text(encoding="utf-8")
bad = '''replace_once(
    "ai_platform/portal/runtime_supervisor/service.py",
    "            state=state,\\n"
    "            state_version=state_version,\\n"
    "            evidence_digest=digest,\\n",
    "            state=state,\\n"
    "            state_version=state_version,\\n"
    "            driver_reason_code=driver_reason_code,\\n"
    "            evidence_digest=digest,\\n",
)
'''
if source.count(bad) != 1:
    raise SystemExit(f"expected obsolete outcome replacement once, got {source.count(bad)}")
source = source.replace(bad, "", 1)
exec(compile(source, str(source_path), "exec"), {"__name__": "__main__"})
