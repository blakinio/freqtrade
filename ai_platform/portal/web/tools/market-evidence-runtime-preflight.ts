import { lstat, readdir } from "node:fs/promises";
import { relative, resolve, sep } from "node:path";

import {
  MarketEvidenceIntegrityError,
  type VerifiedMarketEvidencePackage,
  verifyMarketEvidencePackage,
} from "../lib/market-evidence/integrity";

const RUN_ID_PATTERN = /^wickhunter-production-market-evidence-\d{8}-v\d+-r\d+$/u;
const MARKER = "__PORTAL_MARKET_EVIDENCE_VERIFIED__";

interface MountedRun {
  run_id: string;
  relative_path: string;
}

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

async function runsRoot(dataRoot: string): Promise<string> {
  const nested = resolve(dataRoot, "runs");
  return (await regularDirectory(nested)) ? nested : dataRoot;
}

async function runRoot(dataRoot: string, runId: string): Promise<string> {
  for (const candidate of [resolve(dataRoot, "runs", runId), resolve(dataRoot, runId)]) {
    if (await regularDirectory(candidate)) return candidate;
  }
  throw new MarketEvidenceIntegrityError(`bound run is unavailable: ${runId}`);
}

function relativeRunPath(dataRoot: string, root: string, runId: string): string {
  const value = relative(resolve(dataRoot), resolve(root));
  if (value !== runId && value !== `runs${sep}${runId}`) {
    throw new MarketEvidenceIntegrityError("bound run path escaped the canonical data root");
  }
  return value.split(sep).join("/");
}

async function discoverSelectedRun(dataRoot: string): Promise<string> {
  const root = await runsRoot(dataRoot);
  const entries = await readdir(root, { withFileTypes: true });
  const candidates = entries
    .filter((entry) => entry.isDirectory() && !entry.isSymbolicLink() && RUN_ID_PATTERN.test(entry.name))
    .map((entry) => entry.name)
    .sort()
    .reverse();
  for (const runId of candidates) {
    if (await regularDirectory(resolve(root, runId, "immutable-package"))) return runId;
  }
  throw new MarketEvidenceIntegrityError("no verified immutable Market Evidence run is available");
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
): Promise<{ runId: string; verified: VerifiedMarketEvidencePackage } | null> {
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
  return { runId: baseRunId, verified: verifiedBase };
}

async function collectPackageAccessGroups(
  dataRoot: string,
  runId: string,
  verified: VerifiedMarketEvidencePackage,
  groupIds: Set<number>,
): Promise<MountedRun> {
  const root = await runRoot(dataRoot, runId);
  const runMetadata = await lstat(root);
  if (runMetadata.isSymbolicLink() || !runMetadata.isDirectory() || (runMetadata.mode & 0o050) !== 0o050) {
    throw new MarketEvidenceIntegrityError("run directory is not group-readable and traversable");
  }
  groupIds.add(runMetadata.gid);
  const packageRoot = resolve(root, "immutable-package");

  async function visit(path: string): Promise<void> {
    const metadata = await lstat(path);
    if (metadata.isSymbolicLink()) {
      throw new MarketEvidenceIntegrityError("runtime package path traverses a symlink");
    }
    groupIds.add(metadata.gid);
    if (metadata.isDirectory()) {
      if ((metadata.mode & 0o050) !== 0o050) {
        throw new MarketEvidenceIntegrityError("runtime package directory is not group-readable and traversable");
      }
      const children = await readdir(path, { withFileTypes: true });
      for (const child of children) {
        await visit(resolve(path, child.name));
      }
      return;
    }
    if (!metadata.isFile() || (metadata.mode & 0o040) !== 0o040) {
      throw new MarketEvidenceIntegrityError("runtime package member is not group-readable");
    }
  }

  await visit(packageRoot);
  verified.artifact("run-state.json");
  return { run_id: runId, relative_path: relativeRunPath(dataRoot, root, runId) };
}

async function main(): Promise<void> {
  const [dataRootArg, requestedRunId] = process.argv.slice(2);
  if (!dataRootArg) {
    throw new MarketEvidenceIntegrityError("usage: runtime-preflight <data-root> [run-id]");
  }
  const dataRoot = resolve(dataRootArg);
  const selectedRunId = requestedRunId || (await discoverSelectedRun(dataRoot));
  if (!RUN_ID_PATTERN.test(selectedRunId)) {
    throw new MarketEvidenceIntegrityError("selected run identity is invalid");
  }
  const selected = await verifyRun(dataRoot, selectedRunId);
  const base = await verifyBoundBaseV1(dataRoot, selected);
  const groupIds = new Set<number>();
  const mounts: MountedRun[] = [
    await collectPackageAccessGroups(dataRoot, selectedRunId, selected, groupIds),
  ];
  if (base) {
    mounts.push(await collectPackageAccessGroups(dataRoot, base.runId, base.verified, groupIds));
  }
  process.stdout.write(
    MARKER +
      JSON.stringify({
        run_id: selectedRunId,
        version: selected.version,
        base_v1_run_id: base?.runId ?? null,
        group_ids: [...groupIds].sort((left, right) => left - right),
        mounts,
      }),
  );
}

main().catch((error: unknown) => {
  const message = error instanceof Error ? error.message : "unknown verification failure";
  console.error(`Market Evidence runtime preflight failed: ${message}`);
  process.exitCode = 1;
});
