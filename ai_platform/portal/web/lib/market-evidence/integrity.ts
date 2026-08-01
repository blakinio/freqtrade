import { createHash } from "node:crypto";
import { lstat, readFile, realpath } from "node:fs/promises";
import {
  isAbsolute,
  relative,
  resolve,
  sep,
  win32,
} from "node:path";

const MAX_METADATA_BYTES = 8 * 1024 * 1024;
const MAX_ARTIFACT_BYTES = 64 * 1024 * 1024;
const MAX_PACKAGE_BYTES = 256 * 1024 * 1024;
const MAX_ARTIFACTS = 1_000;
const MAX_NDJSON_ROWS = 30_000;
const SHA256_PATTERN = /^[0-9a-f]{64}$/u;
const RUN_ID_PATTERN = /^wickhunter-production-market-evidence-\d{8}-v\d+-r\d+$/u;
const V1_SOURCES = ["bybit-linear", "binance-usdm"] as const;
const V2_SOURCES = [...V1_SOURCES, "okx-swap"] as const;
const AUTHORITY = {
  execution_enabled: false,
  orders_submitted: 0,
  trading_credentials_present: false,
  model_execution_authorized: false,
  replay_authorized: false,
  performance_research_authorized: false,
  live_capital_authorized: false,
} as const;
const V1_ARTIFACTS = [
  "request.json",
  "policy.json",
  "run-state.json",
  "source-snapshots.ndjson",
  "market-quality-observations.ndjson",
  "instrument-snapshots.ndjson",
  "completed-candles-index.json",
  "source-artifacts-index.json",
] as const;
const V2_ARTIFACTS = [
  "request.json",
  "source-package-binding.json",
  "run-state.json",
  "source-snapshots.ndjson",
  "market-quality-observations.ndjson",
  "instrument-snapshots.ndjson",
  "completed-candles-index.json",
] as const;

interface ArtifactIdentity {
  logical_name: string;
  sha256: string;
  size_bytes: number;
}

export interface VerifyMarketEvidencePackageOptions {
  dataRoot: string;
  packageRoot: string;
  runId: string;
}

export interface VerifiedMarketEvidencePackage {
  version: 1 | 2;
  runId: string;
  packageRoot: string;
  manifest: Record<string, unknown>;
  state: Record<string, unknown>;
  verification: Record<string, unknown>;
  artifact(logicalName: string): Buffer;
}

export class MarketEvidenceIntegrityError extends Error {}

function record(value: unknown, field: string): Record<string, unknown> {
  if (typeof value !== "object" || value === null || Array.isArray(value)) {
    throw new MarketEvidenceIntegrityError(`${field} must be an object`);
  }
  return value as Record<string, unknown>;
}

function array(value: unknown, field: string): unknown[] {
  if (!Array.isArray(value)) throw new MarketEvidenceIntegrityError(`${field} must be a list`);
  return value;
}

function safeInteger(value: unknown, field: string): number {
  if (typeof value !== "number" || !Number.isSafeInteger(value) || value < 0) {
    throw new MarketEvidenceIntegrityError(`${field} must be a non-negative safe integer`);
  }
  return value;
}

function sha256(value: Buffer | string): string {
  return createHash("sha256").update(value).digest("hex");
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
  return sha256(JSON.stringify(sortedValue(value)));
}

function exactArray(value: unknown, expected: readonly string[], field: string): void {
  if (
    !Array.isArray(value) ||
    value.length !== expected.length ||
    expected.some((item, index) => value[index] !== item)
  ) {
    throw new MarketEvidenceIntegrityError(`${field} mismatch`);
  }
}

function authorityIsSafe(value: unknown, field: string): void {
  const candidate = record(value, field);
  if (Object.entries(AUTHORITY).some(([key, expected]) => candidate[key] !== expected)) {
    throw new MarketEvidenceIntegrityError(`${field} authority boundary mismatch`);
  }
}

function flatAuthorityIsSafe(value: Record<string, unknown>, field: string): void {
  if (Object.entries(AUTHORITY).some(([key, expected]) => value[key] !== expected)) {
    throw new MarketEvidenceIntegrityError(`${field} authority boundary mismatch`);
  }
}

