# WickHunter vs Freqtrade reverse-product audit

Date: 2026-09-11  
Repository baseline: `develop@f52a38d102f37888271816897494cab45cbff80a`  
Alias: `FREQTRADE_WICKHUNTER_REVERSE_PRODUCT_AUDIT_V1`  
Remediation alias: `FREQTRADE_WICKHUNTER_AUDIT_PR1708_REMEDIATION`  
Audit terminal state: `WICKHUNTER_VS_FREQTRADE_DECISION_READY`

## Scope and evidence rules

This document records a read-only reverse-product and architecture audit of the official WickHunter beta runtime against:

- the `blakinio/freqtrade` implementation at the recorded audit baseline,
- the accepted Quant Platform target architecture,
- historical/internal WH09 work that may overlap with the vendor product.

The audit and PR #1708 remediation do **not** authorize or perform repository-runtime deployment, Synology mutation, WickHunter modification, proprietary-bundle patching, credential testing, private exchange calls, order placement/cancellation, withdrawals, or capital use. Proprietary vendor code is not copied. Secret values are not printed or persisted.

### Claim taxonomy

- **FACT** — directly verified from repository state, public vendor material, or the bounded read-only runtime observations recorded by the audit.
- **INFERENCE** — conclusion derived from verified facts but not directly demonstrated end-to-end.
- **UNKNOWN** — not safely or sufficiently proven.
- **RECOMMENDATION** — proposed product/architecture action, not proof of implementation.
- **POST-AUDIT EVIDENCE** — evidence supplied after the original inspection and used to correct an earlier interpretation; it is evidence, not repository architecture authority.

### WickHunter product-readiness taxonomy

- `SUPPORTED_UI` — capability is exposed by the current WickHunter UI as ready for use.
- `VENDOR_DOCUMENTED` — capability/interface is described by official vendor material as supported.
- `OBSERVED_RUNTIME` — behavior was directly observed in the bounded runtime inspection.
- `INTERNAL/DORMANT` — code, route, schema, string, feature gate, or state shape exists, but current supported product exposure was not established.
- `UNKNOWN` — evidence is insufficient to classify support/readiness.

**Hard rule:** internal implementation evidence does not establish product readiness or integration authority.

For product-readiness claims, `SUPPORTED_UI` and `VENDOR_DOCUMENTED` are the relevant vendor support signals. `OBSERVED_RUNTIME` proves only the behavior actually observed. `INTERNAL/DORMANT` evidence may explain implementation shape but must not be promoted into a supported capability claim.

**POST-AUDIT EVIDENCE — vendor feedback:** “Things that are ready are displayed in the UI.” This statement is treated as vendor evidence that UI exposure is a readiness signal; it does not override repository authority or prove any capability that was not displayed/documented.

### WickHunter inspection evidence levels

- `WH-E3`: direct bounded runtime behavior demonstrated.
- `WH-E2`: direct runtime interface/state/schema observation; may still be `INTERNAL/DORMANT` for product readiness.
- `WH-E1`: public/static vendor-source evidence.

### Gap classes

- `A` — supported/observed WickHunter capability and ours has a comparable capability.
- `B` — supported/observed WickHunter capability and ours is incomplete.
- `C` — supported/observed WickHunter capability and ours is planned but not implemented.
- `D` — ours has it; equivalent WickHunter product capability was not established.
- `E` — both have relevant capability but semantics materially differ.
- `F` — neither current implementation has it, but the accepted target requires it.
- `G` — WickHunter evidence is insufficient.
- `H` — our repository evidence/authority is insufficient.

Allowed recommendation vocabulary:

`USE_WICKHUNTER`, `INTEGRATE_AROUND`, `BUILD_OURS`, `KEEP_OURS`, `ADOPT_PATTERN`, `DEFER`, `DROP`, `REQUIRES_DECISION`, `UNKNOWN`.

### Remediation risk record

```yaml
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
```

The associated gates are secret-value exclusion, no private exchange calls, no orders, no Synology mutation, no expansion into a real-capital architecture, and no further proprietary-runtime investigation beyond evidence needed to correct this document.

---

## 1. EXECUTIVE DECISION

### Decision

**RECOMMENDATION — keep the hybrid direction, defined as coexistence plus clear ownership boundaries.**

