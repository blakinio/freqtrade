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

path = Path("tests/ai_platform/portal/execution/test_driver.py")
text = path.read_text(encoding="utf-8")
marker = "\ndef test_current_generation_evidence_is_process_local_and_exact"
if text.count(marker) != 1:
    raise SystemExit("expected appended generation-evidence test exactly once")
prefix, tail = text.split(marker, 1)
old = "        external_attestor=_Attestor(),\n    )\n"
new = "        external_attestor=_Attestor(),\n        gateway_attestor=_Attestor(),\n    )\n"
if tail.count(old) != 1:
    raise SystemExit(f"expected generation-evidence driver constructor once, got {tail.count(old)}")
tail = tail.replace(old, new, 1)
path.write_text(prefix + marker + tail, encoding="utf-8")