function parseJson(content: Buffer, field: string): Record<string, unknown> {
  try {
    return record(JSON.parse(content.toString("utf8")) as unknown, field);
  } catch (error) {
    if (error instanceof MarketEvidenceIntegrityError) throw error;
    throw new MarketEvidenceIntegrityError(`${field} is invalid JSON`);
  }
}

function parseIdentity(value: unknown, field: string): ArtifactIdentity {
  const candidate = record(value, field);
  const logicalName = candidate.logical_name;
  const digest = candidate.sha256;
  const size = candidate.size_bytes;
  if (typeof logicalName !== "string" || logicalName.length === 0) {
    throw new MarketEvidenceIntegrityError(`${field} logical name is invalid`);
  }
  if (typeof digest !== "string" || !SHA256_PATTERN.test(digest)) {
    throw new MarketEvidenceIntegrityError(`${field} SHA-256 is invalid`);
  }
  return { logical_name: logicalName, sha256: digest, size_bytes: safeInteger(size, `${field} size`) };
}

async function safeDirectoryTree(dataRoot: string, packageRoot: string): Promise<void> {
  const root = resolve(dataRoot);
  const candidate = resolve(packageRoot);
  const lexical = relative(root, candidate);
  if (!lexical || lexical === ".." || lexical.startsWith(`..${sep}`) || isAbsolute(lexical)) {
    throw new MarketEvidenceIntegrityError("package root escapes the configured data root");
  }
  let current = root;
  for (const part of ["", ...lexical.split(sep)]) {
    if (part) current = resolve(current, part);
    let metadata;
    try {
      metadata = await lstat(current);
    } catch {
      throw new MarketEvidenceIntegrityError("package path component is missing");
    }
    if (metadata.isSymbolicLink() || !metadata.isDirectory()) {
      throw new MarketEvidenceIntegrityError("package path traverses a symlink or non-directory");
    }
  }
  const resolvedRoot = await realpath(root);
  const resolvedCandidate = await realpath(candidate);
  const confined = relative(resolvedRoot, resolvedCandidate);
  if (confined === ".." || confined.startsWith(`..${sep}`) || isAbsolute(confined)) {
    throw new MarketEvidenceIntegrityError("package root escapes the configured data root");
  }
}

async function safeMember(packageRoot: string, logicalName: string): Promise<string> {
  const parts = logicalName.split("/");
  if (
    !logicalName ||
    logicalName.includes("\\") ||
    logicalName.includes("\0") ||
    logicalName.startsWith("/") ||
    win32.isAbsolute(logicalName) ||
    Boolean(win32.parse(logicalName).root) ||
    parts.some((part) => part === "" || part === "." || part === "..")
  ) {
    throw new MarketEvidenceIntegrityError("artifact logical path is unsafe");
  }
  let current = packageRoot;
  for (const [index, part] of parts.entries()) {
    current = resolve(current, part);
    let metadata;
    try {
      metadata = await lstat(current);
    } catch {
      throw new MarketEvidenceIntegrityError("artifact member is missing");
    }
    if (metadata.isSymbolicLink()) {
      throw new MarketEvidenceIntegrityError("artifact path traverses a symlink");
    }
    if (index < parts.length - 1 && !metadata.isDirectory()) {
      throw new MarketEvidenceIntegrityError("artifact path component is not a directory");
    }
    if (index === parts.length - 1 && !metadata.isFile()) {
      throw new MarketEvidenceIntegrityError("artifact member is not a regular file");
    }
  }
  const resolvedRoot = await realpath(packageRoot);
  const resolvedMember = await realpath(current);
  const confined = relative(resolvedRoot, resolvedMember);
  if (confined === ".." || confined.startsWith(`..${sep}`) || isAbsolute(confined)) {
    throw new MarketEvidenceIntegrityError("artifact path escapes its immutable root");
  }
  return current;
}

async function boundedMember(
  packageRoot: string,
  logicalName: string,
  limit: number,
): Promise<Buffer> {
  const path = await safeMember(packageRoot, logicalName);
  const metadata = await lstat(path);
  if (metadata.size > limit) {
    throw new MarketEvidenceIntegrityError(`${logicalName} exceeds its bounded size limit`);
  }
  const content = await readFile(path);
  if (content.length !== metadata.size) {
    throw new MarketEvidenceIntegrityError(`${logicalName} changed while being verified`);
  }
  return content;
}

