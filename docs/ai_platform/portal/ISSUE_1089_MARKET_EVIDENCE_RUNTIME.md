# Issue #1089 — Market Evidence production runtime contract

Status: implementation candidate in PR #1393. Protected-target deployment remains separately authorized.

## Production contract

The production Portal web runtime is API-backed and must not use fixture identity or fixture product data. Market Evidence remains a same-origin, read-only web/BFF projection, but its authorization context comes from the real Portal identity session through the private control-plane boundary.

The Synology OIDC deployment therefore installs a fail-closed Market Evidence runtime guard with these invariants:

- canonical host data root: `/volume1/docker/freqtrade-staging-state/wickhunter-production-market-evidence`;
- container data root: `/market-evidence-data`;
- run discovery is performed in a root-only helper, but immutable-package acceptance is delegated to the canonical production `verifyMarketEvidencePackage()` implementation compiled into the exact web image;
- canonical verification runs as the same unprivileged web UID with the same supplementary group access that the production container receives, so nested traversal/readability failures are detected before cutover;
- immutable schema-v2 evidence is pinned to the selected v2 run **and** its canonically verified `base_v1` binding; both exact run subtrees are mounted read-only and no mutable parent evidence root is exposed;
- active schema-v1 evidence is pinned to the selected run and receives a deployment-owned immutable active-run pointer at `active-wickhunter-production-market-evidence-v1.json`, so the legacy reader cannot drift to an unverified sibling run after preflight;
- `PORTAL_MARKET_EVIDENCE_DATA_ROOT=/market-evidence-data` and `PORTAL_MARKET_EVIDENCE_TENANT_ID=tenant-local` are explicit; selected-run/base-run identities are also recorded in runtime environment and labels;
- deployment verifies that the selected tenant has at least one current active membership owned by an active principal with an authorized Market Evidence role (`analyst`, `model_reviewer`, or `admin`) before starting the web candidate;
- the running web container is inspected after cutover to prove the exact run-specific read-only mount inventory, environment and supplementary groups; an unexpected parent or sibling Market Evidence mount fails closed;
- any missing dataset, invalid run layout, invalid package semantics or binding, inaccessible nested artifact, missing/expired/disabled membership, wrong tenant, invalid runtime mount or unavailable identity boundary fails closed instead of falling back to fixture evidence.

No membership is created implicitly by this guard. The existing explicit owner-membership bootstrap remains the authority for the initial `tenant-local` administrator membership.

## Verification

Focused deployment tests cover exact selected/base run binding, canonical verifier invocation in the exact image, active-v1 pointer pinning, tenant fail-closed behavior, runtime-user/group accessibility, exact read-only mount inventory and candidate/final web wrapping. Repository CI, exact-image API-mode validation and the authenticated Chromium workflow remain the acceptance gates for the exact PR head.

## Safety boundary

This change does not authorize protected production deployment, withdrawals, live trading or live capital. Market Evidence is mounted read-only and private provider/database access remains server-side.
