# Evidence index

Audited head: `6419138e170844d0eb09d9381b4435900d802ab9`

| ID | Classification | Evidence |
|---|---|---|
| E-001 | PROVEN | `develop` resolved to `6419138e170844d0eb09d9381b4435900d802ab9`; current merge is PR #927. |
| E-002 | PROVEN | Open PRs: #833 and #926; review-thread queries returned zero threads. PR #927 is merged and changes only WH-02 replay paths. |
| E-003 | PARTIAL | Exact-head Actions exist: AI Platform CI `30696775622` and Freqtrade CI `30696775642` succeeded for `6419138e...`; equivalent push runs succeeded. No dedicated Market Evidence, Portal npm/Playwright or Compose run exists. |
| E-004 | PROVEN | PR #836 merged as `2e0c2b57376a0a0e4d6389961588d41a0b194115`; head `5d608dd617d6a5e14ee197fc4b34b887d55bbbe2` had successful runs including Market Evidence CI `30591937630`. |
| E-005 | CONFLICT | `docs/agents/tasks/FTAI-20260731-wickhunter-okx-market-evidence-v2.md` remains `in_progress`/`validating` and instructs merging PR #836. |
| E-006 | PROVEN | `production_market_evidence.py:733-819` fetches historical candles at finalization and sets `available_at_ms=close_time_ms_exclusive`. |
| E-007 | PROVEN | `production_market_evidence_wh01.py:340-379,825-856` ignores candle observed availability and labels metrics available at decision time. |
| E-008 | PROVEN | `production_market_evidence_v2.py:1184-1237` lacks intermediate-symlink and resolved-root confinement in supplement verification. |
| E-009 | PROVEN | `production_market_evidence.py:893-909` resolves before symlink checking. |
| E-010 | PROVEN | `reader.ts:519-604` and `reader-v2.ts:382-458` project rows without checking artifact digests/checksum index. |
| E-011 | PROVEN | `proxy.ts:21-43,74-84` and `identity.ts:104-132` require only production cookie presence; Market Evidence routes add no session/RBAC validation. |
| E-012 | PROVEN | v1/v2 daemons map `blocked` to `healthy=true`; healthchecks and deployment probes accept it. |
| E-013 | PROVEN | `reader.ts:286-343` makes completed-package STALE derivation unreachable. |
| E-014 | PROVEN | v1/v2 Compose hardening: non-root, read-only, cap-drop, no-new-privileges, limits, hardened tmpfs, no ports. |
| E-015 | PROVEN | Request workflows enforce exact-one-file addition, exact head checkout, trusted runner identity, immutable request and credential/proxy refusal. |
| E-016 | PROVEN | Portal preview script uses read-only mounts, candidate probes, no Docker socket, non-root runtime and rollback. |
| E-017 | PROVEN | GitHub Actions are commit-SHA pinned; Portal Node base is digest-pinned. |
| E-018 | PROVEN | Collector Python bases are tag-only and CI Python is patch-floating. |
| E-019 | PROVEN | Local audit-branch checkout succeeded at `ccbd8aa1c...`; frozen-SHA source and current develop commit were available. |
| E-020 | PROVEN | Independent session `independent-validator-20260801-1` completed with verdict `FAIL`; all four HIGH findings are `CONFIRMED` with high confidence. |
| E-021 | PROVEN | Requested post-freeze range to `d6cb539c...` contains seven OIDC commits/two net files. Develop then advanced six WH-02 replay-header commits to `5cffc190...`/three additional net files. Neither range changes disputed paths; conclusions are unchanged. |
| E-022 | PROVEN | Linux symlink probe: `verify_supplement` returned `accepted` for a valid regular file reached through a symlinked intermediate directory outside the supplement root (`escaped_root=true`). |
| E-023 | PROVEN | Production Next.js probe: anonymous Market Evidence request returned 401; the same request with an arbitrary forged `__Host-portal_session` cookie returned 200. |
| E-024 | PROVEN | Missing-request probes for v1/v2 returned `blocked/CAPTURE_REQUEST_UNAVAILABLE`, derived `healthy=true`, healthcheck exit 0 and passing deployment workflow predicates. |
| E-025 | PROVEN | Focused local checks: relevant Python compile passed; 18 Linux integration tests passed; focused Ruff passed; Portal npm typecheck/lint/build passed (one unrelated lint warning); frozen OIDC deploy tests passed 10/10. |
| E-026 | BLOCKED | Docker engine unavailable, so local Compose rendering was blocked. Playwright was not run because fixture identity does not exercise production cookie validation; the smaller production server probe covered the disputed path. |
