from __future__ import annotations

import json
import os
import re
import shutil
import tempfile
from pathlib import Path


REQUEST_PATH = Path(
    "ai_platform/market_data/run-requests/"
    "binance-spot-instrument-shadow-acceptance-20260729-v2.json"
)
EXPECTED_REQUEST = {
    "schema_version": 1,
    "request_id": "binance-spot-instrument-shadow-acceptance-20260729-v2",
    "run_id": "binance-spot-instrument-shadow-acceptance-20260729-v2-r1",
    "policy_id": "binance-spot-instrument-shadow-acceptance-v1",
    "source_id": "binance-spot",
    "request_url": "https://api.binance.com/api/v3/exchangeInfo?showPermissionSets=false",
    "duration_seconds": 86400,
    "sample_interval_seconds": 900,
    "host_id": "freqtrade-synology-staging",
    "host_class": "always_on_nonrestricted_linux_staging",
    "github_hosted_runner": False,
    "durable_storage_uri": (
        "file:///var/lib/freqtrade-staging-state/binance-spot-instrument-acceptance"
    ),
    "baseline_artifact_id": 8686988992,
    "baseline_artifact_digest": (
        "sha256:1862d17e8c117e31eec6688c8f34c32cce4a505ec125805cd095df6894cc4f6e"
    ),
    "public_only": True,
    "execution_enabled": False,
    "trading_credentials_present": False,
    "proxy_routing_present": False,
    "performance_research_authorized": False,
    "replay_authorized": False,
    "model_training_authorized": False,
    "strategy_research_authorized": False,
    "orders_submitted": 0,
    "production_source_enabled": False,
}


def _required_environment(name: str) -> str:
    value = os.environ.get(name, "").strip()
    if not value:
        raise SystemExit(f"BINANCE_ACCEPTANCE_V2_{name}_MISSING")
    return value


def _validate_request() -> str:
    payload = json.loads(REQUEST_PATH.read_text(encoding="utf-8"))
    if payload != EXPECTED_REQUEST:
        raise SystemExit("BINANCE_ACCEPTANCE_V2_REQUEST_CONTRACT_MISMATCH")
    for field in ("request_id", "run_id"):
        value = str(payload[field])
        if not re.fullmatch(r"[A-Za-z0-9._-]{3,100}", value):
            raise SystemExit(f"BINANCE_ACCEPTANCE_V2_{field.upper()}_INVALID")
    return str(payload["run_id"])


def _validate_runner() -> None:
    if _required_environment("RUNNER_NAME_VALUE") != "freqtrade-synology-staging":
        raise SystemExit("BINANCE_ACCEPTANCE_V2_RUNNER_NAME_MISMATCH")
    if _required_environment("RUNNER_OS_VALUE") != "Linux":
        raise SystemExit("BINANCE_ACCEPTANCE_V2_RUNNER_OS_MISMATCH")
    if _required_environment("RUNNER_ARCH_VALUE") not in {"X64", "ARM64"}:
        raise SystemExit("BINANCE_ACCEPTANCE_V2_RUNNER_ARCH_MISMATCH")


def _prepare_durable_storage(run_id: str) -> None:
    state_dir = Path(_required_environment("STATE_DIR"))
    durable_root = Path(_required_environment("DURABLE_ROOT"))
    durable_uri = _required_environment("DURABLE_URI")
    runner_temp = Path(_required_environment("RUNNER_TEMP_VALUE"))
    workspace = Path(_required_environment("GITHUB_WORKSPACE_VALUE"))

    if not state_dir.is_absolute() or not durable_root.is_absolute():
        raise SystemExit("BINANCE_ACCEPTANCE_V2_STORAGE_PATH_NOT_ABSOLUTE")
    if durable_root.parent != state_dir:
        raise SystemExit("BINANCE_ACCEPTANCE_V2_DURABLE_ROOT_OUTSIDE_STATE_DIR")
    if durable_uri != f"file://{durable_root}":
        raise SystemExit("BINANCE_ACCEPTANCE_V2_DURABLE_URI_MISMATCH")
    if durable_root == runner_temp or runner_temp in durable_root.parents:
        raise SystemExit("BINANCE_ACCEPTANCE_V2_DURABLE_ROOT_EPHEMERAL")
    if durable_root == workspace or workspace in durable_root.parents:
        raise SystemExit("BINANCE_ACCEPTANCE_V2_DURABLE_ROOT_EPHEMERAL")
    if not state_dir.is_dir() or not os.access(state_dir, os.W_OK):
        raise SystemExit("BINANCE_ACCEPTANCE_V2_STATE_DIR_UNAVAILABLE")

    durable_root.mkdir(mode=0o750, parents=True, exist_ok=True)
    if not durable_root.is_dir() or not os.access(durable_root, os.W_OK):
        raise SystemExit("BINANCE_ACCEPTANCE_V2_DURABLE_ROOT_NOT_WRITABLE")
    if (durable_root / run_id).exists():
        raise SystemExit("BINANCE_ACCEPTANCE_V2_RUN_ID_ALREADY_EXISTS")

    probe_dir = Path(tempfile.mkdtemp(prefix=".acceptance-v2-preflight-", dir=durable_root))
    try:
        source = probe_dir / "probe.tmp"
        target = probe_dir / "probe.sealed"
        payload = b"binance-spot-instrument-shadow-acceptance-v2\n"
        with source.open("xb") as handle:
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
        source.replace(target)
        if target.read_bytes() != payload:
            raise SystemExit("BINANCE_ACCEPTANCE_V2_DURABLE_ROOT_ATOMIC_IO_FAILED")
    finally:
        shutil.rmtree(probe_dir)


def main() -> None:
    _validate_runner()
    run_id = _validate_request()
    _prepare_durable_storage(run_id)
    output_path = Path(_required_environment("GITHUB_OUTPUT"))
    with output_path.open("a", encoding="utf-8") as output:
        output.write(f"run_id={run_id}\n")
    print("BINANCE_ACCEPTANCE_V2_STATIC_PREFLIGHT_PASS")


if __name__ == "__main__":
    main()
