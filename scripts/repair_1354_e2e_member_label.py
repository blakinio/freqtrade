from pathlib import Path

path = Path("tests/ai_platform/portal/execution/test_linux_isolation_backend_e2e.py")
text = path.read_text(encoding="utf-8")
old = '''            "--label",\n            f"ai.portal.runtime_id={runtime_id}",\n            "--dns",\n'''
new = '''            "--label",\n            f"ai.portal.runtime_id={runtime_id}",\n            "--label",\n            f"ai.portal.isolation_plan_digest={plan.digest()}",\n            "--dns",\n'''
if text.count(old) != 1:
    raise SystemExit(f"expected one manual E2E member label site, found {text.count(old)}")
path.write_text(text.replace(old, new, 1), encoding="utf-8")
