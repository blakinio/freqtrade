# WickHunter vs Freqtrade reverse-product audit

Date: 2026-09-11  
Repository baseline: `develop@f52a38d102f37888271816897494cab45cbff80a`  
Alias: `FREQTRADE_WICKHUNTER_REVERSE_PRODUCT_AUDIT_V1`  
Terminal state: `WICKHUNTER_VS_FREQTRADE_DECISION_READY`

## Scope and evidence rules

This document records the completed read-only reverse-product and architecture audit of the official WickHunter beta runtime against:

- the current `blakinio/freqtrade` implementation,
- the currently accepted Quant Platform target architecture,
- historical/internal WH09 work that may now overlap with the vendor product.

The audit did **not** mutate the repository, Synology runtime, Docker state, WickHunter configuration, credentials, models, exchange state, orders, withdrawals, or capital. Proprietary vendor code was not copied. Secret values were not printed or persisted.

Evidence terminology used here:

- **FACT** — directly verified from repository state, public WickHunter source, or read-only runtime inspection.
- **INFERENCE** — conclusion derived from verified facts but not directly demonstrated end-to-end.
- **UNKNOWN** — not safely or sufficiently proven.
- **RECOMMENDATION** — proposed product/architecture action.

WickHunter evidence levels:

- `WH-E3`: direct runtime behavior demonstrated.
- `WH-E2`: direct runtime interface/state/schema evidence.
- `WH-E1`: public/static source evidence.

Gap classes:

- `A` — WickHunter has it; ours has it.
- `B` — WickHunter has it; ours is incomplete.
- `C` — WickHunter has it; ours is planned but not implemented.
- `D` — ours has it; WickHunter does not appear to.
- `E` — both have it but semantics materially differ.
- `F` — neither current implementation has it, but the accepted target requires it.
- `G` — WickHunter evidence is insufficient.
- `H` — our authority/evidence is insufficient.

Allowed recommendation vocabulary:

`USE_WICKHUNTER`, `INTEGRATE_AROUND`, `BUILD_OURS`, `KEEP_OURS`, `ADOPT_PATTERN`, `DEFER`, `DROP`, `REQUIRES_DECISION`, `UNKNOWN`.

---

## 1. EXECUTIVE DECISION

### Decision

**RECOMMENDATION — adopt a hybrid architecture.**

Do not build a second WickHunter product, and do not collapse the platform into WickHunter-only ownership.

The vendor product already covers a broad class of trader-facing capabilities that would be expensive and duplicative to reproduce: bot configuration, exchange-account handling, execution-oriented surfaces, multiple strategy/bot families, diagnostics, P&L/history surfaces, licensing, signed distribution/update, and a central Hub/community boundary.

Our platform should continue to own the capabilities that are strategically distinct and already central to the accepted Quant v2 target: research/data lineage, evaluation integrity, model lifecycle, deterministic simulation/replay/recovery, causal state, PostgreSQL evidence, Portal/BFF workflow, Liquid20/public market data, vendor-independent validation, and an explicit vendor-exit boundary.

### Stop or defer duplicate work

- duplicate trader console parity,
- generic bot configuration UI intended to mirror WickHunter,
- independent first-class Grid/Manual/TV/Hedge product parity,
- permanent Freqtrade execution/state ownership,
- WH09 paper runtime as an enduring product runtime,
- current Portal paths whose only value is recreating vendor trading features.

### Keep and strengthen

- research/evaluation/provenance,
- dataset and feature lineage,
- holdout/no-lookahead controls,
- model comparison and deliberate activation,
- Rust deterministic Quant Core target,
- PostgreSQL causal state and recovery evidence,
- Portal causal-trace workflow,
- Liquid20/public market evidence,
- independent simulation/risk validation,
- vendor-exit and reproducibility boundary.

### Recommended high-level boundary

`our data/research/evaluation/models -> versioned decision contract -> WickHunter/Python decision plane -> Rust deterministic Quant Core -> PostgreSQL causal evidence -> Portal`

The official WickHunter UI may remain a separate vendor console. The current Developer Quant Portal must not become a browser surface for storing or exercising WickHunter private exchange credentials.

---

## 2. VERIFIED BASELINE

### Repository

**FACT** — the exact repository baseline used for final authority readback was:

`develop@f52a38d102f37888271816897494cab45cbff80a`

The associated Git tree SHA is:

`7e29902675ba7199ceed9fdeaaeed4db67f2f9f3`

