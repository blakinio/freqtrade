#!/usr/bin/env python3
"""Generate and validate the exact one-shot residual PyTorch M1 v3 request."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from importlib import import_module
from pathlib import Path
from types import ModuleType
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[2]
CONTRACT_REPO_PATH = (
    "ai_platform/experimental_model_research/"
    "residual-pytorch-bounded-m1-generalization-contract-v3.json"
)
CONTRACT_PATH = REPO_ROOT / CONTRACT_REPO_PATH
REQUEST_REPO_PATH = (
    "ai_platform/experimental_model_research/run-requests/"
    "residual-pytorch-bounded-m1-generalization-v3.json"
)
EXPECTED_REQUEST_ID = "residual-pytorch-bounded-m1-generalization-v3"
EXPECTED_ACTION = "execute_residual_pytorch_bounded_m1_v3_generalization"


class ResidualPyTorchBoundedM1V3RunRequestError(RuntimeError):
    pass


def _execution_module() -> ModuleType:
    try:
        return import_module("ai_platform.scripts.residual_pytorch_bounded_m1_v3_generalization")
    except ModuleNotFoundError as exc:
        if exc.name in {"numpy", "pandas"}:
            raise ResidualPyTorchBoundedM1V3RunRequestError(
                "Canonical request generation requires the numeric validation profile"
            ) from exc
        raise


def _sha256_file(path: Path) -> str:
    try:
        return hashlib.sha256(path.read_bytes()).hexdigest()
    except OSError as exc:
        raise ResidualPyTorchBoundedM1V3RunRequestError(
            f"Unable to hash canonical input {path}: {exc}"
        ) from exc


def _track_binding(track: dict[str, Any]) -> dict[str, Any]:
    binding = {
        "track_id": track["track_id"],
        "manifest_path": track["manifest"],
        "manifest_sha256": _sha256_file(REPO_ROOT / track["manifest"]),
        "config_path": track["config"],
        "config_sha256": _sha256_file(REPO_ROOT / track["config"]),
        "freqai_model": track["freqai_model"],
        "model_path": track["model_file"],
        "model_sha256": _sha256_file(REPO_ROOT / track["model_file"]),
        "identifier": track["identifier"],
    }
    underlying = track.get("underlying_model_file")
    if underlying:
        binding["underlying_model_path"] = underlying
        binding["underlying_model_sha256"] = _sha256_file(REPO_ROOT / underlying)
    return binding


def canonical_run_request() -> dict[str, Any]:
    execution = _execution_module()
    try:
        inputs = execution.canonical_inputs()
    except execution.ResidualPyTorchBoundedM1Error as exc:
        raise ResidualPyTorchBoundedM1V3RunRequestError(str(exc)) from exc
    contract = inputs["contract"]
    return {
        "schema_version": 1,
        "request_id": EXPECTED_REQUEST_ID,
        "action": EXPECTED_ACTION,
        "contract_path": CONTRACT_REPO_PATH,
        "contract_sha256": _sha256_file(CONTRACT_PATH),
        "strategy_path": str(inputs["strategy_path"].relative_to(REPO_ROOT)),
        "strategy_sha256": _sha256_file(inputs["strategy_path"]),
        "instrumentation_path": str(inputs["instrumentation_path"].relative_to(REPO_ROOT)),
        "instrumentation_sha256": _sha256_file(inputs["instrumentation_path"]),
        "geometry": contract["geometry"],
        "market_data": contract["market_data"],
        "audit_track": _track_binding(contract["audit_track"]),
        "tracks": [_track_binding(track) for track in contract["tracks"]],
        "authorization": contract["authorization"],
        "remediation": contract["remediation"],
        "generalization": contract["generalization"],
    }


def load_run_request(path: Path) -> dict[str, Any]:
    try:
        request = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ResidualPyTorchBoundedM1V3RunRequestError(
            f"Unable to read bounded M1 v3 run request {path}: {exc}"
        ) from exc
    if not isinstance(request, dict):
        raise ResidualPyTorchBoundedM1V3RunRequestError("Run request must contain a JSON object")
    if request != canonical_run_request():
        raise ResidualPyTorchBoundedM1V3RunRequestError(
            "Run request drifted from the canonical exact-byte inputs"
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
        except ResidualPyTorchBoundedM1V3RunRequestError as exc:
            print(f"Unable to build canonical run request: {exc}", file=sys.stderr)
            return 1
        print(json.dumps(request, indent=2, sort_keys=True))
        return 0
    if args.request is None:
        print("A request path is required unless --print-canonical is used", file=sys.stderr)
        return 2
    try:
        request = load_run_request(args.request)
    except ResidualPyTorchBoundedM1V3RunRequestError as exc:
        print(f"Bounded M1 v3 run request invalid: {exc}", file=sys.stderr)
        return 1
    if args.request.as_posix() != REQUEST_REPO_PATH:
        print("Bounded M1 v3 request path is not canonical", file=sys.stderr)
        return 1
    print(request["request_id"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
