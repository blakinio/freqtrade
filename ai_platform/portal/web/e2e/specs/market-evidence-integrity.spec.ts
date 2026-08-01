import { createHash } from "node:crypto";
import {
  lstat,
  mkdir,
  mkdtemp,
  readFile,
  rename,
  rm,
  symlink,
  unlink,
  writeFile,
} from "node:fs/promises";
import { tmpdir } from "node:os";
import { dirname, join, relative } from "node:path";

import { expect, test } from "@playwright/test";

import {
  MarketEvidenceIntegrityError,
  verifyMarketEvidencePackage,
} from "../../lib/market-evidence/integrity";
import {
  MarketEvidenceDataUnavailableError,
  MarketEvidenceReadModel,
} from "../../lib/market-evidence/reader";
import { MarketEvidenceReadModel as MarketEvidenceReadModelV2 } from "../../lib/market-evidence/reader-v2";

const AUTHORITY = {
  execution_enabled: false,
  orders_submitted: 0,
  trading_credentials_present: false,
  model_execution_authorized: false,
  replay_authorized: false,
  performance_research_authorized: false,
  live_capital_authorized: false,
} as const;
const V1_SOURCES = ["bybit-linear", "binance-usdm"] as const;
const V2_SOURCES = [...V1_SOURCES, "okx-swap"] as const;

interface ArtifactIdentity {
  logical_name: string;
  sha256: string;
  size_bytes: number;
}

interface PackageFixture {
  dataRoot: string;
  packageRoot: string;
  manifest: Record<string, unknown>;
  runId: string;
  version: 1 | 2;
}

function sortedValue(value: unknown): unknown {
  if (Array.isArray(value)) return value.map(sortedValue);
  if (typeof value !== "object" || value === null) return value;
  return Object.fromEntries(
    Object.entries(value as Record<string, unknown>)
      .sort(([left], [right]) => (left < right ? -1 : left > right ? 1 : 0))
      .map(([key, item]) => [key, sortedValue(item)]),
  );
}

function canonicalSha256(value: unknown): string {
  return createHash("sha256").update(JSON.stringify(sortedValue(value)), "utf8").digest("hex");
}

function bytesSha256(value: Buffer): string {
  return createHash("sha256").update(value).digest("hex");
}

async function writeJson(path: string, value: unknown): Promise<void> {
  await mkdir(dirname(path), { recursive: true });
  await writeFile(path, `${JSON.stringify(value, null, 2)}\n`, "utf8");
}

async function writeRows(path: string, rows: Record<string, unknown>[]): Promise<void> {
  await mkdir(dirname(path), { recursive: true });
  await writeFile(path, `${rows.map((row) => JSON.stringify(row)).join("\n")}\n`, "utf8");
}

async function identity(packageRoot: string, logicalName: string): Promise<ArtifactIdentity> {
  const content = await readFile(join(packageRoot, logicalName));
  return { logical_name: logicalName, sha256: bytesSha256(content), size_bytes: content.length };
}

async function sealPackage(fixture: PackageFixture): Promise<void> {
  const manifestSeed = { ...fixture.manifest };
  delete manifestSeed.manifest_sha256;
  fixture.manifest.manifest_sha256 = canonicalSha256(manifestSeed);
  const manifestPath = join(fixture.packageRoot, "manifest.json");
  await writeJson(manifestPath, fixture.manifest);
  const artifacts = fixture.manifest.artifacts as ArtifactIdentity[];
  const manifestIdentity = await identity(fixture.packageRoot, "manifest.json");
  const checksumLines = [...artifacts, manifestIdentity]
    .map((item) => `${item.sha256}  ${item.logical_name}`)
    .sort();
  await writeFile(
    join(fixture.packageRoot, "artifact-sha256.txt"),
    `${checksumLines.join("\n")}\n`,
    "utf8",
  );
  await writeJson(join(fixture.packageRoot, "verification-report.json"), {
    schema_version: fixture.version,
    status: "verified",
    outcome: "accepted",
    run_id: fixture.runId,
    manifest_sha256: fixture.manifest.manifest_sha256,
    artifact_count: artifacts.length,
    ...(fixture.version === 2
      ? { binding_sha256: fixture.manifest.source_package_binding_sha256 }
      : {}),
    ...(fixture.manifest.record_counts as Record<string, number>),
    wh01_ready: false,
    wh01_blocker: "LIQUIDATION_ARCHIVE_NOT_BOUND",
    ...AUTHORITY,
  });
}

