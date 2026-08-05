from pathlib import Path


def _core_light_block() -> str:
    workflow = Path(".github/workflows/ci.yml").read_text(encoding="utf-8")
    start = workflow.index("  core-light:\n")
    end = workflow.index("\n  pre-commit:\n", start)
    return workflow[start:end]


def test_parallel_focused_core_validation_installs_required_dependencies() -> None:
    block = _core_light_block()
    required_packages = (
        "pytest-xdist==3.8.0",
        "pyyaml==6.0.3",
        "plotly==6.8.0",
        "optuna==4.9.0",
        "datasieve==0.1.9",
        "pip-audit==2.10.1",
    )
    for package in required_packages:
        assert package in block
    assert "pytest -q --durations 20 -n auto" in block