Do not build a second WickHunter product merely to duplicate vendor-facing trader UX. Do not collapse our platform into WickHunter-only ownership either.

The evidence supports a material WickHunter advantage in trader-facing product surface: current UI-visible bot/strategy controls, observed login/session behavior, local product state, diagnostics/health surfaces, and vendor-documented licensing/update/Hub responsibilities. Internal routes or dormant implementation are explicitly excluded from this readiness claim.

Our platform should continue to own capabilities that are strategically distinct and central to the accepted Quant v2 target: research/data lineage, evaluation integrity, model lifecycle, deterministic simulation/replay/recovery, causal state, PostgreSQL evidence, Portal/BFF workflow, Liquid20/public market data, independent validation, and vendor exit/reproducibility.

### Stop or defer duplicate work

- duplicate trader-console parity for capabilities already `SUPPORTED_UI` or `VENDOR_DOCUMENTED` in WickHunter,
- generic bot-configuration UI whose only purpose is vendor-product parity,
- first-class Grid/Manual/TV/Hedge parity unless a distinct Developer Quant requirement justifies it,
- permanent Freqtrade execution/state ownership contrary to the accepted v2 migration target,
- WH09 paper runtime as an enduring product runtime,
- Portal paths whose only value is recreating vendor trading-product behavior.

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

### Corrected integration stance

**RECOMMENDATION — coexistence first; integrate only through vendor-supported/documented interfaces.**

The official WickHunter UI may remain a separate vendor console. Our Developer Quant platform remains independently useful and keeps its own research/evidence/deterministic ownership.

A technical WickHunter adapter is **OPTIONAL / FUTURE / REQUIRES_SUPPORTED_VENDOR_INTERFACE**. The audit did not establish a stable vendor-supported decision API or contract. Internal/dormant routes are not an integration contract, and the document does not recommend patching the proprietary bundle or bypassing feature gates.

---

## 2. VERIFIED BASELINE

### Repository

**FACT** — the exact repository baseline used for the original final authority readback was:

`develop@f52a38d102f37888271816897494cab45cbff80a`

The associated Git tree SHA was:

`7e29902675ba7199ceed9fdeaaeed4db67f2f9f3`

The tree SHA is not the branch/commit HEAD.

### Accepted repository authority

**FACT** — product and target architecture are layered:

- ADR-023: private single-owner Developer Quant product boundary,
- ADR-025: Synology persistent runtime plus GitHub-hosted CI/build/disposable compute,
- ADR-026 as promoted by ADR-027: Quant Platform v2 target architecture.

**FACT** — ADR-023/ADR-027 do not authorize real-money execution, private trading credentials for order submission, withdrawals, or capital authority. A future real-capital system would require a separate owner-approved Execution/Capital Gateway architecture/programme.

### Official WickHunter runtime

**FACT / `OBSERVED_RUNTIME` / WH-E3** — the official runtime returned:

`GET http://127.0.0.1:8090/api/health -> 200 {"ok":true,"version":"0.90.63"}`

Observed official containers included:

- `wickhunter-official-wickhunter-1` using `local/wickhunter-official:0.90.63`,
- `wickhunter-official-https-proxy-1` using `local/wickhunter-caddy:2.10.2`.

Observed hardening/runtime properties included a non-root runtime user, read-only root filesystem, non-privileged container configuration, bounded mounts, restart policy, and a local health contract.

### Credential/environment correction

**FACT / `OBSERVED_RUNTIME` / WH-E2** — a redacted state scan found nonempty encrypted exchange credential fields. No credential values were printed or retained.

**FACT / `OBSERVED_RUNTIME` / WH-E2** — the local WickHunter account record classified the inspected Bitget account with `testnet=false`.

**POST-AUDIT EVIDENCE** — a separate Bitget Demo test supplied after the original audit showed that WickHunter `0.90.63` can persist a Bitget Demo account in local state as `env: mainnet` / `testnet:false` because Bitget Demo is not exposed as a ready/supported UI environment in that version.

**UNKNOWN** — the actual exchange-side environment, permissions, funds, or capital status of the encrypted credentials observed during the audit was not independently proven.

