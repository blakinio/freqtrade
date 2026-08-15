from __future__ import annotations

import datetime as dt
import importlib.util
import tempfile
import unittest
from pathlib import Path

MODULE_PATH = Path(__file__).with_name("repository_lifecycle.py")
SPEC = importlib.util.spec_from_file_location("repository_lifecycle", MODULE_PATH)
assert SPEC and SPEC.loader
rl = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(rl)

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


def pull(number: int, branch: str, sha: str, *, state: str, merged: bool = False, draft: bool = False, body: str = "", updated_at: str = "2026-08-15T00:00:00Z"):
    return {
        "number": number,
        "state": state,
        "merged_at": "2026-08-14T00:00:00Z" if merged else None,
        "merged": merged,
        "draft": draft,
        "title": f"PR {number}",
        "body": body,
        "updated_at": updated_at,
        "head": {
            "ref": branch,
            "sha": sha,
            "repo": {"full_name": "blakinio/freqtrade"},
        },
        "base": {"ref": "develop"},
    }


class PolicyTests(unittest.TestCase):
    def test_policy_accepts_expected_shape(self):
        rl.validate_policy(POLICY)

    def test_policy_rejects_default_branch_missing_from_integration(self):
        bad = dict(POLICY)
        bad["integration_branches"] = []
        with self.assertRaises(rl.LifecycleError):
            rl.validate_policy(bad)

    def test_reserved_tokens_are_token_scoped(self):
        self.assertTrue(rl.is_reserved("backup/foo", POLICY["reserved_name_parts"]))
        self.assertTrue(rl.is_reserved("release-2026", POLICY["reserved_name_parts"]))
        self.assertFalse(rl.is_reserved("feature/releaser-ui", POLICY["reserved_name_parts"]))


class ClassificationTests(unittest.TestCase):
    SHA = "a" * 40

    def classify(self, branch: str, pulls=None, protected=False, claims=None):
        return rl.classify_branch(
            branch=branch,
            sha=self.SHA,
            protected=protected,
            policy=POLICY,
            active_claims=set() if claims is None else claims,
            pulls=[] if pulls is None else pulls,
        )

    def test_default_branch_is_never_candidate(self):
        item = self.classify("develop")
        self.assertEqual(item["classification"], "PROTECTED")
        self.assertFalse(item["deletion_candidate"])

    def test_open_pr_wins_over_terminal_history(self):
        item = self.classify(
            "feature/x",
            [
                pull(1, "feature/x", self.SHA, state="closed", merged=True),
                pull(2, "feature/x", self.SHA, state="open"),
            ],
        )
        self.assertEqual(item["classification"], "OPEN_PR")
        self.assertFalse(item["deletion_candidate"])

    def test_active_claim_wins_when_no_open_pr(self):
        item = self.classify("feature/x", claims={"feature/x"})
        self.assertEqual(item["classification"], "ACTIVE_CLAIM")

    def test_reserved_branch_is_retained(self):
        item = self.classify("backup/important")
        self.assertEqual(item["classification"], "RESERVED")
        self.assertFalse(item["deletion_candidate"])

    def test_exact_merged_head_is_candidate(self):
        item = self.classify("feature/x", [pull(1, "feature/x", self.SHA, state="closed", merged=True)])
        self.assertEqual(item["classification"], "TERMINAL_MERGED")
        self.assertTrue(item["deletion_candidate"])

    def test_exact_closed_unmerged_head_is_candidate(self):
        item = self.classify("feature/x", [pull(1, "feature/x", self.SHA, state="closed", merged=False)])
        self.assertEqual(item["classification"], "TERMINAL_CLOSED_UNMERGED")
        self.assertTrue(item["deletion_candidate"])

    def test_pr_history_sha_mismatch_fails_closed(self):
        item = self.classify("feature/x", [pull(1, "feature/x", "b" * 40, state="closed", merged=True)])
        self.assertEqual(item["classification"], "UNKNOWN")
        self.assertFalse(item["deletion_candidate"])

    def test_no_pr_history_is_unmerged_orphan_not_candidate(self):
        item = self.classify("tmp/orphan")
        self.assertEqual(item["classification"], "UNMERGED_ORPHAN")
        self.assertFalse(item["deletion_candidate"])


