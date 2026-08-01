# WickHunter backend, frontend and Synology deployment audit

## 1. Executive summary

**Primary-auditor verdict: `FAIL`.**

The audit froze `develop` at `6419138e170844d0eb09d9381b4435900d802ab9` and reviewed the repository implementation of Market Evidence v1/v2, the Portal BFF/API/UI projection and Synology deployment definitions. No implementation file was modified.

Four `HIGH` findings prevent a passing verdict:

1. the Portal does not verify the immutable package hash/checksum chain before returning rows;
2. the v2 OKX supplement verifier follows intermediate-directory symlinks outside the package root;
3. the production Market Evidence API gate validates only presence of a session cookie, not the session, tenant membership or role;
4. collectors and deployment gates report healthy when the immutable request is unavailable.

Three `MEDIUM` findings cover temporal provenance, crash recovery and stale-status derivation. No `CRITICAL` condition or enabled trading authority was found.

The exact audited SHA has no GitHub status contexts or workflow runs. Local checkout-based validation was unavailable because the sandbox could not resolve GitHub. Historical CI for the PR #836 head was green, but it is not exact-head evidence. Independent fresh-session validation is also outstanding. These limitations do not remove the static `HIGH` findings, but they limit final assurance.

## 2. Audited baseline and time

- Repository: `blakinio/freqtrade`
- Base branch: `develop`
- Frozen audited SHA: `6419138e170844d0eb09d9381b4435900d802ab9`
- Audit time: `2026-08-01T13:08:51+02:00`
- Audit branch: `audit/FTAI-20260801-wickhunter-backend-frontend-deployment-audit-v1`
- Execution mode: `codex`
- Implementation authorized: `false`
- Primary phase result: `ready_for_validation`

The original starting SHA `8802d99476ad5d59e3e7a72cc99b4a10e0147a62` was stale. At live-state reconciliation, `develop` had advanced to the merge of PR #927. PR #927 changed only WH-02 replay files and is outside the functional audit boundary.

## 3. Scope and exclusions

### Included

- Market Evidence v1 collector, service, daemon, WH-01 adapter and canonical evidence verification.
- Market Evidence v2 OKX supplement, merge service and daemon.
- Portal Market Evidence read models, BFF routes, UI state contracts and E2E coverage.
- Synology collector images, Compose files, request-only workflows and Portal preview deployment.
- Relevant Python, Node/npm, GitHub Actions and container-version declarations.
- Active tasks, open PRs, exact-head CI state, review threads and material path changes.

### Excluded

- WH-02 replay implementation and profitability.
- PR #926 OIDC repair implementation.
- Risk Engine beyond absence of unauthorized linkage.
- Full Liquid20 audit.
- Production execution, credentials, private endpoints, orders and live capital.
- Real deployment, collector execution, request-only trigger and source acquisition.

## 4. Data flow and trust boundaries

```text
exact-one-file request PR
        |
        | trusted Synology runner, request identity and environment refusal
        v
persistent public-only collector v1/v2
        |
        | RW durable state boundary
        v
incremental state + prospective samples
        |
        | finalization / package verifier
        v
immutable package + manifest + checksums + verification report
        |
        | RO bind mount into Portal
        v
Portal server-side read model
        |
        | identity / tenant / RBAC boundary
        v
same-origin BFF APIs
        |
        | cache-control: no-store, bounded normalized response
        v
read-only UI
```

Trust boundaries assessed:

1. GitHub request identity to trusted runner.
2. Public exchange egress to normalization.
3. Writable incremental state to immutable publication.
4. Immutable storage to Portal read-only projection.
5. Browser identity/tenant boundary to BFF.
6. BFF response boundary to UI.

Findings `WH-ME-AUD-001`, `002`, `003` and `004` break boundaries 4, 3, 5 and deployment readiness respectively.

## 5. Evidence sources

- Exact repository files at `6419138e170844d0eb09d9381b4435900d802ab9`.
- PR metadata and changed-file lists for #753, #766, #833, #836, #926 and #927.
- Open PR review-thread queries for #833, #926 and #927.
- Exact-head GitHub status/workflow queries.
- Historical workflow runs for PR #836 head `5d608dd617d6a5e14ee197fc4b34b887d55bbbe2`.
- Compare `2e0c2b57376a0a0e4d6389961588d41a0b194115...6419138e170844d0eb09d9381b4435900d802ab9`.
- Static source/test/workflow/deployment inspection.
- Local capability probe for GitHub checkout.