Therefore the local `testnet=false` classification must **not** be described as proof that the credentials were live, production, mainnet-funded, or real-capital credentials.

**FACT** — all inspected positions files had zero open and zero closed positions at the final original readback.

**SAFETY DECISION** — private exchange endpoints, order placement/cancellation, credential mutation, and real-execution proof were intentionally not exercised and are not part of this remediation.

---

## 3. OFFICIAL WICKHUNTER — WHAT IT ACTUALLY IS

### Supported versus internal evidence

The original static/runtime inventory showed a broad set of routes, schemas, labels, and state families. That evidence is useful for understanding product shape but must be separated from supported readiness.

**`SUPPORTED_UI` / observed labels** included current product-facing families such as:

- `AI Strategy`,
- `Grid`,
- `Hedge Bot`,
- `Liq Scalper`,
- `Manual Bot`,
- `Strategy Builder`,
- `TV Signal`.

Where the UI exposes a capability as ready, it may be treated as a supported product surface for this audit. Exact end-to-end semantics still require separate evidence when material.

**`INTERNAL/DORMANT` / WH-E2** evidence included route or implementation families for authentication, accounts, bot lifecycle, AI draft/apply/replay/status, deal controls, grids, hedging, P&L, replay/what-if, strategy evaluation, terminal/order/deal operations, TradingView signals, and exchange-specific paths. Their existence alone does not prove that each feature is supported, ready, stable, or vendor-authorized for integration.

### Bitget Demo

**POST-AUDIT EVIDENCE** — WickHunter `0.90.63` contains internal Bitget Demo-related implementation elements, but Bitget is classified with `hasDemo: false` in the relevant feature readiness path.

**POST-AUDIT EVIDENCE — vendor feedback** — Bitget Demo is not ready in this version, consistent with the broader vendor statement that ready features are displayed in the UI.

**CONCLUSION** — Bitget Demo is `NOT READY / NOT SUPPORTED` for WickHunter `0.90.63`. Internal implementation elements do not change that classification.

No recommendation is made to patch the bundle, flip hidden/demo flags, or bypass the feature gate.

### Persistence shape

**FACT / `OBSERVED_RUNTIME` / WH-E2** — local runtime state included structures for deal/DCA/hedge/entry activity, liquidation history, contexts, positions, installation/update metadata, and licensing/subscription/lease state.

This proves local persistence structures exist. It does not by itself prove all UI features using those structures are supported or prove crash/reconciliation semantics for exchange-side state.

### Hub / distribution / updates

**FACT / `VENDOR_DOCUMENTED` / WH-E1** — public Hub/release material documents signed release manifests, tarball hashes, release-key verification, update compatibility behavior, and Hub license/check-in/lease surfaces.

**FACT / WH-E1** — public Hub hosting policy contains reachability probes for seven venue families: Bybit, Binance USD-M, Bitget, Bitunix, BloFin, WEEX, and Aster.

That is **reachability/public-source evidence**, not proof that all seven venues are fully supported for trading in the current WickHunter UI.

### What remains unproven

**UNKNOWN** — an exhaustive supported-venue matrix for `0.90.63` was not established by this audit.

**UNKNOWN** — internal route/adapter presence does not prove exchange-specific order semantics, partial-fill handling, reconciliation, restart behavior, or failure recovery.

**UNKNOWN** — long-term/offline license behavior, full configuration portability, and disaster-recovery semantics were not proven.

---

## 4. OUR CURRENT PLATFORM — WHAT ACTUALLY EXISTS

### Portal implementation snapshot

**FACT** — the living exact-head Portal ledger at the recorded baseline reported:

- 32 backend modules,
- 95 backend routes,
- 29 BFF handlers,
- 33 frontend pages.

**FACT** — the product is partially implemented. The exact-head route ledger contains many `PARTIAL`, `DISCONNECTED`, and externally gated entries.

Examples include disconnected bot-builder materialization, command activation/submission, exchange verification, grid policy storage/provider composition, signal processing, terminal intents, order/position/trade reconciliation, and runtime observability sources.

**FACT** — issue `#1098` remains an explicit gap for API-mode browser E2E against the real composed FastAPI/database path; fixture-only browser evidence does not prove browser -> BFF -> backend -> persistence/provider behavior.

