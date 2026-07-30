from __future__ import annotations

from ai_platform.scripts.liquidation_live_stream_okx import okx_credentials_present


def test_okx_live_source_requires_no_credentials() -> None:
    empty = {
        "OKX_API_KEY": "",
        "OKX_API_SECRET": "",
        "OKX_SECRET_KEY": "",
        "OKX_PASSPHRASE": "",
    }
    assert okx_credentials_present(empty) is False

    for name in empty:
        environment = dict(empty)
        environment[name] = "must-not-be-present"
        assert okx_credentials_present(environment) is True
