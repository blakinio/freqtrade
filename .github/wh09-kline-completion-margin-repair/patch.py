from __future__ import annotations

from pathlib import Path


OPERATOR = Path("ai_platform/wickhunter/candidate_paper_runtime_operator.py")
TESTS = Path("tests/ai_platform_integration/test_wickhunter_candidate_paper_runtime_operator.py")
TASK = Path("docs/agents/tasks/FTAI-20260803-wickhunter-wh09-paper-runtime-operator-v1.md")


def replace_once(path: Path, old: str, new: str) -> None:
    text = path.read_text(encoding="utf-8")
    count = text.count(old)
    if count != 1:
        raise SystemExit(f"{path}: expected one marker, found {count}: {old[:180]!r}")
    path.write_text(text.replace(old, new, 1), encoding="utf-8")


def main() -> None:
    replace_once(
        OPERATOR,
        "MAX_PUBLIC_MARKET_WORKERS = 8\n",
        "MAX_PUBLIC_MARKET_WORKERS = 8\nPUBLIC_KLINE_LIMIT = 1500\n",
    )
    replace_once(
        OPERATOR,
        '{"symbol": normalized, "interval": "1m", "limit": 1441},',
        '{"symbol": normalized, "interval": "1m", "limit": PUBLIC_KLINE_LIMIT},',
    )

    replace_once(
        TESTS,
        '''    def __init__(self, *, redirect: bool = False, gap: bool = False) -> None:
        self.redirect = redirect
        self.gap = gap
        self.requests: list[Any] = []

    def _klines(self) -> list[list[object]]:
        rows: list[list[object]] = []
        for index in range(1441):
            close_ms = NOW_MS - (1440 - index) * 60_000 - 1_000
''',
        '''    def __init__(
        self,
        *,
        redirect: bool = False,
        gap: bool = False,
        future_rows: int = 0,
    ) -> None:
        if not 0 <= future_rows < operator_module.PUBLIC_KLINE_LIMIT:
            raise ValueError("future_rows is outside the bounded response")
        self.redirect = redirect
        self.gap = gap
        self.future_rows = future_rows
        self.requests: list[Any] = []

    def _klines(self) -> list[list[object]]:
        rows: list[list[object]] = []
        for index in range(operator_module.PUBLIC_KLINE_LIMIT):
            close_ms = (
                NOW_MS
                - (
                    operator_module.PUBLIC_KLINE_LIMIT
                    - 1
                    - self.future_rows
                    - index
                )
                * 60_000
                - 1_000
            )
''',
    )
    replace_once(
        TESTS,
        '            assert query["limit"] == ["1441"]\n',
        '            assert query["limit"] == [str(operator_module.PUBLIC_KLINE_LIMIT)]\n',
    )
    test_marker = "\n\ndef test_public_market_gap_redirect_host_and_proxy_fail_closed() -> None:\n"
    new_tests = '''


def test_public_market_kline_margin_keeps_decision_time_completion_boundary() -> None:
    snapshot = fetch_public_market_snapshot(
        symbol="BTCUSDT",
        observed_at_ms=NOW_MS,
        opener=cast(Any, _Opener(future_rows=10)),
    )

    assert snapshot.completed_candle_close_ms == NOW_MS - 1_000


def test_public_market_kline_margin_remains_bounded_and_fails_closed() -> None:
    with pytest.raises(
        CandidatePaperRuntimeOperatorError,
        match="must contain 1440 completed",
    ):
        fetch_public_market_snapshot(
            symbol="BTCUSDT",
            observed_at_ms=NOW_MS,
            opener=cast(Any, _Opener(future_rows=61)),
        )
'''
    replace_once(TESTS, test_marker, new_tests + test_marker)

    replace_once(
        TASK,
        "base_sha: 7e191cebc71118a2dee32dceeec49a47153dd8f8\n",
        "base_sha: c33648acfd86a0352836498103857b601b5f486f\n",
    )
    replace_once(
        TASK,
        "branch: fix/wickhunter-wh09-public-market-concurrency-20260805-v1\n",
        "branch: fix/wickhunter-wh09-kline-completion-margin-20260805-v2\n",
    )
    replace_once(
        TASK,
        "next_action: validate bounded public-market concurrency, merge the repair, then deploy a fresh v10 PAPER activation and begin the prospective acceptance window\n",
        "next_action: validate the bounded completed-kline margin, merge the repair, then deploy a fresh v11 PAPER activation and begin the prospective acceptance window\n",
    )
    replace_once(
        TASK,
        "5. consumes public premium index, book ticker, open interest and 1441 one-minute klines, requiring the latest 1440 completed candles to be contiguous;\n",
        "5. consumes public premium index, book ticker, open interest and the Binance maximum 1500 one-minute klines, requiring the latest 1440 candles completed by immutable decision time to be contiguous;\n",
    )
    task_text = TASK.read_text(encoding="utf-8")
    section = '''

## Completed-kline acquisition margin repair

Trusted v10 run `31006885105` produced no generation, but the preserved self-hashed fail-closed health inventoried by run `31011549166` proved the exact error: `public klines must contain 1440 completed one-minute rows`. The operator binds an immutable decision timestamp before public acquisition. Binance returns its most recent rows at response time, so a request for only 1441 rows loses one completed row for every minute that elapses before a symbol response and has effectively no bounded acquisition margin.

The repair requests Binance's endpoint maximum of 1500 one-minute rows and still filters every candle by the immutable decision timestamp before selecting exactly the latest 1440 contiguous completed rows. This provides a bounded margin of up to 60 advancing response rows without allowing future evidence into the decision. Focused tests prove that ten trailing post-decision rows are excluded while the exact 1440-row contract succeeds, and that 61 trailing rows still fail closed. Public host, TLS, redirect, proxy, credential, size and staleness boundaries remain unchanged. Failed v10 identities remain retired; the next deployment must use fresh v11 identities.
'''
    if "## Completed-kline acquisition margin repair" in task_text:
        raise SystemExit("task already contains completed-kline margin repair")
    TASK.write_text(task_text.rstrip() + section.rstrip() + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
