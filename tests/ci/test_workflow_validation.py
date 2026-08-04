from pathlib import Path

from tools.ci.validate_workflows import validate_repository


def test_repository_workflows_satisfy_routing_and_security_contract() -> None:
    assert validate_repository(Path()) == []
