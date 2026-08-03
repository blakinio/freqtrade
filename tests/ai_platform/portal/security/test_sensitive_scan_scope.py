from __future__ import annotations

import json
from pathlib import Path

from ai_platform.portal.security.sensitive_data import classify_sensitive_key
from ai_platform.portal.security.sensitive_scan import scan_paths


def test_environment_variable_name_descriptor_is_not_secret_material() -> None:
    assert classify_sensitive_key("access_client_secret_env_name") is None


def test_generated_dependency_manifest_is_excluded_from_persisted_data_scan(
    tmp_path: Path,
) -> None:
    package_lock = tmp_path / "package-lock.json"
    package_lock.write_text(
        json.dumps(
            {
                "packages": {
                    f"node_modules/generated-{index}": {"optional": True}
                    for index in range(300)
                }
            }
        ),
        encoding="utf-8",
    )
    application_data = tmp_path / "audit.json"
    application_data.write_text(
        json.dumps({"authorization_status": "denied"}),
        encoding="utf-8",
    )

    report = scan_paths((tmp_path,))

    assert report.scanned_files == 1
    assert report.findings == ()
    assert report.errors == ()
