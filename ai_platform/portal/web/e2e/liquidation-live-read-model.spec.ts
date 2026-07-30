import { expect, test } from "@playwright/test";
import { appendFile, mkdir, mkdtemp, rename, rm, writeFile } from "node:fs/promises";
import { tmpdir } from "node:os";
import { join } from "node:path";

import { LiquidationLiveReadModel, type LiquidationSource } from "@/lib/liquidations";

function event(source: LiquidationSource, id: string, occurredAtMs: number): string {
  return JSON.stringify({
    schema_version: 1,
    source,
    source_event_id: id,
    symbol: "BTCUSDT",
    liquidated_position_side: "long",
    occurred_at_ms: occurredAtMs,
    received_at_ms: occurredAtMs + 25,
    price: "100",
    quantity: "2",
    notional_usd: "200",
    raw_side: "Sell",
  });
}

function sourceState(now: number, configured: boolean) {
  return {
    configured,
    connected: configured,
    last_event_at_ms: configured ? now - 1_000 : null,
    last_event_received_at_ms: configured ? now - 975 : null,
    last_heartbeat_at_ms: configured ? now - 500 : null,
    ingest_lag_ms: configured ? 25 : null,
    reconnect_count: 0,
    observed_symbol_count: configured ? 1 : 0,
    subscription_symbol_count: configured ? 250 : 0,
    events_written: configured ? 1 : 0,
    error_count: 0,
    parse_error_count: 0,
    latest_error: null,
  };
}

function liveState(runId: string, now: number, runState: "active" | "completed" = "active") {
  const state = {
    schema_version: 1,
    contract: "liquidation-live-state-v1",
    run_id: runId,
    run_state: runState,
    data_mode: runState === "active" ? "live" : "historical",
    collector_started_at_ms: now - 60_000,
    collector_heartbeat_at_ms: now - 500,
    last_event_at_ms: now - 1_000,
    last_event_received_at_ms: now - 975,
    completed_at_ms: runState === "completed" ? now - 100 : null,
    completion_reason: runState === "completed" ? "collector-stopped" : null,
    collector_commit: "a".repeat(40),
    host_id: "test",
    execution_enabled: false,
    trading_authorized: false,
    trading_credentials_present: false,
    orders_submitted: 0,
    sources: {
      "bybit-linear": sourceState(now, true),
      "binance-usdm": sourceState(now, true),
      "okx-swap": sourceState(now, false),
    },
  };
  return {
    schema_version: 1,
    contract: "liquidation-live-state-v1",
    active_run_id: runState === "active" ? runId : null,
    collector_heartbeat_at_ms: state.collector_heartbeat_at_ms,
    state,
  };
}

async function createDataRoot(now: number) {
  const dataRoot = await mkdtemp(join(tmpdir(), "portal-liquidations-live-"));
  const historicalId = "liquid20-20990101T000000Z-9";
  const historicalRoot = join(dataRoot, "runs", historicalId);
  await mkdir(historicalRoot, { recursive: true });
  await writeFile(
    join(historicalRoot, "bybit-linear.ndjson"),
    `${event("bybit-linear", "historical", now - 86_400_000)}\n`,
  );
  await writeFile(join(historicalRoot, "binance-usdm.ndjson"), "");
  await writeFile(
    join(historicalRoot, "multi-source-acceptance-report.json"),
    JSON.stringify({ run_id: historicalId, passed: true, failed_gates: [] }),
  );
  return { dataRoot, historicalId, cleanup: () => rm(dataRoot, { recursive: true, force: true }) };
}

async function createLiveRun(dataRoot: string, runId: string, now: number) {
  const runRoot = join(dataRoot, "live", "runs", runId);
  await mkdir(runRoot, { recursive: true });
  await writeFile(
    join(runRoot, "bybit-linear.ndjson"),
    `${event("bybit-linear", "live-1", now - 1_000)}\n`,
  );
  await writeFile(join(runRoot, "binance-usdm.ndjson"), "");
  await writeFile(
    join(dataRoot, "live", "live-state-v1.json"),
    JSON.stringify(liveState(runId, now)),
  );
  return runRoot;
}