The tree SHA is not the branch/commit HEAD.

### Current accepted authority

**FACT** — current product and target architecture remain layered:

- ADR-023: private single-owner Developer Quant product boundary,
- ADR-025: Synology persistent runtime + GitHub-hosted CI/build/disposable compute,
- ADR-026 as promoted by ADR-027: Quant Platform v2 target architecture.

**FACT** — current Portal authority excludes real-money execution, private trading credentials for order submission, withdrawals, and capital authority. Any future real-capital capability requires a separate owner-approved Execution/Capital Gateway architecture/programme.

### Official WickHunter runtime

**FACT / WH-E3** — official runtime returned:

`GET http://127.0.0.1:8090/api/health -> 200 {"ok":true,"version":"0.90.63"}`

Observed official containers:

- `wickhunter-official-wickhunter-1` using `local/wickhunter-official:0.90.63`,
- `wickhunter-official-https-proxy-1` using `local/wickhunter-caddy:2.10.2`.

Observed hardening/runtime properties included:

- non-root runtime user `1032:100`,
- `ReadonlyRootfs=true`,
- `Privileged=false`,
- restart policy `unless-stopped`,
- read-only secrets mount,
- writable application-data mount,
- local health contract.

### Credential-boundary correction

**FACT / WH-E2** — a redacted state scan found nonempty encrypted credential fields in `accounts.json`:

- `apiKeyEnc`,
- `apiSecretEnc`,
- `apiPassphraseEnc`,
- a nonempty masked key field.

The scanned account was configured for `bitget` with `testnet=false`.

No credential values were printed or retained.

**FACT** — this invalidates any assumption that the official runtime is merely a no-credential or non-trading demo instance.

**FACT** — all inspected positions files had zero currently open and zero closed positions at final readback.

**SAFETY DECISION** — private exchange endpoints, order placement/cancellation, credential mutation, and real-execution proof were intentionally not exercised.

---

## 3. OFFICIAL WICKHUNTER — WHAT IT ACTUALLY IS

### Product shape

**FACT / WH-E2** — the installed package exposed product/interface families for:

- authentication/session,
- accounts and active-account selection,
- bot creation/update/retirement,
- AI draft/apply/recommend/replay/status,
- config export,
- deal controls including close/add-funds/DCA operations,
- diagnostics/logs,
- grid creation/update/delete/backtest/fills/restart/stop/suggest,
- hedge controls and simulations,
- Hub FAQ/feedback/community strategy publishing/voting,
- license check-in and lease challenge,
- liquidation screener/history/sources,
- market caps,
- P&L summary/trades/verification,
- replay and what-if,
- strategy save/eval/backtest/visualize/AI critique/draft/explain,
- terminal/order/deal/hedge/plan surfaces,
- TradingView bot/signals,
- private-looking exchange route families.

**FACT / WH-E2** — static product labels included:

- `AI Strategy`,
- `Grid`,
- `Hedge Bot`,
- `Liq Scalper`,
- `Manual Bot`,
- `Strategy Builder`,
- `TV Signal`.

### Persistence shape

**FACT / WH-E2** — runtime data included local persistent state for:

- DCA, hedge, deal and entry events,
- liquidation history,
- activity events,
- bot contexts,
- positions,
- percentile/materialized data,
- install identity,
- latest-version/update metadata,
- licensing/subscription/lease state.

Observed runtime JSON schemas showed bot configuration, runtime contexts, deal overrides, entry state, filters, hedge state, notifications, strategy state, open/closed positions, decision/feature/skip metadata and liquidation records.

### Hub / distribution / updates

**FACT / WH-E1** — public source repository: `WickHunter/wickhunter-hub`.

At audit time the public Hub `main` head was `be0944b881c0d10dfa85ae87e3b6f2284f2ea497`.

**FACT / WH-E1** — public hosting policy exposed reachability/support probes for seven venues:

- Bybit,
- Binance USD-M,
- Bitget,
- Bitunix,
- BloFin,
- WEEX,
- Aster.

**FACT / WH-E1** — the release contract uses signed manifests and tarball hashes. Public release-key material is separated from the offline private release key. Both Hub and installer/updater independently verify relevant update integrity properties. Rollback can be represented by moving `latest.json` to an older signed tarball.

### What is not proven

**UNKNOWN** — route existence does not prove complete live-execution correctness.