### Research/ML/evaluation strength

**FACT** — the repository contains substantial quant/WickHunter research infrastructure including baseline strategy, bounded optimization, candidate evaluation/activation support, deterministic replay, datasets/features/materialization, LightGBM scoring, paper-validation history, production-research evidence modules, replay price paths, and extensive research-integrity/model-comparison tests.

**FACT** — tests include protected/final holdout guards, model comparison suites, candidate identity checks, runtime-mode checks, health checks, and other provenance/evaluation controls.

### Implementation-status evidence boundary

**FACT** — `tools/portal_audit/ledger/index.json` is the living exact-head implementation inventory referenced by the repository's Portal status contract. At the recorded baseline that contract grants no live trading, real capital, withdrawals, private-trading credential use, automatic model/strategy promotion, protected-target mutation, or deployment authority.

This audit is evidence and analysis; it does not create a second implementation-status source.

---

## 5. OUR INTENDED TARGET — WHAT WE WERE BUILDING

### Product workflow

**FACT** — ADR-023 defines the Developer Quant vertical slice as:

`REALTIME_PUBLIC -> bot/model decisions including NO_TRADE -> simulated positions/outcomes -> durable chronological dataset/labels -> local challenger training -> active/challenger/baseline comparison -> deliberate active-model selection -> restart-safe continued observation`

### Runtime placement

**FACT** — ADR-025 places persistent application runtime and durable storage on Synology and uses GitHub-hosted Actions for stateless/disposable CI, tests, scans, packaging, image builds, and bounded jobs.

### Quant v2 target

**FACT** — ADR-026 as promoted by ADR-027 selects:

- Rust Quant Core for deterministic ordering, simulation, journal/replay/recovery, and causal state,
- Python for strategy/ML semantics,
- PostgreSQL as the recovery spine,
- FastAPI + Next.js as the owner-facing Portal boundary,
- Freqtrade as reference oracle/migration input/temporary compatibility rather than permanent v2 state owner.

The promoted target includes a first-slice concept using frozen canonical public market/WickHunter evidence and a Python WickHunter decision producer.

**IMPORTANT INTERPRETATION** — the target's use of “WickHunter”/“Python WickHunter decision” describes the repository's selected strategy/reference plane and fixtures. It does **not** prove that the proprietary official WickHunter runtime exposes a stable supported vendor decision API. ADR-027 also states that architecture promotion does not activate implementation.

---

## 6. ARCHITECTURE COMPARISON

### Official WickHunter — observed product shape

Approximate observed shape:

`Browser -> HTTPS proxy -> proprietary WickHunter runtime -> vendor bot/strategy/state surfaces -> local product data`

with a separate Hub boundary for licensing, updates, distribution, and community concerns.

This is an observational topology, not a declaration that every internal exchange/terminal route is a supported product interface.

### Our current platform

Approximate current shape:

`Next.js -> BFF/FastAPI -> platform/control packages -> Freqtrade/simulator/WH09/reference paths -> mixed persistence + public market data`

with a comparatively strong research/evaluation/provenance subsystem.

### Accepted target

`Next.js -> FastAPI -> Rust Quant Core <-> Python strategy/ML -> PostgreSQL`

with public data inputs, deterministic simulation/recovery, causal evidence, and explicit migration/reference boundaries.

### Architectural interpretation

**INFERENCE** — WickHunter is materially ahead in trader-facing productization, while the accepted Quant v2 target is intentionally stronger around reproducible research, deterministic simulation/recovery, causal evidence, and owned data/model lifecycle.

**RECOMMENDATION** — preserve those distinct ownership strengths and use coexistence as the default architecture. Any later technical bridge to official WickHunter must be based on a supported/documented vendor interface, not reverse-inferred from internal routes.

---

## 7. MASTER CAPABILITY MATRIX