class ActiveClaimTests(unittest.TestCase):
    def test_completed_task_does_not_hold_branch(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            target = root / "docs/agents/tasks/active"
            target.mkdir(parents=True)
            (target / "a.md").write_text("status: active\nbranch: feat/live\n", encoding="utf-8")
            (target / "b.md").write_text("status: completed\nbranch: feat/done\n", encoding="utf-8")
            self.assertEqual(rl.active_branch_claims(root), {"feat/live"})


class ApprovalTests(unittest.TestCase):
    def inventory(self):
        candidates = [{
            "branch": "feat/x",
            "classification": "TERMINAL_MERGED",
            "pr_numbers": [1],
            "sha": "a" * 40,
        }]
        return {
            "candidate_count": 1,
            "entries_sha256": rl.entries_sha256(candidates),
            "policy_sha256": rl.policy_sha256(POLICY),
        }

    def approval(self, inventory):
        return {
            "schema_version": 1,
            "issue": 1559,
            "repository": "blakinio/freqtrade",
            "apply_on_develop": True,
            "confirmation": "DELETE_EXACT_REVIEWED_TERMINAL_BRANCHES_ISSUE_1559",
            "candidate_count": inventory["candidate_count"],
            "entries_sha256": inventory["entries_sha256"],
            "policy_sha256": inventory["policy_sha256"],
            "reviewed_at": "2026-08-15T21:20:00Z",
            "reviewed_by": "agent:test",
            "review_summary": "Reviewed exact generated terminal candidate set.",
        }

    def test_exact_approval_passes(self):
        inv = self.inventory()
        rl.validate_approval(self.approval(inv), inv, POLICY)

    def test_candidate_drift_fails(self):
        inv = self.inventory()
        approval = self.approval(inv)
        approval["entries_sha256"] = "0" * 64
        with self.assertRaises(rl.LifecycleError):
            rl.validate_approval(approval, inv, POLICY)

    def test_policy_drift_fails(self):
        inv = self.inventory()
        approval = self.approval(inv)
        approval["policy_sha256"] = "0" * 64
        with self.assertRaises(rl.LifecycleError):
            rl.validate_approval(approval, inv, POLICY)


class PrAuditTests(unittest.TestCase):
    NOW = dt.datetime(2026, 8, 15, 21, 20, tzinfo=dt.timezone.utc)

    def classify(self, body: str, **kwargs):
        return rl.classify_pr_health(
            pull(1, "feature/x", "a" * 40, state="open", body=body, **kwargs),
            now=self.NOW,
            stale_days=3,
        )

    def test_request_only_is_not_auto_closed(self):
        item = self.classify("This PR must close without merge after terminal protected evidence.")
        self.assertEqual(item["health"], "REQUEST_ONLY")
        self.assertFalse(item["auto_close"])

    def test_generic_request_only_wording_does_not_self_classify(self):
        item = self.classify("The audit reports request-only PRs but this PR itself is normal governance work.")
        self.assertEqual(item["health"], "ACTIVE")

    def test_reference_to_another_request_pr_does_not_self_classify(self):
        item = self.classify(
            "This implementation remains mergeable after validation. Existing request-only deployment machinery may be reused, but the request PR must not be merged."
        )
        self.assertEqual(item["health"], "ACTIVE")

    def test_standalone_must_not_merge_is_request_only(self):
        item = self.classify("Request-only protected operation.\n\n**MUST NOT BE MERGED.**\nClose after terminal evidence.")
        self.assertEqual(item["health"], "REQUEST_ONLY")

    def test_stale_is_signal_only(self):
        item = rl.classify_pr_health(
            pull(2, "feature/old", "a" * 40, state="open", updated_at="2026-08-10T00:00:00Z"),
            now=self.NOW,
            stale_days=3,
        )
        self.assertEqual(item["health"], "STALLED_SIGNAL")
        self.assertFalse(item["auto_close"])

    def test_draft_prose_mismatch_is_detected(self):
        item = self.classify("This PR remains draft until final validation.", draft=False)
        self.assertEqual(item["health"], "METADATA_INCONSISTENT")


class FakeInventoryClient:
    repo = "blakinio/freqtrade"

    def repo_metadata(self):
        return {"full_name": self.repo, "default_branch": "develop"}

    def pulls(self, state="all"):
        return []

    def branches(self):
        return [{"name": "develop", "protected": True, "commit": {"sha": "a" * 40}}]


class InventoryTests(unittest.TestCase):
    def test_admin_merge_settings_may_be_unavailable_to_actions_token(self):
        with tempfile.TemporaryDirectory() as tmp:
            result = rl.build_inventory(FakeInventoryClient(), POLICY, Path(tmp))
            self.assertEqual(result["candidate_count"], 0)
            self.assertEqual(result["repository_merge_settings"]["delete_branch_on_merge"], "UNAVAILABLE_TOKEN_SCOPE")
            self.assertEqual(result["entries"][0]["classification"], "PROTECTED")


if __name__ == "__main__":
    unittest.main(verbosity=2)
