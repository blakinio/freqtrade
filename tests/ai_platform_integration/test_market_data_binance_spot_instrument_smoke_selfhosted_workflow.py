from pathlib import Path


REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
WORKFLOW_PATH = (
    REPOSITORY_ROOT / ".github/workflows/ai-platform-binance-spot-instrument-smoke-selfhosted.yml"
)
TRIGGER_PATH = (
    "ai_platform/market_data/run-requests/binance-spot-instrument-smoke-selfhosted-v1.json"
)


def _workflow() -> str:
    return WORKFLOW_PATH.read_text(encoding="utf-8")


def test_selfhosted_workflow_is_exact_request_gated() -> None:
    workflow = _workflow()

    assert "types: [opened]" in workflow
    assert f'- "{TRIGGER_PATH}"' in workflow
    assert f"expected=$'A\\t{TRIGGER_PATH}'" in workflow
    assert "pull_request_target" not in workflow
    assert "workflow_dispatch" not in workflow
    assert "schedule:" not in workflow


def test_selfhosted_workflow_requires_owner_managed_runner() -> None:
    workflow = _workflow()

    assert "runs-on: [self-hosted, Linux, freqtrade-staging]" in workflow
    assert "environment: synology-staging" in workflow
    assert '[[ "$RUNNER_NAME_VALUE" == "freqtrade-synology-staging" ]]' in workflow
    assert '[[ "$RUNNER_OS_VALUE" == "Linux" ]]' in workflow
    assert '"X64" || "$RUNNER_ARCH_VALUE" == "ARM64"' in workflow


def test_selfhosted_workflow_refuses_credentials_and_proxies() -> None:
    workflow = _workflow()

    for name in (
        "BINANCE_API_KEY",
        "BINANCE_API_SECRET",
        "BYBIT_API_KEY",
        "OKX_API_KEY",
        "FREQTRADE__EXCHANGE__KEY",
        "HTTP_PROXY",
        "HTTPS_PROXY",
        "ALL_PROXY",
        "http_proxy",
        "https_proxy",
        "all_proxy",
    ):
        assert name in workflow


def test_selfhosted_workflow_reuses_frozen_smoke_contract() -> None:
    workflow = _workflow()

    assert "ai_platform/market_data/binance-spot-instrument-smoke-policy-v1.json" in workflow
    assert "ai_platform.market_data.binance_spot_instrument_smoke" in workflow
    assert '"jsonschema==4.26.0"' in workflow
    assert "api1.binance.com" not in workflow
    assert "api-gcp.binance.com" not in workflow
    assert "data-api.binance.vision" not in workflow
    assert "curl " not in workflow
    assert "wget " not in workflow


def test_selfhosted_workflow_preserves_one_shot_evidence() -> None:
    workflow = _workflow()

    assert "persist-credentials: false" in workflow
    assert "cancel-in-progress: false" in workflow
    assert "Upload bounded failure evidence" in workflow
    assert "Upload immutable smoke evidence" in workflow
    assert "retention-days: 30" in workflow
    assert "Remove isolated smoke runtime" in workflow
