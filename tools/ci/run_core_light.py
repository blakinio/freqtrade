#!/usr/bin/env python3
"""Run the deterministic, dependency-light core smoke suite."""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
from pathlib import Path


MANIFEST_PATH = Path(__file__).with_name("core-light-tests.txt")
MIN_TESTS = 200
MAX_TESTS = 800


def load_targets(path: Path = MANIFEST_PATH) -> list[str]:
    targets: list[str] = []
    for line_number, raw_line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        target = raw_line.split("#", 1)[0].strip()
        if not target:
            continue
        candidate = Path(target)
        if candidate.is_absolute() or ".." in candidate.parts:
            raise ValueError(f"unsafe target on line {line_number}: {target}")
        if not candidate.exists():
            raise ValueError(f"missing target on line {line_number}: {target}")
        if not candidate.parts or candidate.parts[0] != "tests":
            raise ValueError(f"target must remain under tests/: {target}")
        targets.append(target)
    if not targets:
        raise ValueError("core-light target manifest is empty")
    if len(targets) != len(set(targets)):
        raise ValueError("core-light target manifest contains duplicates")
    return targets


def parse_collection_count(output: str) -> int:
    matches = re.findall(r"(?m)^(\d+) tests? collected(?: in .*)?$", output)
    if not matches:
        raise ValueError("pytest collection summary was not found")
    return int(matches[-1])


def collect_test_count(targets: list[str]) -> int:
    command = [sys.executable, "-m", "pytest", "--collect-only", "-q", *targets]
    completed = subprocess.run(command, check=False, capture_output=True, text=True)
    sys.stdout.write(completed.stdout)
    sys.stderr.write(completed.stderr)
    if completed.returncode != 0:
        raise subprocess.CalledProcessError(completed.returncode, command)
    count = parse_collection_count(completed.stdout + completed.stderr)
    if not MIN_TESTS <= count <= MAX_TESTS:
        raise RuntimeError(f"core-light collected {count} tests; expected {MIN_TESTS}..{MAX_TESTS}")
    print(f"core-light collection accepted: {count} tests")
    return count


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--collect-only", action="store_true")
    args = parser.parse_args(argv)
    targets = load_targets()
    collect_test_count(targets)
    if args.collect_only:
        return 0
    subprocess.run(
        [
            sys.executable,
            "-m",
            "pytest",
            "-q",
            "--durations",
            "20",
            "-n",
            "auto",
            *targets,
        ],
        check=True,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
