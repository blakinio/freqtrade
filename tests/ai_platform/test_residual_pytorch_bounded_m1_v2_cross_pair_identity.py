from __future__ import annotations

import hashlib
import importlib.util
import tempfile
import unittest
from pathlib import Path
from typing import Any


NUMERIC_RUNTIME_AVAILABLE = (
    importlib.util.find_spec("numpy") is not None and importlib.util.find_spec("pandas") is not None
)


def _execution() -> Any:
    from ai_platform.scripts import residual_pytorch_bounded_m1_v2_execution as execution

    return execution


def _hash(names: list[str]) -> str:
    return hashlib.sha256("\n".join(names).encode()).hexdigest()


def _report(pair: str, names: list[str]) -> dict[str, Any]:
    return {
        "outcome": "audit_supported_for_bounded_m1",
        "pair": pair,
        "expanded_feature_count": len(names),
        "expanded_feature_names": names,
        "expanded_feature_names_sha256": _hash(names),
        "target": {"trailing_null_rows": 12},
        "post_pipeline": {"transformed_feature_count": len(names)},
        "liquidation_features_used": False,
    }


@unittest.skipUnless(NUMERIC_RUNTIME_AVAILABLE, "requires NumPy and Pandas")
class ResidualPyTorchBoundedM1V2CrossPairIdentityTests(unittest.TestCase):
    def test_pair_qualified_feature_names_validate_by_primary_and_correlation_roles(self) -> None:
        execution = _execution()
        btc_names = [
            "%-rsi-period_14_BTC/USDT_15m",
            "%-rsi-period_14_ETH/USDT_15m",
            "%-day-of-week",
        ]
        eth_names = [
            "%-rsi-period_14_ETH/USDT_15m",
            "%-rsi-period_14_BTC/USDT_15m",
            "%-day-of-week",
        ]
        self.assertNotEqual(_hash(btc_names), _hash(eth_names))

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            execution.write_json(root / "btc-usdt.json", _report("BTC/USDT", btc_names))
            execution.write_json(root / "eth-usdt.json", _report("ETH/USDT", eth_names))

            result = execution.validate_audit_directory(root)

        self.assertEqual(result["audit_id"], "residual-pytorch-bounded-m1-cross-pair-audit-v2")
        self.assertEqual(
            result["feature_identity_normalization"],
            "primary_and_correlated_pair_roles",
        )
        self.assertEqual(result["expanded_feature_count"], 3)
        self.assertNotEqual(
            result["pair_qualified_feature_names_sha256"]["BTC/USDT"],
            result["pair_qualified_feature_names_sha256"]["ETH/USDT"],
        )

    def test_semantic_feature_drift_still_fails_closed_after_pair_normalization(self) -> None:
        execution = _execution()
        btc_names = [
            "%-rsi-period_14_BTC/USDT_15m",
            "%-rsi-period_14_ETH/USDT_15m",
        ]
        eth_names = [
            "%-mfi-period_14_ETH/USDT_15m",
            "%-rsi-period_14_BTC/USDT_15m",
        ]

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            execution.write_json(root / "btc-usdt.json", _report("BTC/USDT", btc_names))
            execution.write_json(root / "eth-usdt.json", _report("ETH/USDT", eth_names))

            with self.assertRaisesRegex(
                execution.ResidualPyTorchBoundedM1Error,
                "Cross-pair feature identity drifted",
            ):
                execution.validate_audit_directory(root)


if __name__ == "__main__":
    unittest.main()
