from __future__ import annotations

import importlib.util
import json
import tempfile
import unittest
from copy import deepcopy
from pathlib import Path
from typing import Any
from unittest import mock

from ai_platform.scripts import residual_pytorch_bounded_m1_run_request as run_request


REPO_ROOT = Path(__file__).resolve().parents[2]
CONTRACT_PATH = (
    REPO_ROOT
    / "ai_platform/experimental_model_research/"
    "residual-pytorch-bounded-m1-execution-contract-v1.json"
)
REQUEST_PATH = REPO_ROOT / run_request.REQUEST_REPO_PATH
WORKFLOW_PATH = (
    REPO_ROOT / ".github/workflows/residual-pytorch-bounded-m1-execution.yml"
)
TASK_PATH = (
    REPO_ROOT
    / "docs/agents/tasks/FTAI-20260726-residual-pytorch-bounded-m1-execution.md"
)
NUMERIC_RUNTIME_AVAILABLE = (
    importlib.util.find_spec("numpy") is not None
    and importlib.util.find_spec("pandas") is not None
)

execution: Any = None
np: Any = None
pd: Any = None
if NUMERIC_RUNTIME_AVAILABLE:
    import numpy as np
    import pandas as pd

    from ai_platform.scripts import residual_pytorch_bounded_m1_execution as execution


