from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

from tools.ci.classify_wickhunter_wh09_deploy_request import (
    DeployRequestClassificationError,
    diagnostic_request_changed_in_push,
)


DIAGNOSTIC_PATH = (
    "deploy/synology/wickhunter-production-research-runtime/run-requests/"
    "diagnose-wh09-production-research-20260808-v4.json"
)


def _git(repo: Path, *args: str) -> str:
    return subprocess.check_output(["git", *args], cwd=repo, text=True).strip()


def _commit(repo: Path, message: str) -> str:
    subprocess.run(["git", "add", "-A"], cwd=repo, check=True)
    subprocess.run(["git", "commit", "-m", message], cwd=repo, check=True)
    return _git(repo, "rev-parse", "HEAD")


def _repo(tmp_path: Path) -> Path:
    repo = tmp_path / "repo"
    repo.mkdir()
    subprocess.run(["git", "init", "-b", "develop"], cwd=repo, check=True)
    subprocess.run(["git", "config", "user.email", "test@example.invalid"], cwd=repo, check=True)
    subprocess.run(["git", "config", "user.name", "WH09 test"], cwd=repo, check=True)
    (repo / "base.txt").write_text("base\n", encoding="utf-8")
    _commit(repo, "base")
    return repo


def test_actions_style_push_without_changed_file_arrays_uses_exact_git_range(
    tmp_path: Path,
) -> None:
    repo = _repo(tmp_path)
    before = _git(repo, "rev-parse", "HEAD")

    (repo / "unrelated.txt").write_text("one\n", encoding="utf-8")
    _commit(repo, "unrelated")
    target = repo / DIAGNOSTIC_PATH
    target.parent.mkdir(parents=True)
    target.write_text("{}\n", encoding="utf-8")
    after = _commit(repo, "diagnostic request")

    event = {
        "before": before,
        "after": after,
        "commits": [
            {"id": after, "message": "GitHub Actions payload intentionally has no file arrays"}
        ],
    }
    assert diagnostic_request_changed_in_push(event, DIAGNOSTIC_PATH, repo_root=repo) is True


def test_git_range_classifier_requires_exact_path_element(tmp_path: Path) -> None:
    repo = _repo(tmp_path)
    before = _git(repo, "rev-parse", "HEAD")
    lookalike = repo / f"{DIAGNOSTIC_PATH}.bak"
    lookalike.parent.mkdir(parents=True)
    lookalike.write_text("{}\n", encoding="utf-8")
    after = _commit(repo, "lookalike only")

    event = {"before": before, "after": after, "commits": [{"id": after}]}
    assert diagnostic_request_changed_in_push(event, DIAGNOSTIC_PATH, repo_root=repo) is False


def test_git_range_classifier_fails_closed_for_unprovable_push_range(tmp_path: Path) -> None:
    repo = _repo(tmp_path)
    after = _git(repo, "rev-parse", "HEAD")
    event = {"before": "0" * 40, "after": after, "commits": [{"id": after}]}

    with pytest.raises(DeployRequestClassificationError, match="null Git SHA"):
        diagnostic_request_changed_in_push(event, DIAGNOSTIC_PATH, repo_root=repo)