async function createPackage(version: 1 | 2): Promise<PackageFixture> {
  const dataRoot = await mkdtemp(join(tmpdir(), `market-evidence-v${version}-`));
  const runId = `wickhunter-production-market-evidence-20260729-v${version}-r1`;
  const packageRoot = join(dataRoot, "runs", runId, "immutable-package");
  await mkdir(packageRoot, { recursive: true });
  const sources = version === 1 ? V1_SOURCES : V2_SOURCES;
  const request = { schema_version: version, run_id: runId, sources, symbols: ["BTCUSDT"] };
  await writeJson(join(packageRoot, "request.json"), request);
  if (version === 1) await writeJson(join(packageRoot, "policy.json"), { pre_roll_ms: 86_400_000 });
  const sourceRows = sources.map((source, index) => ({
    source,
    sample_index: 0,
    scheduled_at_ms: 1_785_347_700_000,
    available_at_ms: 1_785_347_700_100 + index,
    connected: true,
    healthy: true,
  }));
  const qualityRows = sources.map((source) => ({
    source,
    canonical_symbol: "BTCUSDT",
    available_at_ms: 1_785_347_700_100,
    last_price: "100",
  }));
  const instrumentRows = sources.map((source) => ({
    source,
    canonical_symbol: "BTCUSDT",
    native_symbol: "BTCUSDT",
    market: "perpetual",
    active: true,
    captured_at_ms: 1_785_347_700_100,
  }));
  await writeRows(join(packageRoot, "source-snapshots.ndjson"), sourceRows);
  await writeRows(join(packageRoot, "market-quality-observations.ndjson"), qualityRows);
  await writeRows(join(packageRoot, "instrument-snapshots.ndjson"), instrumentRows);
  await writeJson(join(packageRoot, "run-state.json"), {
    schema_version: version,
    run_id: runId,
    state: "completed",
    active: false,
    verification_result: "accepted",
    ...AUTHORITY,
  });
  const candleArtifacts: Record<string, unknown>[] = [];
  const candleIdentities: ArtifactIdentity[] = [];
  for (const source of sources) {
    const logicalName = `candles/${source}/BTCUSDT-5m.ndjson`;
    let normalized: ArtifactIdentity;
    if (version === 2) {
      await writeRows(join(packageRoot, logicalName), [{ source, canonical_symbol: "BTCUSDT" }]);
      normalized = await identity(packageRoot, logicalName);
      candleIdentities.push(normalized);
    } else {
      normalized = {
        logical_name: logicalName,
        sha256: "0".repeat(64),
        size_bytes: 3,
      };
    }
    candleArtifacts.push({
      source,
      symbol: "BTCUSDT",
      record_count: 1,
      normalized_file: normalized,
    });
  }
  await writeJson(
    join(packageRoot, "completed-candles-index.json"),
    version === 1 ? candleArtifacts : { schema_version: 2, artifacts: candleArtifacts },
  );
  if (version === 1) await writeJson(join(packageRoot, "source-artifacts-index.json"), []);
  let bindingSha256: string | undefined;
  if (version === 2) {
    const requestIdentity = await identity(packageRoot, "request.json");
    const binding: Record<string, unknown> = {
      schema_version: 2,
      binding_type: "WickHunterMarketEvidenceSourcePackageBinding",
      run_id: runId,
      base_v1: {
        run_id: "wickhunter-production-market-evidence-20260728-v1-r1",
        manifest_sha256: "1".repeat(64),
        request_sha256: "2".repeat(64),
        verification_manifest_sha256: "1".repeat(64),
      },
      okx_supplement: {
        run_id: runId,
        manifest_sha256: "3".repeat(64),
        request_sha256: requestIdentity.sha256,
        verification_manifest_sha256: "3".repeat(64),
      },
      geometry: {
        pre_roll_start_ms: 1_785_218_400_000,
        decision_start_ms: 1_785_304_800_000,
        decision_end_ms: 1_785_348_000_000,
      },
      sources,
      symbols: ["BTCUSDT"],
      source_separated: true,
      cross_exchange_deduplication: false,
      immutable_inputs_mutated: false,
      ...AUTHORITY,
    };
    binding.binding_sha256 = canonicalSha256(binding);
    bindingSha256 = String(binding.binding_sha256);
    await writeJson(join(packageRoot, "source-package-binding.json"), binding);
  }
  const topLevel =
    version === 1
      ? [
          "request.json",
          "policy.json",
          "run-state.json",
          "source-snapshots.ndjson",
          "market-quality-observations.ndjson",
          "instrument-snapshots.ndjson",
          "completed-candles-index.json",
          "source-artifacts-index.json",
        ]
      : [
          "request.json",
          "source-package-binding.json",
          "run-state.json",
          "source-snapshots.ndjson",
          "market-quality-observations.ndjson",
          "instrument-snapshots.ndjson",
          "completed-candles-index.json",
        ];
  const artifacts = await Promise.all(topLevel.map((name) => identity(packageRoot, name)));
  artifacts.push(...candleIdentities);
  const capture = {
    pre_roll_start_ms: 1_785_218_400_000,
    decision_start_ms: 1_785_304_800_000,
    decision_end_ms: 1_785_348_000_000,
    pre_roll_ms: 86_400_000,
    cadence_seconds: 300,
    timeframe: "5m",
  };
  const manifest: Record<string, unknown> = {
    schema_version: version,
    artifact_type: "WickHunterProductionMarketEvidencePackage",
    ...(version === 2 ? { contract_id: "wickhunter-production-market-evidence-v2" } : {}),
    run_id: runId,
    ...(version === 2
      ? {
          base_v1_run_id: "wickhunter-production-market-evidence-20260728-v1-r1",
          source_package_binding_sha256: bindingSha256,
          base_request_identity_sha256: canonicalSha256(request),
        }
      : {
          request_sha256: (await identity(packageRoot, "request.json")).sha256,
          policy_sha256: (await identity(packageRoot, "policy.json")).sha256,
          inner_manifest_sha256: "4".repeat(64),
          run_root_identity_sha256: canonicalSha256({ run_id: runId, inner: "4".repeat(64) }),
        }),
    state: "completed",
    verification_result: "accepted",
    collector_commit: "a".repeat(40),
    sources,
    instruments: ["BTCUSDT"],
    capture,
    record_counts: {
      market_quality_observations: qualityRows.length,
      instrument_snapshots: instrumentRows.length,
      source_health_snapshots: sourceRows.length,
      completed_candles: candleArtifacts.length,
    },
    gaps: [],
    wh01: {
      market_evidence_ready: true,
      ready: false,
      blocker_code: "LIQUIDATION_ARCHIVE_NOT_BOUND",
    },
    artifacts,
    authorities: AUTHORITY,
    host_paths_exposed: false,
    raw_exchange_payloads_exposed_by_portal: false,
  };
  const fixture = { dataRoot, packageRoot, manifest, runId, version } satisfies PackageFixture;
  await sealPackage(fixture);
  return fixture;
}

