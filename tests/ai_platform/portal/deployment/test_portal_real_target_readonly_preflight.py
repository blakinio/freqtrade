from __future__ import annotations

import importlib.util
from pathlib import Path


MODULE_PATH = (
    Path(__file__).parents[4]
    / "deploy"
    / "synology"
    / "portal"
    / "real_target_preflight.py"
)
SPEC = importlib.util.spec_from_file_location("portal_real_target_preflight", MODULE_PATH)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def test_bind_scope_is_sanitized() -> None:
    assert MODULE.bind_scope("127.0.0.1") == "loopback"
    assert MODULE.bind_scope("0.0.0.0") == "all_interfaces"
    assert MODULE.bind_scope("192.168.1.2") == "private_lan"


def test_environment_values_are_redacted_by_default() -> None:
    names, safe_values, presence = MODULE.parse_env(
        [
            "EXCHANGE_SECRET=do-not-record",
            "PORTAL_WEB_DATA_MODE=fixture",
            "PORTAL_CONTROL_PLANE_URL=https://private.internal",
        ]
    )
    assert "EXCHANGE_SECRET" in names
    assert "EXCHANGE_SECRET" not in safe_values
    assert safe_values == {"PORTAL_WEB_DATA_MODE": "fixture"}
    assert presence == {"PORTAL_CONTROL_PLANE_URL": True}


def test_mount_source_is_fingerprinted() -> None:
    mounts = MODULE.sanitized_mounts(
        {
            "Mounts": [
                {
                    "Source": "/private/target/path",
                    "Destination": "/data",
                    "Type": "bind",
                    "RW": False,
                }
            ]
        }
    )
    assert mounts[0]["destination"] == "/data"
    assert mounts[0]["source_fingerprint"] != "/private/target/path"
    assert len(mounts[0]["source_fingerprint"]) == 16


def test_relevant_roles_exclude_unrelated_containers() -> None:
    assert MODULE.relevant_role("freqtrade-portal-staging", "local/portal", {}) == "portal_web"
    assert MODULE.relevant_role("portal-authentik-server-1", "authentik/server", {}) == "authentik"
    assert MODULE.relevant_role("unrelated", "nginx:stable", {}) is None


def test_request_is_frozen_and_read_only(tmp_path: Path) -> None:
    request_path = tmp_path / "request.json"
    request_path.write_text(__import__("json").dumps(MODULE.EXPECTED_REQUEST), encoding="utf-8")
    assert MODULE.load_request(request_path)["mutation_authorized"] is False

    changed = dict(MODULE.EXPECTED_REQUEST)
    changed["mutation_authorized"] = True
    request_path.write_text(__import__("json").dumps(changed), encoding="utf-8")
    try:
        MODULE.load_request(request_path)
    except ValueError:
        pass
    else:
        raise AssertionError("mutation-authorized request must be rejected")
