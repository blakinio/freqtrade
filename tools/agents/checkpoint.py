#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path

CHECKPOINT_HEADING = "## Context checkpoint"
LIST_KEYS = {
    "context_routes",
    "owned_paths",
    "proven",
    "derived",
    "unknown",
    "conflicts",
    "rejected_hypotheses",
    "changed_paths",
    "blockers",
}
PLACEHOLDER_NEXT_ACTIONS = {
    "",
    "none",
    "unknown",
    "pending",
    "n/a",
    "tbd",
    "todo",
    "later",
}


@dataclass(frozen=True)
class Contract:
    version: str
    required_fields: tuple[str, ...]
    allowed_statuses: frozenset[str]
    allowed_validation_results: frozenset[str]
    evidence_fields: tuple[str, ...]
    compactness_limits: dict[str, int]


def repository_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _string_items(value: object, label: str) -> tuple[str, ...]:
    if not isinstance(value, list) or not all(isinstance(item, str) for item in value):
        raise ValueError(f"invalid {label} in governance contract")
    return tuple(value)


def load_contract() -> Contract:
    path = repository_root() / "docs/agents/GOVERNANCE_CONTRACT.json"
    raw = json.loads(path.read_text(encoding="utf-8"))
    shared = raw.get("shared_checkpoint_contract")
    if not isinstance(shared, dict):
        raise ValueError(f"{path}: invalid shared checkpoint contract")

    evidence_map = shared.get("evidence_state_fields")
    limits = shared.get("compactness_limits")
    if not isinstance(evidence_map, dict) or not isinstance(limits, dict):
        raise ValueError(f"{path}: invalid evidence or compactness contract")
    if not all(
        isinstance(key, str) and isinstance(value, str) for key, value in evidence_map.items()
    ):
        raise ValueError(f"{path}: invalid evidence state mapping")
    if not all(
        isinstance(key, str) and isinstance(value, int) and value > 0
        for key, value in limits.items()
    ):
        raise ValueError(f"{path}: invalid compactness limits")

    return Contract(
        version=str(shared.get("version", "")),
        required_fields=_string_items(shared.get("required_fields"), "required_fields"),
        allowed_statuses=frozenset(
            _string_items(shared.get("allowed_statuses"), "allowed_statuses")
        ),
        allowed_validation_results=frozenset(
            _string_items(shared.get("allowed_validation_results"), "allowed_validation_results")
        ),
        evidence_fields=tuple(evidence_map.values()),
        compactness_limits={key: int(value) for key, value in limits.items()},
    )


def scalar(value: str) -> str:
    value = value.strip()
    if len(value) >= 2 and value[0] == value[-1] and value[0] in {'"', "'"}:
        return value[1:-1]
    return value


def _checkpoint_lines(path: Path) -> list[str] | None:
    text = path.read_text(encoding="utf-8")
    matches = list(re.finditer(r"(?m)^## Context checkpoint\s*$", text))
    if not matches:
        return None
    if len(matches) != 1:
        raise ValueError(f"{path}: expected exactly one {CHECKPOINT_HEADING} section")

    remainder = text[matches[0].end() :]
    next_heading = re.search(r"(?m)^##\s+", remainder)
    section = remainder[: next_heading.start()] if next_heading else remainder
    fence = re.search(r"```(?:yaml|yml)\s*\n", section, re.IGNORECASE)
    if not fence:
        raise ValueError(f"{path}: checkpoint has no fenced YAML block")
    block_end = section.find("```", fence.end())
    if block_end < 0:
        raise ValueError(f"{path}: checkpoint fence is not closed")
    return section[fence.end() : block_end].splitlines()


def _parse_top_level(data: dict[str, object], line: str, path: Path, line_number: int) -> str:
    if ":" not in line:
        raise ValueError(f"{path}:{line_number}: invalid checkpoint line")
    key, value = line.split(":", 1)
    key = key.strip()
    value = value.strip()
    if key in data:
        raise ValueError(f"{path}:{line_number}: duplicate key {key}")

    if key in LIST_KEYS or key == "validation":
        if value not in {"", "[]"}:
            raise ValueError(f"{path}:{line_number}: {key} must be a YAML list")
        data[key] = []
    elif key == "first_failure":
        if value:
            raise ValueError(f"{path}:{line_number}: first_failure must be a mapping")
        data[key] = {}
    else:
        data[key] = scalar(value)
    return key


def _parse_list_item(
    data: dict[str, object], key: str, line: str, indent: int, path: Path, line_number: int
) -> None:
    values = data.get(key)
    if indent != 2 or not line.startswith("- ") or not isinstance(values, list):
        raise ValueError(f"{path}:{line_number}: invalid list item under {key}")
    values.append(scalar(line[2:]))


def _parse_failure_item(
    data: dict[str, object], line: str, indent: int, path: Path, line_number: int
) -> None:
    mapping = data.get("first_failure")
    if indent != 2 or ":" not in line or not isinstance(mapping, dict):
        raise ValueError(f"{path}:{line_number}: invalid first_failure item")
    key, value = line.split(":", 1)
    mapping[key.strip()] = scalar(value)


