from pathlib import Path

path = Path("tests/ai_platform/portal/execution/test_driver.py")
text = path.read_text(encoding="utf-8")
old = '''        timeout = kwargs.get("timeout")
        observed["timeout"] = timeout if isinstance(timeout, float) else None
        raise subprocess.TimeoutExpired(cmd=["docker", "info"], timeout=float(timeout))
'''
new = '''        timeout = kwargs.get("timeout")
        if not isinstance(timeout, (int, float)):
            raise AssertionError("subprocess timeout must be numeric")
        observed["timeout"] = float(timeout)
        raise subprocess.TimeoutExpired(cmd=["docker", "info"], timeout=float(timeout))
'''
if text.count(old) != 1:
    raise SystemExit(f"expected exact mypy block once, got {text.count(old)}")
path.write_text(text.replace(old, new, 1), encoding="utf-8")