class ResidualPyTorchBoundedM1ExecutionTests(unittest.TestCase):
    def test_dependency_light_contract_preserves_frozen_boundaries(self) -> None:
        contract = json.loads(CONTRACT_PATH.read_text(encoding="utf-8"))

        self.assertEqual(contract["contract_id"], "residual-pytorch-bounded-m1-execution-v1")
        self.assertEqual(contract["geometry"]["timerange"], "20260301-20260501")
        self.assertEqual(contract["geometry"]["download_timerange"], "20250801-20260501")
        self.assertEqual(contract["geometry"]["executions_per_track"], 1)
        self.assertEqual(len(contract["tracks"]), 3)
        self.assertFalse(contract["authorization"]["historical_oos_used"])
        self.assertFalse(contract["authorization"]["final_holdout_used"])
        self.assertFalse(contract["authorization"]["winner_selection_allowed"])
        self.assertFalse(contract["feature_target_contract"]["liquidation_features_allowed"])
        self.assertFalse(REQUEST_PATH.exists())

    def test_request_module_import_is_dependency_light(self) -> None:
        missing = ModuleNotFoundError("No module named 'numpy'")
        missing.name = "numpy"
        with mock.patch.object(run_request, "import_module", side_effect=missing):
            with self.assertRaisesRegex(
                run_request.ResidualPyTorchBoundedM1RunRequestError,
                "full numeric validation profile",
            ):
                run_request._execution_module()

    def test_workflow_is_opened_only_exact_request_and_has_no_cache_fallback(self) -> None:
        workflow = WORKFLOW_PATH.read_text(encoding="utf-8")
        self.assertIn("types: [opened]", workflow)
        self.assertNotIn("workflow_dispatch", workflow)
        self.assertIn(run_request.REQUEST_REPO_PATH, workflow)
        self.assertIn("expected=$'A\\t", workflow)
        self.assertNotIn("restore-keys:", workflow)
        self.assertIn("--timerange 20250801-20260501", workflow)
        self.assertEqual(workflow.count("run_track \\\n"), 3)
        self.assertNotIn("selection-decision", workflow)

    def test_task_checkpoint_keeps_exactly_one_next_action(self) -> None:
        task = TASK_PATH.read_text(encoding="utf-8")
        self.assertEqual(task.count("next_action:"), 1)
        self.assertIn("consumed May-June historical OOS", task)
        self.assertIn("protected final holdout", task)

    def test_request_cli_requires_canonical_path(self) -> None:
        with mock.patch.object(run_request, "load_run_request") as loader:
            loader.return_value = {"request_id": run_request.EXPECTED_REQUEST_ID}
            result = run_request.main(["not-canonical.json"])
        self.assertEqual(result, 1)

    @unittest.skipUnless(NUMERIC_RUNTIME_AVAILABLE, "requires NumPy and Pandas")
    def test_contract_and_all_frozen_inputs_validate_without_request(self) -> None:
        report = execution.build_contract_report()

        self.assertEqual(report["status"], "infrastructure_ready_execution_not_requested")
        self.assertEqual(report["timerange"], "20260301-20260501")
        self.assertEqual(report["download_timerange"], "20250801-20260501")
        self.assertFalse(report["run_request_present"])
        self.assertEqual(len(report["tracks"]), 4)

    @unittest.skipUnless(NUMERIC_RUNTIME_AVAILABLE, "requires NumPy and Pandas")
    def test_contract_rejects_consumed_oos_authorization(self) -> None:
        contract = json.loads(CONTRACT_PATH.read_text(encoding="utf-8"))
        changed = deepcopy(contract)
        changed["authorization"]["historical_oos_used"] = True

        with self.assertRaisesRegex(
            execution.ResidualPyTorchBoundedM1Error,
            "Authorization contract drifted",
        ):
            execution.validate_contract(changed)

    @unittest.skipUnless(NUMERIC_RUNTIME_AVAILABLE, "requires NumPy and Pandas")
    def test_raw_matrix_audit_records_exact_feature_and_target_geometry(self) -> None:
        rows = 2200
        dates = pd.date_range("2025-12-01", periods=rows, freq="15min", tz="UTC")
        target = np.linspace(-0.01, 0.01, rows)
        target[-12:] = np.nan
        frame = pd.DataFrame(
            {
                "date": dates,
                "%feature_a": np.linspace(1.0, 2.0, rows),
                "%feature_b": np.sin(np.arange(rows) / 17.0),
                "&-future_return": target,
            }
        )

        report = execution.build_raw_matrix_audit(
            frame,
            ["%feature_a", "%feature_b"],
            ["&-future_return"],
            pair="BTC/USDT",
        )
        self.assertEqual(report["expanded_feature_count"], 2)
        self.assertEqual(report["target"]["trailing_null_rows"], 12)
        self.assertEqual(report["eligible_rows_before_split"], rows - 12)

        finalized = execution.finalize_matrix_audit(
            report,
            {
                "train_features": np.ones((1500, 2)),
                "train_labels": np.ones((1500, 1)),
                "test_features": np.ones((400, 2)),
                "test_labels": np.ones((400, 1)),
            },
        )
        self.assertEqual(finalized["outcome"], "audit_supported_for_bounded_m1")

    @unittest.skipUnless(NUMERIC_RUNTIME_AVAILABLE, "requires NumPy and Pandas")
    def test_cross_pair_audit_requires_identical_feature_identity(self) -> None:
        base = {
            "outcome": "audit_supported_for_bounded_m1",
            "expanded_feature_count": 2,
            "expanded_feature_names_sha256": "same",
            "target": {"trailing_null_rows": 12},
            "post_pipeline": {"transformed_feature_count": 2},
            "liquidation_features_used": False,
        }
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for pair, slug in (("BTC/USDT", "btc-usdt"), ("ETH/USDT", "eth-usdt")):
                execution.write_json(root / f"{slug}.json", dict(base, pair=pair))
            report = execution.validate_audit_directory(root)
            self.assertEqual(report["expanded_feature_count"], 2)

            changed = dict(base, pair="ETH/USDT", expanded_feature_names_sha256="different")
            execution.write_json(root / "eth-usdt.json", changed)
            with self.assertRaisesRegex(
                execution.ResidualPyTorchBoundedM1Error,
                "Cross-pair feature identity drifted",
            ):
                execution.validate_audit_directory(root)

    @unittest.skipUnless(NUMERIC_RUNTIME_AVAILABLE, "requires NumPy and Pandas")
    def test_prediction_diagnostics_are_development_only_and_descriptive(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for pair, slug, offset in (
                ("BTC/USDT", "btc-usdt", 0.0),
                ("ETH/USDT", "eth-usdt", 0.001),
            ):
                actual = np.array([-0.01, -0.002, 0.003, 0.012]) + offset
                prediction = np.array([-0.008, -0.001, 0.002, 0.01]) + offset
                pd.DataFrame(
                    {
                        "date": pd.date_range(
                            "2026-03-01", periods=len(actual), freq="15min", tz="UTC"
                        ),
                        "pair": pair,
                        "actual_target": actual,
                        "prediction": prediction,
                        "do_predict": [1, 1, 1, 1],
                    }
                ).to_csv(root / f"{slug}-window.csv", index=False)

            report = execution.build_prediction_diagnostics(
                root,
                track_id="residual-pytorch-m1-lightgbm-v1",
            )
        self.assertEqual(report["valid_prediction_rows"], 8)
        self.assertFalse(report["winner_selection_allowed"])

    @unittest.skipUnless(NUMERIC_RUNTIME_AVAILABLE, "requires NumPy and Pandas")
    def test_canonical_request_binds_hashes_and_rejects_tampering(self) -> None:
        canonical = run_request.canonical_run_request()
        self.assertEqual(canonical["request_id"], run_request.EXPECTED_REQUEST_ID)
        self.assertEqual(len(canonical["tracks"]), 3)

        with tempfile.TemporaryDirectory() as directory:
            request_path = Path(directory) / "request.json"
            request_path.write_text(
                json.dumps(canonical, indent=2, sort_keys=True) + "\n",
                encoding="utf-8",
            )
            self.assertEqual(run_request.load_run_request(request_path), canonical)
            changed = deepcopy(canonical)
            changed["geometry"]["timerange"] = "20260301-20260701"
            request_path.write_text(json.dumps(changed), encoding="utf-8")
            with self.assertRaises(run_request.ResidualPyTorchBoundedM1RunRequestError):
                run_request.load_run_request(request_path)

    @unittest.skipUnless(NUMERIC_RUNTIME_AVAILABLE, "requires NumPy and Pandas")
    def test_summary_rejects_forbidden_execution_boundary(self) -> None:
        payload = {
            "status": "success",
            "experiment_id": "residual-pytorch-m1-lightgbm-v1",
            "git_commit": "abc",
            "timerange": "20260301-20260501",
            "download_timerange": "20250801-20260501",
            "commands": [["freqtrade", "backtesting", "--timerange", "20260301-20260701"]],
        }
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "summary.json"
            execution.write_json(path, payload)
            with self.assertRaisesRegex(
                execution.ResidualPyTorchBoundedM1Error,
                "Forbidden temporal boundary",
            ):
                execution.validate_run_summary(
                    path,
                    track_id="residual-pytorch-m1-lightgbm-v1",
                    expected_head="abc",
                )


if __name__ == "__main__":
    unittest.main()