function parseRows(content: Buffer, field: string): Record<string, unknown>[] {
  const lines = content
    .toString("utf8")
    .split(/\r?\n/u)
    .filter((line) => line.trim().length > 0);
  if (lines.length > MAX_NDJSON_ROWS) {
    throw new MarketEvidenceIntegrityError(`${field} exceeds its bounded row limit`);
  }
  return lines.map((line, index) => {
    try {
      return record(JSON.parse(line) as unknown, `${field} row ${index + 1}`);
    } catch (error) {
      if (error instanceof MarketEvidenceIntegrityError) throw error;
      throw new MarketEvidenceIntegrityError(`${field} row ${index + 1} is invalid JSON`);
    }
  });
}

function validateRows(
  buffers: ReadonlyMap<string, Buffer>,
  manifest: Record<string, unknown>,
  identities: ReadonlyMap<string, ArtifactIdentity>,
  version: 1 | 2,
): void {
  const counts = record(manifest.record_counts, "record counts");
  const sources = array(manifest.sources, "sources");
  const instruments = array(manifest.instruments, "instruments");
  if (!instruments.length || instruments.some((item) => typeof item !== "string")) {
    throw new MarketEvidenceIntegrityError("instrument coverage is invalid");
  }
  const rowFiles = [
    ["source-snapshots.ndjson", "source_health_snapshots"],
    ["market-quality-observations.ndjson", "market_quality_observations"],
    ["instrument-snapshots.ndjson", "instrument_snapshots"],
  ] as const;
  for (const [logicalName, countField] of rowFiles) {
    const content = buffers.get(logicalName);
    if (!content) throw new MarketEvidenceIntegrityError(`${logicalName} is missing after verification`);
    const rows = parseRows(content, logicalName);
    if (rows.length !== safeInteger(counts[countField], countField)) {
      throw new MarketEvidenceIntegrityError(`${countField} row count mismatch`);
    }
    for (const row of rows) {
      if (!sources.includes(row.source)) {
        throw new MarketEvidenceIntegrityError(`${logicalName} source geometry mismatch`);
      }
      if (
        logicalName !== "source-snapshots.ndjson" &&
        !instruments.includes(row.canonical_symbol)
      ) {
        throw new MarketEvidenceIntegrityError(`${logicalName} instrument geometry mismatch`);
      }
    }
  }
  const indexContent = buffers.get("completed-candles-index.json");
  if (!indexContent) throw new MarketEvidenceIntegrityError("completed candle index is missing");
  let parsed: unknown;
  try {
    parsed = JSON.parse(indexContent.toString("utf8")) as unknown;
  } catch {
    throw new MarketEvidenceIntegrityError("completed candle index is invalid JSON");
  }
  const entries = array(
    version === 2 ? record(parsed, "completed candle index").artifacts : parsed,
    "completed candle artifacts",
  );
  const expectedPairs = new Set(
    sources.flatMap((source) => instruments.map((symbol) => `${String(source)}:${String(symbol)}`)),
  );
  let completedCandles = 0;
  for (const item of entries) {
    const candle = record(item, "completed candle artifact");
    const source = String(candle.source ?? "");
    const symbol = String(candle.symbol ?? "");
    const pair = `${source}:${symbol}`;
    if (!expectedPairs.delete(pair)) {
      throw new MarketEvidenceIntegrityError("completed candle source-symbol geometry mismatch");
    }
    completedCandles += safeInteger(candle.record_count, "completed candle record count");
    const normalized = parseIdentity(candle.normalized_file, "normalized candle identity");
    if (version === 2) {
      const declared = identities.get(normalized.logical_name);
      if (
        !declared ||
        declared.sha256 !== normalized.sha256 ||
        declared.size_bytes !== normalized.size_bytes
      ) {
        throw new MarketEvidenceIntegrityError("normalized candle identity mismatch");
      }
    }
  }
  if (expectedPairs.size !== 0) {
    throw new MarketEvidenceIntegrityError("completed candle coverage is incomplete");
  }
  if (completedCandles !== safeInteger(counts.completed_candles, "completed candles")) {
    throw new MarketEvidenceIntegrityError("completed candle row count mismatch");
  }
}