**UNKNOWN** — end-to-end semantics for real order submission, restart recovery with live positions, reconciliation, partial-fill handling, disconnect recovery, exchange-specific failure handling, and long-term license outage behavior were not safely demonstrated.

---

## 4. OUR CURRENT PLATFORM — WHAT ACTUALLY EXISTS

### Portal implementation

**FACT** — the living Portal ledger reported approximately:

- 32 backend modules,
- 95 backend routes,
- 29 BFF handlers,
- 33 frontend pages.

**FACT** — Portal documentation describes the product as partially implemented and actively evolving.

**FACT** — a Synology package candidate existed, but protected target acceptance remained external/incomplete, and broader real API-mode browser E2E remained incomplete.

### Material disconnected/partial areas

Examples observed in the exact-head ledger:

- bot builder drafts/finalize/preview/revise — disconnected,
- command lifecycle/order/position control — disconnected,
- exchange verification — disconnected,
- grid policies/preview — disconnected,
- signal endpoints/process — disconnected,
- terminal intents — disconnected,
- orders/positions/trades/execution activity — disconnected,
- real runtime observability source — disconnected,
- browser-to-BFF-to-backend API-mode closure — partial.

Issue `#1098` remained open for real composed API-mode browser E2E. Fixture-only coverage does not prove browser -> BFF -> backend -> persistence/provider behavior.

### Research/ML/evaluation strength

**FACT** — the repository contains substantial WickHunter/quant research infrastructure including:

- baseline strategy,
- bounded optimization,
- candidate activation/evaluation,
- deterministic replay,
- dataset/features/materialization,
- LightGBM scoring,
- paper validation,
- production evaluation and market evidence,
- replay price paths,
- production research/runtime support,
- extensive research-integrity and model-comparison tests.

Tests include protected/final holdout guards, model comparison suites, candidate identity checks, runtime-mode checks, health checks and other research integrity controls.

### Current implementation authority

**FACT** — the living status authority explicitly does not grant live trading, real capital, withdrawals, private-trading credential use, model/strategy promotion beyond the defined lifecycle, protected mutation, or production deployment authority.

---

## 5. OUR INTENDED TARGET — WHAT WE WERE BUILDING

### Product workflow

**FACT** — ADR-023 defines the current canonical Developer Quant vertical slice as:

`REALTIME_PUBLIC -> bot/model decisions including NO_TRADE -> simulated positions/outcomes -> durable chronological dataset/labels -> local challenger training -> active/challenger/baseline comparison -> deliberate active-model selection -> restart-safe continued observation`

### Runtime placement

**FACT** — ADR-025 places persistent application runtime and durable storage on Synology while using GitHub-hosted Actions for CI, tests, scanning, packaging, image builds and bounded disposable jobs.

### Quant v2 target

**FACT** — ADR-027/ADR-026 define the target ownership split:

- Rust Quant Core: deterministic event ordering, simulation, journal/replay/recovery and causal state,
- Python: WickHunter/strategy/ML plane,
- PostgreSQL: recovery spine,
- FastAPI + Next.js: owner-facing Portal boundary,
- Freqtrade: reference oracle, migration input, temporary compatibility layer, bounded offline reference.

The first target slice is:

`Frozen canonical public market/WickHunter input -> Rust Quant Core acceptance/order -> Python WickHunter decision -> Rust deterministic simulation -> PostgreSQL causal persistence -> Portal causal-trace view`

**FACT** — `NO_TRADE` is a successful attributable decision and must not be fabricated when the decision engine is unavailable.

**FACT** — architecture promotion did not activate implementation. Quant v2 execution governance remains a separate prerequisite.

---

## 6. ARCHITECTURE COMPARISON

### Official WickHunter — observed

Approximate observed product topology:

`Browser -> HTTPS proxy -> Node WickHunter runtime -> bot/strategy/exchange adapters -> local persistent files`

with a separate Hub boundary for licensing, lease/check-in, updates and community/distribution concerns.

### Our current platform

Approximate current topology:

`Next.js -> BFF/FastAPI -> platform/control packages -> Freqtrade/simulator/WH09/reference paths -> mixed persistence + public market data`

alongside a relatively strong research/evaluation/provenance subsystem.

### Accepted target

`Next.js -> FastAPI -> Rust Quant Core <-> Python decision/ML -> PostgreSQL`

with public data inputs, deterministic simulation/recovery, causal evidence, and explicit vendor/reference boundaries.

### Architectural interpretation

