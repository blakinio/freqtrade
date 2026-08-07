from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def test_wickhunter_runtime_requires_exact_liquid20_reader_group() -> None:
    compose = (ROOT / "deploy/synology/wickhunter-paper-runtime/compose.yaml").read_text(
        encoding="utf-8"
    )
    readme = (ROOT / "deploy/synology/wickhunter-paper-runtime/README.md").read_text(
        encoding="utf-8"
    )
    preflight = (ROOT / "deploy/synology/wickhunter-paper-runtime/V13_PREFLIGHT.md").read_text(
        encoding="utf-8"
    )

    assert 'user: "65532:65532"' in compose
    assert "group_add:" in compose
    assert (
        '"${LIQUID20_READER_GID:?set exact GID of LIQUID20_LIVE_HOST}"' in compose
    )
    assert "LIQUID20_LIVE_HOST:?set read-only Liquid20 live root" in compose
    assert "read_only: true" in compose
    assert "privileged: false" in compose
    assert "cap_drop:\n      - ALL" in compose

    assert "LIQUID20_READER_GID" in readme
    assert 'stat -c %g "$LIQUID20_LIVE_HOST"' in readme
    assert "supplementary group" in readme
    assert "world-readable" in readme

    assert 'stat -c %g "$LIQUID20_LIVE_HOST"' in preflight
    assert "supplementary group" in preflight
    assert "world-readable" in preflight
    assert "atomically republished" in preflight