function validateCompletion(
  manifest: Record<string, unknown>,
  state: Record<string, unknown>,
  verification: Record<string, unknown>,
  runId: string,
  version: 1 | 2,
  artifactCount: number,
): void {
  if (
    manifest.schema_version !== version ||
    manifest.artifact_type !== "WickHunterProductionMarketEvidencePackage" ||
    manifest.run_id !== runId ||
    manifest.state !== "completed" ||
    manifest.verification_result !== "accepted"
  ) {
    throw new MarketEvidenceIntegrityError("immutable package completion identity mismatch");
  }
  if (
    state.schema_version !== version ||
    state.run_id !== runId ||
    state.state !== "completed" ||
    state.active !== false ||
    state.verification_result !== "accepted"
  ) {
    throw new MarketEvidenceIntegrityError("immutable run-state identity mismatch");
  }
  if (
    verification.schema_version !== version ||
    verification.run_id !== runId ||
    verification.outcome !== "accepted" ||
    verification.manifest_sha256 !== manifest.manifest_sha256 ||
    verification.artifact_count !== artifactCount
  ) {
    throw new MarketEvidenceIntegrityError("verification report identity mismatch");
  }
  if (
    version === 2 &&
    verification.binding_sha256 !== manifest.source_package_binding_sha256
  ) {
    throw new MarketEvidenceIntegrityError("verification binding identity mismatch");
  }
  authorityIsSafe(manifest.authorities, "manifest");
  flatAuthorityIsSafe(state, "run state");
  flatAuthorityIsSafe(verification, "verification report");
  const expectedSources = version === 1 ? V1_SOURCES : V2_SOURCES;
  exactArray(manifest.sources, expectedSources, "source coverage");
  const capture = record(manifest.capture, "capture geometry");
  const preRollStart = safeInteger(capture.pre_roll_start_ms, "pre-roll start");
  const decisionStart = safeInteger(capture.decision_start_ms, "decision start");
  const decisionEnd = safeInteger(capture.decision_end_ms, "decision end");
  if (
    preRollStart >= decisionStart ||
    decisionStart >= decisionEnd ||
    capture.pre_roll_ms !== decisionStart - preRollStart ||
    capture.cadence_seconds !== 300 ||
    capture.timeframe !== "5m"
  ) {
    throw new MarketEvidenceIntegrityError("capture geometry mismatch");
  }
  const counts = record(manifest.record_counts, "record counts");
  for (const field of [
    "market_quality_observations",
    "instrument_snapshots",
    "source_health_snapshots",
    "completed_candles",
  ]) {
    const expected = safeInteger(counts[field], field);
    if (verification[field] !== expected) {
      throw new MarketEvidenceIntegrityError(`verification ${field} mismatch`);
    }
  }
  if (!Array.isArray(manifest.gaps)) {
    throw new MarketEvidenceIntegrityError("gap geometry is invalid");
  }
}

function validateV1Identities(
  manifest: Record<string, unknown>,
  buffers: ReadonlyMap<string, Buffer>,
  identities: ReadonlyMap<string, ArtifactIdentity>,
  runId: string,
): void {
  const request = parseJson(buffers.get("request.json") ?? Buffer.alloc(0), "request");
  if (request.run_id !== runId) throw new MarketEvidenceIntegrityError("request run identity mismatch");
  if (
    manifest.request_sha256 !== identities.get("request.json")?.sha256 ||
    manifest.policy_sha256 !== identities.get("policy.json")?.sha256
  ) {
    throw new MarketEvidenceIntegrityError("v1 request or policy identity mismatch");
  }
  if (
    typeof manifest.inner_manifest_sha256 !== "string" ||
    !SHA256_PATTERN.test(manifest.inner_manifest_sha256) ||
    manifest.run_root_identity_sha256 !==
      canonicalSha256({ run_id: runId, inner: manifest.inner_manifest_sha256 })
  ) {
    throw new MarketEvidenceIntegrityError("v1 inner package identity mismatch");
  }
}

