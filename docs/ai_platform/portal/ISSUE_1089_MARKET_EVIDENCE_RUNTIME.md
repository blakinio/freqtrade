# Issue #1089 — Market Evidence production runtime contract

Status: implementation candidate in PR #1393. Protected-target deployment remains separately authorized.

## Production contract

The production Portal web runtime is API-backed and must not use fixture identity or fixture product data. Market Evidence remains a same-origin, read-only web/BFF projection, but its authorization context comes from the real Portal identity session through the private control-plane boundary.

The Synology OIDC deployment therefore installs a fail-closed Market Evidence runtime guard with these invariants:

- canonical host data root: `/volume1/docker/freqtrade-staging-state/wickhunter-production-market-evidence`;
- container data root: `/market-evidence-data`;
- bind mount is read-only and its group-readable/run-layout contract is checked using the exact web image before cutover;
- `PORTAL_MARKET_EVIDENCE_DATA_ROOT=/market-evidence-data` is explicit;
- `PORTAL_MARKET_EVIDENCE_TENANT_ID=tenant-local` matches the explicit owner-membership bootstrap contract;
- deployment verifies that the selected tenant has at least one current active membership with an authorized Market Evidence role (`analyst`, `model_reviewer`, or `admin`) before starting the web candidate;
- the running web container is inspected after cutover to prove the exact read-only mount, environment and supplementary group;
- any missing dataset, invalid run layout, missing/expired/disabled membership, wrong tenant, invalid runtime mount or unavailable identity boundary fails closed instead of falling back to fixture evidence.

No membership is created implicitly by this guard. The existing explicit owner-membership bootstrap remains the authority for the initial `tenant-local` administrator membership.

## Verification

Focused deployment tests cover argument injection, immutable-run preflight parsing, tenant fail-closed behavior, exact read-only mount verification and candidate/final web wrapping. Repository CI, exact-image API-mode validation and the authenticated Chromium workflow remain the acceptance gates for the exact PR head.

## Safety boundary

This change does not authorize protected production deployment, withdrawals, live trading or live capital. Market Evidence is mounted read-only and private provider/database access remains server-side.