def _parse_validation_item(
    data: dict[str, object],
    current: dict[str, str] | None,
    line: str,
    indent: int,
    path: Path,
    line_number: int,
) -> dict[str, str] | None:
    items = data.get("validation")
    if not isinstance(items, list):
        raise ValueError(f"{path}:{line_number}: invalid validation container")
    if indent == 2 and line.startswith("- ") and ":" in line[2:]:
        key, value = line[2:].split(":", 1)
        current = {key.strip(): scalar(value)}
        items.append(current)
        return current
    if indent == 4 and current is not None and ":" in line:
        key, value = line.split(":", 1)
        current[key.strip()] = scalar(value)
        return current
    raise ValueError(f"{path}:{line_number}: invalid validation item")


def parse_checkpoint(path: Path) -> dict[str, object] | None:
    lines = _checkpoint_lines(path)
    if lines is None:
        return None

    data: dict[str, object] = {}
    current_key: str | None = None
    current_validation: dict[str, str] | None = None
    for line_number, raw in enumerate(lines, start=1):
        if not raw.strip() or raw.lstrip().startswith("#"):
            continue
        indent = len(raw) - len(raw.lstrip(" "))
        line = raw.strip()
        if indent == 0:
            current_key = _parse_top_level(data, line, path, line_number)
            current_validation = None
        elif current_key in LIST_KEYS:
            _parse_list_item(data, current_key, line, indent, path, line_number)
        elif current_key == "first_failure":
            _parse_failure_item(data, line, indent, path, line_number)
        elif current_key == "validation":
            current_validation = _parse_validation_item(
                data, current_validation, line, indent, path, line_number
            )
        else:
            raise ValueError(f"{path}:{line_number}: nested value has no valid parent")
    return data


def normalized_fact(value: str) -> str:
    return " ".join(value.casefold().split())


def _validate_core(data: dict[str, object], contract: Contract, path: Path) -> list[str]:
    errors = [
        f"{path}: missing checkpoint field {key}"
        for key in contract.required_fields
        if key not in data
    ]
    if str(data.get("checkpoint_version", "")) != contract.version:
        errors.append(f"{path}: wrong checkpoint_version")
    if str(data.get("status", "")) not in contract.allowed_statuses:
        errors.append(f"{path}: unsupported status")
    if str(data.get("next_action", "")).strip().casefold() in PLACEHOLDER_NEXT_ACTIONS:
        errors.append(f"{path}: next_action must be concrete")
    return errors


def _validate_failure_and_validation(
    data: dict[str, object], contract: Contract, path: Path
) -> list[str]:
    errors: list[str] = []
    failure = data.get("first_failure")
    if not isinstance(failure, dict) or not all(
        str(failure.get(key, "")).strip() for key in ("marker", "evidence")
    ):
        errors.append(f"{path}: invalid first_failure")

    validation = data.get("validation")
    if not isinstance(validation, list):
        return [*errors, f"{path}: validation must be a list"]
    for index, item in enumerate(validation, start=1):
        if not isinstance(item, dict) or not all(
            str(item.get(key, "")).strip() for key in ("command", "result", "evidence")
        ):
            errors.append(f"{path}: invalid validation item {index}")
        elif str(item["result"]) not in contract.allowed_validation_results:
            errors.append(f"{path}: unsupported validation result")
    return errors


def _validate_compactness(data: dict[str, object], contract: Contract, path: Path) -> list[str]:
    errors: list[str] = []
    for key, limit in contract.compactness_limits.items():
        value = data.get(key, [])
        if not isinstance(value, list):
            errors.append(f"{path}: {key} must be a list")
        elif len(value) > limit:
            errors.append(f"{path}: {key} has {len(value)} items; compactness limit is {limit}")
    return errors


def _validate_evidence(data: dict[str, object], contract: Contract, path: Path) -> list[str]:
    evidence_sets = {
        key: {normalized_fact(str(item)) for item in data.get(key, []) if str(item).strip()}
        for key in contract.evidence_fields
    }
    errors: list[str] = []
    for index, left in enumerate(contract.evidence_fields):
        for right in contract.evidence_fields[index + 1 :]:
            overlap = evidence_sets[left] & evidence_sets[right]
            errors.extend(
                f"{path}: evidence fact appears in both {left} and {right}: {fact}"
                for fact in sorted(overlap)
            )
    return errors


def validate_checkpoint(data: dict[str, object], path: Path) -> list[str]:
    contract = load_contract()
    return [
        *_validate_core(data, contract, path),
        *_validate_failure_and_validation(data, contract, path),
        *_validate_compactness(data, contract, path),
        *_validate_evidence(data, contract, path),
    ]


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate compact agent task checkpoints")
    parser.add_argument("task", nargs="?", type=Path)
    parser.add_argument("--tasks", type=Path)
    parser.add_argument("--require-checkpoint", action="store_true")
    args = parser.parse_args()
    if bool(args.task) == bool(args.tasks):
        parser.error("provide exactly one task or --tasks directory")

    paths = [args.task] if args.task else sorted(args.tasks.glob("*.md"))
    errors: list[str] = []
    for path in paths:
        try:
            data = parse_checkpoint(path)
        except (OSError, ValueError) as exc:
            errors.append(str(exc))
            continue
        if data is None:
            if args.require_checkpoint:
                errors.append(f"{path}: missing {CHECKPOINT_HEADING}")
        else:
            errors.extend(validate_checkpoint(data, path))

    for error in errors:
        print(f"ERROR: {error}", file=sys.stderr)
    if errors:
        return 1
    print(f"Validated {len(paths)} checkpoint task(s).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
