# FTAI-QUANT-PLATFORM-V2-GUI-BASELINE-PR1665-FINAL-CLOSEOUT-CONTINUE

Continue the existing Quant Platform v2 GUI baseline work in `blakinio/freqtrade` autonomously. Do not restart the design work and do not recreate already preserved documentation unless fresh repository evidence requires it.

## Source of truth

Resolve fresh before making changes:

- the protected base branch used by PR #1665;
- the current head of PR #1665;
- root `AGENTS.md`;
- `docs/agents/PROMPTING_STANDARD.md`;
- `docs/agents/PROMPTING_HANDOVER.md`;
- all binding ADRs referenced by the task, especially ADR-023 and ADR-025.

Do not assume SHAs in this handover are still current. At handover creation time PR #1665 was open against `develop`, with head branch `docs/quant-platform-v2-gui-baseline` and previously observed head `555210d4fc7f16bc628395070e6a2b7d89f502e1`.

## Goal

Finish the repository closeout for the clean-sheet Quant Platform v2 design baseline, repair the remaining asset/CI issue, obtain exact-head green CI, merge PR #1665 according to branch protection, and verify the merged state on the protected base branch.

## Preserved design baseline

The work already preserves the proposed Quant Platform v2 information architecture and UX baseline:

- Overview / Command Center;
- Trading: Bots, Create Bot, Positions, Orders, Markets, Alerts;
- Research: Strategies, Backtests, Replays, Experiments, Comparisons;
- ML / Models: Model Registry, Training Jobs, BASELINE, CHALLENGER, ACTIVE, Features, Datasets;
- AI Lab: Ollama, Research Agent, Experiment Analysis, Research History;
- Infrastructure: Runtime Nodes, Synology, Training PC, Workers, Market Data, Services;
- System: Logs, Alerts, Integrations, Settings, Audit.

UX direction is dark-premium and WickHunter-inspired but operator-first rather than a 1:1 copy: denser information, stronger contrast, left navigation, persistent contextual/right summary panel, explicit Operations / Research / Admin separation, Create Bot as a wizard, and a Decision Inspector showing `market -> features/model -> strategy -> decision -> simulated outcome`.

The clean-sheet architecture proposal remains:

- Rust core for market data, streaming, event processing, simulation/paper execution, bot runtime/supervision/state machines/recovery;
- Python for feature engineering, datasets, LightGBM/XGBoost/scikit-learn/PyTorch training, tuning, evaluation and research;
- Ollama/local LLM as a non-authoritative research/copilot layer;
- Next.js/TypeScript for the Portal UI;
- Freqtrade/FreqAI as transition/reference components rather than strategic product core.

## Safety and authority boundary

This task is documentation/design closeout only.

- Current product capability remains simulation-only.
- Do not add real-capital/live-exchange execution authority.
- Do not add private exchange credentials, withdrawals or capital authority.
- Future real execution must remain a separately governed Execution/Capital Gateway with explicit owner-approved authority.
- Do not treat this proposal as authority to supersede binding ADR-023 or ADR-025.

## Known blocker and corrected evidence state

Do not trust earlier checkpoint claims that the visual archive restore had already passed merely because they are written in the branch. During follow-up debugging the repository asset package and its manifest/parts were found to be inconsistent, and the earlier validation evidence must be reproduced from the current Git contents before it can be called PASS.

The intended canonical visual package was recorded as:

- archive size: `363551` bytes;
- ZIP members: `33`;
- intended SHA-256: `8c6ede71a275b2c3063ea8dcc6bcea94aaa854a9433f6fee0d56b449747367a9`.

Treat these as an expected target, not proof. Reconstruct from the current repository contents and establish the truth from fresh evidence. If a newer legitimate source-of-truth intentionally differs, document why and establish a new truthful manifest instead of forcing the old hash.

The previously observed exact-head CI had a failing gate caused by `Pre-commit checks`; other relevant documentation/component/security routing checks were largely green or correctly skipped. Re-resolve all current check runs because CI may have changed since handover creation.

## Required execution sequence

1. **Fresh resolution**
   - resolve current protected base branch and SHA;
   - resolve current PR #1665 state, base, head SHA, mergeability, reviews and protection requirements;
   - resolve all current exact-head checks.

2. **Systematic debugging**
   - inspect the full failing `Pre-commit checks` log/annotations;
   - identify the exact hook and exact files;
   - reproduce the failure minimally;
   - fix the root cause only, without speculative edits.

3. **Asset integrity**
   - audit `ASSET_MANIFEST.json`, restore tooling and all archive parts actually present on the PR head;
   - verify ordering, completeness, Base64 validity and EOF/pre-commit compatibility;
   - reconstruct the ZIP using only repository data;
   - verify archive size, SHA-256, ZIP integrity and member count;
   - do not write PASS into the checkpoint until fresh commands prove it.

4. **Pre-commit compatibility**
   - run the repository pre-commit suite;
   - fix EOF, trailing-whitespace, formatting or other hooks actually reported;
   - ensure any EOF fix does not corrupt Base64 restore semantics;
   - if the restore script accepts whitespace between chunks, it must still strictly validate the actual Base64 payload.

5. **Documentation validation**
   - verify Markdown and relative links;
   - verify the asset index/README distinguishes `REFERENCE ASSETS` from `PROPOSED V2 MOCKUPS`;
   - verify privacy-redacted reference captures remain the only committed authenticated WickHunter references.

6. **Durable handover/checkpoint**
   - update `docs/agents/tasks/FTAI-20260826-quant-platform-v2-gui-baseline.md` with fresh evidence;
   - record branch/head/PR/risk/validation/blockers;
   - keep exactly one `next_action`.

7. **Exact-head CI**
   - push the minimal fix;
   - resolve the new PR head SHA;
   - require CI for that exact SHA;
   - repair every real required blocker without bypassing governance.

8. **Merge**
   - only when required checks/reviews/protection are terminal and acceptable, merge PR #1665 using the repository's permitted merge method;
   - do not bypass protection rules.

9. **Post-merge verification**
   - resolve fresh protected base SHA after merge;
   - confirm the design baseline, manifest, restore tooling and assets exist in merged state;
   - rerun the archive reconstruction/hash/ZIP-member verification from the merged tree;
   - verify post-merge CI if the repository triggers it.

10. **Terminal closeout**
    - stop only after merge and post-merge verification, or when a genuine external blocker prevents safe completion;
    - if blocked, report the exact external blocker and leave one `next_action`.

## Final report contract

The final report must include:

- protected base branch and starting SHA;
- final PR head SHA;
- exact root cause;
- exact fix;
- changed files;
- asset reconstruction result;
- ZIP size;
- ZIP SHA-256;
- ZIP member count and integrity result;
- pre-commit result;
- exact-head CI result;
- PR #1665 final state;
- merge SHA;
- post-merge base SHA;
- post-merge verification evidence;
- remaining risks/blockers, or explicitly `No remaining blockers`.

## Operational constraints

Prefer GitHub, GitHub Actions/runners and standard repository tooling. Do not use Remote Desktop for routine repository/CI work. Do not mark the task DONE before `exact-head CI PASS -> merge -> post-merge verification` is actually proven.