test("active live run wins over a lexicographically newer accepted historical run", async () => {
  const now = 1_784_956_800_000;
  const fixture = await createDataRoot(now);
  try {
    const liveId = "liquid20-20260727T000000Z-0";
    await createLiveRun(fixture.dataRoot, liveId, now);
    const model = new LiquidationLiveReadModel({ dataRoot: fixture.dataRoot, now: () => now });

    const page = await model.list({ limit: 20 });
    const health = await model.health();
    expect(page.run_id).toBe(liveId);
    expect(page.mode).toBe("live");
    expect(page.events.map((item) => item.source_event_id)).toEqual(["live-1"]);
    expect(health.mode).toBe("live");
    expect(health.latest_completed_acceptance?.run_id).toBe(fixture.historicalId);
    expect(health.trading_authorized).toBe(false);
  } finally {
    await fixture.cleanup();
  }
});

test("completed accepted data stays historical when no live contract exists", async () => {
  const now = 1_784_956_800_000;
  const fixture = await createDataRoot(now);
  try {
    const model = new LiquidationLiveReadModel({ dataRoot: fixture.dataRoot, now: () => now });
    const health = await model.health();
    expect(health.mode).toBe("historical");
    expect(health.run_state).toBe("completed");
    expect(health.acceptance_status).toBe("accepted");
    expect(health.collector_heartbeat_at_ms).toBeNull();
  } finally {
    await fixture.cleanup();
  }
});

test("heartbeat advances without changing event time and transitions stale then offline", async () => {
  let now = 1_784_956_800_000;
  const fixture = await createDataRoot(now);
  try {
    const liveId = "liquid20-20260727T000000Z-0";
    await createLiveRun(fixture.dataRoot, liveId, now);
    const model = new LiquidationLiveReadModel({
      dataRoot: fixture.dataRoot,
      collectorStaleAfterMs: 30_000,
      collectorOfflineAfterMs: 120_000,
      eventStaleAfterMs: 300_000,
      sourceStaleAfterMs: 45_000,
      now: () => now,
    });
    const first = await model.health();
    const firstEvent = first.last_event_at_ms;

    now += 5_000;
    const advanced = liveState(liveId, now);
    advanced.state.last_event_at_ms = firstEvent ?? advanced.state.last_event_at_ms;
    advanced.state.last_event_received_at_ms =
      first.last_event_received_at_ms ?? advanced.state.last_event_received_at_ms;
    await writeFile(
      join(fixture.dataRoot, "live", "live-state-v1.json"),
      JSON.stringify(advanced),
    );
    const second = await model.health();
    expect(second.collector_heartbeat_at_ms).toBeGreaterThan(first.collector_heartbeat_at_ms ?? 0);
    expect(second.last_event_at_ms).toBe(firstEvent);

    now += 31_000;
    expect((await model.health()).mode).toBe("stale");
    now += 91_000;
    expect((await model.health()).mode).toBe("offline");
  } finally {
    await fixture.cleanup();
  }
});

test("incremental polling sees appended events and recovers from replacement and rotation", async () => {
  let now = 1_784_956_800_000;
  const fixture = await createDataRoot(now);
  try {
    const firstId = "liquid20-20260727T000000Z-0";
    const firstRoot = await createLiveRun(fixture.dataRoot, firstId, now);
    const model = new LiquidationLiveReadModel({ dataRoot: fixture.dataRoot, now: () => now });
    expect((await model.list({ limit: 20 })).events).toHaveLength(1);

    await appendFile(
      join(firstRoot, "bybit-linear.ndjson"),
      `${event("bybit-linear", "live-2", now - 500)}\n`,
    );
    expect((await model.list({ limit: 20 })).events.map((item) => item.source_event_id)).toEqual([
      "live-2",
      "live-1",
    ]);

    const replacement = join(firstRoot, "bybit-linear.next");
    await writeFile(replacement, `${event("bybit-linear", "replacement", now - 250)}\n`);
    await rename(replacement, join(firstRoot, "bybit-linear.ndjson"));
    expect((await model.list({ limit: 20 })).events.map((item) => item.source_event_id)).toEqual([
      "replacement",
    ]);

    now += 86_400_000;
    const secondId = "liquid20-20260728T000000Z-0";
    await createLiveRun(fixture.dataRoot, secondId, now);
    expect((await model.list({ limit: 20 })).run_id).toBe(secondId);
  } finally {
    await fixture.cleanup();
  }
});