| Capability | WickHunter evidence/readiness | Gap | Assessment | Recommendation |
|---|---|---:|---|---|
| Login/auth/session | `OBSERVED_RUNTIME` plus UI exposure | B | Working vendor product boundary observed; our broader workflow closure remains incomplete | `KEEP_OURS` |
| Bot configuration UI | `SUPPORTED_UI` | B | Vendor is materially ahead in trader-facing configuration | `USE_WICKHUNTER` |
| Grid/Manual/TV/Hedge product families | `SUPPORTED_UI` for displayed families; exact semantics vary | B/C | Do not duplicate solely for parity | `DEFER` |
| Bitget Demo environment | `INTERNAL/DORMANT`; `hasDemo: false`; vendor says not ready | G | **NOT READY / NOT SUPPORTED** in `0.90.63` | `DEFER` |
| Private exchange account state | `OBSERVED_RUNTIME` encrypted state exists | E/G | Local state existence proven; exchange-side environment/capital status of inspected credentials is `UNKNOWN`; current Portal forbids private execution credentials | `REQUIRES_DECISION` |
| Seven-venue reachability probes | `VENDOR_DOCUMENTED` public Hub source | G | Reachability probes are not a trading-support matrix | `UNKNOWN` |
| Supported multi-venue trading | UI/documentation must decide readiness | G | Exhaustive current supported venue set and semantics not established here | `UNKNOWN` |
| Exchange adapter/route strings | `INTERNAL/DORMANT` | G | Presence does not establish readiness or integration contract | `UNKNOWN` |
| Liquidation/public market data | public/vendor and our direct evidence | A/E | Both have relevant capability with different semantics/ownership | `KEEP_OURS` |
| Liquidation strategy semantics | mixed observed/internal evidence | E/G | Comparable domain; equivalence not proven | `ADOPT_PATTERN` |
| DCA/TP/SL/hedge execution semantics | UI/internal evidence, no safe E2E execution proof | E/G | Do not infer live correctness from route/UI presence; ours remains simulation-only | `DEFER` |
| Durable product state / P&L / history | `OBSERVED_RUNTIME` local state plus visible product surfaces | E | Vendor local product state differs from our target causal/recovery model | `BUILD_OURS` |
| Diagnostics / replay | UI/runtime/internal evidence | G/D | Vendor has useful product surfaces; deterministic/research equivalence not proven | `KEEP_OURS` |
| Research provenance | insufficient vendor evidence; strong repo evidence ours | D/G | Differentiator remains ours | `KEEP_OURS` |
| Protected holdout / no-lookahead | strong repo evidence ours | D/G | Equivalent vendor controls not established | `KEEP_OURS` |
| Model lifecycle | strong explicit repo authority ours | D/G | Vendor-equivalent lifecycle not established | `KEEP_OURS` |
| Deterministic simulation/recovery | insufficient vendor evidence; target-only ours | G/F | Accepted target still requires owned deterministic core semantics | `BUILD_OURS` |
| Portal causal trace | current partial; accepted target requires it | D/F | Finish as our evidence surface | `BUILD_OURS` |
| Signed update chain | `VENDOR_DOCUMENTED` | E | Mature vendor pattern worth learning from | `ADOPT_PATTERN` |
| Hub/community distribution | `VENDOR_DOCUMENTED` / visible vendor boundary | C | Vendor already owns this product class | `USE_WICKHUNTER` |
| Supported vendor integration API | not established | G | No stable vendor-authorized decision contract proven | `UNKNOWN` |
| Vendor independence / exit | our architectural property | D | Preserve independent data/research/evidence and migration fixtures | `KEEP_OURS` |

---

## 8. WHAT WICKHUNTER ALREADY SOLVES

The strategic conclusion remains, but only at evidence-calibrated scope.

**FACT / `SUPPORTED_UI` or `OBSERVED_RUNTIME` where noted** — WickHunter provides meaningful trader-facing product value through visible bot/strategy configuration families, authentication/session behavior, local application state, health/diagnostic surfaces, and other UI-visible workflows.

**FACT / `VENDOR_DOCUMENTED`** — the vendor ecosystem also owns licensing/check-in/lease, signed update/distribution behavior, and Hub/community concerns documented in public vendor material.

**RECOMMENDATION** — we should not automatically recreate those classes of product surface when a vendor-supported WickHunter workflow already satisfies the user need.

**LIMIT** — internal terminal/order/exchange routes, adapter strings, dormant feature gates, or local schemas are not counted as “already solved” unless the capability is also supported/documented or directly observed at the required product level.

The durable strategic differentiators for our platform remain:

