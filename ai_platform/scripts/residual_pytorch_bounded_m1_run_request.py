#!/usr/bin/env python3
"""Generate and validate the exact one-shot residual PyTorch M1 execution request."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from ai_platform.scripts.residual_pytorch_bounded_m1_execution import (
    CONTRACT_PATH,
    CONTRACT_REPO_PATH,
    REPO_ROOT,
    REQUEST_REPO_PATH,
    ResidualPyTorchBoundedM1Error,
    canonical_inputs,
    sha256_file,
)


EXPECTED_REQUEST_ID = "residual-pytorch-bounded-m1-execution-v1"
EXPECTED_ACTION = "execute_residual_pytorch_bounded_m1_development_comparison"


class ResidualPyTorchBoundedM1RunRequestError(RuntimeError):
    """Raised when the one-shot request is not the exact canonical payload."""


def _track_binding(track: dict[str, Any]) -> dict[str, Any]:
    binding = {
        "track_id": track["track_id"],
        "manifest_path": track["manifest"],
        "manifest_sha256": sha256_file(REPO_ROOT / track["manifest"]),
        "config_path": track["config"],
        "config_sha256": sha256_file(REPO_ROOT / track["config"]),
        "freqai_model": track["freqai_model"],
        "model_path": track["model_file"],
        "model_sha256": sha256_file(REPO_ROOT / track["model_file"]),
        "identifier": track["identifier"],
    }
    underlying = track.get("underlying_model_file")
    if underlying:
        binding["underlying_model_path"] = underlying
        binding["underlying_model_sha256"] = sha256_file(REPO_ROOT / underlying)
    return binding


def canonical_run_request() -> dict[str, Any]:
    """Return the only request authorized by the bounded M1 workflow."""
    try:
        inputs = canonical_inputs()
    except ResidualPyTorchBoundedM1Error as exc:
        raise ResidualPyTorchBoundedM1RunRequestError(str(exc)) from exc
    contract = inputs["contract"]
    return {
        "schema_version": 1,
        "request_id": EXPECTED_REQUEST_ID,
        "action": EXPECTED_ACTION,
        "contract_path": CONTRACT_REPO_PATH,
        "contract_sha256": sha256_file(CONTRACT_PATH),
        "strategy_path": str(inputs["strategy_path"].relative_to(REPO_ROOT)),
        "strategy_sha256": sha256_file(inputs["strategy_path"]),
        "instrumentation_path": str(inputs["instrumentation_path"].relative_to(REPO_ROOT)),
        "instrumentation_sha256": sha256_file(inputs["instrumentation_path"]),
        "geometry": contract["geometry"],
        "market_data": contract["market_data"],
        "audit_track": _track_binding(contract["audit_track"]),
        "tracks": [_track_binding(track) for track in contract["tracks"]],
        "authorization": contract["authorization"],
    }


def load_run_request(path: Path) -> dict[str, Any]:
    try:
        request = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ResidualPyTorchBoundedM1RunRequestError(
            f"Unable to read bounded M1 run request {path}: {exc}"
        ) from exc
    if not isinstance(request, dict):
        raise ResidualPyTorchBoundedM1RunRequestError("Run request must contain a JSON object")
    expected = canonical_run_request()
    if request != expected:
        missing = sorted(set(expected) - set(request))
        extra = sorted(set(request) - set(expected))
        details = []
        if missing:
            details.append("missing=" + ",".join(missing))
        if extra:
            details.append("extra=" + ",".join(extra))
        suffix = f" ({'; '.join(details)})" if details else ""
        raise ResidualPyTorchBoundedM1RunRequestError(
            "Run request drifted from the canonical exact-byte inputs" + suffix
        )
    return request


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("request", nargs="?", type=Path)
    parser.add_argument("--print-canonical", action="store_true")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(sys.argv[1:] if argv is None else argv)
    if args.print_canonical:
        if args.request is not None:
            print("Do not pass a request with --print-canonical", file=sys.stderr)
            return 2
        try:
            request = canonical_run_request()
        except ResidualPyTorchBoundedM1RunRequestError as exc:
            print(f"Unable to build canonical run request: {exc}", file=sys.stderr)
            return 1
        print(json.dumps(request, indent=2, sort_keys=True))
        return 0
    if args.request is None:
        print("A request path is required unless --print-canonical is used", file=sys.stderr)
        return 2
    try:
        request = load_run_request(args.request)
    except ResidualPyTorchBoundedM1RunRequestError as exc:
        print(f"Bounded M1 run request invalid: {exc}", file=sys.stderr)
        return 1
    if args.request.as_posix() != REQUEST_REPO_PATH:
        print("Bounded M1 request path is not canonical", file=sys.stderr)
        return 1
    print(request["request_id"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
