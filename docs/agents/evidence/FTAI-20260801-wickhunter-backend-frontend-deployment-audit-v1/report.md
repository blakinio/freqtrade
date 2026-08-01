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

Fresh validation found exact-SHA CI that was unavailable to the primary auditor. `AI Platform CI` run `30696775622` and `Freqtrade CI` run `30696775642` both completed successfully for the exact audited SHA, as did equivalent push runs. Those workflows prove broad Python/core checks, but no exact-SHA dedicated Market Evidence workflow, Portal npm/Playwright job or Compose validation ran. Independent source review and focused runtime probes confirmed all four `HIGH` findings.

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
| Exact-head combined status | No legacy status contexts; Actions evidence exists separately |
| Exact-head workflow runs | PARTIAL PASS — exact SHA has successful AI Platform CI `30696775622` and Freqtrade CI `30696775642`; no dedicated Market Evidence, Portal npm/Playwright or Compose run |
| Historical PR #836 head workflows | PASS for that historical head — Market Evidence CI `30591937630`, AI Platform CI `30591937626`, Portal Web `30591937576`, Portal E2E `30591937620`, Freqtrade CI `30591937588`, zizmor `30591937640` |
| Local checkout | PASS — audit branch cloned at `ccbd8aa1c93e6da630c515cff4040e19713db924`; frozen SHA available locally |
| Focused Python compile/pytest/ruff | PASS — compile succeeded; 18 focused integration tests passed under WSL; Ruff `0.15.21` passed |
| Portal npm/typecheck/lint/build | PASS — exact dependencies installed; typecheck and build passed; lint had one unrelated warning and zero errors |
| Focused exploit/readiness probes | PASS as reproductions — v2 verifier accepted an out-of-root file through an intermediate symlink; forged production cookie changed Market Evidence response from 401 to 200; blocked v1/v2 results passed both healthchecks and workflow predicates |
| Playwright | NOT RUN — fixture-identity browser tests do not exercise the disputed production-cookie path; the smaller production-mode API probe did |
| Docker Compose render | BLOCKED — Docker engine unavailable; static Compose review and healthcheck execution completed |
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

- `WH-ME-AUD-011` — Exact-head general CI exists, but dedicated Market Evidence/Portal/Compose assurance is absent.
- `WH-ME-AUD-012` — Independent validation completed in this report.

Complete structured findings are in `findings.json`.

## 11. UNKNOWN and CONFLICT

### UNKNOWN

- Exact-head dedicated Market Evidence, Portal npm/Playwright and Compose conclusions.
- Real Compose rendering with a running Docker engine.
- Real Synology permissions, image IDs, runtime health and rollback behavior.

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

- No real Docker engine, Synology filesystem or production evidence package was available.
- Playwright was not run because its fixture identity mode cannot validate the production-cookie defect; a smaller production Next.js server probe was used instead.
- The Windows-native focused pytest attempt was non-representative because `Path.as_uri()` round-tripping differs from the Linux deployment target; the same 18 tests passed under WSL/Linux.
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

## 16. Independent validation

Independent-validator verdict: `FAIL`.

### Live state and post-freeze scope

- Audit branch and initial validator HEAD: `audit/FTAI-20260801-wickhunter-backend-frontend-deployment-audit-v1` at `ccbd8aa1c93e6da630c515cff4040e19713db924`.
- The checkpoint's `f9e52e74ae9a1389735147860eb8d45aaae06088` was followed only by three audit-artifact commits: `d11523210`, `301571682` and `ccbd8aa1c`; it was not a competing implementation head.
- No PR exists for the audit branch, only one worktree was present, and no concurrent writer was found.
- The requested post-freeze range through `d6cb539c...` contains seven commits and has a two-file net diff: `deploy/synology/portal-oidc/deploy.py` removes the invalid trailing `,rw` bind option, and its test records default read-write semantics.
- Before commit, `develop` advanced by six more commits to `5cffc1902479bdaffb753622925f9e92b294a9c8`. The additional range changes only `ai_platform/wickhunter/replay_price_path.py`, its WH-02 regression test and a WH-02 task record to accept Binance `transact_time` headers.
- Scope-invalidation decision: `UNCHANGED` for both ranges. The OIDC change enables the existing control-plane state mount, while the later change is WH-02 replay-only. Neither alters Portal middleware, production session validation, Market Evidence routes/readers, collector daemons, healthchecks or production workflows. The identity backend already contains strong session validation; Market Evidence bypasses it.

### Independent finding dispositions

