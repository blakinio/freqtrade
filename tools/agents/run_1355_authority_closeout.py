from __future__ import annotations

from pathlib import Path

source_path = Path("tools/agents/apply_1355_authority_closeout.py")
source = source_path.read_text(encoding="utf-8")
start_marker = '''replace_method(
    "tests/ai_platform/portal/execution/test_adapter.py",
    "_adapter",
'''
end_marker = '''# replace_method expects indented methods, so repair the top-level helper directly if needed below.
'''
if source.count(start_marker) != 1 or source.count(end_marker) != 1:
    raise SystemExit("authority closeout adapter helper patch markers are not unique")
start = source.index(start_marker)
end = source.index(end_marker)
replacement = '''adapter_tests = Path("tests/ai_platform/portal/execution/test_adapter.py")
text = adapter_tests.read_text(encoding="utf-8")
helper_start = text.index("def _adapter(")
helper_end = text.index("\\ndef test_", helper_start)
helper = ''' + repr('''def _adapter(
    tmp_path: Path,
) -> tuple[ExecutionAdapter, _FakeSupervisor, _Resolver, RuntimeWorkspaceStore]:
    supervisor = _FakeSupervisor()
    resolver = _Resolver()
    resolver.register(_material())
    store = RuntimeWorkspaceStore(tmp_path)
    adapter = FreqtradeExecutionAdapter(supervisor, resolver, store, clock=lambda: NOW)
    protocol_adapter: ExecutionAdapter = adapter
    return protocol_adapter, supervisor, resolver, store
''') + '''
adapter_tests.write_text(text[:helper_start] + helper + text[helper_end + 1 :], encoding="utf-8")
'''
source = source[:start] + replacement + source[end:]
exec(compile(source, str(source_path), "exec"), {"__name__": "__main__"})