**INFERENCE** — official WickHunter is already a vertically integrated trading-product runtime, while our accepted target is increasingly an evidence-first deterministic quant/research platform. The products overlap at bot/strategy/control surfaces but have materially different long-term ownership goals.

---

## 7. MASTER CAPABILITY MATRIX

| Capability | Gap | Assessment | Recommendation |
|---|---:|---|---|
| Login/auth/session | B | WickHunter has working product auth; ours has Portal auth but broader workflow closure remains incomplete | `KEEP_OURS` |
| Bot configuration UI | B | WickHunter appears materially ahead | `USE_WICKHUNTER` |
| Grid/Manual/TV/Hedge product surfaces | B/C | Vendor product already exposes them; ours is incomplete/planned | `DEFER` |
| Private exchange account management | E | Both boundaries exist conceptually, but current Portal authority forbids private execution credentials | `REQUIRES_DECISION` |
| Multi-venue exchange support | B/E | WickHunter exposes broad venue support; our target should not duplicate every adapter | `INTEGRATE_AROUND` |
| Liquidation/public market data | A/E | Both have relevant data capability with different semantics/ownership | `KEEP_OURS` |
| Liquidation strategy semantics | E | Comparable domain, not proven identical | `ADOPT_PATTERN` |
| DCA/TP/SL/hedge execution | E | WickHunter exposes execution-oriented surfaces; our current product should remain simulation-only | `DEFER` |
| Durable product state / P&L / history | E | WickHunter has local product state; our target requires causal evidence/recovery semantics | `BUILD_OURS` |
| Diagnostics / replay | G/D | WickHunter exposes diagnostic/replay surfaces; ours has stronger deterministic/research evidence goals | `KEEP_OURS` |
| Research provenance | D/G | Strong direct evidence ours; insufficient proof vendor matches this standard | `KEEP_OURS` |
| Protected holdout / no-lookahead controls | D | Ours has explicit tests and controls | `KEEP_OURS` |
| Model lifecycle | D/G | Ours has explicit BASELINE/CHALLENGER/ACTIVE/ARCHIVED authority | `KEEP_OURS` |
| Deterministic simulation/recovery | G/F | Vendor semantics insufficiently proven; accepted target still requires ours | `BUILD_OURS` |
| Portal causal trace | D/F | Current partial, target requires full causal trace | `BUILD_OURS` |
| Signed update chain | E | WickHunter pattern is mature and explicit | `ADOPT_PATTERN` |
| Community / Hub distribution | C | Vendor already provides this class of product capability | `USE_WICKHUNTER` |
| Vendor independence / exit | D | Our architecture can preserve this | `KEEP_OURS` |

---

## 8. WHAT WICKHUNTER ALREADY SOLVES

**FACT / RECOMMENDATION** — WickHunter already supplies credible product value in areas we should not automatically duplicate:

- trader-facing configuration and control surfaces,
- multiple bot families,
- exchange-account plumbing,
- execution-oriented interfaces,
- product-local persistence/history,
- diagnostics/P&L/replay surfaces,
- licensing/subscription/lease lifecycle,
- distribution/update lifecycle,
- a central Hub/community boundary,
- signed release/update integrity.

**INFERENCE** — even without proving every live-trading edge case, the breadth and integration density are sufficient to justify treating WickHunter as a serious vendor dependency rather than merely an inspiration/reference implementation.

---

## 9. WHAT WE CAN STOP OR DEFER BUILDING

The following current work should be reclassified before further implementation if its purpose is substantially vendor parity:

- Portal bot-builder parity (`#1090`) — `DEFER`,
- grid-control parity (`#1096`) — `DEFER`,
- signal-control parity (`#1095`) — `DEFER`,
- generic execution-submission / terminal execution paths (`#1086`, `#1091`) — stop as current-product live-execution work,
- exchange-management parity (`#1097`) — `DEFER`,
- permanent Freqtrade state/execution ownership — stop as target architecture,
- WH09 candidate paper runtime as enduring product runtime — retirement candidate,
- WH09 paper egress/runtime pair — retirement candidate after evidence freeze,
- obsolete first-generation market-evidence runtime — retirement candidate.

**RECOMMENDATION** — do not delete evidence or code merely because a runtime is now duplicative. Freeze useful fixtures/evidence first, then retire operational ownership deliberately.

---

## 10. WHAT WE SHOULD STILL OWN

The strategic core that remains ours:

