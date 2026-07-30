import { expect, test } from "@playwright/test";
import { mkdir, mkdtemp, rm, writeFile } from "node:fs/promises";
import { tmpdir } from "node:os";
import { join } from "node:path";

import {
  LiquidationLiveReadModel,
  type LiquidationDataSource,
} from "@/lib/liquidations";

function event(source: LiquidationDataSource, id: string, occurredAtMs: number): string {
  return JSON.stringify({
    schema_version: 1,
    source,
    source_event_id: id,
    symbol: source === "okx-swap" ? "ETHUSDT" : "BTCUSDT",
    liquidated_position_side: source === "okx-swap" ? "short" : "long",
    occurred_at_ms: occurredAtMs,
    received_at_ms: occurredAtMs + 25,
    price: "100",
    quantity: "2",
    notional_usd: "200",
    raw_side: "test",
  });
}

function sourceState(
  now: number,
  events: number,
  connected = true,
  configured = true,
  eventAgeMs = 1_000,
) {
  return {
    configured,
    connected: configured && connected,
    last_event_at_ms: events > 0 ? now - eventAgeMs : null,
    last_event_received_at_ms: events > 0 ? now - eventAgeMs + 25 : null,
    last_heartbeat_at_ms: now - 500,
    ingest_lag_ms: events > 0 ? 25 : null,
    reconnect_count: connected ? 0 : 1,
    observed_symbol_count: events > 0 ? 1 : 0,
    subscription_symbol_count: configured ? 2 : 0,
    events_written: events,
    error_count: connected ? 0 : 1,
    parse_error_count: 0,
    latest_error: connected ? null : "connection closed",
  };
}

async function fixture(
  now: number,
  okxConnected = true,
  okxConfigured = true,
  okxEventAgeMs = 1_000,
) {
  const dataRoot = await mkdtemp(join(tmpdir(), "portal-liquidations-okx-live-"));
  const runId = "liquid20-20260730T000000Z-0";
  const runRoot = join(dataRoot, "live", "runs", runId);
  await mkdir(runRoot, { recursive: true });
  await writeFile(
    join(runRoot, "bybit-linear.ndjson"),
    `${event("bybit-linear", "bybit-1", now - 3_000)}\n`,
  );
  await writeFile(
    join(runRoot, "binance-usdm.ndjson"),
    `${event("binance-usdm", "binance-1", now - 2_000)}\n`,
  );
  await writeFile(
    join(runRoot, "okx-swap.ndjson"),
    `${event("okx-swap", "okx-1", now - okxEventAgeMs)}\n`,
  );
  const state = {
    schema_version: 1,
    contract: "liquidation-live-state-v1",
    run_id: runId,
    run_state: "active",
    data_mode: "live",
    collector_started_at_ms: now - 60_000,
    collector_heartbeat_at_ms: now - 500,
    last_event_at_ms: now - 1_000,
    last_event_received_at_ms: now - 975,
    completed_at_ms: null,
    completion_reason: null,
    collector_commit: "a".repeat(40),
    host_id: "test",
    execution_enabled: false,
    trading_authorized: false,
    trading_credentials_present: false,
    orders_submitted: 0,
    sources: {
      "bybit-linear": sourceState(now, 1, true, true, 3_000),
      "binance-usdm": sourceState(now, 1, true, true, 2_000),
      "okx-swap": sourceState(now, 1, okxConnected, okxConfigured, okxEventAgeMs),
    },
  };
  await writeFile(
    join(dataRoot, "live", "live-state-v1.json"),
    JSON.stringify({
      schema_version: 1,
      contract: "liquidation-live-state-v1",
      active_run_id: runId,
      collector_heartbeat_at_ms: state.collector_heartbeat_at_ms,
      state,
    }),
  );
  return {
    dataRoot,
    runId,
    cleanup: () => rm(dataRoot, { recursive: true, force: true }),
  };
}