The detailed mapping is in `evidence-index.md`.

## 6. Backend coverage matrix

| Control | Status | Evidence/result |
|---|---|---|
| Exact request schema and identity | PROVEN | v1/v2 loaders require fixed IDs, source order, geometry, catalog/universe hashes and authority flags. |
| Public endpoint allowlist | PROVEN | HTTPS host/path allowlists, disabled proxies and redirects, size bounds. |
| Credential/proxy/private endpoint refusal | PROVEN | Code, request workflows and focused tests. |
| Source/market/native-canonical identity | PROVEN | Strict source and symbol mappings; exact source-separated geometry. |
| Completed-candle exact coverage | PROVEN | 432-row exact intervals per source/symbol and confirmed OKX candles. |
| Temporal availability | DERIVED defect | `WH-ME-AUD-005`. |
| Gap detection | PROVEN | Exact cadence and coverage checks reject missing/duplicate rows. |
| Restart recovery | PROVEN defect | `WH-ME-AUD-006`. |
| Atomic final publication | PROVEN | Partial directory followed by atomic rename; existing final output is verified or refused. |
| No-overwrite | PROVEN | Exclusive creation and immutable final roots. |
| Path confinement and symlinks | FAILED | `WH-ME-AUD-002` and `WH-ME-AUD-008`. |
| Artifact SHA-256 and manifest self-hash | PARTIAL | Backend verifies hashes, but v2 supplement confinement is bypassable and Portal does not continue the chain. |
| Idempotent verification | PROVEN | Existing final packages are verified rather than overwritten. |
| v1/v2 source binding | PROVEN | Base run ID, capture geometry and source package binding are checked. |
| WH-01 readiness blocker | PROVEN | Combined package remains blocked on `LIQUIDATION_ARCHIVE_NOT_BOUND`. |
| Authority flags / zero orders | PROVEN | All reviewed collectors, packages and adapters keep authorities false and orders zero. |

## 7. Portal/API/UI coverage matrix

| Control | Status | Evidence/result |
|---|---|---|
| Explicit data root outside fixture mode | PROVEN | Missing production root returns safe 503. |
| Fixed-path confinement and direct symlink refusal | PROVEN | Root/run/files use fixed children and `lstat`; no client-provided paths. |
| Immutable package digest verification | FAILED | `WH-ME-AUD-001`. |
| Session, tenant and RBAC enforcement | FAILED | `WH-ME-AUD-003`. |
| Query validation and pagination | PROVEN | Source/quality/sort/direction/page bounds, max page size 100. |
| Response/file bounds | PROVEN | Metadata, NDJSON, row, run and response pagination bounds. |
| No host paths, parser detail, secrets/raw payloads | PROVEN by code/test design | Safe errors, normalized rows and E2E assertions. Exact-head execution remains UNKNOWN. |
| `cache-control: no-store` | PROVEN | Success and error routes. |
| Source separation and OKX capability mapping | PROVEN | Source-specific rows and v2 OKX overlay. |
| Status derivation | FAILED | Completed package cannot become STALE; `WH-ME-AUD-007`. |
| API/UI consistency | PARTIAL | Shared contracts and E2E fixtures exist; cryptographic trust and stale behavior are incorrect. |
| Loading/empty/unavailable/error UI states | PROVEN by source/test presence | Runtime execution on audited SHA is UNKNOWN. |
| Mutation/trade/order controls | PROVEN absent | GET-only Market Evidence routes and E2E assertions. |
| Corrupt/partial data fail-closed | PARTIAL | Parse/size errors fail closed, but validly parsed tampered rows are trusted without digest verification. |

## 8. Deployment and supply-chain coverage matrix