1. **Research integrity** — protected holdout, no-lookahead, reproducible evaluation.
2. **Data lineage** — canonical datasets, feature schemas, provenance and immutable identity.
3. **Model lifecycle** — `BASELINE | CHALLENGER | ACTIVE | ARCHIVED`, deliberate attributable activation.
4. **Deterministic core** — ordering, simulation, replay, restart/recovery, causal state.
5. **PostgreSQL evidence spine** — durable causal records independent of vendor-local files.
6. **Portal owner workflow** — especially causal trace, model comparison, research state and recovery evidence.
7. **Independent simulation/risk validation** — vendor claims should remain testable externally.
8. **Liquid20/public-data capability** — keep public-data evidence and market-observation ownership.
9. **Vendor-exit boundary** — preserve canonical contracts and data so the platform is not trapped by one proprietary runtime.

---

## 11. HISTORICAL WH09 WORK — KEEP / REPURPOSE / RETIRE

### Keep / repurpose

- `portal-wh09-runtime-observer` — healthy; keep temporarily as read-only reference/evidence observer.
- production research runtime — healthy; repurpose as reference oracle/fixture source, not target product runtime.
- `wickhunter-market-evidence-v2` — healthy; keep temporarily where it supplies unique evidence.
- `binance-v3-acceptance-sampler` — healthy; keep as provider/public-market acceptance evidence where still relevant.
- `liquid20-live` — keep; strategically distinct public-data capability.

### Retire candidates after evidence freeze

- `wickhunter-paper-runtime-v12` — running but unhealthy with `ModuleNotFoundError: No module named 'ai_platform'` in its healthcheck.
- `wickhunter-wh09-egress-v12` — no healthcheck; retire with the paper-runtime path if no unique evidence dependency remains.
- older `wickhunter-market-evidence` — unhealthy; retire after confirming no surviving acceptance/evidence dependency.
- obsolete exited collector instances — classify individually before cleanup; do not infer deletability merely from age/stopped state.

**RECOMMENDATION** — historical WH09 work should become reference/migration/evidence infrastructure, not a second vendor-like product stack.

---

## 12. SECURITY + VENDOR-DEPENDENCY ANALYSIS

### Positive vendor security signals

**FACT** — official runtime demonstrated useful container hardening:

- non-root execution,
- read-only root filesystem,
- no privileged mode,
- bounded secrets/data mounts,
- healthcheck,
- dedicated HTTPS proxy.

**FACT / WH-E1** — signed release/update chain uses explicit manifest signing and hash verification with offline private signing material.

### Material risks

**FACT** — encrypted non-testnet exchange credentials are present in official runtime state.

This is a material trust-boundary change compared with treating WickHunter as a public-data-only research tool.

**UNKNOWN** — audit did not prove:

- long-term offline license behavior,
- credential portability,
- disaster-recovery restore semantics,
- behavior during Hub outage while positions are open,
- live exchange reconciliation correctness,
- private endpoint fail-closed behavior across every supported venue.

### Vendor dependency impact

If the vendor disappears or Hub/update/licensing becomes unavailable, we may lose:

- proprietary runtime updates,
- some license/lease capability,
- vendor bot/strategy implementations,
- vendor exchange UI/control semantics,
- vendor community/Hub distribution.

We can retain, if we preserve our own boundary:

- datasets and provenance,
- research/evaluation assets,
- our models and feature schemas,
- public-data collectors/Liquid20,
- Portal research/causal views,
- target Rust deterministic core,
- PostgreSQL causal history,
- WH09/reference fixtures already lawfully captured as our own generated evidence.

---

## 13. HYBRID ARCHITECTURE OPTIONS

### Option A — WickHunter-only

**REJECT.**

Pros: fastest path to mature trader-facing features.  
Cons: excessive vendor dependency, weak control over research integrity/evidence semantics, incompatible with our accepted deterministic-core and causal-state goals.

### Option B — ours-only full duplication

**REJECT.**

Pros: maximal ownership.  
Cons: high duplication cost, repeated exchange/bot/UI work, unnecessary implementation risk, slower progress on unique quant/research capabilities.

### Option C — hybrid

**RECOMMEND.**

Use WickHunter where it is already a strong product; integrate around it with explicit versioned boundaries; keep deterministic evidence/research/model/data ownership on our side.

---

## 14. RECOMMENDED TARGET ARCHITECTURE AFTER THIS DISCOVERY