| Finding | Disposition | Classification | Severity | Confidence | Independent result |
|---|---|---|---|---|---|
| `WH-ME-AUD-001` | `CONFIRMED` | immutable-evidence integrity verification bypass | `HIGH` | high | v1 and v2 API paths read normalized rows after metadata predicates only. Neither reader verifies manifest self-hash, artifact SHA-256, artifact size or checksum index. v1 checks run IDs and authority metadata but not request/binding identities or actual row geometry; v2 checks run ID, exact source labels and authority metadata but not request/base bindings or actual row geometry. A host writer, compromised publisher or storage corruption that leaves parseable metadata can therefore change projected evidence. Invoke a complete read-only package verifier before projection and fail closed. |
| `WH-ME-AUD-002` | `CONFIRMED` | path-confinement bypass | `HIGH` | high | `verify_supplement` validates relative syntax and only the final path's symlink bit, then hashes through intermediate parents. A Linux regression probe created `root/candles -> outside` and a valid outside regular file with matching digest/size; the verifier returned `accepted` with `escaped_root=true`. The service's `_safe_member` is stronger but is not called here. Prerequisite: ability to supply or alter a supplement package/member layout. Share component-wise safe-member resolution and add intermediate-parent tests. |
| `WH-ME-AUD-003` | `CONFIRMED` | application authentication/authorization bypass | `HIGH` | high | Production middleware checks only cookie presence. Market Evidence handlers do not call `/v1/identity/session` or enforce tenant/role state. A production-mode Next.js probe returned 401 without a cookie and 200 for `__Host-portal_session=forged-arbitrary-value`. The deployed identity backend can validate hashed token existence, revocation, expiry, principal, membership, membership version, roles and MFA, but no reviewed ingress contract performs that validation on these routes. Prerequisite: network reachability to the Portal origin or passage through any independent edge gate. The data is read-only public-market evidence, but the documented application tenant/RBAC boundary is bypassed. Validate every protected request against the session backend and authorize the route. |
| `WH-ME-AUD-004` | `CONFIRMED` | liveness/readiness conflation | `HIGH` | high | Both daemons return `blocked/CAPTURE_REQUEST_UNAVAILABLE` for a missing immutable request and derive `healthy=true` because only `failed`/`rejected` are unhealthy. A focused v1/v2 probe produced `healthy=true`, healthcheck exit 0 and a passing workflow predicate for both versions. Accepted container states are every fresh `healthy=true` payload; accepted workflow states are every status except `failed` and `rejected`, including `blocked`. Prerequisite: missing, unreadable or mis-mounted request before initialization. Keep liveness separate and require explicit readiness states that exclude `blocked`. |

### Deduplication and overlap

- `WH-ME-AUD-001` and `WH-ME-AUD-002` share the immutable-evidence trust chain but are not duplicates: one omits verification at the Portal consumer, the other bypasses confinement inside a backend verifier.
- `WH-ME-AUD-001` partially overlaps `WH-ME-AUD-007` only at Portal output; integrity verification and stale-state derivation have different root causes and remediations.
- `WH-ME-AUD-002` partially overlaps `WH-ME-AUD-008` as unsafe-path handling, but v2 permits out-of-root traversal while v1 loses an in-root symlink invariant. They remain distinct findings, though one shared safe-member primitive can repair both.
- `WH-ME-AUD-003` is independent. Existing identity PRs implement a capable backend but do not bind Market Evidence routes to it; PR #926/#928 changes only mount syntax.
- `WH-ME-AUD-004` partially overlaps `WH-ME-AUD-006` operationally, but false readiness and non-resumable crash recovery are different defects. Open PR #833 coordinates historical Market Evidence recovery and does not remediate this accepted-state bug.
- Repository task/issue/PR searches found no existing remediation that makes any of `001`-`004` a duplicate or accepted risk.

### Exact-SHA CI interpretation

- `AI Platform CI` run `30696775622`: exact head `6419138e...`, event `pull_request`, conclusion `success`; its sole job compiled `ai_platform`/`tests/ai_platform`, ran 1,039 tests with 71 skipped, and passed Ruff, Ruff format, Codespell and three JSON validations. It does not run `tests/ai_platform_integration`, Portal npm/Playwright or Compose.
- `Freqtrade CI` run `30696775642`: exact head `6419138e...`, event `pull_request`, conclusion `success`; pre-commit, CI scope, documentation build, core tests for Python 3.11-3.14, distribution build and CI Gate succeeded. Coverage ran only on the Python 3.12 core job; compatibility and online/live jobs were skipped. It does not prove the disputed Market Evidence paths.
- Equivalent exact-head push runs `30696709205` and `30696709212` succeeded. Exact-head documentation deployment run `30696709213` failed while fetching `gh-pages`; this is unrelated to the four findings but prevents describing all exact-head workflows as green.
- No exact-head run of `AI Platform WickHunter Market Evidence CI`, Portal Web, Portal E2E/Playwright or Compose validation was found. Missing dedicated coverage remains an assurance gap, not a pass.

The four findings remain independently `CONFIRMED / HIGH / high confidence`; therefore the independent overall verdict is `FAIL`.