- research provenance and evaluation integrity,
- deterministic replay/simulation/recovery,
- data and feature lineage,
- explicit model lifecycle,
- causal evidence and PostgreSQL recovery semantics,
- independent public-market-data evidence,
- vendor exit and reproducibility.

---

## 9. WHAT WE CAN STOP OR DEFER BUILDING

**RECOMMENDATION** — stop or defer work whose only goal is direct parity with supported vendor trader UX:

- duplicate bot-builder UX (`#1090`) when it adds no Developer Quant-specific research value,
- generic Grid parity (`#1096`),
- generic signal/TradingView parity (`#1095`),
- exchange-management parity (`#1097`) unless a safe Developer Quant requirement remains,
- generic terminal/order submission surfaces (`#1086`, `#1091`) as a current product objective,
- permanent Freqtrade state/execution ownership in the v2 end state,
- WH09 paper-runtime productization as a permanent user product.

This is prioritization, not destructive authority. It does not authorize deleting code, closing runtimes, removing evidence, or changing open issues without a separate bounded task.

Do **not** defer capabilities that are unique to our research/evidence target merely because an internal WickHunter route with a similar name exists.

---

## 10. WHAT WE SHOULD STILL OWN

Keep ownership of:

- research experiments and evaluation methodology,
- dataset/feature/model/config identities and lineage,
- no-lookahead/holdout integrity,
- deliberate `BASELINE | CHALLENGER | ACTIVE | ARCHIVED` lifecycle,
- deterministic simulation, replay, idempotency, snapshot/recovery, and causal tracing,
- PostgreSQL evidence/recovery spine,
- Portal/BFF presentation of our causal research truth,
- Liquid20/public data collection and attributable market evidence,
- independent risk/simulation verification,
- vendor-exit fixtures and reproducibility.

**RECOMMENDATION** — official WickHunter should not become the sole owner of data, evidence, model identity, or reproducibility required to evaluate our platform independently.

---

## 11. HISTORICAL WH09 WORK — KEEP / REPURPOSE / RETIRE

The original read-only runtime inventory showed mixed health. Classification remains evidence-preserving and non-destructive:

| Historical/internal asset | Observation | Recommendation |
|---|---|---|
| WH09 runtime observer | healthy read-only observer | `KEEP_OURS` as bounded reference/evidence adapter |
| production-research runtime | healthy research/reference path | `KEEP_OURS` / repurpose as reference oracle and fixture source |
| candidate paper runtime v12 | unhealthy; healthcheck import failure | `DEFER` as product, retire candidate only after evidence freeze and separate authority |
| WH09 egress v12 | running companion to paper path | retire candidate with paper path only under separate task |
| market-evidence v2 | healthy | keep temporarily as evidence input |
| older market-evidence runtime | unhealthy | retire candidate after provenance/evidence needs are frozen |
| `liquid20-live` | running public-data capability | `KEEP_OURS` |
| Binance v3 acceptance sampler | healthy acceptance evidence | keep while it remains useful for provider evidence |

“Retire candidate” here is classification, not permission to stop/remove a container or delete persistent data.

---

## 12. SECURITY + VENDOR-DEPENDENCY ANALYSIS

### Positive observations

**FACT / `OBSERVED_RUNTIME`** — the inspected official container used useful hardening properties such as non-root execution, non-privileged mode, read-only root filesystem, and bounded mounts.

**FACT / `VENDOR_DOCUMENTED`** — the public release design uses signed release metadata and artifact hashing, with public verification material separated from the private signing key.

### Credential interpretation

**FACT** — encrypted exchange credential fields existed locally.

**FACT** — the local account record used `testnet=false`.

**POST-AUDIT EVIDENCE** — Bitget Demo can still be represented locally with that classification in `0.90.63` because Demo is not a supported UI environment.

**UNKNOWN** — whether the inspected credential set was exchange-side demo, test, mainnet, funded, unfunded, read-only, or order-capable was not proven.

Accordingly this audit treats credential presence as an `auth_or_secrets` risk boundary, not as evidence of real-capital operation.

### Vendor dependency

If the vendor or Hub became unavailable, likely affected classes include future updates, licensing/check-in behavior, proprietary trader UI/runtime capabilities, and vendor community/distribution features. Exact degradation under prolonged Hub/license outage remains `UNKNOWN`.

