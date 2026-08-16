from __future__ import annotations

import importlib.util
import sys
import tempfile
import unittest
from pathlib import Path
from typing import Any
from unittest.mock import patch


ROOT = Path(__file__).resolve().parent


def _load(name: str, path: str) -> Any:
    spec = importlib.util.spec_from_file_location(name, ROOT / path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"unable to load {name}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    sys.modules[name] = module
    return module


rl = _load("repository_lifecycle", "repository_lifecycle.py")
destructive = _load("repository_lifecycle_destructive", "repository_lifecycle_destructive.py")
preflight = _load("repository_lifecycle_preflight", "repository_lifecycle_preflight.py")
approval = _load("repository_lifecycle_approval", "repository_lifecycle_approval.py")
apply = _load("repository_lifecycle_apply", "repository_lifecycle_apply.py")

POLICY = {
    "schema_version": 1,
    "issue": 1559,
    "repository": "blakinio/freqtrade",
    "default_branch": "develop",
    "integration_branches": ["develop"],
    "reserved_name_parts": ["release", "rollback", "recovery", "backup"],
    "stale_pr_days": 3,
    "deletion_classifications": ["TERMINAL_CLOSED_UNMERGED", "TERMINAL_MERGED"],
}
BASE_SHA = "d" * 40
MERGED_SHA = "a" * 40
CLOSED_SHA = "b" * 40


def candidate(branch: str, sha: str, classification: str, pr: int) -> dict[str, Any]:
    return {
        "branch": branch,
        "sha": sha,
        "classification": classification,
        "pr_numbers": [pr],
    }


def inventory(candidates: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "branch_count": len(candidates) + 1,
        "candidate_count": len(candidates),
        "candidates": candidates,
        "entries_sha256": rl.entries_sha256(candidates),
        "policy_sha256": rl.policy_sha256(POLICY),
        "entries": [
            {
                "branch": "develop",
                "sha": BASE_SHA,
                "classification": "PROTECTED",
                "deletion_candidate": False,
                "protected": True,
                "pr_numbers": [],
                "reason": "default branch",
            }
        ],
    }


def safe_manifest(candidates: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "base_sha": BASE_SHA,
        "candidate_count": len(candidates),
        "candidates": candidates,
        "entries_sha256": rl.entries_sha256(candidates),
        "policy_sha256": rl.policy_sha256(POLICY),
        "source_inventory_candidate_count": len(candidates),
        "retained_count": 0,
        "retained": [],
        "already_absent_count": 0,
        "already_absent": [],
    }


def fake_client() -> Any:
    return type(
        "Client",
        (),
        {"repo": "blakinio/freqtrade", "root": Path(), "token": "token"},
    )()


class HistoricalPreflightRateLimitTests(unittest.TestCase):
    def test_source_head_claims_use_git_snapshot_not_per_candidate_rest(self) -> None:
        merged = candidate("feature/merged", MERGED_SHA, "TERMINAL_MERGED", 1)
        closed = candidate(
            "feature/closed",
            CLOSED_SHA,
            "TERMINAL_CLOSED_UNMERGED",
            2,
        )
        live_inventory = inventory([merged, closed])
        client = fake_client()
        with (
            patch.object(rl, "build_inventory", side_effect=[live_inventory, live_inventory]),
            patch.object(
                preflight,
                "_fetch_snapshot_refs",
                return_value=(
                    BASE_SHA,
                    {"feature/closed": "refs/lifecycle-preflight/source-0000"},
                    ["refs/lifecycle-preflight/base", "refs/lifecycle-preflight/source-0000"],
                ),
            ),
            patch.object(
                preflight,
                "_task_tree",
                side_effect=[{}, {"docs/agents/tasks/active/closed.md": "c" * 40}],
            ),
            patch.object(preflight, "_tree_claims", return_value=set()),
            patch.object(preflight, "_source_only_claims", return_value={"feature/closed"}),
            patch.object(destructive, "remote_ref_sha", return_value=BASE_SHA),
            patch.object(preflight, "_cleanup_local_refs"),
            patch.object(destructive, "revalidate_candidate") as old_rest_revalidation,
        ):
            result = preflight.build_preflight(client, POLICY, Path())

        old_rest_revalidation.assert_not_called()
        self.assertEqual(result["candidate_count"], 1)
        self.assertEqual(result["candidates"], [merged])
        self.assertEqual(result["retained_count"], 1)
        self.assertEqual(result["retained"][0]["branch"], "feature/closed")
        self.assertEqual(result["snapshot_transport"], "git-immutable-refs")

    def test_current_base_claim_retains_merged_candidate(self) -> None:
        merged = candidate("feature/merged", MERGED_SHA, "TERMINAL_MERGED", 1)
        live_inventory = inventory([merged])
        client = fake_client()
        with (
            patch.object(rl, "build_inventory", side_effect=[live_inventory, live_inventory]),
            patch.object(
                preflight,
                "_fetch_snapshot_refs",
                return_value=(BASE_SHA, {}, ["refs/lifecycle-preflight/base"]),
            ),
            patch.object(preflight, "_task_tree", return_value={}),
            patch.object(preflight, "_tree_claims", return_value={"feature/merged"}),
            patch.object(destructive, "remote_ref_sha", return_value=BASE_SHA),
            patch.object(preflight, "_cleanup_local_refs"),
        ):
            result = preflight.build_preflight(client, POLICY, Path())

        self.assertEqual(result["candidate_count"], 0)
        self.assertEqual(result["retained_count"], 1)

    def test_raw_candidate_digest_drift_fails_closed(self) -> None:
        merged = candidate("feature/merged", MERGED_SHA, "TERMINAL_MERGED", 1)
        first = inventory([merged])
        second = dict(first)
        second["entries_sha256"] = "0" * 64
        client = fake_client()
        with (
            patch.object(rl, "build_inventory", side_effect=[first, second]),
            patch.object(
                preflight,
                "_fetch_snapshot_refs",
                return_value=(BASE_SHA, {}, ["refs/lifecycle-preflight/base"]),
            ),
            patch.object(preflight, "_task_tree", return_value={}),
            patch.object(preflight, "_tree_claims", return_value=set()),
            patch.object(preflight, "_cleanup_local_refs") as cleanup,
        ):
            with self.assertRaises(rl.LifecycleError):
                preflight.build_preflight(client, POLICY, Path())
        cleanup.assert_called_once()


class ApprovalWaveTests(unittest.TestCase):
    def test_large_safe_set_is_deterministically_sliced_to_wave_limit(self) -> None:
        candidates = [
            candidate(f"feature/{index:04d}", f"{index:040x}"[-40:], "TERMINAL_MERGED", index)
            for index in range(1, 1011)
        ]
        manifest = safe_manifest(candidates)
        wave = approval.approval_wave_manifest(manifest)
        self.assertEqual(wave["candidate_count"], approval.APPROVAL_WAVE_SIZE)
        self.assertEqual(wave["candidates"], candidates[: approval.APPROVAL_WAVE_SIZE])
        self.assertEqual(
            wave["entries_sha256"],
            rl.entries_sha256(candidates[: approval.APPROVAL_WAVE_SIZE]),
        )

    def test_requested_wave_larger_than_limit_fails_closed(self) -> None:
        candidates = [
            candidate(f"feature/{index}", MERGED_SHA, "TERMINAL_MERGED", index)
            for index in range(1, approval.APPROVAL_WAVE_SIZE + 2)
        ]
        with self.assertRaises(rl.LifecycleError):
            approval.approval_wave_manifest(
                safe_manifest(candidates),
                candidate_count=approval.APPROVAL_WAVE_SIZE + 1,
            )


class HistoricalApplyRateLimitTests(unittest.TestCase):
    def test_immediate_revalidation_uses_git_and_one_open_pr_query(self) -> None:
        item = candidate("feature/merged", MERGED_SHA, "TERMINAL_MERGED", 1)
        client = fake_client()
        with (
            patch.object(
                destructive,
                "remote_ref_sha",
                side_effect=[BASE_SHA, MERGED_SHA],
            ),
            patch.object(destructive, "open_pulls_for_branch", return_value=[]) as open_query,
        ):
            result = apply._revalidate_immediately_before_delete(
                client,
                POLICY,
                item,
                approved_base_sha=BASE_SHA,
            )

        self.assertEqual(result["status"], "DELETE_SAFE")
        open_query.assert_called_once_with(client, "feature/merged")

    def test_new_open_pr_retains_approved_candidate(self) -> None:
        item = candidate("feature/merged", MERGED_SHA, "TERMINAL_MERGED", 1)
        client = fake_client()
        with (
            patch.object(
                destructive,
                "remote_ref_sha",
                side_effect=[BASE_SHA, MERGED_SHA],
            ),
            patch.object(
                destructive,
                "open_pulls_for_branch",
                return_value=[{"number": 99}],
            ),
        ):
            with self.assertRaises(destructive.RetainBranch):
                apply._revalidate_immediately_before_delete(
                    client,
                    POLICY,
                    item,
                    approved_base_sha=BASE_SHA,
                )

    def test_apply_uses_only_approved_prefix_of_larger_safe_set(self) -> None:
        candidates = [
            candidate(f"feature/{index:04d}", f"{index:040x}"[-40:], "TERMINAL_MERGED", index)
            for index in range(1, approval.APPROVAL_WAVE_SIZE + 3)
        ]
        manifest = safe_manifest(candidates)
        wave = approval.approval_wave_manifest(manifest)
        approval_record = {
            "apply_on_develop": True,
            "candidate_count": wave["candidate_count"],
        }
        client = fake_client()
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            with (
                patch.object(preflight, "build_preflight", return_value=manifest),
                patch.object(rl, "load_json", return_value=approval_record),
                patch.object(rl, "validate_approval"),
                patch.object(
                    destructive,
                    "safe_recovery_test",
                    return_value={"result": "PASS"},
                ),
                patch.object(
                    apply,
                    "_revalidate_immediately_before_delete",
                    return_value={"status": "DELETE_SAFE"},
                ) as revalidate,
                patch.object(apply, "_delete_git_exact", return_value="DELETED") as delete,
                patch.object(destructive, "revalidate_candidate") as legacy_revalidate,
                patch.object(destructive, "delete_branch_exact") as legacy_delete,
            ):
                result = apply.apply_reviewed_safe_manifest(
                    client,
                    POLICY,
                    root,
                    root / "apply.json",
                )

        self.assertEqual(revalidate.call_count, approval.APPROVAL_WAVE_SIZE)
        self.assertEqual(delete.call_count, approval.APPROVAL_WAVE_SIZE)
        legacy_revalidate.assert_not_called()
        legacy_delete.assert_not_called()
        self.assertEqual(result["reviewed_candidate_count"], approval.APPROVAL_WAVE_SIZE)
        self.assertEqual(result["approved_candidates"], candidates[: approval.APPROVAL_WAVE_SIZE])
        self.assertEqual(len(result["deleted"]), approval.APPROVAL_WAVE_SIZE)

    def test_apply_rejects_approval_count_above_wave_limit_before_recovery(self) -> None:
        candidates = [
            candidate(f"feature/{index}", MERGED_SHA, "TERMINAL_MERGED", index)
            for index in range(1, approval.APPROVAL_WAVE_SIZE + 2)
        ]
        manifest = safe_manifest(candidates)
        client = fake_client()
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            with (
                patch.object(preflight, "build_preflight", return_value=manifest),
                patch.object(
                    rl,
                    "load_json",
                    return_value={
                        "apply_on_develop": True,
                        "candidate_count": approval.APPROVAL_WAVE_SIZE + 1,
                    },
                ),
                patch.object(destructive, "safe_recovery_test") as recovery,
            ):
                with self.assertRaises(rl.LifecycleError):
                    apply.apply_reviewed_safe_manifest(
                        client,
                        POLICY,
                        root,
                        root / "apply.json",
                    )
        recovery.assert_not_called()


if __name__ == "__main__":
    unittest.main(verbosity=2)
