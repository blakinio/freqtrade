# FTAI AI Trading Portal Program

## Program ID

`FTAI-PROGRAM-AI-TRADING-PORTAL`

## Status

`production-like-staging-blocked`

## Mission

Build a secure, modern and extensible portal above the existing Freqtrade AI Platform that can manage dry-run bot runtimes, model lifecycle, deterministic risk, post-trade intelligence, safe continual learning, Cloudflare-protected access and autonomous full-platform validation.

## Current program state

Repository-backed implementation has progressed through P12 simulation-first acceptance, the remaining software-addressable portal product surfaces merged in PR #232, completed PI-01 through PI-04 repository-side integration packages, completed Bot Operations convergence in PR #320, completed the bounded PI-06 repository identity backend in PR #341 and completed the same-origin BFF/browser-session package in PR #361.

Canonical stage status is maintained in `docs/ai_platform/portal/DELIVERY_ROADMAP.md`:

- P0-P10 are complete for their declared bounded acceptance criteria;
- P11 repository-side staging contracts, verifier, workflows and runbooks are complete, but real Cloudflare/protected GitHub External E2E remains blocked/deferred and production-like staging is not accepted;
- P12 simulation-first autonomous diagnosis/repair acceptance is complete and is not a substitute for P11;
- P13 measured-need assessment completed with NO-GO, so scale/service extraction is deferred until evidence demonstrates a need;
- P14 remains separately blocked and this program does not authorize live capital.

The remaining authoritative-source, private-runtime, identity, observability and provider integrations are specified in `docs/ai_platform/portal/POST_P12_INTEGRATION_BACKLOG.md` as PI-01 through PI-08. PI-01, PI-02, PI-03 and PI-04 are complete. PI-06 is active: the architecture decision, repository identity backend and same-origin BFF/browser-session integration are complete, while real Authentik/Synology provisioning, MFA enrollment, recovery, backup/restore and target-environment acceptance remain. PI-05, PI-07 and PI-08 remain separately planned and gated.

Current task selection, repair priorities and the exact next authorized route are maintained in `docs/ai_platform/portal/NEXT_WORK_AND_REPAIR_PLAN.md`. The next dependency-ordered identity action is a separate Authentik/Synology deployment package. It may add pinned deployment definitions and runbooks without credentials, but real acceptance remains owner-managed target-environment evidence. Cloudflare P11 remains separate.

Current execution is also intentionally incomplete for real trading: the deterministic risk-gated terminal exists, but the concrete `FreqtradeExecutionAdapter.submit_approved_intent` path remains fail-closed with `ORDER_SUBMISSION_NOT_IMPLEMENTED`. P10 provides deterministic simulated execution only.

## Source of truth

In order:

1. current repository/Git/PR/CI state;
2. `AGENTS.md`;
3. existing AI Platform lifecycle/evidence records;
4. portal architecture documents under `docs/ai_platform/portal/`;
5. active bounded task record and its context checkpoint.

Chat history and private UI captures are not durable program state.

## Required reads

- `AGENTS.md`
- `docs/agents/CONTEXT_HANDOFF.md`
- `docs/ai_platform/ARCHITECTURE.md`
- `docs/ai_platform/ROADMAP.md`
- `docs/ai_platform/portal/README.md`
- `docs/ai_platform/portal/SYSTEM_ARCHITECTURE.md`
- `docs/ai_platform/portal/SECURITY_ARCHITECTURE.md`
- `docs/ai_platform/portal/DELIVERY_ROADMAP.md`
- `docs/ai_platform/portal/POST_P12_INTEGRATION_BACKLOG.md`
- `docs/ai_platform/portal/NEXT_WORK_AND_REPAIR_PLAN.md`
- `docs/ai_platform/portal/AGENT_EXECUTION_PLAN.md`

Task-specific agents read additional portal documents only when relevant.

## Program invariants

- Freqtrade is an internal execution engine, not a public portal backend.
- Browser traffic never talks directly to Freqtrade or exchanges.
- Portal execution reaches Freqtrade only through a controlled private adapter boundary.
- AI predictions are not unrestricted execution authority.
- Every execution intent is subject to deterministic risk gates before it may reach an execution submitter.
- Exchange credentials are stored behind a secret boundary and never committed.
- Withdrawal permission remains disabled.
- Research workers cannot access production exchange credentials.
- Models/configs/strategies/risk policies used for decisions are immutable and attributable.
- Post-trade analysis may create insights/experiments/candidates, not immediate production mutation.
- Autonomous repair creates regression tests, branches and PRs; it does not patch production.
- Live capital requires a separate explicit reviewed work package.
- Repository or simulated P11 evidence cannot be represented as real Cloudflare production-like staging acceptance.
- A planned PI package is not active and cannot be used as completion evidence until its separate task and acceptance gates pass.
- Cloudflare Access supplements product authorization and never replaces portal-owned tenant membership, capability enforcement or local session revocation.
- Browser-readable storage receives no IdP access, ID or refresh token.