Our owned research datasets, model/evaluation evidence, public-data pipelines, Portal code, accepted deterministic-core target, and frozen migration/reference fixtures remain the strategic vendor-exit boundary.

### Security conclusion

Do not copy vendor credentials into Portal, do not expose proprietary internal routes to the browser, and do not promote dormant/private internals into integration contracts.

---

## 13. HYBRID ARCHITECTURE OPTIONS

### Option A — WickHunter-only

Reject as the platform end state.

Reason: it would make proprietary vendor behavior too central to research/evidence/model lifecycle and weaken independent reproducibility/vendor exit.

### Option B — build our own full trader-product parity

Reject as the default programme.

Reason: it duplicates a substantial vendor-facing product surface without clear differentiation and spends effort outside the strongest Developer Quant value.

### Option C — coexistence + clear ownership boundaries

**RECOMMENDED.**

- WickHunter remains a standalone vendor/trader console for its supported product workflows.
- Our platform owns public-data research, evaluation, model lifecycle, deterministic simulation/recovery, causal evidence, and Portal research workflows.
- No direct technical coupling is assumed.
- A future adapter is permitted only after an official supported/documented interface exists and a separate bounded integration task validates that contract.
- Internal/dormant endpoints are explicitly not sufficient.

This is the corrected meaning of “hybrid”.

---

## 14. RECOMMENDED TARGET ARCHITECTURE AFTER THIS DISCOVERY

The accepted Quant v2 architecture remains the repository target; this audit does not amend ADR-027.

Recommended product boundary after the WickHunter discovery:

```text
GitHub-hosted CI/build/test
          |
          v
Synology Developer Quant runtime
          |
          +--> public collectors / Liquid20
          |          |
          |          v
          |    canonical public market input
          |          |
          |          v
          |    Python strategy/ML plane
          |          |
          |          v
          |    Rust deterministic Quant Core   [target, not yet implemented]
          |          |
          |          v
          |      PostgreSQL causal state
          |          |
          |          v
          |     FastAPI/BFF -> Next.js Portal
          |
          +--> WickHunter standalone vendor console
                    |
                    +--> future optional bounded integration
                         ONLY via a vendor-supported/documented interface
```

**RECOMMENDATION** — the direct path `our platform -> proprietary WickHunter decision adapter -> Rust Quant Core` is **not** an established contract and must not be treated as the default implementation plan.

If a supported vendor interface later appears, a separate task may evaluate:

`vendor-supported contract -> bounded adapter -> explicitly versioned internal contract`

until then, coexistence is the correct architecture.

---

## 15. P0 / P1 / P2 / P3 ROADMAP

### P0 — evidence calibration and product boundary

- keep official WickHunter `0.90.63` as a secret-free behavioral/reference baseline where lawful and useful,
- distinguish `SUPPORTED_UI` / `VENDOR_DOCUMENTED` / `OBSERVED_RUNTIME` / `INTERNAL/DORMANT` / `UNKNOWN`,
- classify Bitget Demo as `NOT READY / NOT SUPPORTED`,
- reclassify duplicate Portal/WH09 work before further target-driven implementation,
- keep private credentials and exchange execution outside the Developer Quant product.

### P1 — close our own evidence gaps

- complete the real API-mode causal-trace/browser closure represented by issue `#1098`,
- preserve research/provenance/Liquid20 capabilities,
- freeze useful WH09 fixtures/reference evidence before any separately authorized retirement,
- document a vendor integration surface **only if** the vendor publishes/supports one; do not implement an adapter from internal/dormant endpoints.

### P2 — Quant v2 target implementation after governance activation

- implement V2-S1 only under the separate execution-governance authority required by ADR-027,
- preserve deterministic parity/intentional-difference evidence, replay, restart/recovery, and Portal proof,
- perform vendor-exit/restore exercises using secret-free fixtures/reference evidence.

### P3 — optional vendor ecosystem integration

- consider Hub/community or other vendor integration only where a supported contract and product benefit exist,
- any future real-capital Execution/Capital Gateway remains an entirely separate owner-approved programme.

---

## 16. OPEN QUESTIONS + SAFE EXPERIMENTS

