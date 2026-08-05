from pathlib import Path


def _core_light_block() -> str:
    workflow = Path(".github/workflows/ci.yml").read_text(encoding="utf-8")
    start = workflow.index("  core-light:\n")
    end = workflow.index("\n  pre-commit:\n", start)
    return workflow[start:end]


def test_parallel_focused_core_validation_installs_xdist() -> None:
    block = _core_light_block()
    assert "pytest-xdist==3.8.0" in block
    assert "pytest -q --durations 20 -n auto" in block