| Control | Status | Evidence/result |
|---|---|---|
| Non-root runtime | PROVEN | Configurable collector UID/GID; Portal runtime uses `node`. |
| Read-only root | PROVEN | Collector and Portal runtime definitions. |
| Capability drop / no-new-privileges | PROVEN | v1/v2 Compose and Portal deployment. |
| PID/memory limits | PROVEN | 128/512 MiB collectors; 256/768 MiB Portal preview. |
| Hardened tmpfs | PROVEN | noexec/nosuid/nodev for collectors. |
| Request `ro`, state `rw` | PROVEN | Both collector Compose files. |
| Host/container path consistency | PROVEN by static workflow review | Runner derives host bind source and passes matching container root. |
| No Portal Docker socket at runtime | PROVEN | Preview post-deploy inspection rejects socket mount. |
| Network exposure | PROVEN | Collectors publish no ports and do not use host network; bridge egress only. |
| Collector egress | PROVEN broad | Dedicated external bridge, but no network-level host allowlist. Application URL allowlists are present. |
| Health/readiness | FAILED | `WH-ME-AUD-004`. |
| Restart behavior | PARTIAL | Restart policy exists, but staged operation recovery is incomplete (`WH-ME-AUD-006`). |
| Bounded runner occupation | PROVEN | Persistent container owns sampling; scheduled polling job disabled. |
| Exact-one-file request trigger | PROVEN | Merge-base diff must equal one added canonical request file. |
| Immutable request identity | PROVEN | 0444 persisted request, compare-on-reuse, no symlinks. |
| Runner name/OS/architecture | PROVEN | Explicit assertions. |
| Credential/proxy refusal | PROVEN | Workflow and runtime checks. |
| Portal candidate/preflight/probes | PROVEN by static review | Read-only mounts, group readability, authenticated probes and bounded response checks. |
| Replacement and rollback | PROVEN by static review | Candidate first, previous-image rollback after failed replacement. |
| Base image and version pinning | PARTIAL | Portal image is digest-pinned; collectors are not (`WH-ME-AUD-009`). |
| GitHub Actions pinning | PROVEN | Reviewed actions use full commit SHAs. |

## 9. Validation commands and results

| Validation | Result |
|---|---|
| Freeze develop head | PASS — `6419138e170844d0eb09d9381b4435900d802ab9` |
| Open PR and review-thread reconciliation | PASS — #833/#926 open, no review threads; #927 merged and out of functional scope |
| Exact-head combined status | UNKNOWN — zero status contexts |
| Exact-head workflow runs | UNKNOWN — zero runs |
| Historical PR #836 head workflows | PASS for that historical head — Market Evidence CI `30591937630`, AI Platform CI `30591937626`, Portal Web `30591937576`, Portal E2E `30591937620`, Freqtrade CI `30591937588`, zizmor `30591937640` |
| Local checkout | BLOCKED — `git ls-remote` exit 128, `Could not resolve host: github.com` |
| Focused Python compile/pytest/ruff | NOT RUN — no checkout |
| Portal npm/typecheck/lint/build/Playwright | NOT RUN — no checkout |
| Docker Compose render/health script compile | NOT RUN — no checkout/Docker evidence in this sandbox |
| Static source/workflow/deployment review | PASS as an audit method; findings recorded |
| Independent validator session | NOT RUN — `WH-ME-AUD-012` |

No production operation or source acquisition was executed.

## 10. Findings by severity

### CRITICAL

None found.

### HIGH

- `WH-ME-AUD-001` — Portal projects package rows without verifying the immutable evidence chain.
- `WH-ME-AUD-002` — OKX supplement verifier follows intermediate-directory symlinks outside the package root.
- `WH-ME-AUD-003` — Market Evidence API authorization accepts any production session-cookie value.
- `WH-ME-AUD-004` — Collectors and deployment checks report healthy when the immutable request is unavailable.

### MEDIUM

- `WH-ME-AUD-005` — Completed-candle availability is backdated to close time without enforcing observed availability in WH-01.
- `WH-ME-AUD-006` — Crash recovery is fail-closed but not restart-resumable.
- `WH-ME-AUD-007` — Portal cannot classify an old completed immutable package as STALE.

### LOW

- `WH-ME-AUD-008` — v1 inner verifier loses symlink identity after resolving.
- `WH-ME-AUD-009` — Collector base images are not digest-pinned.
- `WH-ME-AUD-010` — Durable v2 task state conflicts with merged PR #836.

### INFO / assurance gaps

- `WH-ME-AUD-011` — No exact-head CI evidence exists.
- `WH-ME-AUD-012` — Independent validation is outstanding.

Complete structured findings are in `findings.json`.

## 11. UNKNOWN and CONFLICT

### UNKNOWN

- Exact-head focused CI conclusions for `6419138e170844d0eb09d9381b4435900d802ab9`.
- Local compile, pytest, ruff, npm, build, Playwright and Compose results.
- Real Synology permissions, image IDs, runtime health and rollback behavior.
- Independent fresh-session validation verdict.

### CONFLICT