### Open questions

1. What exact WickHunter `0.90.63` venue/features are `SUPPORTED_UI` versus merely present internally?
2. Does the vendor publish a stable supported machine-to-machine decision/configuration interface suitable for third-party integration?
3. What are the documented semantics for configuration export/import, backup/restore, and license outage?
4. Which vendor-facing product capabilities materially replace planned Portal work, and which Portal capabilities remain uniquely research/evidence oriented?
5. Which WH09 fixtures are still required for v2 reference/parity work before historical runtime retirement can be considered?

### Safe future evidence work

No additional proprietary-runtime experiment is required for PR #1708 remediation.

If later separately authorized, safe work should prefer:

- official vendor documentation/UI inspection,
- secret-free config export/import portability checks if supported,
- restart/recovery exercises on an isolated secret-free clone,
- license-outage behavior on an isolated clone with exchange credentials removed,
- supported public-data or non-capital test interfaces documented by the vendor.

Do not use Bitget Demo as a currently supported WickHunter `0.90.63` environment, do not enable hidden/demo flags, and do not test real/private exchange execution under this audit.

---

## 17. EVIDENCE INDEX

### Repository authority and implementation evidence

- `AGENTS.md` at the recorded baseline.
- `ARCHITECTURE_REGISTRY.yaml` — ADR-027 latest accepted architecture change, `accepted_target_not_implemented`.
- `docs/ai_platform/portal/ADR-023_DEVELOPER_QUANT_PORTAL.md`.
- `docs/ai_platform/portal/ADR-025_SYNOLOGY_PERSISTENT_RUNTIME_GITHUB_BUILD_PLANE.md`.
- `docs/ai_platform/portal/ADR-027_QUANT_PLATFORM_V2_ARCHITECTURE_PROMOTION.md` and promoted ADR-026 target.
- `docs/ai_platform/portal/QUANT_PLATFORM_V2_TARGET_ARCHITECTURE.md`.
- `tools/portal_audit/ledger/index.json` and task-relevant ledger sections.
- Issue `#1098` for API-mode browser E2E gap.

### Official WickHunter evidence recorded by the original audit

- bounded runtime health and container-property observations for version `0.90.63`,
- redacted credential-field presence and local account metadata without secret values,
- local persistent-state schema/file-family observations,
- static/internal route and label inventory, explicitly reclassified by this remediation where support was not established,
- public `WickHunter/wickhunter-hub` source and release/update documentation.

### Post-audit corrective evidence

- owner-supplied Bitget Demo test: a Demo credential/account can be persisted by WickHunter `0.90.63` with local `env: mainnet` / `testnet:false`; this remediation did not repeat credential testing,
- owner-supplied/vendor feedback: “Things that are ready are displayed in the UI.”,
- owner-supplied/vendor feedback that Bitget Demo is not ready,
- internal readiness evidence supplied for review: Bitget `hasDemo: false`.

These post-audit items correct product-readiness/environment interpretation. They do not expand repository architecture authority and do not prove any exchange-side capital status.

### CI evidence for PR #1708 remediation

Before remediation, exact PR head `b93a0f3d546fce1f4f872746cbfcf4d2e8e6b139` had one failing `Freqtrade CI` lightweight routing-contract test because this audit document used wording reserved for the repository's Portal status source. Documentation build and pre-commit were green on that head. The remediation changes the document wording rather than governance/tests/workflows.

Final exact-head CI is evaluated on the PR after this document update; no result is pre-claimed inside the audit.

---

## 18. HANDOVER

PR #1708 is the durable handover for this documentation remediation.

Per `docs/agents/PROMPTING_HANDOVER.md`, a separate continuation checkpoint is unnecessary when the bounded documentation task reaches terminal PR closeout. The previous audit YAML checkpoint that named `branch: develop` and the baseline commit as if they were the PR branch/head has therefore been removed.

The `develop@f52a38d102f37888271816897494cab45cbff80a` value retained near the top of this document is the **historical audit evidence baseline**, not a claim about the current PR head.

Final PR readiness must be decided from live GitHub state on the exact final PR head. No runtime, Synology, WickHunter, credential, exchange, deployment, model, or capital mutation is part of this PR.
