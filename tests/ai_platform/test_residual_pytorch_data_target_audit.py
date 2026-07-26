from __future__ import annotations

import importlib.util
import json
import math
import unittest
from copy import deepcopy
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[2]
MODULE_PATH = REPO_ROOT / "ai_platform/scripts/residual_pytorch_data_target_audit.py"
CONTRACT_PATH = (
    REPO_ROOT / "ai_platform/experimental_model_research/"
    "residual-pytorch-data-target-audit-contract-v1.json"
)
SPEC = importlib.util.spec_from_file_location("residual_pytorch_data_target_audit", MODULE_PATH)
if SPEC is None or SPEC.loader is None:
    raise RuntimeError(f"Unable to load audit module from {MODULE_PATH}")
AUDIT = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(AUDIT)


class ResidualPyTorchDataTargetAuditTests(unittest.TestCase):
    def test_strategy_target_matches_explicit_future_offsets(self) -> None:
        close = [100.0 + index * 0.25 for index in range(64)]
        horizon = 12
        actual = AUDIT.strategy_target(close, horizon)

        self.assertEqual(actual[: horizon - 1], [None] * (horizon - 1))
        self.assertEqual(actual[-horizon:], [None] * horizon)
        for index in range(horizon - 1, len(close) - horizon):
            expected = AUDIT.explicit_target(close, index, horizon)
            self.assertTrue(math.isclose(float(actual[index]), expected, abs_tol=1e-15))

    def test_synthetic_audit_proves_horizon_and_edge_geometry(self) -> None:
        report = AUDIT.run_synthetic_audit(horizon=12, rows=64)

        self.assertEqual(report["leading_unavailable_rows"], 11)
        self.assertEqual(report["trailing_unavailable_rows"], 12)
        self.assertEqual(report["max_absolute_alignment_error"], 0.0)
        self.assertFalse(report["past_close_influences_target_numerator"])
        self.assertTrue(all(report["future_offset_influence"].values()))
        self.assertFalse(report["offset_after_horizon_influences_target"])

    def test_contract_rejects_forbidden_market_data_authorization(self) -> None:
        payload = json.loads(CONTRACT_PATH.read_text(encoding="utf-8"))
        contract: dict[str, Any] = deepcopy(payload)
        contract["authorization"]["market_data_access"] = True

        with self.assertRaisesRegex(AUDIT.ResidualDataTargetAuditError, "Forbidden authorization"):
            AUDIT.validate_contract(contract)

    def test_full_report_remains_inconclusive_without_historical_matrix(self) -> None:
        report: dict[str, Any] = AUDIT.build_report()

        self.assertEqual(report["outcome"], "audit_inconclusive")
        self.assertTrue(report["target"]["synthetic_alignment_supported"])
        self.assertIsNone(report["feature_audit"]["freqai_expanded_feature_count"])
        self.assertIsNone(report["historical_label_distribution"]["summary"])
        for flag in (
            "market_data_used",
            "exchange_download_performed",
            "training_performed",
            "backtest_performed",
            "historical_oos_used",
            "protected_holdout_used",
            "liquidation_features_used",
        ):
            self.assertFalse(report[flag], flag)


if __name__ == "__main__":
    unittest.main()
