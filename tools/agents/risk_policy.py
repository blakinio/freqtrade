#!/usr/bin/env python3
"""Deterministic risk-to-gate policy evaluator for repository tasks."""

from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Iterable
from pathlib import Path
from typing import Any


DEFAULT_POLICY = (
    Path(__file__).resolve().parents[2] / "docs/agents/RISK_BASED_EXECUTION_POLICY.json"
)


def load_policy(path: Path = DEFAULT_POLICY) -> dict[str, Any]:
    policy = json.loads(path.read_text(encoding="utf-8"))
    if policy.get("schema_version") != 1:
        raise ValueError("unsupported risk policy schema_version")
    if not isinstance(policy.get("baseline_gates"), list):
        raise ValueError("risk policy must define baseline_gates")
    if not isinstance(policy.get("risk_dimensions"), dict):
        raise ValueError("risk policy must define risk_dimensions")
    return policy


def _unique(values: Iterable[str]) -> list[str]:
    return list(dict.fromkeys(values))


def derive_policy(
    risks: Iterable[str],
    *,
    policy: dict[str, Any] | None = None,
) -> dict[str, Any]:
    policy = policy or load_policy()
    dimensions = policy["risk_dimensions"]
    selected = sorted({risk.strip() for risk in risks if risk.strip()})
    unknown = sorted(set(selected) - set(dimensions))
    if unknown:
        raise ValueError(f"unknown risk dimension(s): {', '.join(unknown)}")

    escalation_gates: list[str] = []
    stop_reasons: list[str] = []
    for risk in selected:
        definition = dimensions[risk]
        escalation_gates.extend(str(gate) for gate in definition.get("gates", []))
        if definition.get("stop") is True:
            stop_reasons.append(str(definition.get("reason") or f"{risk} is stop-gated"))

    baseline = [str(gate) for gate in policy["baseline_gates"]]
    escalation = _unique(escalation_gates)
    return {
        "schema_version": policy["schema_version"],
        "selected_risks": selected,
        "baseline_gates": baseline,
        "escalation_gates": escalation,
        "required_gates": _unique([*baseline, *escalation]),
        "stopped": bool(stop_reasons),
        "stop_reasons": stop_reasons,
    }


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--policy", type=Path, default=DEFAULT_POLICY)
    parser.add_argument("--risk", action="append", default=[])
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        result = derive_policy(args.risk, policy=load_policy(args.policy))
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        return 2
    print(json.dumps(result, indent=2, sort_keys=True))
    return 2 if result["stopped"] else 0


if __name__ == "__main__":
    sys.exit(main())