test("three-source BFF model lists, filters and aggregates OKX liquidation data", async () => {
  const now = 1_784_956_800_000;
  const data = await fixture(now);
  try {
    const model = new LiquidationLiveReadModel({ dataRoot: data.dataRoot, now: () => now });
    const health = await model.health();
    const all = await model.list({ limit: 20 });
    const okx = await model.list({ source: "okx-swap", limit: 20 });
    const summary = await model.summary();

    expect(health.mode).toBe("live");
    expect(health.active_sources).toEqual(
      expect.arrayContaining(["bybit-linear", "binance-usdm", "okx-swap"]),
    );
    expect(health.sources["okx-swap"]?.configured).toBe(true);
    expect(health.sources["okx-swap"]?.connected).toBe(true);
    expect(health.sources["okx-swap"]?.events).toBe(1);
    expect(health.source_semantics["okx-swap"]).toContain("public ctVal");
    expect(all.events.map((item) => item.source)).toEqual([
      "okx-swap",
      "binance-usdm",
      "bybit-linear",
    ]);
    expect(okx.events).toHaveLength(1);
    expect(okx.events[0].source_event_id).toBe("okx-1");
    expect(okx.events[0].symbol).toBe("ETHUSDT");
    expect(summary.windows.find((item) => item.window === "24h")?.by_source["okx-swap"]).toEqual(
      { event_count: 1, notional_usd: "200" },
    );
  } finally {
    await data.cleanup();
  }
});

test("one disconnected OKX source degrades the collector view without changing other sources", async () => {
  const now = 1_784_956_800_000;
  const data = await fixture(now, false);
  try {
    const model = new LiquidationLiveReadModel({ dataRoot: data.dataRoot, now: () => now });
    const health = await model.health();

    expect(health.mode).toBe("stale");
    expect(health.sources["okx-swap"]?.connected).toBe(false);
    expect(health.sources["okx-swap"]?.reconnect_count).toBe(1);
    expect(health.sources["bybit-linear"]?.connected).toBe(true);
    expect(health.sources["binance-usdm"]?.connected).toBe(true);
  } finally {
    await data.cleanup();
  }
});

test("an unconfigured OKX source can never be reported as healthy", async () => {
  const now = 1_784_956_800_000;
  const data = await fixture(now, false, false);
  try {
    const model = new LiquidationLiveReadModel({ dataRoot: data.dataRoot, now: () => now });
    const health = await model.health();
    const page = await model.list({ limit: 20 });
    const summary = await model.summary();

    expect(health.mode).toBe("stale");
    expect(health.active_sources).not.toContain("okx-swap");
    expect(health.sources["okx-swap"]?.configured).toBe(false);
    expect(health.sources["okx-swap"]?.connected).toBe(false);
    expect(page.mode).toBe("stale");
    expect(summary.mode).toBe("stale");
    expect(health.sources["bybit-linear"]?.connected).toBe(true);
    expect(health.sources["binance-usdm"]?.connected).toBe(true);
  } finally {
    await data.cleanup();
  }
});

test("stale OKX events degrade the view even while its heartbeat remains fresh", async () => {
  const now = 1_784_956_800_000;
  const data = await fixture(now, true, true, 300_001);
  try {
    const model = new LiquidationLiveReadModel({ dataRoot: data.dataRoot, now: () => now });
    const health = await model.health();
    const page = await model.list({ limit: 20 });

    expect(health.mode).toBe("stale");
    expect(page.mode).toBe("stale");
    expect(health.sources["okx-swap"]?.configured).toBe(true);
    expect(health.sources["okx-swap"]?.connected).toBe(true);
    expect(health.sources["okx-swap"]?.last_heartbeat_at_ms).toBe(now - 500);
    expect(health.sources["bybit-linear"]?.connected).toBe(true);
    expect(health.sources["binance-usdm"]?.connected).toBe(true);
  } finally {
    await data.cleanup();
  }
});

test("Portal OKX implementation remains filesystem/BFF only", async () => {
  const root = join(process.cwd());
  const reader = await import("node:fs/promises").then(({ readFile }) =>
    readFile(join(root, "lib/liquidations/reader.ts"), "utf8"),
  );
  const dashboard = await import("node:fs/promises").then(({ readFile }) =>
    readFile(join(root, "components/liquidations-live-dashboard.tsx"), "utf8"),
  );
  const content = `${reader}\n${dashboard}`;

  expect(content).not.toContain("wss://ws.okx.com");
  expect(content).not.toContain("new WebSocket");
  expect(dashboard).toContain("/api/market/liquidations");
  expect(dashboard).toContain("OKX SWAP");
  expect(dashboard).toContain('value="okx-swap"');
});
