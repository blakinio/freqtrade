from __future__ import annotations

from pathlib import Path

source = Path("tools/agents/apply_1355_terminal_audit_findings.py")
exec(compile(source.read_text(encoding="utf-8"), str(source), "exec"), {"__name__": "__main__"})

path = Path("tests/ai_platform/portal/runtime_supervisor/test_transport.py")
text = path.read_text(encoding="utf-8")
if "import pytest\n" not in text:
    text = text.replace("from uuid import uuid4\n", "from uuid import uuid4\n\nimport pytest\n", 1)
text = text.replace(
    "tmp_path: Path, monkeypatch: object\n",
    "tmp_path: Path, monkeypatch: pytest.MonkeyPatch\n",
)
text = text.replace(
    'getattr(monkeypatch, "setattr")(server, "_validate_socket_root", lambda: socket.AF_UNIX)',
    'monkeypatch.setattr(server, "_validate_socket_root", lambda: socket.AF_UNIX)',
)
path.write_text(text, encoding="utf-8")
