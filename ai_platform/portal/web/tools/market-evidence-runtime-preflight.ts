import { lstat } from "node:fs/promises";
import { resolve } from "node:path";

import {
  MarketEvidenceIntegrityError,
  type VerifiedMarketEvidencePackage,
  verifyMarketEvidencePackage,
} from "../lib/market-evidence/integrity";

const RUN_ID_PATTERN = /^wickhunter-production-market-evidence-\d{8}-v\d+-r\d+$/u;
const MARKER = "__PORTAL_MARKET_EVIDENCE_VERIFIED__";

function record(value: unknown, field: string): Record<string, unknown> {
  if (typeof value !== "object" || value === null || Array.isArray(value)) {
    throw new MarketEvidenceIntegrityError(`${field} must be an object`);
  }
  return value as Record<string, unknown>;
}

function nonEmptyString(value: unknown, field: string): string {
  if (typeof value !== "string" || value.length === 0) {
    throw new MarketEvidenceIntegrityError(`${field} must be a non-empty string`);
  }
  return value;
}

async function regularDirectory(path: string): Promise<boolean> {
  try {
    const entry = await lstat(path);
    return entry.isDirectory() && !entry.isSymbolicLink();
  } catch {
    return false;
  }
}

async function runRoot(dataRoot: string, runId: string): Promise<string> {
  for (const candidate of [resolve(dataRoot, "runs", runId), resolve(dataRoot, runId)]) {
    if (await regularDirectory(candidate)) return candidate;
  }
  throw new MarketEvidenceIntegrityError(`bound run is unavailable: ${runId}`);
}

async function verifyRun(dataRoot: string, runId: string): Promise<VerifiedMarketEvidencePackage> {
  if (!RUN_ID_PATTERN.test(runId)) {
    throw new MarketEvidenceIntegrityError("run identity is invalid");
  }
  const root = await runRoot(dataRoot, runId);
  return verifyMarketEvidencePackage({
    dataRoot,
    packageRoot: resolve(root, "immutable-package"),
    runId,
  });
}

async function verifyBoundBaseV1(
  dataRoot: string,
  selected: VerifiedMarketEvidencePackage,
): Promise<string | null> {
  if (selected.version !== 2) return null;
  const binding = record(
    JSON.parse(selected.artifact("source-package-binding.json").toString("utf8")) as unknown,
    "source package binding",
  );
  const base = record(binding.base_v1, "base v1 binding");
  const baseRunId = nonEmptyString(base.run_id, "base v1 run identity");
  if (!RUN_ID_PATTERN.test(baseRunId) || !baseRunId.includes("-v1-")) {
    throw new MarketEvidenceIntegrityError("base v1 run identity is invalid");
  }
  const verifiedBase = await verifyRun(dataRoot, baseRunId);
  if (verifiedBase.version !== 1) {
    throw new MarketEvidenceIntegrityError("bound base package is not schema v1");
  }
  const manifestSha = nonEmptyString(
    verifiedBase.manifest.manifest_sha256,
    "base v1 manifest identity",
  );
  const requestSha = nonEmptyString(
    verifiedBase.manifest.request_sha256,
    "base v1 request identity",
  );
  const verificationManifestSha = nonEmptyString(
    verifiedBase.verification.manifest_sha256,
    "base v1 verification manifest identity",
  );
  if (
    base.manifest_sha256 !== manifestSha ||
    base.request_sha256 !== requestSha ||
    base.verification_manifest_sha256 !== verificationManifestSha
  ) {
    throw new MarketEvidenceIntegrityError("bound base v1 package identity mismatch");
  }
  return baseRunId;
}

async function main(): Promise<void> {
  const [dataRootArg, runId] = process.argv.slice(2);
  if (!dataRootArg || !runId) {
    throw new MarketEvidenceIntegrityError("usage: runtime-preflight <data-root> <run-id>");
  }
  const dataRoot = resolve(dataRootArg);
  const selected = await verifyRun(dataRoot, runId);
  const baseV1RunId = await verifyBoundBaseV1(dataRoot, selected);
  process.stdout.write(
    MARKER +
      JSON.stringify({
        run_id: runId,
        version: selected.version,
        base_v1_run_id: baseV1RunId,
      }),
  );
}

main().catch((error: unknown) => {
  const message = error instanceof Error ? error.message : "unknown verification failure";
  console.error(`Market Evidence runtime preflight failed: ${message}`);
  process.exitCode = 1;
});
