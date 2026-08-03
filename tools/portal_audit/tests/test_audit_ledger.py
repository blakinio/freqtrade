from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from audit_ledger import (  # noqa: E402
    AuditLedgerError,
    canonical_digest,
    composition_signature,
    ledger_metadata,
    load_ledger,
    resolve_exact_head,
    validate_inventory,
    validate_ledger,
    validate_report_metadata,
)


HEAD = "a" * 40


def minimal_fixture() -> tuple[dict[str, object], dict[str, object]]:
    evidence = {"UnavailableRuntimeValuationSource(": ["portal/api.py:10: source = UnavailableRuntimeValuationSource("]}
    module_inventory = ["valuation"]
    route_inventory = [{"method": "GET", "route": "/v1/valuations", "file": "portal/router.py"}]
    page_inventory = ["/performance"]
    bff_inventory = ["/api/performance"]
    inventory = {
        "backend_modules": {"count": len(module_inventory), "sha256": canonical_digest(module_inventory)},
        "backend_routes": {"count": len(route_inventory), "sha256": canonical_digest(route_inventory)},
        "frontend_pages": {"count": len(page_inventory), "sha256": canonical_digest(page_inventory)},
        "bff_handlers": {"count": len(bff_inventory), "sha256": canonical_digest(bff_inventory)},
        "composition_signature_sha256": canonical_digest(composition_signature(evidence)),
    }
    rule = {"status": "DISCONNECTED", "issue": "#1093", "reason": "provider is unavailable"}
    ledger: dict[str, object] = {
        "schema_version": "portal-completeness-ledger-v2",
        "ledger_version": "test.1",
        "mode": "living_exact_head_gate",
        "inventory": inventory,
        "classifications": {
            "backend_modules": {"valuation": rule},
            "backend_routes": {"GET /v1/valuations": rule},
            "frontend_pages": {"/performance": rule},
            "bff_handlers": {"/api/performance": rule},
            "expected_absent_backend_routes": {},
            "runtime_fixture_boundaries": [],
            "deployment_boundaries": [],
            "runtime_notes": {},
            "navigation": [
                {
                    "group": "Overview",
                    "label": "Performance",
                    "route": "/performance",
                    "frontend": "COMPLETE",
                    "api_boundary": "COMPLETE",
                    "backend": "DISCONNECTED",
                    "persistence_provider": "DISCONNECTED",
                    "tests": "PARTIAL",
                    "overall": "DISCONNECTED",
                    "issues": "#1093",
                    "reason": "provider is unavailable",
                }
            ],
        },
    }
    data: dict[str, object] = {
        "backend_modules": [{"module": "valuation"}],
        "backend_routes": [{"method": "GET", "route": "/v1/valuations", "file": "portal/router.py"}],
        "frontend_pages": [{"route": "/performance"}],
        "bff_handlers": [{"route": "/api/performance"}],
        "composition_evidence": evidence,
    }
    return ledger, data


class AuditLedgerTests(unittest.TestCase):
    def test_repository_ledger_is_valid(self) -> None:
        ledger = load_ledger()
        self.assertEqual(ledger["mode"], "living_exact_head_gate")

    def test_added_route_requires_explicit_ledger_update(self) -> None:
        ledger, data = minimal_fixture()
        data["backend_routes"].append(
            {"method": "POST", "route": "/v1/valuations", "file": "portal/router.py"}
        )
        with self.assertRaisesRegex(AuditLedgerError, "backend_routes drift"):
            validate_inventory(data, ledger)

    def test_provider_composition_change_fails_closed(self) -> None:
        ledger, data = minimal_fixture()
        data["composition_evidence"] = {
            "UnavailableRuntimeValuationSource(": [],
            "HttpPrivateRuntimeValuationSource(": [
                "portal/api.py:10: source = HttpPrivateRuntimeValuationSource("
            ],
        }
        with self.assertRaisesRegex(AuditLedgerError, "composition evidence changed"):
            validate_inventory(data, ledger)

    def test_completed_issue_reference_is_rejected(self) -> None:
        ledger, _data = minimal_fixture()
        with self.assertRaisesRegex(AuditLedgerError, "marked COMPLETE"):
            validate_ledger(ledger, completed={1093})

    def test_report_metadata_must_match_exact_head_and_ledger(self) -> None:
        ledger, _data = minimal_fixture()
        report = ledger_metadata(ledger, HEAD)
        validate_report_metadata(report, ledger, HEAD)
        report["audited_head"] = "b" * 40
        with self.assertRaisesRegex(AuditLedgerError, "metadata mismatch"):
            validate_report_metadata(report, ledger, HEAD)

    def test_exact_head_rejects_checkout_mismatch(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / ".git").mkdir()
            with mock.patch("audit_ledger.subprocess.check_output", return_value="b" * 40 + "\n"):
                with self.assertRaisesRegex(AuditLedgerError, "head mismatch"):
                    resolve_exact_head(HEAD, root)

    def test_digest_is_order_independent_for_mapping_keys(self) -> None:
        left = {"a": 1, "b": {"c": 2}}
        right = {"b": {"c": 2}, "a": 1}
        self.assertEqual(canonical_digest(left), canonical_digest(right))


if __name__ == "__main__":
    unittest.main()