async function expectIntegrityFailure(fixture: PackageFixture): Promise<void> {
  await expect(
    verifyMarketEvidencePackage({
      dataRoot: fixture.dataRoot,
      packageRoot: fixture.packageRoot,
      runId: fixture.runId,
    }),
  ).rejects.toBeInstanceOf(MarketEvidenceIntegrityError);
}

for (const version of [1, 2] as const) {
  test(`@regression accepts a valid immutable v${version} package`, async () => {
    const fixture = await createPackage(version);
    try {
      const verified = await verifyMarketEvidencePackage({
        dataRoot: fixture.dataRoot,
        packageRoot: fixture.packageRoot,
        runId: fixture.runId,
      });
      expect(verified.version).toBe(version);
      expect(verified.manifest.run_id).toBe(fixture.runId);
      const page =
        version === 1
          ? await new MarketEvidenceReadModel({ dataRoot: fixture.dataRoot }).instruments()
          : await new MarketEvidenceReadModelV2({ dataRoot: fixture.dataRoot }).instruments();
      expect(page.items.length).toBeGreaterThan(0);
      if (version === 2) expect(page.items.every((item) => item.source === "okx-swap")).toBe(true);
    } finally {
      await rm(fixture.dataRoot, { recursive: true, force: true });
    }
  });
}

test("@regression rejects manifest self-hash mismatch", async () => {
  const fixture = await createPackage(1);
  try {
    fixture.manifest.collector_commit = "b".repeat(40);
    await writeJson(join(fixture.packageRoot, "manifest.json"), fixture.manifest);
    await expectIntegrityFailure(fixture);
  } finally {
    await rm(fixture.dataRoot, { recursive: true, force: true });
  }
});

