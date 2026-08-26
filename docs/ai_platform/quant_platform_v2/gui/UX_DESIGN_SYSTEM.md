# UX and visual design system baseline

## Principles

1. **Operator-first** — maximize clarity of state, freshness, decisions and failures before visual decoration.
2. **Research-aware** — datasets, experiments, models and provenance are first-class concepts.
3. **Dense but calm** — more information per viewport than current WickHunter references, without turning every page into a log console.
4. **Progressive disclosure** — summary first, details on demand, advanced controls behind explicit expansion.
5. **High contrast** — avoid the low-contrast labels/placeholders visible in parts of the reference UI.
6. **Consistent status semantics** — state must be expressed by text/icon plus color, never color alone.
7. **Fail closed in UI** — unknown/stale/ambiguous state is visibly different from healthy/ready state.
8. **No hidden authority** — model activation, runtime changes and future execution-sensitive actions are explicit and attributable.

## Visual direction

The visual language is a refined dark quant cockpit inspired by the supplied WickHunter UI:

- near-black/navy surfaces;
- restrained indigo-to-violet accent gradient;
- subtle borders rather than heavy glow everywhere;
- 10–14 px card radii;
- compact typography with clear hierarchy;
- monospaced treatment for hashes, IDs, versions and low-level runtime identifiers;
- charts and tables use the same state vocabulary as the rest of the product.

Suggested accent direction: `#4F8CFF -> #A342F4`. Exact production tokens require accessibility validation before implementation.

## Layout rules

- Persistent left navigation on desktop; collapsible rail at medium widths.
- Page title, object identity and global mode/freshness in the top region.
- Optional sticky right inspector for create/review/compare flows.
- Do not reserve a right rail when there is no actionable context.
- Prefer 2–4 meaningful panels per viewport over grids of tiny decorative cards.
- Dense tables for bots, runs, models and datasets; cards for summaries and decision explanations.

## Status vocabulary

Current product concepts should be shown explicitly:

- runtime/service: `HEALTHY`, `DEGRADED`, `STOPPED`, `UNKNOWN` (exact implementation vocabulary may differ; UI must map deterministically);
- model lifecycle: `BASELINE`, `CHALLENGER`, `ACTIVE`, `ARCHIVED`;
- data source: `REALTIME_PUBLIC`, `REPLAY`;
- runtime/storage location: `LOCAL`, `SYNOLOGY`.

Do not reintroduce `SHADOW`, `PAPER`, `LIVE` as current Portal modes. Legacy Freqtrade `dry_run: true` may exist behind adapters but is not a user-facing product mode.

## Forms

Long bot configuration must be wizard/section based. Requirements:

- clear completion state per step;
- inline validation plus global summary;
- explicit units next to all numeric fields;
- avoid placeholder-only labels;
- advanced values show defaults and provenance;
- review screen shows all derived risk/exposure values before creation;
- unsaved changes are obvious and recoverable.

## Decision Inspector

A decision is represented as a causal timeline:

1. market-data snapshot and freshness;
2. derived features;
3. model output, if a model participates;
4. strategy rule evaluation;
5. guard/risk decisions;
6. final `TRADE` or `NO_TRADE`;
7. simulated position/outcome when applicable.

Every stage should expose its identity/version so the user can reconstruct which code/model/dataset produced the decision.

## Accessibility and responsiveness

- Target WCAG AA contrast for normal text and controls.
- Keyboard navigation for primary workflows.
- Never encode success/failure only through green/red.
- Desktop is primary, but critical overview/alert/bot state must remain usable on tablet/mobile.
- Responsive layouts should collapse secondary panels rather than shrink data into illegibility.

## Explicit anti-patterns

Do not copy these aspects of the WickHunter references:

- huge decorative empty areas;
- low-contrast form text;
- one extremely long create-bot page;
- unrelated operational/profile/subscription concepts sharing equal visual priority;
- decorative glow obscuring information hierarchy;
- UI structure dictated by backend endpoints or Freqtrade internals.
