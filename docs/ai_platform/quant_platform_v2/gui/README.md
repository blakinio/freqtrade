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

Open [`ASSET_GALLERY.md`](ASSET_GALLERY.md) for the complete visual inventory. The images are stored in a reconstructable compressed archive; run `python docs/ai_platform/quant_platform_v2/gui/restore_visual_assets.py --extract <dir>` from a checkout to restore them.

## Asset groups

### Real WickHunter references

The repository stores optimized WebP copies of the owner-supplied real WickHunter captures inside a reconstructable archive under `reference/wickhunter/`. `previews/wickhunter-reference-contact-sheet.webp` is included inside the archive. These are reference material only. They are not a claim that WickHunter is part of the v2 implementation and are not to be copied pixel-for-pixel.

The reference set covers dashboard, bot creation variants, terminal views, bot list, grid bots, marketplace, open deals, PnL reporting, signal wizard/logs, liquidation logs, profile/subscription and the later optimized-liquidation-bot form.

### Proposed v2 mockups

The same visual archive contains generated design concepts under `mockups/`, with `previews/v2-mockups-contact-sheet.webp` included inside the archive, for:

- command center / overview;
- create-bot workflow;
- model registry;
- bot control/detail view;
- an earlier broad dashboard concept.

These are directional mockups, not final production specifications. Layout hierarchy and workflow are authoritative only to the degree described by the Markdown design docs.

## Image optimization

The original captures were converted to repository-friendly WebP reference copies (max width 800 px, quality 55) and packed into a deterministic design archive. Before public-repository packaging, authenticated account/avatar regions were blurred on WickHunter references, with the profile identity area additionally redacted; original source hashes remain recorded for provenance and original unredacted captures are not committed. Because this execution path writes repository text reliably but not large binary payloads, the archive is stored losslessly as ordered Base64 text parts under `assets/archive_parts/`; `restore_visual_assets.py` reconstructs and SHA-256 verifies the ZIP. `ASSET_MANIFEST.json` records original-source, archive-member, part and reconstructed-archive hashes. The original 43 MB capture ZIP itself is not committed because all 24 captures are represented in the optimized archive, together with the two later optimized-liquidation captures and five generated v2 mockups.
