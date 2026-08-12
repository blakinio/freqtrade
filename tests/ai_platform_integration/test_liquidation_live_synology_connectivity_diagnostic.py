from __future__ import annotations

import textwrap
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
WORKFLOW = ROOT / ".github/workflows/liquidations-live-synology.yml"


def _diagnostic_block(workflow: str) -> str:
    return workflow.split(
        "- name: Diagnose public WebSocket connectivity after deploy failure",
        maxsplit=1,
    )[1].split("- name: Publish final status", maxsplit=1)[0]


def test_failed_deploy_runs_bounded_secret_free_public_connectivity_diagnostic() -> None:
    workflow = WORKFLOW.read_text(encoding="utf-8")

    assert "Diagnose public WebSocket connectivity after deploy failure" in workflow
    assert "if: failure() && steps.deploy.outcome == 'failure'" in workflow
    assert "timeout-minutes: 3" in workflow
    assert "timeout 120s docker run --rm --interactive" in workflow
    assert 'image="local/liquid20-collector:sha-${GITHUB_SHA}"' in workflow
    assert '--name "liquid20-connectivity-${GITHUB_RUN_ID}-${GITHUB_RUN_ATTEMPT}"' in workflow
    assert '--label "freqtrade.task=FTAI-20260812-wh09-e2e-recovery-1396"' in workflow
    assert '--label "freqtrade.github-run-id=${GITHUB_RUN_ID}"' in workflow
    assert '--label "freqtrade.github-run-attempt=${GITHUB_RUN_ATTEMPT}"' in workflow
    assert "--read-only" in workflow
    assert "--cap-drop ALL" in workflow
    assert "--security-opt no-new-privileges:true" in workflow
    assert "--memory 256m" in workflow

    diagnostic_block = _diagnostic_block(workflow)
    for credential_name in (
        "BYBIT_API_KEY",
        "BYBIT_API_SECRET",
        "BINANCE_API_KEY",
        "BINANCE_API_SECRET",
        "OKX_API_KEY",
        "OKX_API_SECRET",
        "OKX_SECRET_KEY",
        "OKX_PASSPHRASE",
    ):
        assert credential_name not in diagnostic_block

    assert '"dns_error"] = error_signature(error)' in diagnostic_block
    assert '"tls_error"] = error_signature(error)' in diagnostic_block
    assert '"websocket_error"] = error_signature(error)' in diagnostic_block
    assert "str(error)" not in diagnostic_block
    assert '"protocol"] = classify_protocol(source, payload)' in diagnostic_block


def test_each_probe_is_process_isolated_and_terminable() -> None:
    workflow = WORKFLOW.read_text(encoding="utf-8")
    diagnostic_block = _diagnostic_block(workflow)

    assert 'multiprocessing.get_context("fork")' in diagnostic_block
    assert "context.Pipe(duplex=False)" in diagnostic_block
    assert "if receiver.poll(30):" in diagnostic_block
    assert "process.terminate()" in diagnostic_block
    assert "process.kill()" in diagnostic_block
    assert '"probe_process": "timeout"' in diagnostic_block


def test_embedded_connectivity_probe_is_valid_python() -> None:
    workflow = WORKFLOW.read_text(encoding="utf-8")
    diagnostic_block = _diagnostic_block(workflow)
    embedded = diagnostic_block.split("<<'PY'\n", maxsplit=1)[1].split(
        "\n          PY", maxsplit=1
    )[0]

    compile(textwrap.dedent(embedded), "liquidations-live-connectivity-diagnostic", "exec")


def test_connectivity_diagnostic_is_uploaded_as_operational_evidence() -> None:
    workflow = WORKFLOW.read_text(encoding="utf-8")

    upload_block = workflow.split("- name: Upload operational evidence", maxsplit=1)[1]
    assert "${{ runner.temp }}/liquidations-live-connectivity-diagnostic.json" in upload_block
    assert "retention-days: 30" in upload_block
