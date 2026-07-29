from __future__ import annotations

import json
from pathlib import Path
from typing import Self

import pytest

from ai_platform.market_data import binance_spot_instrument_acceptance_incremental as incremental
from ai_platform.market_data.binance_spot_instrument_acceptance import (
    POLICY_PATH,
    evaluate_package,
)
from ai_platform.market_data.binance_spot_instrument_smoke import (
    BINANCE_SPOT_REDUCED_PAYLOAD_URL,
)
from ai_platform.market_data.common import canonical_json_bytes


COMMIT = "a" * 40
REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
WORKFLOW_PATH = (
    REPOSITORY_ROOT
    / ".github/workflows/ai-platform-binance-spot-instrument-shadow-acceptance-v3.yml"
)
BLOCKING_V2_WORKFLOW_PATH = (
    REPOSITORY_ROOT
    / ".github/workflows/ai-platform-binance-spot-instrument-shadow-acceptance-v2.yml"
)
TRIGGER_PATH = (
    "ai_platform/market_data/run-requests/"
    "binance-spot-instrument-shadow-acceptance-20260729-v3.json"
)
INTERVAL_NS = 900 * 1_000_000_000


def _payload() -> dict[str, object]:
    return {
        "timezone": "UTC",
        "serverTime": 1,
        "symbols": [
            {
                "symbol": "BTCUSDT",
                "status": "TRADING",
                "baseAsset": "BTC",
                "quoteAsset": "USDT",
                "filters": [
                    {"filterType": "PRICE_FILTER", "tickSize": "0.1"},
                    {"filterType": "LOT_SIZE", "stepSize": "0.00001"},
                ],
            },
            {
                "symbol": "ETHUSDT",
                "status": "TRADING",
                "baseAsset": "ETH",
                "quoteAsset": "USDT",
                "filters": [
                    {"filterType": "PRICE_FILTER", "tickSize": "0.01"},
                    {"filterType": "LOT_SIZE", "stepSize": "0.0001"},
                ],
            },
        ],
    }


class FakeResponse:
    status = 200

    def __init__(self, payload: bytes) -> None:
        self.payload = payload
        self.headers = {
            "Content-Type": "application/json;charset=UTF-8",
            "Content-Length": str(len(payload)),
        }

    def geturl(self) -> str:
        return BINANCE_SPOT_REDUCED_PAYLOAD_URL

    def read(self, amount: int = -1) -> bytes:
        return self.payload if amount < 0 else self.payload[:amount]

    def __enter__(self) -> Self:
        return self

    def __exit__(self, exc_type: object, exc: object, traceback: object) -> None:
        return None


class FakeOpener:
    def __init__(self) -> None:
        self.calls = 0

    def __call__(self, request: object, *, timeout: float, context: object) -> FakeResponse:
        del request, context
        assert timeout == 20.0
        self.calls += 1
        payload = _payload()
        payload["serverTime"] = self.calls
        return FakeResponse(canonical_json_bytes(payload))


class Clock:
    def __init__(self) -> None:
        self.value = 1_800_000_000 * 1_000_000_000
        self.value -= self.value % INTERVAL_NS

    def now(self) -> int:
        return self.value

    def advance(self) -> None:
        self.value += INTERVAL_NS


def _policy_path(tmp_path: Path) -> Path:
    policy = json.loads((REPOSITORY_ROOT / POLICY_PATH).read_text(encoding="utf-8"))
    policy["thresholds"].update(
        {
            "minimum_successful_samples": 97,
            "minimum_availability_ratio": 1.0,
            "maximum_consecutive_failures": 0,
            "maximum_transport_failures": 0,
            "maximum_parse_failures": 0,
            "minimum_instrument_count": 2,
            "maximum_instrument_count": 10,
            "minimum_active_instrument_count": 2,
            "maximum_consecutive_catalog_count_change_ratio": 0.01,
        }
    )
    path = tmp_path / "policy.json"
    path.write_bytes(canonical_json_bytes(policy) + b"\n")
    return path


