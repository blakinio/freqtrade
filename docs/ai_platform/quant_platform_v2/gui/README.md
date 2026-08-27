# Quant Platform v2 GUI baseline

This directory freezes the first clean-sheet GUI baseline derived from real WickHunter screenshots supplied by the owner and from the v2 mockups generated during the design session on 2026-08-26.

## Design intent

The visual direction is **WickHunter-inspired, operator-first, data-dense and research-aware**. WickHunter contributes useful visual cues — dark premium theme, indigo/violet accents, left navigation, rounded cards and a right-side action summary — but its long forms, low information density and decorative empty space are not copied as product architecture.

The v2 Portal is organized around user intent:

- understand platform health quickly;
- inspect a bot and its latest decisions;
- create or revise a bot safely;
- inspect market context and the exact decision chain;
- train, compare and deliberately activate models;
- trace datasets and experiments;
- use a local LLM as a research copilot;
- diagnose runtime nodes and services.

## Primary screen families

1. **Overview / Command Center**
2. **Trading** — Bots, Create Bot, Positions, Orders, Markets, Alerts
3. **Research** — Strategies, Backtests, Replays, Experiments, Comparisons
4. **ML / Models** — Model Registry, Training Jobs, Features, Datasets, lifecycle views
5. **AI Lab** — Ollama, Research Agent, Experiment Analysis, Research History
6. **Infrastructure** — Runtime Nodes, Synology, Training PC, Workers, Market Data, Services
7. **System** — Logs, Integrations, Settings, Audit

## Asset gallery
Open [`ASSET_GALLERY.md`](ASSET_GALLERY.md) for the visual inventory. Repository-safe WebP files are committed directly under `assets/`; run `python docs/ai_platform/quant_platform_v2/gui/restore_visual_assets.py --extract <dir>` to reproduce and verify the deterministic ZIP archive.

## Asset groups

### Real WickHunter references

Privacy-redacted WebP copies of the supplied WickHunter captures are committed under `assets/reference/wickhunter/`. `assets/previews/wickhunter-reference-contact-sheet.webp` provides a compact overview. These files are reference material only; WickHunter is not part of the v2 implementation and the UI is not intended to be copied pixel-for-pixel.

The preserved set covers dashboard, bot creation variants, terminal views, bot list, grid bots, marketplace, open deals, PnL reporting, signal wizard/logs, liquidation logs, profile/subscription and the later optimized-liquidation-bot form. One standalone profile capture from the earlier shard transport could not be recovered; the alternate profile reference and contact-sheet coverage remain available and the omission is recorded in `ASSET_MANIFEST.json`.

### Proposed v2 mockups

Generated design concepts are committed under `assets/mockups/`, with `assets/previews/v2-mockups-contact-sheet.webp` as the overview, for:

- command center / overview;
- create-bot workflow;
- model registry;
- bot control/detail view;
- an earlier broad dashboard concept.

These are directional mockups, not final production specifications. Layout hierarchy and workflow are authoritative only to the degree described by the Markdown design docs.

## Image integrity and privacy

`ASSET_MANIFEST.json` records each committed member path, size and SHA-256 plus the deterministic archive size/hash/member list. `restore_visual_assets.py` verifies every committed asset before rebuilding the ZIP with fixed ordering, metadata and compression, then verifies the archive hash, member count and ZIP CRC integrity.

Only privacy-redacted WickHunter copies are committed. The inconsistent Base64 shard transport has been removed rather than treated as evidence of a valid archive. Original source material is not required by the restore path and is not committed.