- `WH-ME-AUD-010`: v2 task says `in_progress`/`validating` and still instructs merging PR #836; PR #836 is already merged and its head had terminal green workflows.

## 12. Positive controls confirmed

- Exact request schemas, source order, geometry, catalog/universe identity and authority boundaries are strict.
- Public acquisition uses explicit HTTPS allowlists, no redirects and no proxy routing.
- Recognized credential environments and private/mutating exchange endpoints are refused.
- Market rows preserve source labels and prevent cross-exchange deduplication.
- Exact 5-minute candle coverage and confirmed OKX candles are required.
- Atomic partial-to-final publication and no-overwrite behavior are present.
- Combined v2 package binds base v1 and OKX supplement identities and keeps WH-01 blocked until archive binding exists.
- Collector containers are non-root, read-only, capability-dropped, no-new-privileges, bounded and do not publish ports.
- Portal mounts evidence read-only, has no runtime Docker socket and contains no Market Evidence mutations or trading controls.
- All reviewed authority flags remain disabled and `orders_submitted == 0`.

## 13. Audit limitations

- The environment could access GitHub only through the connector; DNS prevented a local clone.
- No real Docker engine, browser run, Synology filesystem or production evidence package was available.
- Static code evidence establishes the reported defects, but dynamic exploit/regression reproduction is pending.
- No fresh independent validation session has yet reviewed severity or evidence-chain completeness.
- Open PR #926 was excluded from baseline and was not assessed as a fix.

## 14. Verdict

`FAIL`

Rationale: four `HIGH` defects break immutable evidence projection, path confinement, application authentication and deployment readiness. Exact-head CI and independent validation are additionally absent.

## 15. Minimal deduplicated recommended follow-up tasks

No task was created.

### A. End-to-end immutable evidence verification repair

- Root cause: verifier implementations are inconsistent and the Portal trusts metadata instead of verifying the package.
- Minimal owned scope: shared safe-member/digest verifier, v1/v2 package verification adapters, Portal read-model invocation, focused tamper/symlink tests.
- Acceptance: intermediate and final symlinks fail; any artifact/manifest/checksum mutation yields Portal `UNAVAILABLE`; valid v1/v2 fixtures remain readable.
- Dependencies: none beyond exact package contracts.
- Suggested severity/priority: `HIGH / P0`.
- One task: yes; keep backend verifier and Portal consumption in one task because they form one trust chain.

### B. Portal production session enforcement

- Root cause: production proxy checks only cookie presence.
- Minimal owned scope: shared Portal identity/session validation and Market Evidence production-mode authorization tests.
- Acceptance: forged, expired, revoked and cross-tenant cookies are denied; valid role/tenant membership succeeds; fixture behavior remains isolated to test mode.
- Dependencies: coordinate with, but do not assume, PR #926.
- Suggested severity/priority: `HIGH / P0`.
- One task: yes.

### C. Collector readiness and restart recovery

- Root cause: liveness/readiness states are conflated and write stages are not resumable.
- Minimal owned scope: daemon state model, healthchecks, deployment probes, sample/finalization staging and restart tests for v1/v2.
- Acceptance: missing request is not ready; SIGKILL at each write boundary resumes or deterministically reports a typed blocker without false healthy state.
- Dependencies: immutable request and no-overwrite contracts.
- Suggested severity/priority: `HIGH / P1`.
- One task: yes; v1/v2 share the same root cause.

### D. Temporal provenance and stale-state semantics

- Root cause: observed candle availability is not bound to acquisition time and completed-package age is ignored by Portal.
- Minimal owned scope: candle availability contract, WH-01 as-of checks, Portal completed-package freshness derivation and tests.
- Acceptance: post-decision acquisition cannot satisfy prospective availability; historical-only mode is explicit; completed packages become STALE according to policy.
- Dependencies: owner decision on prospective versus historical candle semantics.
- Suggested severity/priority: `MEDIUM / P1`.
- One task: yes after a short contract decision.

### E. Reproducibility and durable-state cleanup

- Root cause: unpinned collector base images and stale v2 checkpoint.
- Minimal owned scope: collector Dockerfile digests/SBOM metadata plus a separate documentation-only checkpoint repair.
- Acceptance: identical SHA rebuild resolves identical base digest; task state records merged SHA and exact workflow IDs.
- Dependencies: approved Python base digest.
- Suggested severity/priority: `LOW / P2`.
- One task: no; keep supply-chain change and historical checkpoint correction separate.