for (const field of ["sha256", "size_bytes"] as const) {
  test(`@regression rejects declared artifact ${field} mismatch`, async () => {
    const fixture = await createPackage(1);
    try {
      const artifacts = fixture.manifest.artifacts as ArtifactIdentity[];
      const target = artifacts.find((item) => item.logical_name === "market-quality-observations.ndjson");
      expect(target).toBeDefined();
      if (!target) return;
      if (field === "sha256") target.sha256 = "f".repeat(64);
      else target.size_bytes += 1;
      await sealPackage(fixture);
      await expectIntegrityFailure(fixture);
    } finally {
      await rm(fixture.dataRoot, { recursive: true, force: true });
    }
  });
}

test("@regression rejects a missing or inconsistent checksum index", async () => {
  const fixture = await createPackage(1);
  try {
    await writeFile(join(fixture.packageRoot, "artifact-sha256.txt"), "invalid\n", "utf8");
    await expectIntegrityFailure(fixture);
    await unlink(join(fixture.packageRoot, "artifact-sha256.txt"));
    await expectIntegrityFailure(fixture);
  } finally {
    await rm(fixture.dataRoot, { recursive: true, force: true });
  }
});

test("@regression rejects a substituted normalized NDJSON artifact", async () => {
  const fixture = await createPackage(1);
  try {
    await writeFile(
      join(fixture.packageRoot, "market-quality-observations.ndjson"),
      '{"source":"binance-usdm","canonical_symbol":"ATTACK"}\n',
      "utf8",
    );
    await expectIntegrityFailure(fixture);
  } finally {
    await rm(fixture.dataRoot, { recursive: true, force: true });
  }
});

test("@regression rejects declared row-count mismatch", async () => {
  const fixture = await createPackage(1);
  try {
    const counts = fixture.manifest.record_counts as Record<string, number>;
    counts.market_quality_observations += 1;
    await sealPackage(fixture);
    await expectIntegrityFailure(fixture);
  } finally {
    await rm(fixture.dataRoot, { recursive: true, force: true });
  }
});

test("@security rejects an unsafe artifact logical path", async () => {
  const fixture = await createPackage(1);
  try {
    const artifacts = fixture.manifest.artifacts as ArtifactIdentity[];
    artifacts[0].logical_name = "../request.json";
    await sealPackage(fixture);
    await expectIntegrityFailure(fixture);
  } finally {
    await rm(fixture.dataRoot, { recursive: true, force: true });
  }
});

test("@security rejects final and intermediate symlinks", async () => {
  const finalFixture = await createPackage(1);
  const intermediateFixture = await createPackage(1);
  try {
    const finalPath = join(finalFixture.packageRoot, "market-quality-observations.ndjson");
    const finalTarget = join(finalFixture.packageRoot, "quality-target.ndjson");
    await rename(finalPath, finalTarget);
    try {
      await symlink(finalTarget, finalPath, "file");
    } catch (error) {
      if ((error as NodeJS.ErrnoException).code === "EPERM") {
        test.skip(true, "the local Windows host does not grant symlink creation");
        return;
      }
      throw error;
    }
    await expectIntegrityFailure(finalFixture);

    const artifacts = intermediateFixture.manifest.artifacts as ArtifactIdentity[];
    const target = artifacts.find((item) => item.logical_name === "market-quality-observations.ndjson");
    expect(target).toBeDefined();
    if (!target) return;
    const original = join(intermediateFixture.packageRoot, target.logical_name);
    const realDirectory = join(intermediateFixture.packageRoot, "real");
    await mkdir(realDirectory);
    await rename(original, join(realDirectory, "market-quality-observations.ndjson"));
    await symlink(realDirectory, join(intermediateFixture.packageRoot, "linked"), "junction");
    target.logical_name = "linked/market-quality-observations.ndjson";
    await sealPackage(intermediateFixture);
    await expectIntegrityFailure(intermediateFixture);
  } finally {
    await rm(finalFixture.dataRoot, { recursive: true, force: true });
    await rm(intermediateFixture.dataRoot, { recursive: true, force: true });
  }
});

test("@regression reader fails closed without projecting partial rows", async () => {
  const fixture = await createPackage(1);
  try {
    await writeFile(join(fixture.packageRoot, "instrument-snapshots.ndjson"), "{}\n", "utf8");
    const reader = new MarketEvidenceReadModel({ dataRoot: fixture.dataRoot });
    await expect(reader.instruments()).rejects.toBeInstanceOf(MarketEvidenceDataUnavailableError);
  } finally {
    const metadata = await lstat(fixture.dataRoot);
    expect(metadata.isDirectory()).toBe(true);
    expect(relative(tmpdir(), fixture.dataRoot).startsWith("..")).toBe(false);
    await rm(fixture.dataRoot, { recursive: true, force: true });
  }
});
