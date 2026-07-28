from __future__ import annotations

import json
from pathlib import Path
from typing import Self

import pytest

from ai_platform.market_data.binance_spot_instrument_acceptance import (
    POLICY_PATH,
    BinanceSpotInstrumentAcceptancePolicy,
    evaluate_package,
    run_acceptance,
    validate_request,
)
from ai_platform.market_data.binance_spot_instrument_smoke import (
    BINANCE_SPOT_REDUCED_PAYLOAD_URL,
)
from ai_platform.market_data.common import canonical_json_bytes


COMMIT = "a" * 40
REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
WORKFLOW_PATH = (
    REPOSITORY_ROOT / ".github/workflows/ai-platform-binance-spot-instrument-shadow-acceptance.yml"
)
DOCUMENTATION_PATH = (
    REPOSITORY_ROOT / "docs/ai_platform/market_data/BINANCE_SPOT_INSTRUMENT_SHADOW_ACCEPTANCE.md"
)
TRIGGER_PATH = (
    "ai_platform/market_data/run-requests/"
    "binance-spot-instrument-shadow-acceptance-20260728-v1.json"
)


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


def _request() -> dict[str, object]:
    return {
        "schema_version": 1,
        "request_id": "binance-spot-instrument-shadow-acceptance-test-v1",
        "run_id": "binance-spot-instrument-shadow-acceptance-test-r1",
        "policy_id": "binance-spot-instrument-shadow-acceptance-v1",
        "source_id": "binance-spot",
        "request_url": BINANCE_SPOT_REDUCED_PAYLOAD_URL,
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


def _test_policy(tmp_path: Path) -> Path:
    policy = json.loads((REPOSITORY_ROOT / POLICY_PATH).read_text(encoding="utf-8"))
    thresholds = policy["thresholds"]
    thresholds.update(
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


def _write_request(tmp_path: Path) -> Path:
    path = tmp_path / "request.json"
    path.write_bytes(canonical_json_bytes(_request()) + b"\n")
    return path


class FakeClock:
    def __init__(self) -> None:
        self.value = 0.0
        self.base_ns = 1_800_000_000_000_000_000

    def monotonic(self) -> float:
        return self.value

    def sleep(self, seconds: float) -> None:
        self.value += max(0.0, seconds)

    def wall_ns(self) -> int:
        return self.base_ns + int(self.value * 1_000_000_000)


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
    def __init__(self, *, invalid_call: int | None = None) -> None:
        self.calls = 0
        self.invalid_call = invalid_call

    def __call__(self, request: object, *, timeout: float, context: object) -> FakeResponse:
        del request, context
        assert timeout == 20.0
        self.calls += 1
        payload = _payload()
        payload["serverTime"] = self.calls
        if self.calls == self.invalid_call:
            payload["symbols"] = [
                {
                    "symbol": "BTCUSDT",
                    "status": "TRADING",
                    "baseAsset": "BTC",
                    "quoteAsset": "USDT",
                    "filters": [],
                }
            ]
        return FakeResponse(canonical_json_bytes(payload))


def _run_package(
    tmp_path: Path,
    *,
    invalid_call: int | None = None,
) -> tuple[dict[str, object], Path, Path, FakeOpener]:
    policy_path = _test_policy(tmp_path)
    request_path = _write_request(tmp_path)
    output = tmp_path / "acceptance"
    opener = FakeOpener(invalid_call=invalid_call)
    clock = FakeClock()
    report = run_acceptance(
        request_path=request_path,
        policy_path=policy_path,
        output_root=output,
        collector_commit=COMMIT,
        environment={},
        opener=opener,
        sleeper=clock.sleep,
        monotonic=clock.monotonic,
        wall_clock_ns=clock.wall_ns,
    )
    return report, output, policy_path, opener


def test_frozen_policy_and_request_contract() -> None:
    policy = BinanceSpotInstrumentAcceptancePolicy.load(REPOSITORY_ROOT / POLICY_PATH)
    request = validate_request(_request(), policy=policy)

    assert policy.minimum_duration_seconds == 86400
    assert policy.sample_interval_seconds == 900
    assert policy.retries_per_sample == 0
    assert policy.thresholds.minimum_attempted_samples == 97
    assert policy.thresholds.required_active_native_symbols == ("BTCUSDT", "ETHUSDT")
    assert request.baseline_artifact_id == 8686988992

    shortened = _request()
    shortened["duration_seconds"] = 86399
    with pytest.raises(ValueError, match="shorter than policy minimum"):
        validate_request(shortened, policy=policy)

    enabled = _request()
    enabled["production_source_enabled"] = True
    with pytest.raises(ValueError, match="production_source_enabled"):
        validate_request(enabled, policy=policy)


def test_acceptance_run_and_independent_evaluator_accept_complete_package(
    tmp_path: Path,
) -> None:
    report, output, policy_path, opener = _run_package(tmp_path)

    assert opener.calls == 97
    assert report["outcome"] == "accepted"
    assert report["source_acceptance"] is False
    assert report["production_source_enabled"] is False
    assert len(list((output / "samples").glob("*/sample-report.json"))) == 97
    assert len(list((output / "samples").glob("*/raw-response.json"))) == 97
    assert len(list((output / "samples").glob("*/instrument-catalog-snapshot.json"))) == 97

    independently_verified = evaluate_package(run_root=output, policy_path=policy_path)
    assert independently_verified == report


def test_parse_failure_rejects_without_retry_or_partial_raw_payload(tmp_path: Path) -> None:
    report, output, policy_path, opener = _run_package(tmp_path, invalid_call=50)

    assert opener.calls == 97
    assert report["outcome"] == "rejected"
    failed_root = output / "samples/0049"
    failed = json.loads((failed_root / "sample-report.json").read_text())
    assert failed["failure_stage"] == "parse_and_normalize"
    assert failed["attempt_count"] == 1
    assert failed["raw_payload_persisted"] is False
    assert not (failed_root / "raw-response.json").exists()
    assert not (failed_root / "instrument-catalog-snapshot.json").exists()
    assert evaluate_package(run_root=output, policy_path=policy_path)["outcome"] == "rejected"


def test_acceptance_refuses_credentials_and_proxy_before_transport(tmp_path: Path) -> None:
    policy_path = _test_policy(tmp_path)
    request_path = _write_request(tmp_path)
    opener = FakeOpener()

    for environment, match in (
        ({"BINANCE_API_KEY": "secret"}, "BINANCE_API_KEY"),
        ({"HTTPS_PROXY": "http://proxy.invalid"}, "HTTPS_PROXY"),
    ):
        with pytest.raises(RuntimeError, match=match):
            run_acceptance(
                request_path=request_path,
                policy_path=policy_path,
                output_root=tmp_path / f"blocked-{match}",
                collector_commit=COMMIT,
                environment=environment,
                opener=opener,
            )
    assert opener.calls == 0


def test_independent_evaluator_rejects_tampered_durable_raw_evidence(
    tmp_path: Path,
) -> None:
    _, output, policy_path, _ = _run_package(tmp_path)
    raw_path = output / "samples/0000/raw-response.json"
    raw_path.write_bytes(raw_path.read_bytes() + b" ")

    with pytest.raises(ValueError, match="manifest artifact hash mismatch"):
        evaluate_package(run_root=output, policy_path=policy_path)


def test_workflow_is_exact_one_file_owner_runner_gated() -> None:
    workflow = WORKFLOW_PATH.read_text(encoding="utf-8")

    assert "types: [opened]" in workflow
    assert f'- "{TRIGGER_PATH}"' in workflow
    assert f"expected=$'A\\t{TRIGGER_PATH}'" in workflow
    assert "runs-on: [freqtrade-staging]" in workflow
    assert "environment: synology-staging" in workflow
    assert "ACCEPTANCE_HOST_ID: freqtrade-synology-staging" in workflow
    assert '[[ "$RUNNER_ARCH_VALUE" != "X64" && "$RUNNER_ARCH_VALUE" != "ARM64" ]]' in workflow
    assert "pull_request_target" not in workflow
    assert "workflow_dispatch" not in workflow
    assert "schedule:" not in workflow


def test_workflow_preserves_durable_public_only_zero_order_boundary() -> None:
    workflow = WORKFLOW_PATH.read_text(encoding="utf-8")

    assert "STATE_DIR: /var/lib/freqtrade-staging-state" in workflow
    assert (
        "DURABLE_ROOT: /var/lib/freqtrade-staging-state/"
        "binance-spot-instrument-acceptance" in workflow
    )
    assert 'duration_seconds": 86400' in workflow
    assert 'sample_interval_seconds": 900' in workflow
    assert 'production_source_enabled": False' in workflow
    assert 'orders_submitted": 0' in workflow
    assert "BINANCE_API_KEY" in workflow
    assert "HTTPS_PROXY" in workflow
    assert "curl " not in workflow
    assert "wget " not in workflow
    assert "api1.binance.com" not in workflow
    assert "data-api.binance.vision" not in workflow


def test_workflow_uploads_metadata_but_keeps_raw_package_durable() -> None:
    workflow = WORKFLOW_PATH.read_text(encoding="utf-8")

    assert "samples/*/sample-report.json" in workflow
    assert "binance-spot-instrument-acceptance-summary.json" in workflow
    assert "binance-spot-instrument-acceptance-manifest.json" in workflow
    assert "binance-spot-instrument-acceptance-report.json" in workflow
    assert "artifact-sha256.txt" in workflow
    upload_section = workflow.split("- name: Upload bounded metadata evidence", 1)[1]
    upload_section = upload_section.split("- name: Remove isolated acceptance runtime", 1)[0]
    assert "raw-response.json" not in upload_section
    assert "instrument-catalog-snapshot.json" not in upload_section
    assert "production source remains disabled" in workflow


def test_documentation_matches_frozen_acceptance_boundary() -> None:
    documentation = DOCUMENTATION_PATH.read_text(encoding="utf-8")

    for expected in (
        "24 hours",
        "15 minutes",
        "97",
        "8686988992",
        "freqtrade-synology-staging",
        "/var/lib/freqtrade-staging-state/binance-spot-instrument-acceptance",
        "accepted",
        "rejected",
        "inconclusive_incomplete_window",
        "production_source_enabled = false",
    ):
        assert expected in documentation
