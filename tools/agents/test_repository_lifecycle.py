from __future__ import annotations

import datetime as dt
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

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
        pulls = [
            pull(1, "feature/x", self.SHA, state="closed", merged=True),
            pull(2, "feature/x", self.SHA, state="open"),
        ]
        item = self.classify("feature/x", pulls)
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
            claims = rl.active_branch_claims(root)
            self.assertEqual(claims, {"feat/live"})


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
            "reviewed_by": "repository-owner",
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

    def test_request_only_is_not_auto_closed(self):
        item = rl.classify_pr_health(
            pull(
                1,
                "ops/request",
                "a" * 40,
                state="open",
                body="MUST NOT BE MERGED. Close after terminal protected evidence.",
            ),
            now=self.NOW,
            stale_days=3,
        )
        self.assertEqual(item["health"], "REQUEST_ONLY")
        self.assertFalse(item["auto_close"])

    def test_stale_is_signal_only(self):
        item = rl.classify_pr_health(
            pull(
                2,
                "feature/old",
                "a" * 40,
                state="open",
                updated_at="2026-08-10T00:00:00Z",
            ),
            now=self.NOW,
            stale_days=3,
        )
        self.assertEqual(item["health"], "STALLED_SIGNAL")
        self.assertFalse(item["auto_close"])

    def test_draft_prose_mismatch_is_detected(self):
        item = rl.classify_pr_health(
            pull(
                3,
                "feature/x",
                "a" * 40,
                state="open",
                draft=False,
                body="This PR remains draft until final validation.",
            ),
            now=self.NOW,
            stale_days=3,
        )
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
            self.assertEqual(
                result["repository_merge_settings"]["delete_branch_on_merge"],
                "UNAVAILABLE_TOKEN_SCOPE",
            )
            self.assertEqual(result["entries"][0]["classification"], "PROTECTED")


class FakeEventClient:
    def __init__(self, *, current_sha, protected=False, open_pulls=None):
        self.repo = "blakinio/freqtrade"
        self.current_sha = current_sha
        self.protected = protected
        self.open_pulls = [] if open_pulls is None else open_pulls
        self.deleted = []

    def get_ref_sha(self, branch):
        return self.current_sha

    def branches(self):
        return [{"name": "feature/x", "protected": self.protected, "commit": {"sha": self.current_sha}}]

    def pulls(self, state="open"):
        return self.open_pulls

    def delete_branch_exact(self, branch, sha):
        self.deleted.append((branch, sha))
        self.current_sha = None


class EventCleanupTests(unittest.TestCase):
    SHA = "a" * 40

    def event_file(self, tmp, p):
        path = Path(tmp) / "event.json"
        path.write_text(json.dumps({"action": "closed", "pull_request": p}), encoding="utf-8")
        return path

    def test_closed_unmerged_exact_head_deletes(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = pull(7, "feature/x", self.SHA, state="closed", merged=False)
            client = FakeEventClient(current_sha=self.SHA)
            result = rl.event_cleanup(client, POLICY, Path(tmp), self.event_file(tmp, p))
            self.assertEqual(result["result"], "PASS")
            self.assertEqual(client.deleted, [("feature/x", self.SHA)])

    def test_merged_exact_head_deletes_as_auto_delete_fallback(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = pull(6, "feature/x", self.SHA, state="closed", merged=True)
            client = FakeEventClient(current_sha=self.SHA)
            result = rl.event_cleanup(client, POLICY, Path(tmp), self.event_file(tmp, p))
            self.assertEqual(result["result"], "PASS")
            self.assertEqual(client.deleted, [("feature/x", self.SHA)])

    def test_branch_move_retains(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = pull(7, "feature/x", self.SHA, state="closed", merged=False)
            client = FakeEventClient(current_sha="b" * 40)
            result = rl.event_cleanup(client, POLICY, Path(tmp), self.event_file(tmp, p))
            self.assertEqual(result["result"], "RETAINED")
            self.assertFalse(client.deleted)

    def test_active_claim_retains(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            target = root / "docs/agents/tasks/active"
            target.mkdir(parents=True)
            (target / "task.md").write_text("status: waiting\nbranch: feature/x\n", encoding="utf-8")
            p = pull(7, "feature/x", self.SHA, state="closed", merged=False)
            client = FakeEventClient(current_sha=self.SHA)
            result = rl.event_cleanup(client, POLICY, root, self.event_file(tmp, p))
            self.assertEqual(result["result"], "RETAINED")
            self.assertFalse(client.deleted)

    def test_protected_retains(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = pull(7, "feature/x", self.SHA, state="closed", merged=False)
            client = FakeEventClient(current_sha=self.SHA, protected=True)
            result = rl.event_cleanup(client, POLICY, Path(tmp), self.event_file(tmp, p))
            self.assertEqual(result["result"], "RETAINED")
            self.assertFalse(client.deleted)

    def test_another_open_pr_retains(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = pull(7, "feature/x", self.SHA, state="closed", merged=False)
            open_pr = pull(8, "feature/x", self.SHA, state="open")
            client = FakeEventClient(current_sha=self.SHA, open_pulls=[open_pr])
            result = rl.event_cleanup(client, POLICY, Path(tmp), self.event_file(tmp, p))
            self.assertEqual(result["result"], "RETAINED")
            self.assertFalse(client.deleted)


if __name__ == "__main__":
    unittest.main(verbosity=2)
