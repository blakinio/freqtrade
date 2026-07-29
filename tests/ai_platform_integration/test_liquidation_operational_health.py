from __future__ import annotations

import json
import subprocess
from pathlib import Path

from ai_platform.scripts.liquidation_operational_health import inspect_container_data


DATA_ROOT = Path("/volume1/docker/freqtrade-liquidations/data")


def test_container_observation_uses_validated_production_data_mount(monkeypatch) -> None:
    pointer = {
        "contract": "liquidation-live-state-v1",
        "state": {"contract": "liquidation-live-state-v1", "run_state": "active"},
    }
    calls: list[list[str]] = []

    def fake_run(command: list[str], **kwargs) -> subprocess.CompletedProcess[str]:
        calls.append(command)
        if command[:2] == ["docker", "inspect"]:
            mounts = [
                {
                    "Type": "bind",
                    "Source": str(DATA_ROOT),
                    "Destination": "/data",
                    "RW": True,
                }
            ]
            return subprocess.CompletedProcess(command, 0, json.dumps(mounts), "")
        payload = {
            "pointer": pointer,
            "disk": {"total": 1_000, "used": 400, "free": 600},
        }
        assert command == ["docker", "exec", "--interactive", "liquid20-live", "python", "-"]
        assert 'Path("/data")' in kwargs["input"]
        return subprocess.CompletedProcess(command, 0, json.dumps(payload), "")

    monkeypatch.setattr(subprocess, "run", fake_run)

    observed_pointer, disk, error = inspect_container_data("liquid20-live", DATA_ROOT)

    assert error is None
    assert observed_pointer == pointer
    assert disk == {"total": 1_000, "used": 400, "free": 600}
    assert len(calls) == 2


def test_container_observation_fails_closed_on_untrusted_mount(monkeypatch) -> None:
    mounts = [
        {
            "Type": "bind",
            "Source": "/volume1/docker/other-data",
            "Destination": "/data",
            "RW": True,
        }
    ]

    def fake_run(command: list[str], **kwargs) -> subprocess.CompletedProcess[str]:
        return subprocess.CompletedProcess(command, 0, json.dumps(mounts), "")

    monkeypatch.setattr(subprocess, "run", fake_run)

    pointer, disk, error = inspect_container_data("liquid20-live", DATA_ROOT)

    assert pointer is None
    assert disk == {"total": 0, "used": 0, "free": 0}
    assert error is not None
    assert "trusted host root" in error