## Protected existing AI boundaries

This program cannot change:

- frozen `entry_prediction_threshold = 0.006`;
- frozen `exit_prediction_threshold = -0.009`;
- protected final holdout v2 `20260801-20260930` or its authorization date;
- completed Phase 6 candidates/policy/evidence;
- authoritative Phase 6 `selected_model = null`;
- historical PyTorch/RL evidence status.

Any future work affecting those boundaries requires a separately declared research work package governed by the existing AI Platform lifecycle.

## Program architecture

Six planes:

1. Portal / UX Plane
2. Control Plane
3. Execution Plane
4. AI / Research Plane
5. Data Plane
6. Quality & Autonomous Validation Plane

Cross-cutting:

- Security;
- Risk;
- Observability.

## Delivery sequence

Canonical stage order, current statuses and acceptance boundaries are defined in `docs/ai_platform/portal/DELIVERY_ROADMAP.md`.

The historical first implementation task after architecture merge was `FTAI-20260722-portal-p1-contracts-security`. That sequence has now progressed through completed P12 simulation-first acceptance; it is no longer the program's next software action.

Post-P12 integration contracts remain in `POST_P12_INTEGRATION_BACKLOG.md`. PI-01 through PI-04 are complete. PI-06 has an accepted Authentik architecture, a merged repository backend and merged same-origin browser integration; its remaining work is separately controlled target-environment provisioning and real identity acceptance. PI-05 requires a provider/channel decision and PI-07 must precede PI-08. No package authorizes live capital.

The Bot Operations product completion package is complete. The continuation route in `NEXT_WORK_AND_REPAIR_PLAN.md` authorizes only a bounded Authentik/Synology deployment package after a fresh path-ownership preflight. It does not authorize Cloudflare P11 acceptance, PI-07, PI-08 or P14.

## PI-06 repository backend evidence

Task `FTAI-20260726-portal-pi06-product-identity-lifecycle` delivered the bounded Python identity backend in PR #341, squash merge `41834d18f3a05b0dfa44dc5af9b97942e685d2a1`.

The package includes:

- Authentik-compatible OIDC discovery and Authorization Code plus PKCE;
- signed JWKS, issuer, audience, expiry and nonce validation;
- immutable external principal mapping by `iss` plus `sub`;
- portal-owned memberships, roles, validity and membership versions;
- opaque server-side sessions with keyed hashes only in storage;
- secure host-only session cookies and CSRF enforcement;
- membership-derived tenant and capability context;
- MFA and five-minute step-up enforcement;
- logout, logout-all, membership-change revocation and OIDC back-channel logout;
- migrations, deterministic configuration and security regression tests.

Exact final backend head `c258567cabd1c9ddf3d90c63f36319be99463978` passed AI Platform CI #1415, Freqtrade CI #1713 and GitHub Actions Security Analysis #1580.

## PI-06 BFF and browser-session evidence

Task `FTAI-20260726-portal-pi06-bff-browser-session-integration` delivered the same-origin Next.js boundary in PR #361, squash merge `4f76eecadcb8dda964a8d247327db9dc6ef1c931`.

The package includes:

- same-origin login, callback, session, logout and logout-all routes;
- HTTPS-only authorization redirects and relative-only application return redirects;
- forwarding of opaque backend session/CSRF cookies without exposing IdP tokens;
- optimistic Proxy checks plus Route Handler defense in depth;
- double-submit CSRF for existing browser mutations;
- visible tenant/MFA session state and logout controls;
- deterministic fixture states for anonymous, expired, revoked, MFA-missing, stale-step-up and cross-tenant denial;
- 37 Chromium tests covering the identity lifecycle while preserving existing product E2E.

Exact final implementation head `ec1970a9272bec241a1bab3c447ebd36f53afa58` passed Portal Web CI #287, Portal Universal E2E #292, AI Platform CI #1521, Freqtrade CI #1837 and GitHub Actions Security Analysis #1702.

This remains repository and fixture browser evidence. No real Authentik instance, user, MFA device, recovery flow, secret, Synology deployment or Cloudflare resource has been provisioned or accepted.

## Parallelization policy