function validateV2Identities(
  manifest: Record<string, unknown>,
  buffers: ReadonlyMap<string, Buffer>,
  identities: ReadonlyMap<string, ArtifactIdentity>,
  runId: string,
): void {
  if (manifest.contract_id !== "wickhunter-production-market-evidence-v2") {
    throw new MarketEvidenceIntegrityError("v2 contract identity mismatch");
  }
  const request = parseJson(buffers.get("request.json") ?? Buffer.alloc(0), "request");
  if (
    request.run_id !== runId ||
    typeof manifest.base_request_identity_sha256 !== "string" ||
    !SHA256_PATTERN.test(manifest.base_request_identity_sha256)
  ) {
    throw new MarketEvidenceIntegrityError("v2 request identity mismatch");
  }
  const binding = parseJson(
    buffers.get("source-package-binding.json") ?? Buffer.alloc(0),
    "source package binding",
  );
  const bindingSeed = { ...binding };
  delete bindingSeed.binding_sha256;
  if (
    typeof binding.binding_sha256 !== "string" ||
    !SHA256_PATTERN.test(binding.binding_sha256) ||
    canonicalSha256(bindingSeed) !== binding.binding_sha256 ||
    manifest.source_package_binding_sha256 !== binding.binding_sha256 ||
    binding.run_id !== runId
  ) {
    throw new MarketEvidenceIntegrityError("source package binding identity mismatch");
  }
  exactArray(binding.sources, V2_SOURCES, "binding source coverage");
  const manifestInstruments = array(manifest.instruments, "manifest instruments");
  exactArray(binding.symbols, manifestInstruments.map(String), "binding symbol coverage");
  const manifestCapture = record(manifest.capture, "manifest capture");
  const bindingGeometry = record(binding.geometry, "binding geometry");
  for (const key of ["pre_roll_start_ms", "decision_start_ms", "decision_end_ms"] as const) {
    if (bindingGeometry[key] !== manifestCapture[key]) {
      throw new MarketEvidenceIntegrityError("binding capture geometry mismatch");
    }
  }
  if (
    binding.source_separated !== true ||
    binding.cross_exchange_deduplication !== false ||
    binding.immutable_inputs_mutated !== false
  ) {
    throw new MarketEvidenceIntegrityError("binding authority semantics mismatch");
  }
  flatAuthorityIsSafe(binding, "source package binding");
  const base = record(binding.base_v1, "base v1 binding");
  const supplement = record(binding.okx_supplement, "OKX supplement binding");
  for (const [field, value] of [
    ["base manifest", base.manifest_sha256],
    ["base request", base.request_sha256],
    ["base verification", base.verification_manifest_sha256],
    ["supplement manifest", supplement.manifest_sha256],
    ["supplement request", supplement.request_sha256],
    ["supplement verification", supplement.verification_manifest_sha256],
  ] as const) {
    if (typeof value !== "string" || !SHA256_PATTERN.test(value)) {
      throw new MarketEvidenceIntegrityError(`${field} identity mismatch`);
    }
  }
  if (
    base.run_id !== manifest.base_v1_run_id ||
    base.verification_manifest_sha256 !== base.manifest_sha256 ||
    supplement.run_id !== runId ||
    supplement.verification_manifest_sha256 !== supplement.manifest_sha256 ||
    supplement.request_sha256 !== identities.get("request.json")?.sha256
  ) {
    throw new MarketEvidenceIntegrityError("supplement package identity mismatch");
  }
}

