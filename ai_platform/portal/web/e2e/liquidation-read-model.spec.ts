import { expect, test } from "@playwright/test";
import {
  appendFile,
  chmod,
  mkdir,
  mkdtemp,
  readFile,
  rm,
  symlink,
  utimes,
  writeFile,
} from "node:fs/promises";
import { tmpdir } from "node:os";
import { join, resolve } from "node:path";

import {
  addDecimalStrings,
  LiquidationQueryError,
  LiquidationReadModel,
  type LiquidationSource,
} from "@/lib/liquidations";

const FIXTURE_ROOT = resolve(process.cwd(), "fixtures/liquidations");

function event(
  source: LiquidationSource,
  id: string,
  occurredAtMs: number,
  options: {
    symbol?: string;
    side?: "long" | "short";
    notional?: string;
  } = {},
): string {
  return JSON.stringify({
    schema_version: 1,
    source,
    source_event_id: id,
    symbol: options.symbol ?? "BTCUSDT",
    liquidated_position_side: options.side ?? "long",
    occurred_at_ms: occurredAtMs,
    received_at_ms: occurredAtMs + 50,
    price: "100",
    quantity: "2",
    notional_usd: options.notional ?? "200",
    raw_side: options.side === "short" ? "Sell" : "Buy",
  });
}

async function createRunRoot(runId: string): Promise<{
  dataRoot: string;
  runRoot: string;
  cleanup: () => Promise<void>;
}> {
  const dataRoot = await mkdtemp(join(tmpdir(), "portal-liquidations-"));
  const runRoot = join(dataRoot, "runs", runId);
  await mkdir(runRoot, { recursive: true });
  return {
    dataRoot,
    runRoot,
    cleanup: () => rm(dataRoot, { recursive: true, force: true }),
  };
}

test("reads the completed fixture with stable filtering, pagination and exact aggregates", async () => {
  const model = new LiquidationReadModel({
    dataRoot: FIXTURE_ROOT,
    now: () => 1784905000000,
  });

  const firstPage = await model.list({ limit: 2 });
  expect(firstPage.mode).toBe("historical");
  expect(firstPage.events.map((item) => item.source_event_id)).toEqual([
    "bybit-sol-1",
    "binance-eth-1",
  ]);
  expect(firstPage.next_cursor).not.toBeNull();
  expect(firstPage.events[0]).toEqual(
    expect.objectContaining({
      source: "bybit-linear",
      symbol: "SOLUSDT",
      notional_usd: "3000",
      ingest_latency_ms: 120,
    }),
  );
  expect(firstPage.events[0]).not.toHaveProperty("raw_side");

  const secondPage = await model.list({ limit: 2, cursor: firstPage.next_cursor ?? undefined });
  expect(secondPage.events.map((item) => item.source_event_id)).toEqual([
    "bybit-eth-1",
    "shared-1",
  ]);

  const binance = await model.list({ source: "binance-usdm", limit: 20 });
  expect(binance.events).toHaveLength(2);
  expect(binance.events.every((item) => item.source === "binance-usdm")).toBe(true);

  const btc = await model.list({ symbol: "btcusdt", limit: 20 });
  expect(btc.events).toHaveLength(2);
  expect(new Set(btc.events.map((item) => item.source))).toEqual(
    new Set(["bybit-linear", "binance-usdm"]),
  );
  expect(btc.events.map((item) => item.source_event_id)).toEqual(["shared-1", "shared-1"]);

  const longs = await model.list({ side: "long", limit: 20 });
  expect(longs.events).toHaveLength(3);
  const timeRange = await model.list({
    since: 1784904860000,
    until: 1784904890000,
    limit: 20,
  });
  expect(timeRange.events.map((item) => item.source_event_id)).toEqual([
    "binance-eth-1",
    "bybit-eth-1",
  ]);

  const summary = await model.summary();
  expect(summary.windows.find((window) => window.window === "24h")).toEqual(
    expect.objectContaining({
      event_count: 5,
      notional_usd: "30230",
      long: { event_count: 3, notional_usd: "18235" },
      short: { event_count: 2, notional_usd: "11995" },
    }),
  );
  expect(summary.ranking_24h.map((ranking) => ranking.symbol)).toEqual([
    "BTCUSDT",
    "ETHUSDT",
    "SOLUSDT",
  ]);
  expect(summary.ranking_24h[0]).toEqual(
    expect.objectContaining({
      notional_usd: "14995",
      long_event_count: 1,
      short_event_count: 1,
    }),
  );

  const health = await model.health();
  expect(health).toEqual(
    expect.objectContaining({
      mode: "historical",
      acceptance_status: "failed",
      failed_gates: ["binance-usdm.maximum_latency_over_threshold_ratio"],
      active_sources: ["bybit-linear", "binance-usdm"],
      observed_symbol_count: 3,
      research_preview: true,
      trading_authorized: false,
      stale: false,
    }),
  );
  expect(health.latest_completed_acceptance).toEqual({
    run_id: "liquid20-20260724T170830Z-1",
    status: "failed",
    failed_gates: ["binance-usdm.maximum_latency_over_threshold_ratio"],
  });
  expect(health.sources["bybit-linear"].availability_ratio).toBe(0.998885);
  expect(health.sources["binance-usdm"].disconnects_per_hour).toBe(0);
  expect(health.source_semantics["binance-usdm"]).toContain("1000 ms");
});

