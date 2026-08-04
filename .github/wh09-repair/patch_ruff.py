from __future__ import annotations

import argparse
from pathlib import Path


def _replace_once(text: str, old: str, new: str, *, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise SystemExit(f"{label}: expected exactly one match, found {count}")
    return text.replace(old, new, 1)


def patch_operator(path: Path) -> None:
    text = path.read_text(encoding="utf-8")
    text = _replace_once(
        text,
        "from decimal import Decimal, InvalidOperation\n",
        "from decimal import Decimal, InvalidOperation\nfrom itertools import pairwise\n",
        label="pairwise import",
    )
    text = _replace_once(
        text,
        "def _load_liquid20_live_root(\n",
        "def _load_liquid20_live_root(  # noqa: C901\n",
        label="live-root complexity declaration",
    )
    text = _replace_once(
        text,
        "def fetch_public_market_snapshot(\n",
        "def fetch_public_market_snapshot(  # noqa: C901\n",
        label="public-market complexity declaration",
    )
    text = _replace_once(
        text,
        "for previous, current in zip(\n"
        "            completed[:-1], completed[1:], strict=True\n"
        "        )",
        "for previous, current in pairwise(completed)",
        label="completed-candle pairwise iteration",
    )
    text = _replace_once(
        text,
        "for previous, current in zip(\n"
        "            atr_rows[:-1], atr_rows[1:], strict=True\n"
        "        )",
        "for previous, current in pairwise(atr_rows)",
        label="ATR pairwise iteration",
    )
    text = _replace_once(
        text,
        "for previous, current in zip(\n"
        "            closes[:-1], closes[1:], strict=True\n"
        "        )",
        "for previous, current in pairwise(closes)",
        label="return pairwise iteration",
    )
    compile(text, str(path), "exec")
    path.write_text(text, encoding="utf-8")


def patch_healthcheck(path: Path) -> None:
    text = path.read_text(encoding="utf-8")
    text = _replace_once(
        text,
        (
            "        if any(value > now_ms for value in "
            "(checked_at_ms, last_success_at_ms, last_observed_at_ms)):\n"
        ),
        "        if any(\n"
        "            value > now_ms\n"
        "            for value in (checked_at_ms, last_success_at_ms, last_observed_at_ms)\n"
        "        ):\n",
        label="health timestamp line wrapping",
    )
    compile(text, str(path), "exec")
    path.write_text(text, encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("operator", type=Path)
    parser.add_argument("healthcheck", type=Path)
    args = parser.parse_args()
    patch_operator(args.operator)
    patch_healthcheck(args.healthcheck)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