export async function verifyMarketEvidencePackage(
  options: VerifyMarketEvidencePackageOptions,
): Promise<VerifiedMarketEvidencePackage> {
  if (!RUN_ID_PATTERN.test(options.runId)) {
    throw new MarketEvidenceIntegrityError("run identity is invalid");
  }
  await safeDirectoryTree(options.dataRoot, options.packageRoot);
  const manifestContent = await boundedMember(
    options.packageRoot,
    "manifest.json",
    MAX_METADATA_BYTES,
  );
  const manifest = parseJson(manifestContent, "manifest");
  const version = manifest.schema_version;
  if (version !== 1 && version !== 2) {
    throw new MarketEvidenceIntegrityError("package schema version is unsupported");
  }
  if (!options.runId.includes(`-v${version}-`)) {
    throw new MarketEvidenceIntegrityError("package schema and run identity mismatch");
  }
  const claimedManifestSha = manifest.manifest_sha256;
  const manifestSeed = { ...manifest };
  delete manifestSeed.manifest_sha256;
  if (
    typeof claimedManifestSha !== "string" ||
    !SHA256_PATTERN.test(claimedManifestSha) ||
    canonicalSha256(manifestSeed) !== claimedManifestSha
  ) {
    throw new MarketEvidenceIntegrityError("manifest self-hash mismatch");
  }
  const rawArtifacts = array(manifest.artifacts, "manifest artifacts");
  if (rawArtifacts.length === 0 || rawArtifacts.length > MAX_ARTIFACTS) {
    throw new MarketEvidenceIntegrityError("manifest artifact index is invalid");
  }
  const identities = new Map<string, ArtifactIdentity>();
  for (const [index, item] of rawArtifacts.entries()) {
    const parsed = parseIdentity(item, `artifact ${index + 1}`);
    if (identities.has(parsed.logical_name)) {
      throw new MarketEvidenceIntegrityError("manifest contains duplicate artifact paths");
    }
    identities.set(parsed.logical_name, parsed);
  }
  const required = version === 1 ? V1_ARTIFACTS : V2_ARTIFACTS;
  if (required.some((name) => !identities.has(name)) || (version === 1 && identities.size !== required.length)) {
    throw new MarketEvidenceIntegrityError(`v${version} required artifact set mismatch`);
  }
  const buffers = new Map<string, Buffer>();
  let totalBytes = 0;
  for (const item of identities.values()) {
    if (item.size_bytes > MAX_ARTIFACT_BYTES) {
      throw new MarketEvidenceIntegrityError("declared artifact exceeds the bounded size limit");
    }
    totalBytes += item.size_bytes;
    if (totalBytes > MAX_PACKAGE_BYTES) {
      throw new MarketEvidenceIntegrityError("declared package exceeds the bounded size limit");
    }
    const content = await boundedMember(options.packageRoot, item.logical_name, MAX_ARTIFACT_BYTES);
    if (content.length !== item.size_bytes || sha256(content) !== item.sha256) {
      throw new MarketEvidenceIntegrityError("declared artifact identity mismatch");
    }
    buffers.set(item.logical_name, content);
  }
  const manifestIdentity = `${sha256(manifestContent)}  manifest.json`;
  const expectedChecksum = new Set([
    ...[...identities.values()].map((item) => `${item.sha256}  ${item.logical_name}`),
    manifestIdentity,
  ]);
  const checksumContent = await boundedMember(
    options.packageRoot,
    "artifact-sha256.txt",
    MAX_METADATA_BYTES,
  );
  const checksumLines = checksumContent
    .toString("utf8")
    .split(/\r?\n/u)
    .filter((line) => line.length > 0);
  if (
    checksumLines.length !== expectedChecksum.size ||
    new Set(checksumLines).size !== checksumLines.length ||
    checksumLines.some((line) => !expectedChecksum.has(line))
  ) {
    throw new MarketEvidenceIntegrityError("checksum index mismatch");
  }
  const state = parseJson(buffers.get("run-state.json") ?? Buffer.alloc(0), "run state");
  const verification = parseJson(
    await boundedMember(options.packageRoot, "verification-report.json", MAX_METADATA_BYTES),
    "verification report",
  );
  validateCompletion(manifest, state, verification, options.runId, version, identities.size);
  if (version === 1) validateV1Identities(manifest, buffers, identities, options.runId);
  else validateV2Identities(manifest, buffers, identities, options.runId);
  validateRows(buffers, manifest, identities, version);
  return {
    version,
    runId: options.runId,
    packageRoot: options.packageRoot,
    manifest,
    state,
    verification,
    artifact(logicalName: string): Buffer {
      const content = buffers.get(logicalName);
      if (!content) throw new MarketEvidenceIntegrityError("verified artifact is unavailable");
      return content;
    },
  };
}

export function parseVerifiedNdjson(
  verified: VerifiedMarketEvidencePackage,
  logicalName: string,
  field: string,
): Record<string, unknown>[] {
  return parseRows(verified.artifact(logicalName), field);
}