Recommended architecture:

```text
GitHub CI/build
    |
    v
Synology persistent runtime
    |
    +--> Public market collectors / Liquid20
    |         |
    |         v
    |    Canonical public market input
    |         |
    |         v
    |    Python vendor adapter / WickHunter decision boundary
    |         |
    |         +--> NO_TRADE / SIGNAL / bounded decision payload
    |                        |
    |                        v
    |                 Rust Quant Core
    |          deterministic ordering/simulation
    |             replay/recovery/causal state
    |                        |
    |                        v
    |                   PostgreSQL
    |                        |
    |                        v
    +-----------------> FastAPI/BFF
                             |
                             v
                         Next.js Portal
```

### Boundary rules

- Official WickHunter UI can remain a standalone vendor console.
- Portal should not copy or persist WickHunter private exchange credentials.
- Current Portal should not expose a Portal -> WickHunter -> real exchange order path.
- The vendor adapter should use a versioned decision contract and must preserve attributable `NO_TRADE` vs unavailable/error states.
- Rust Quant Core remains authoritative for deterministic simulation/recovery and causal evidence in the accepted target.
- PostgreSQL remains the system-of-record/recovery spine for our target state.

---

## 15. P0 / P1 / P2 / P3 ROADMAP

### P0 — architecture and scope freeze

1. Freeze official WickHunter `0.90.63` as the canonical observed vendor reference for this audit, using only secret-free behavioral evidence.
2. Reclassify duplicate Portal/WH09 workstreams as `KEEP_NOW | SIMPLIFY | DEFER | OBSOLETE`.
3. Formalize the vendor boundary: reference/decision dependency versus separate capital/execution authority.
4. Preserve useful WH09 evidence/fixtures before retiring broken duplicate runtimes.

### P1 — integration and workflow proof

1. Define a versioned WickHunter decision adapter contract.
2. Complete real API-mode causal-trace E2E (`#1098`) for our Portal path.
3. Preserve and strengthen research provenance/model lifecycle/Liquid20 ownership.
4. Turn WH09 reference outputs into bounded regression/parity fixtures where lawful and useful.
5. Prove that vendor-local state is not silently promoted to our authoritative causal state.

### P2 — Quant v2 implementation after governance activation

1. Activate the separate Quant v2 execution-governance package.
2. Implement V2-S1 Rust Quant Core target slice.
3. Demonstrate deterministic replay, restart/recovery and causal persistence.
4. Exercise vendor-exit/restore using safe, no-private-credential fixtures.

### P3 — optional expansion

1. Optional Hub/community integration if product value justifies it.
2. Optional richer vendor decision adapters.
3. Any real-capital gateway only as a separate owner-approved architecture/programme.

---

## 16. OPEN QUESTIONS + SAFE EXPERIMENTS

The following are useful but were intentionally not executed during the audit:

1. **License outage behavior** — cloned/isolation environment with exchange credentials removed.
2. **Restart/recovery semantics** — isolated no-credential fixture.
3. **Config export/import portability** — verify whether product configuration can be moved without secret leakage.
4. **Decision-only output** — public-data input with no configured private account.
5. **Multi-account reconciliation** — testnet only if future authority requires it.
6. **Open-position + Hub/license disconnect behavior** — testnet only.
7. **Update rollback behavior** — verify signed rollback on isolated clone.

Explicitly outside this audit:

- live private exchange execution,
- placing/cancelling orders,
- modifying account credentials,
- withdrawals,
- testing with real capital.

---

## 17. EVIDENCE INDEX

### Repository authority

- `AGENTS.md`
- `ARCHITECTURE_REGISTRY.yaml`
- `docs/agents/PROMPTING_STANDARD.md`
- `docs/agents/PROMPTING_HANDOVER.md`
- `docs/agents/RISK_BASED_EXECUTION_POLICY.json`
- `docs/ai_platform/portal/ADR-023_DEVELOPER_QUANT_PORTAL.md`
- `docs/ai_platform/portal/ADR-025_SYNOLOGY_PERSISTENT_RUNTIME_GITHUB_BUILD_PLANE.md`
- `docs/ai_platform/portal/ADR-027_QUANT_PLATFORM_V2_ARCHITECTURE_PROMOTION.md`
- `docs/ai_platform/portal/ADR-026_QUANT_PLATFORM_V2_CORE_AND_FREQTRADE_RETIREMENT.md`
- `docs/ai_platform/portal/QUANT_PLATFORM_V2_TARGET_ARCHITECTURE.md`
- `docs/ai_platform/portal/DEVELOPER_QUANT_PORTAL_ARCHITECTURE.md`
- `docs/ai_platform/portal/README.md`
- `tools/portal_audit/ledger/index.json`
- `tools/portal_audit/ledger/runtime.json`
- `tools/portal_audit/ledger/status_authority.json`
- `tools/portal_audit/ledger/backend_routes.json`
- `ai_platform/wickhunter/**`
- `tests/ai_platform/**`

