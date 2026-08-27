# Quant Platform v2 — clean-sheet product baseline

Status: **design baseline / proposal**  
Date: 2026-08-26  
Target integration branch: `develop`

This directory captures the clean-sheet direction for a successor to the current experimental Portal/Freqtrade-derived stack. It is intentionally a product and architecture baseline, not an implementation claim and not an accepted ADR by itself.

## Binding boundaries inherited from current authority

Until a later owner-approved ADR explicitly supersedes them, ADR-023 and ADR-025 remain binding for the current product:

- private, single-owner developer/quant/research platform;
- market inputs are `REALTIME_PUBLIC | REPLAY`;
- persistent runtime/storage target is `LOCAL | SYNOLOGY`;
- model lifecycle is `BASELINE | CHALLENGER | ACTIVE | ARCHIVED`;
- real-money order submission, private capital authority and withdrawals remain out of scope;
- any future real-capital capability requires a separate owner-approved Execution/Capital Gateway programme.

The v2 proposal deliberately keeps those safety boundaries while rethinking the implementation from a clean sheet.

## Product thesis

The current repository is valuable as a sandbox, behavioural reference, test corpus and source of lessons, but it should not dictate the shape of a clean v2 platform. The v2 target is a coherent quant cockpit rather than a Freqtrade-shaped UI.

The proposed technology split is:

- **Rust core** for market-data ingestion, streaming, deterministic simulation/event processing, bot runtime/supervision/recovery and other long-lived performance-sensitive services;
- **Python ML/research** for feature engineering, datasets, LightGBM, XGBoost, PyTorch, tuning, training, evaluation and research workflows;
- **Ollama/local LLMs** as an isolated research-assistant service, never as an implicit direct trading authority;
- **Next.js/TypeScript** for the Portal UI;
- **Freqtrade/FreqAI** retained only as legacy/reference/transition components where they still provide useful behaviour while native replacements reach parity.

## Documents

- [`gui/README.md`](gui/README.md) — GUI baseline and asset index.
- [`gui/GUI_INFORMATION_ARCHITECTURE.md`](gui/GUI_INFORMATION_ARCHITECTURE.md) — screen map and navigation model.
- [`gui/UX_DESIGN_SYSTEM.md`](gui/UX_DESIGN_SYSTEM.md) — operator-first UX and visual language.
- [`gui/TECHNICAL_ARCHITECTURE.md`](gui/TECHNICAL_ARCHITECTURE.md) — proposed clean-sheet service split.
- [`gui/MIGRATION_AND_LEGACY_BOUNDARY.md`](gui/MIGRATION_AND_LEGACY_BOUNDARY.md) — how Freqtrade/FreqAI and the current Portal are treated during migration.
- [`gui/ASSET_MANIFEST.json`](gui/ASSET_MANIFEST.json) — provenance and hashes for the visual reference set.

## Implementation rule

Do not implement the whole v2 at once. The first implementation should be one vertical slice:

`public exchange WS -> market data -> WickHunter decision -> native simulation -> durable outcome -> Portal view`

Only after that slice is correct and restart-safe should datasets, training, model registry, challenger comparison, AI Lab and additional bot types be layered on.
