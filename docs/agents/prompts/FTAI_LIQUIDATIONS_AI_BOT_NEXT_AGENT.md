# Liquidations AI Bot — Next Agent Prompt

Copy the prompt below into a new agent session.

```text
Continue the Liquid20 liquidation-aware AI bot program from the current repository state in `blakinio/freqtrade`.

Do not rely on previous chat history. The current repository, Git state, open pull requests, GitHub Actions, immutable Liquid20 evidence, task checkpoints and deployment evidence are the source of truth.

Primary goal

Start the next legal bounded package: LQ-02 accepted dataset selection preflight and contract. Do not start replay, strategy tuning, AI training, order submission, DCA, leverage or live capital before the required data gate is proven.

Required reads

- AGENTS.md
- docs/agents/CONTEXT_HANDOFF.md
- docs/ai_platform/ARCHITECTURE.md
- docs/ai_platform/ROADMAP.md
- docs/ai_platform/LIQUIDATION_REVERSAL_RESEARCH.md
- docs/ai_platform/LIQUIDATION_DATA_ONLY_STAGING.md
- docs/ai_platform/LIQUIDATION_MULTI_SOURCE.md
- docs/ai_platform/portal/LIQUIDATIONS_AND_AI_BOT_ARCHITECTURE.md
- docs/ai_platform/portal/LIQUIDATIONS_AI_BOT_IMPLEMENTATION_BLUEPRINT.md
- docs/ai_platform/portal/liquidations-ai-bot-architecture-v1.json
- docs/ai_platform/portal/liquidations-ai-bot-artifact-contracts-v1.json
- docs/agents/tasks/FTAI-20260726-liquidations-ai-bot-agent-package.md

Existing foundations to verify, not assume

- canonical `LiquidationEvent` and source-specific deterministic identity;
- conservative `received_at_ms` decision-availability rule;
- completed-candle alignment helper;
- pure counter-trade signal-policy foundation;
- Bybit and Binance source adapters with different feed semantics;
- fixed `liquid20-v1` symbol universe;
- frozen data-only and multi-source acceptance policies;
- Synology Liquid20 collector deployment;
- read-only portal read-model, BFF, UI and Synology mount;
- `research_preview=true` and `trading_authorized=false`.

Mandatory live-state preflight

1. Read root AGENTS.md and the active task checkpoint first.
2. Inspect current `develop` HEAD, branch, open PRs, path ownership and required checks.
3. Verify the current Synology collector image/container, running state, data root, newest run IDs and storage state.
4. Inspect every relevant completed multi-source acceptance report. Performance research is allowed only when the selected report explicitly contains `passed: true`.
5. Verify source NDJSON, summaries, manifests and acceptance-report hashes without mutating evidence.
6. Locate the intended versioned candle source and prove its files, time coverage, timeframe, pair mapping and hashes. If no adequate candle evidence exists, record that as the first blocker.
7. Verify protected-holdout constraints and whether any requested interval has already been used for tuning or diagnosis.
8. Inspect existing code and tests before declaring new paths.

Task declaration

Create a dated task record and dedicated feature branch for only LQ-02. Own the smallest necessary paths, expected to be under:

- ai_platform/research/liquidations/datasets/
- ai_platform/scripts/liquidation_dataset_selector.py
- tests/ai_platform_integration/test_liquidation_dataset_selection.py
- one immutable dataset-selection evidence path
- the new task record

Do not own replay, strategy, models, execution, portal UI, credentials or deployment paths unless live repository evidence proves an unavoidable dependency and it is explicitly documented.

Required contract

Implement or durably specify a `DatasetSelectionManifest` compatible with:

- docs/ai_platform/portal/liquidations-ai-bot-artifact-contracts-v1.json
- docs/ai_platform/portal/examples/liquidations-dataset-selection-v1.example.json

The manifest must include exact run IDs, logical source files, SHA-256 hashes, record counts, collector/parser/catalog/universe identities, final acceptance status, accepted and quarantined intervals, candle artifact identities and hashes, protected-holdout result, purpose classification and `performance_research_authorized`.

Non-negotiable rules

- A run is accepted only when its own final report explicitly contains `passed: true`.
- Failed or incomplete evidence may be diagnostic-only but cannot authorize performance research.
- Preserve Bybit and Binance source identity; do not deduplicate across exchanges.
- Decisions cannot precede `received_at_ms`.
- Do not use final values from a containing candle without exact intrabar evidence.
- Missing, stale or unavailable data never becomes zero or healthy implicitly.
- Do not mutate completed Liquid20 evidence.
- Do not expose evidence paths, collector endpoints, Freqtrade, Docker or credentials to the browser.
- AI is optional and has no execution authority.
- New trading configurations remain `dry_run: true`.
- No DCA, leverage optimization, withdrawals or live capital.

Required tests

At minimum cover:

- valid accepted selection;
- explicit rejection when final `passed: true` is absent;
- diagnostic-only selection for failed evidence;
- deterministic hashing and repeated output;
- changed-file/hash detection;
- missing required source file;
- source mismatch;
- interval acceptance/quarantine boundaries;
- candle coverage and hash validation;
- protected-holdout rejection;
- no evidence mutation;
- malformed manifest/input failure.

Validation and delivery

- Run the narrowest deterministic tests first.
- Validate the task checkpoint with `python tools/agents/checkpoint.py <task-path> --require-checkpoint`.
- Run applicable pre-commit and repository CI.
- Open a PR against `develop`.
- Require exact-current-head CI before merge.
- Preserve negative or blocked results.
- Update the task checkpoint after every material discovery, commit, PR or CI state change.
- Leave exactly one concrete `next_action`.
- Generate the continuation prompt with `python tools/agents/resume.py --task <task-path>`.

Stop condition

If no completed Liquid20 run explicitly passes the frozen acceptance policy, or no valid versioned candle evidence exists, do not improvise and do not start replay. Record the exact missing evidence, hashes/run IDs checked, the first failing gate and the smallest owner/operator action required to unblock LQ-02.
```