def _request_path(
    tmp_path: Path,
    durable_root: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> Path:
    request = dict(incremental.EXPECTED_REQUEST)
    request["durable_storage_uri"] = f"file://{durable_root}"
    monkeypatch.setattr(incremental, "EXPECTED_REQUEST", request)
    path = tmp_path / "request.json"
    path.write_bytes(canonical_json_bytes(request) + b"\n")
    return path


def test_incremental_acceptance_collects_one_due_sample_per_invocation(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    durable_root = tmp_path / "durable"
    policy_path = _policy_path(tmp_path)
    request_path = _request_path(tmp_path, durable_root, monkeypatch)
    clock = Clock()
    opener = FakeOpener()

    initialized = incremental.initialize_incremental_acceptance(
        request_path=request_path,
        policy_path=policy_path,
        durable_root=durable_root,
        collector_commit=COMMIT,
        environment={},
        wall_clock_ns=clock.now,
    )
    assert initialized["status"] == "initialized"
    assert initialized["next_sample_index"] == 0

    first = incremental.collect_due_incremental_sample(
        policy_path=policy_path,
        durable_root=durable_root,
        environment={},
        opener=opener,
        wall_clock_ns=clock.now,
    )
    assert first["status"] == "sampled"
    assert first["sample_index"] == 0
    assert opener.calls == 1

    early = incremental.collect_due_incremental_sample(
        policy_path=policy_path,
        durable_root=durable_root,
        environment={},
        opener=opener,
        wall_clock_ns=clock.now,
    )
    assert early["status"] == "not_due"
    assert opener.calls == 1


def test_incremental_acceptance_finalizes_after_97_spaced_invocations(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    durable_root = tmp_path / "durable"
    policy_path = _policy_path(tmp_path)
    request_path = _request_path(tmp_path, durable_root, monkeypatch)
    clock = Clock()
    opener = FakeOpener()

    initialized = incremental.initialize_incremental_acceptance(
        request_path=request_path,
        policy_path=policy_path,
        durable_root=durable_root,
        collector_commit=COMMIT,
        environment={},
        wall_clock_ns=clock.now,
    )
    run_root = Path(str(initialized["run_root"]))
    result: dict[str, object] = {}
    for index in range(97):
        result = incremental.collect_due_incremental_sample(
            policy_path=policy_path,
            durable_root=durable_root,
            environment={},
            opener=opener,
            wall_clock_ns=clock.now,
        )
        if index < 96:
            assert result["status"] == "sampled"
            assert result["sample_index"] == index
            clock.advance()

    assert result["status"] == "finalized"
    assert result["outcome"] == "accepted"
    assert opener.calls == 97
    assert not (durable_root / incremental.ACTIVE_POINTER_NAME).exists()
    assert len(list((run_root / "samples").glob("*/sample-report.json"))) == 97
    assert evaluate_package(run_root=run_root, policy_path=policy_path)["outcome"] == "accepted"


def test_interrupted_attempt_becomes_failure_without_retry(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    durable_root = tmp_path / "durable"
    policy_path = _policy_path(tmp_path)
    request_path = _request_path(tmp_path, durable_root, monkeypatch)
    clock = Clock()
    opener = FakeOpener()

    initialized = incremental.initialize_incremental_acceptance(
        request_path=request_path,
        policy_path=policy_path,
        durable_root=durable_root,
        collector_commit=COMMIT,
        environment={},
        wall_clock_ns=clock.now,
    )
    run_root = Path(str(initialized["run_root"]))
    sample_root = run_root / "samples/0000"
    sample_root.mkdir()
    marker = sample_root / incremental.ATTEMPT_MARKER_NAME
    marker.write_text("{}\n", encoding="utf-8")
    (sample_root / "raw-response.json").write_text("partial", encoding="utf-8")

    recovered = incremental.collect_due_incremental_sample(
        policy_path=policy_path,
        durable_root=durable_root,
        environment={},
        opener=opener,
        wall_clock_ns=clock.now,
    )
    report = json.loads((sample_root / "sample-report.json").read_text(encoding="utf-8"))

    assert recovered["status"] == "sampled"
    assert report["status"] == "fail"
    assert report["failure_stage"] == "interrupted"
    assert report["attempt_count"] == 1
    assert opener.calls == 0
    assert not marker.exists()
    assert not (sample_root / "raw-response.json").exists()


def test_incremental_initialization_refuses_parallel_active_run(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    durable_root = tmp_path / "durable"
    policy_path = _policy_path(tmp_path)
    request_path = _request_path(tmp_path, durable_root, monkeypatch)
    clock = Clock()

    incremental.initialize_incremental_acceptance(
        request_path=request_path,
        policy_path=policy_path,
        durable_root=durable_root,
        collector_commit=COMMIT,
        environment={},
        wall_clock_ns=clock.now,
    )
    with pytest.raises(FileExistsError, match="active Binance acceptance v3"):
        incremental.initialize_incremental_acceptance(
            request_path=request_path,
            policy_path=policy_path,
            durable_root=durable_root,
            collector_commit=COMMIT,
            environment={},
            wall_clock_ns=clock.now,
        )


def test_v3_workflow_releases_runner_between_samples() -> None:
    workflow = WORKFLOW_PATH.read_text(encoding="utf-8")

    assert not BLOCKING_V2_WORKFLOW_PATH.exists()
    assert 'cron: "*/15 * * * *"' in workflow
    assert f'- "{TRIGGER_PATH}"' in workflow
    assert f"expected=$'A\t{TRIGGER_PATH}'" in workflow
    assert workflow.count("timeout-minutes: 10") == 2
    assert "timeout-minutes: 1500" not in workflow
    assert "Run frozen 24-hour acceptance package" not in workflow
    assert "Collect at most one due sample" in workflow
    assert "cancel-in-progress: false" in workflow
    assert "runs-on: [freqtrade-staging]" in workflow
    assert "pull_request_target" not in workflow
    assert "workflow_dispatch" not in workflow
    assert "sleep " not in workflow


def test_v3_workflow_uploads_only_bounded_terminal_metadata() -> None:
    workflow = WORKFLOW_PATH.read_text(encoding="utf-8")
    upload = workflow.split("- name: Upload bounded terminal metadata evidence", 1)[1]
    upload = upload.split("- name: Remove isolated acceptance runtime", 1)[0]

    assert "sample-report.json" in upload
    assert "incremental-state.json" in upload
    assert "binance-spot-instrument-acceptance-report.json" in upload
    assert "raw-response.json" not in upload
    assert "instrument-catalog-snapshot.json" not in upload
