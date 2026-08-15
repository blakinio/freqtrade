from __future__ import annotations

import importlib.util
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parent

RL_SPEC = importlib.util.spec_from_file_location("repository_lifecycle", ROOT / "repository_lifecycle.py")
assert RL_SPEC and RL_SPEC.loader
rl = importlib.util.module_from_spec(RL_SPEC)
RL_SPEC.loader.exec_module(rl)

import sys
sys.modules["repository_lifecycle"] = rl

D_SPEC = importlib.util.spec_from_file_location(
    "repository_lifecycle_destructive", ROOT / "repository_lifecycle_destructive.py"
)
assert D_SPEC and D_SPEC.loader
destructive = importlib.util.module_from_spec(D_SPEC)
D_SPEC.loader.exec_module(destructive)

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
SHA = "a" * 40


def terminal_pull(number: int = 7, *, merged: bool = False):
    return {
        "number": number,
        "state": "closed",
        "merged": merged,
        "merged_at": "2026-08-15T00:00:00Z" if merged else None,
        "head": {
            "ref": "feature/x",
            "sha": SHA,
            "repo": {"full_name": "blakinio/freqtrade"},
        },
        "base": {"ref": "develop"},
    }


class ClaimTests(unittest.TestCase):
    def test_completed_task_does_not_claim(self):
        self.assertEqual(
            destructive._claims_from_text("status: completed\nbranch: feature/x\n"),
            set(),
        )

    def test_active_source_task_claim_is_detected(self):
        self.assertEqual(
            destructive._claims_from_text("status: waiting\nbranch: feature/x\n"),
            {"feature/x"},
        )


class RevalidationTests(unittest.TestCase):
    def candidate(self, classification="TERMINAL_CLOSED_UNMERGED"):
        return {
            "branch": "feature/x",
            "sha": SHA,
            "classification": classification,
            "pr_numbers": [7],
        }

    def test_source_head_only_active_claim_retains_branch(self):
        client = type("Client", (), {"repo": "blakinio/freqtrade", "get_ref_sha": lambda self, ref: "b" * 40})()
        with (
            patch.object(destructive, "branch_metadata", return_value={"protected": False, "commit": {"sha": SHA}}),
            patch.object(destructive, "open_pulls_for_branch", return_value=[]),
            patch.object(destructive, "source_only_claims", return_value={"feature/x"}),
        ):
            with self.assertRaises(destructive.RetainBranch):
                destructive.revalidate_candidate(
                    client,
                    POLICY,
                    self.candidate(),
                    base_ref="develop",
                    base_directory={},
                    base_claims=set(),
                )

    def test_new_open_pr_ownership_retains_branch(self):
        client = type("Client", (), {"repo": "blakinio/freqtrade"})()
        with (
            patch.object(destructive, "branch_metadata", return_value={"protected": False, "commit": {"sha": SHA}}),
            patch.object(destructive, "open_pulls_for_branch", return_value=[{"number": 99}]),
        ):
            with self.assertRaises(destructive.RetainBranch):
                destructive.revalidate_candidate(
                    client,
                    POLICY,
                    self.candidate(),
                    base_ref="develop",
                    base_directory={},
                    base_claims=set(),
                )

    def test_exact_terminal_state_is_delete_safe(self):
        client = type("Client", (), {"repo": "blakinio/freqtrade", "get_ref_sha": lambda self, ref: "b" * 40})()
        with (
            patch.object(destructive, "branch_metadata", return_value={"protected": False, "commit": {"sha": SHA}}),
            patch.object(destructive, "open_pulls_for_branch", return_value=[]),
            patch.object(destructive, "source_only_claims", return_value=set()),
            patch.object(destructive, "pull_by_number", return_value=terminal_pull()),
        ):
            result = destructive.revalidate_candidate(
                client,
                POLICY,
                self.candidate(),
                base_ref="develop",
                base_directory={},
                base_claims=set(),
            )
        self.assertEqual(result["status"], "DELETE_SAFE")
        self.assertEqual(result["terminal_prs"], [7])


class RecoveryClient:
    repo = "blakinio/freqtrade"

    def __init__(self):
        self.refs = {"develop": "d" * 40}
        self.fail_create = True
        self.root = Path(".")
        self.token = "test-token"

    def get_ref_sha(self, branch):
        return self.refs.get(branch)

    def create_ref(self, branch, sha):
        self.refs[branch] = sha
        if self.fail_create:
            self.fail_create = False
            raise rl.LifecycleError("synthetic post-create failure")


class RecoveryTests(unittest.TestCase):
    def test_failure_after_create_still_removes_owned_recovery_ref(self):
        client = RecoveryClient()

        def fake_delete(_client, branch, expected_sha):
            self.assertEqual(client.refs.get(branch), expected_sha)
            client.refs.pop(branch, None)

        with patch.object(destructive, "delete_branch_exact", side_effect=fake_delete):
            with self.assertRaises(rl.LifecycleError):
                destructive.safe_recovery_test(client, "develop", 1559)
        leftovers = [name for name in client.refs if name.startswith("recovery-test/")]
        self.assertEqual(leftovers, [])


class ApplyPreflightTests(unittest.TestCase):
    def test_any_preflight_ownership_drift_aborts_before_recovery_or_delete(self):
        candidate = {
            "branch": "feature/x",
            "sha": SHA,
            "classification": "TERMINAL_MERGED",
            "pr_numbers": [7],
        }
        inventory = {
            "candidates": [candidate],
            "candidate_count": 1,
            "entries_sha256": "e" * 64,
            "policy_sha256": "p" * 64,
        }
        client = type("Client", (), {"repo": "blakinio/freqtrade", "get_ref_sha": lambda self, ref: "d" * 40})()
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            approval = root / "docs/agents/REPOSITORY_LIFECYCLE_APPROVAL.json"
            approval.parent.mkdir(parents=True)
            approval.write_text("{}\n", encoding="utf-8")
            with (
                patch.object(rl, "build_inventory", return_value=inventory),
                patch.object(rl, "load_json", return_value={"apply_on_develop": True}),
                patch.object(rl, "validate_approval"),
                patch.object(destructive, "claim_snapshot", return_value=({}, set())),
                patch.object(
                    destructive,
                    "revalidate_candidate",
                    side_effect=destructive.RetainBranch("feature/x: new ownership"),
                ),
                patch.object(destructive, "safe_recovery_test") as recovery,
                patch.object(destructive, "delete_branch_exact") as delete,
            ):
                with self.assertRaises(rl.LifecycleError):
                    destructive.apply_reviewed_cleanup(client, POLICY, root, None)
            recovery.assert_not_called()
            delete.assert_not_called()


class EventTests(unittest.TestCase):
    def test_terminal_event_uses_full_revalidation(self):
        event = {"action": "closed", "pull_request": terminal_pull()}
        client = type("Client", (), {"repo": "blakinio/freqtrade"})()
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "event.json"
            path.write_text(json.dumps(event), encoding="utf-8")
            with (
                patch.object(
                    destructive,
                    "revalidate_candidate",
                    side_effect=destructive.RetainBranch("feature/x: active source-head task"),
                ),
                patch.object(destructive, "delete_branch_exact") as delete,
            ):
                result = destructive.event_cleanup(client, POLICY, Path(tmp), path)
            self.assertEqual(result["result"], "RETAINED")
            delete.assert_not_called()


if __name__ == "__main__":
    unittest.main(verbosity=2)
