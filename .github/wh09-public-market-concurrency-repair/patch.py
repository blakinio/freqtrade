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
        "import argparse\n",
        "import argparse\nfrom concurrent.futures import ThreadPoolExecutor\n",
    )
    replace_once(
        OPERATOR,
        "DEFAULT_MAX_SOURCE_AGE_MS = 300_000\n",
        "DEFAULT_MAX_SOURCE_AGE_MS = 300_000\nMAX_PUBLIC_MARKET_WORKERS = 8\n",
    )
    method_marker = "    def run_once(self, *, observed_at_ms: int | None = None) -> int:\n"
    method = '''    def _fetch_public_market_snapshots(
        self,
        *,
        symbols: tuple[str, ...],
        observed_at_ms: int,
    ) -> tuple[PublicMarketSnapshot, ...]:
        def fetch(symbol: str) -> PublicMarketSnapshot:
            return fetch_public_market_snapshot(
                symbol=symbol,
                observed_at_ms=observed_at_ms,
                base_url=self.public_market_base_url,
                opener=self.opener,
            )

        if self.opener is not None or len(symbols) <= 2:
            return tuple(fetch(symbol) for symbol in symbols)
        workers = min(MAX_PUBLIC_MARKET_WORKERS, len(symbols))
        with ThreadPoolExecutor(
            max_workers=workers,
            thread_name_prefix="wickhunter-public-market",
        ) as executor:
            return tuple(executor.map(fetch, symbols))

'''
    replace_once(OPERATOR, method_marker, method + method_marker)
    replace_once(
        OPERATOR,
        '''        markets = tuple(
            fetch_public_market_snapshot(
                symbol=symbol,
                observed_at_ms=now_ms,
                base_url=self.public_market_base_url,
                opener=self.opener,
            )
            for symbol in market_symbols
        )
''',
        '''        markets = self._fetch_public_market_snapshots(
            symbols=market_symbols,
            observed_at_ms=now_ms,
        )
''',
    )

    replace_once(TESTS, "import json\n", "import json\nimport threading\n")
    test_marker = "\n\ndef test_operator_refuses_non_paper_binding(tmp_path: Path) -> None:\n"
    new_test = '''


def test_run_once_bounds_parallel_public_market_fetches_and_preserves_result_order(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class StopAfterCompose(RuntimeError):
        pass

    symbols = tuple(f"ASSET{index}USDT" for index in range(10))
    events: list[dict[str, object]] = []
    for index, symbol in enumerate(symbols):
        events.extend(
            (
                _event(
                    f"event-history-{index}",
                    symbol=symbol,
                    received_at_ms=NOW_MS - 3_600_000,
                ),
                _event(
                    f"event-current-{index}",
                    symbol=symbol,
                    received_at_ms=NOW_MS - 1_000,
                ),
            )
        )
    service = _service()
    captured_tick: object | None = None

    def stop_after_compose(tick: object) -> None:
        nonlocal captured_tick
        captured_tick = tick
        raise StopAfterCompose

    service.step = stop_after_compose
    root = _write_live_root(tmp_path / "parallel-liquid20", events=events)
    runtime_operator = CandidatePaperRuntimeOperator(
        service=cast(Any, service),
        liquid20_root_path=root.resolve(),
        health_path=(tmp_path / "parallel-health.json").resolve(),
        operator_commit=CODE_SHA,
    )
    lock = threading.Lock()
    release = threading.Event()
    started = 0
    active = 0
    maximum_active = 0
    fetched: list[str] = []

    def fake_market_snapshot(
        *,
        symbol: str,
        observed_at_ms: int,
        base_url: str,
        opener: object,
    ) -> PublicMarketSnapshot:
        del base_url, opener
        nonlocal started, active, maximum_active
        with lock:
            started += 1
            active += 1
            maximum_active = max(maximum_active, active)
            fetched.append(symbol)
            if started >= 4:
                release.set()
        if not release.wait(timeout=2):
            raise AssertionError("public market fetches did not overlap")
        with lock:
            active -= 1
        return _market(symbol=symbol, observed_at_ms=observed_at_ms)

    monkeypatch.setattr(
        operator_module,
        "fetch_public_market_snapshot",
        fake_market_snapshot,
    )
    with pytest.raises(StopAfterCompose):
        runtime_operator.run_once(observed_at_ms=NOW_MS)

    assert maximum_active >= 4
    assert maximum_active <= operator_module.MAX_PUBLIC_MARKET_WORKERS
    assert set(fetched) == set(symbols)
    assert captured_tick is not None
    mark_prices = cast(Any, captured_tick).mark_prices
    assert tuple(symbol for symbol, _price in mark_prices) == tuple(sorted(symbols))
'''
    replace_once(TESTS, test_marker, new_test + test_marker)

    replace_once(
        TASK,
        "status: validating\n",
        "status: implementing\n",
    )
    replace_once(
        TASK,
        "base_sha: c1d1f9f3db5e95e245c297f3d29be079533db301\n",
        "base_sha: 7e191cebc71118a2dee32dceeec49a47153dd8f8\n",
    )
    replace_once(
        TASK,
        "branch: fix/wickhunter-wh09-pointer-availability-clock-20260805-v1\n",
        "branch: fix/wickhunter-wh09-public-market-concurrency-20260805-v1\n",
    )
    replace_once(TASK, "product_pr: 1231\n", "product_pr: pending\n")
    replace_once(
        TASK,
        "next_action: validate bounded pointer availability on exact head, merge PR 1231, then deploy a fresh v9 PAPER activation with retry-stable reads and collision-safe networking\n",
        "next_action: validate bounded public-market concurrency, merge the repair, then deploy a fresh v10 PAPER activation and begin the prospective acceptance window\n",
    )
    task_text = TASK.read_text(encoding="utf-8")
    section = '''

## First-generation public-market concurrency repair

Trusted Synology deployment v9 run `31001468857` built the exact operator and constrained gateway images, passed Liquid20 smoke validation, published a fresh zero-authority activation and started the operator. The operator stayed alive but produced neither generation 1 nor fail-closed health during the bounded 20-minute first-generation gate. The only blocking work after successful initialization is the public market acquisition path, which performed four HTTPS requests sequentially for every selected Liquid20 symbol: up to 80 serial requests for the canonical top-20 universe.

This repair keeps every request allowlisted, credential-free, redirect-free and individually time-bounded, but executes independent symbol acquisitions through a bounded eight-worker pool. `executor.map` preserves the deterministic input/result order, injected test openers remain sequential, exceptions still fail closed, and no journal mutation occurs until the complete market tuple has succeeded. A focused regression proves at least four overlapping acquisitions, enforces the worker ceiling and verifies stable sorted mark output. Failed v9 identities are retired; the next deployment must use fresh v10 activation, state, journal, container and network identities.
'''
    if "## First-generation public-market concurrency repair" in task_text:
        raise SystemExit("task already contains public-market concurrency repair")
    TASK.write_text(task_text.rstrip() + section.rstrip() + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