### Repository state references

- `develop@f52a38d102f37888271816897494cab45cbff80a`
- PR `#1681` — Quant v2 execution-governance design lifecycle closeout; programme remains unactivated.
- Issue `#1098` — real composed API-mode browser E2E gap.

### Official WickHunter direct runtime evidence

- version `0.90.63`, healthy local `/api/health`,
- official runtime and proxy container metadata,
- authenticated versus unauthenticated route behavior,
- installed application/static route inventory,
- local runtime-state filenames and secret-free schema inspection,
- presence of encrypted non-testnet credential fields,
- zero open/closed positions in inspected position files at final readback,
- no mutation performed.

### Public WickHunter evidence

- `WickHunter/wickhunter-hub`,
- current Hub branch inspected during audit,
- public hosting policy / venue probes,
- `releases/README.md` signed-release contract,
- public license/check-in and lease challenge interfaces,
- historical `WickHunter/Wick-Hunter` repository treated as deprecated, not current product authority.

### Internal Synology reference evidence

Observed read-only runtime state included:

- healthy WH09 observer,
- healthy production research/reference runtime,
- unhealthy WH09 paper runtime with missing `ai_platform` module in healthcheck,
- running WH09 egress path without healthcheck,
- healthy market-evidence-v2,
- unhealthy older market-evidence runtime,
- healthy Binance v3 acceptance sampler,
- running Liquid20 live capability,
- obsolete exited collector requiring individual evidence review before cleanup.

---

## 18. HANDOVER

```yaml
checkpoint_version: 1
updated_at: 2026-09-11T18:33:15+02:00
branch: develop
head: f52a38d102f37888271816897494cab45cbff80a
status: ready
context_routes:
  - FREQTRADE_WICKHUNTER_REVERSE_PRODUCT_AUDIT_V1
  - ADR-023 Developer Quant product authority
  - ADR-025 Synology persistent runtime / GitHub build plane
  - ADR-027 promotion of ADR-026 Quant Platform v2 target
risk:
  persistent_data: false
  research_integrity: true
  model_activation: false
  auth_or_secrets: true
  shared_synology_mutation: false
  deployment: false
  user_workflow_change: false
  destructive_operation: false
  real_capital: false
  governance_or_ci: false
risk_gates:
  - preserve protected research/evaluation evidence and avoid stronger claims than direct evidence supports
  - do not print, copy, export or exercise private credential values
  - do not test private/live exchange execution in this task
proven:
  - official WickHunter 0.90.63 was healthy at final readback
  - vendor runtime exposes broad bot, account, strategy, diagnostics, replay, licensing and update surfaces
  - encrypted non-testnet private exchange credentials exist in vendor state
  - current Portal remains partially implemented with material disconnected execution/control surfaces
  - current accepted Quant v2 target retains Rust deterministic core, Python decision/ML, PostgreSQL causal state and Portal boundary
  - current product authority excludes real-capital execution
  - hybrid architecture is sufficient for a bounded strategic decision
unknown:
  - live order/reconciliation semantics across supported venues
  - long-term offline license behavior
  - disaster-recovery portability of vendor-local state
  - open-position behavior during Hub/license outage
conflicts:
  - prior no-credential/non-trading assumption for official runtime was disproved by direct state inspection
validation:
  - command: read-only repository/runtime/public-source verification
    result: PASS
    evidence: exact repository head, direct runtime health, route/state inventory, public Hub/release contract
blockers:
  - private/live execution proof intentionally blocked by credential and real-capital safety boundary
next_action: >
  Formalize one bounded architecture decision that designates official WickHunter
  as a third-party decision/console dependency, freezes it as the canonical V2
  reference fixture, and reclassifies duplicate Portal/WH09 workstreams before
  any Quant V2 implementation is activated.
```

## Final terminal state

`WICKHUNTER_VS_FREQTRADE_DECISION_READY`