test("tolerates an incomplete active line and incrementally consumes it after completion", async () => {
  const now = Date.now();
  const run = await createRunRoot("liquid20-20260725T220000Z-1");
  try {
    const bybitPath = join(run.runRoot, "bybit-linear.ndjson");
    const complete = event("bybit-linear", "complete", now - 2_000);
    const partial = event("bybit-linear", "partial", now - 1_000);
    await writeFile(bybitPath, `${complete}\nnot-json\n${partial}`, "utf8");
    await writeFile(join(run.runRoot, "binance-usdm.ndjson"), "", "utf8");

    const model = new LiquidationReadModel({ dataRoot: run.dataRoot, now: () => now });
    const initial = await model.list({ limit: 20 });
    expect(initial.mode).toBe("live");
    expect(initial.events.map((item) => item.source_event_id)).toEqual(["complete"]);
    expect(initial.rejected_records).toBe(1);

    await appendFile(bybitPath, "\n", "utf8");
    const completed = await model.list({ limit: 20 });
    expect(completed.events.map((item) => item.source_event_id)).toEqual([
      "partial",
      "complete",
    ]);
    expect(completed.rejected_records).toBe(1);
    expect((await model.health()).acceptance_status).toBe("in-progress");
  } finally {
    await run.cleanup();
  }
});

test("stays bounded, ignores symlinked runs and reads source files without write access", async () => {
  const now = Date.now();
  const run = await createRunRoot("liquid20-20260725T210000Z-1");
  const outside = await mkdtemp(join(tmpdir(), "portal-liquidations-outside-"));
  try {
    const bybitPath = join(run.runRoot, "bybit-linear.ndjson");
    await writeFile(
      bybitPath,
      [
        event("bybit-linear", "oldest", now - 10_000, { notional: "1.01" }),
        event("bybit-linear", "middle", now - 9_000, { notional: "2.02" }),
        event("bybit-linear", "latest", now - 8_000, { notional: "3.03" }),
      ].join("\n") + "\n",
      "utf8",
    );
    await writeFile(join(run.runRoot, "binance-usdm.ndjson"), "", "utf8");
    await chmod(bybitPath, 0o444);
    const before = await readFile(bybitPath, "utf8");

    const outsideRun = join(outside, "liquid20-20990101T000000Z-1");
    await mkdir(outsideRun);
    await symlink(outsideRun, join(run.dataRoot, "runs", "liquid20-20990101T000000Z-1"));

    const old = new Date(now - 60 * 60 * 1_000);
    await utimes(bybitPath, old, old);
    await utimes(run.runRoot, old, old);
    const model = new LiquidationReadModel({
      dataRoot: run.dataRoot,
      maxEvents: 2,
      staleAfterMs: 60_000,
      now: () => now,
    });
    const page = await model.list({ limit: 20 });
    expect(page.run_id).toBe("liquid20-20260725T210000Z-1");
    expect(page.mode).toBe("stale");
    expect(page.truncated).toBe(true);
    expect(page.events.map((item) => item.source_event_id)).toEqual(["latest", "middle"]);
    expect(await readFile(bybitPath, "utf8")).toBe(before);
  } finally {
    await chmod(join(run.runRoot, "bybit-linear.ndjson"), 0o644).catch(() => undefined);
    await run.cleanup();
    await rm(outside, { recursive: true, force: true });
  }
});

test("rejects unbounded or malformed query input and keeps decimal arithmetic exact", async () => {
  const model = new LiquidationReadModel({ dataRoot: FIXTURE_ROOT });
  await expect(model.list({ limit: 201 })).rejects.toBeInstanceOf(LiquidationQueryError);
  await expect(model.list({ cursor: "not-a-cursor" })).rejects.toBeInstanceOf(
    LiquidationQueryError,
  );
  await expect(model.list({ symbol: "../../secret" })).rejects.toBeInstanceOf(
    LiquidationQueryError,
  );
  await expect(model.list({ since: 2, until: 1 })).rejects.toBeInstanceOf(
    LiquidationQueryError,
  );
  expect(addDecimalStrings("0.1", "0.2")).toBe("0.3");
  expect(addDecimalStrings("10000.000", "4995")).toBe("14995");
});