Shared contract changes are serialized through a dedicated contract-change task. New work must inspect current `develop`, open PRs and active task ownership before editing shared paths.

Every PI package requires its own dated task, branch, exact owned paths, authoritative source definition, fail-closed states and acceptance evidence. Adjacent PI packages must not be silently combined because their security and capital risks differ.

Product completion packages such as Bot Operations also require a separate dated task and exact web/BFF ownership. They must not silently implement PI-07, PI-08, P11 or P14.

P13 scale/service extraction remains deferred unless measured bottleneck/SLO evidence justifies a separately declared work package.

## Quality policy

Every implementation workstream adds tests at its layer. Full-platform acceptance includes, as applicable:

- unit/contract/integration;
- security E2E;
- Playwright browser E2E;
- deterministic exchange simulator;
- AI learning-loop E2E;
- visual/responsive acceptance;
- chaos/recovery scenarios;
- bounded autonomous diagnosis/repair.

Simulation/local/CI evidence must remain labeled as such. Real production-like staging acceptance requires the real protected external ingress path.

## Security posture

Target ingress:

```text
Internet -> Cloudflare -> Tunnel -> Portal
```

Privileged surfaces add Zero Trust/Access policy. Freqtrade remains private.

Staging E2E must traverse the real protected ingress path without a hidden security bypass and uses simulated capital by default.

The current P11 blocker is external: owner-approved Cloudflare Tunnel/DNS/Access/WAF/rate-limit/origin-denial state plus protected GitHub staging variables/secrets must be provisioned or confirmed and the real External E2E workflow must pass. Repository-side P11 implementation alone is not acceptance.

## Product surface

Canonical navigation is defined in `docs/ai_platform/portal/UI_INFORMATION_ARCHITECTURE.md` and includes:

- Dashboard;
- PNL & Performance;
- Open Positions;
- Trading Terminal;
- Bots/Create Bot/Signal Wizard/Strategy Catalog/Grid Bots;
- AI Intelligence/Trade Analysis/Insights/Model Health/Experiments/Learning History;
- Operations/Logs/Risk/Runtime Health/Audit;
- Exchange Connections/Profile/Security/Notifications/Admin.

The bot list and detail routes expose bounded bot-scoped operational convergence, filtering, immutable-revision creation and desired-state lifecycle controls over existing canonical APIs. They preserve tenant attribution, desired/observed separation, explicit degraded evidence and the private execution boundary.

Protected browser paths now use the same-origin PI-06 BFF boundary with opaque session cookies, CSRF, optimistic anonymous denial and backend-authoritative tenant/capability enforcement. Fixture identity remains explicit test evidence and must not be described as real Authentik acceptance.

Third-party private captures are inspiration/evidence only and must not be copied into public product code with personal data or proprietary assets.

## Completion definition

The program reaches its first major completion milestone when a production-like staging deployment can:

1. authenticate a test user through the protected ingress path;
2. create a tenant-scoped dry-run AI bot;
3. provision an isolated Freqtrade runtime privately;
4. execute a deterministic simulated trade through risk gates;
5. reconcile PNL and execution evidence;
6. produce a post-trade analysis and AI insight;
7. create a bounded learning experiment/candidate without changing the active model;
8. pass critical browser/security/AI E2E;
9. generate an autonomous evidence-based repair PR for a seeded defect;
10. prove no public Freqtrade exposure and no live-capital authorization.

Repository-side and simulation-first evidence already cover many of these software boundaries, but the milestone is **not complete** until real P11 protected external ingress acceptance passes.

## Next actions by authorization lane

Next autonomous identity/deployment action: declare a separate `FTAI-YYYYMMDD-portal-pi06-authentik-synology-deployment` task after a fresh `develop`, open-PR and path-ownership preflight. Add pinned Authentik/PostgreSQL deployment definitions, runtime-injected secret placeholders, restricted bootstrap, health checks, backup/restore and recovery runbooks, and deterministic configuration validation. Do not commit credentials or claim real acceptance without owner-managed target probes.

Next real identity acceptance action: on owner-managed Synology resources, prove OIDC login, MFA enrollment/challenge, session cookies, logout, logout-all, membership revocation, recovery and restore. Record unavailability rather than simulating successful target connectivity.

Next owner/external action: when the owner intentionally starts the real infrastructure phase, resume P11, provision or confirm the owner-approved Cloudflare staging resources and protected GitHub staging environment, then run `Portal Staging External E2E` until all five real ingress, Access and direct-denial probes pass.

Do not start PI-05, PI-07, PI-08 or P14 without their explicit provider/security/capital decisions. Do not enable live capital as part of any continuation action.
