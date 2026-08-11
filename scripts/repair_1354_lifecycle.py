from pathlib import Path


def replace_once(path: str, old: str, new: str) -> None:
    target = Path(path)
    text = target.read_text(encoding="utf-8")
    count = text.count(old)
    if count != 1:
        raise SystemExit(f"{path}: expected one replacement, found {count}")
    target.write_text(text.replace(old, new, 1), encoding="utf-8")


replace_once(
    "ARCHITECTURE_REGISTRY.yaml",
    '  lifecycle_reconciled_at: "2026-08-11"\n',
    '  lifecycle_reconciled_at: "2026-08-10"\n',
)
replace_once(
    "ARCHITECTURE_REGISTRY.yaml",
    '''    - issue: 1354\n      id: FTAI-ARCH-RUNTIME-ISOLATION\n      status: completed\n      evidence_pr: 1464\n''',
    "",
)
replace_once(
    "tests/ci/test_architecture_registry.py",
    '        (1354, "FTAI-ARCH-RUNTIME-ISOLATION"),\n',
    "",
)
