from __future__ import annotations

from pathlib import Path

source_path = Path("tools/agents/apply_1355_final_repair.py")
source = source_path.read_text(encoding="utf-8")
obsolete_blocks = [
    '''replace_once(
    "ai_platform/portal/runtime_supervisor/service.py",
    "            state=state,\\n"
    "            state_version=state_version,\\n"
    "            evidence_digest=digest,\\n",
    "            state=state,\\n"
    "            state_version=state_version,\\n"
    "            driver_reason_code=driver_reason_code,\\n"
    "            evidence_digest=digest,\\n",
)
''',
    '''replace_once(
    "tests/ai_platform/portal/runtime_supervisor/test_service.py",
    "            [\\\"inspect\\\"],\\n"
    "        ),\\n"
    "        (\\n"
    "            SupervisorOperation.ENSURE_STOPPED,\\n",
    "            [\\\"inspect\\\", \\\"start\\\"],\\n"
    "        ),\\n"
    "        (\\n"
    "            SupervisorOperation.ENSURE_STOPPED,\\n",
)
''',
]
for obsolete in obsolete_blocks:
    count = source.count(obsolete)
    if count != 1:
        raise SystemExit(f"expected obsolete replacement once, got {count}")
    source = source.replace(obsolete, "", 1)
exec(compile(source, str(source_path), "exec"), {"__name__": "__main__"})
