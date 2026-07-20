# AGENTS.md

## Purpose

This fork extends upstream Freqtrade with an AI-assisted strategy research and validation platform.

The repository, current Git state, active pull requests, CI results, and files in this repository are the source of truth. Do not rely on chat history when repository state can be checked directly.

## Global context efficiency baseline

- Work autonomously until the bounded task is complete or a real blocker/required decision is reached.
- Do not narrate routine file reads, searches, tool calls, commands, or unchanged checks.
- Send user-facing progress only for a material milestone, blocker, required decision, or material scope/risk change; keep each update to at most three short sentences.
- Run the full repository/task preflight once per bounded task or continuation session. Afterwards verify only state that may have changed and can invalidate the next action.
- Repeat the full preflight only after a material external repository-state change, a long interruption/session replacement, or evidence that durable task state conflicts with live state.
- Search before reading large indexes or documents in full and load only task-relevant documentation/source evidence.
- Do not paste full logs, diffs, artifacts, or whole source files when exact identifiers and focused excerpts are sufficient.
- Treat chat history as disposable. Keep durable task/handoff state compact and leave exactly one concrete next action when handing work off.
- When the next action is safe and autonomous, continue without waiting for acknowledgement.

## Durable continuation

- For substantial work, use `docs/agents/CONTEXT_HANDOFF.md` and maintain one compact `## Context checkpoint` in the task record.
- Validate it with `python tools/agents/checkpoint.py <task-path> --require-checkpoint`.
- Generate the next-agent prompt with `python tools/agents/resume.py --task <task-path>`.
- Resume from Git, the checkpoint and live PR/CI state; never require the previous chat transcript.

## Upstream boundary

- Treat `freqtrade/`, upstream tests, and upstream documentation as vendor/core code.
- Prefer adding project-specific code under `ai_platform/` and project-specific documentation under `docs/ai_platform/`.
- Modify upstream core only when the required capability cannot be implemented through supported Freqtrade extension points.
- Keep changes easy to rebase or merge from `freqtrade/freqtrade`.

## Safety rules

- Never commit exchange API keys, secrets, tokens, wallet credentials, or private endpoints.
- New trading configurations must default to `dry_run: true`.
- Do not enable withdrawals in exchange API credentials.
- Do not promote an experimental strategy directly to live trading.
- Any live-capital change requires an explicit, separately reviewed work package.

## Strategy lifecycle

Strategies move through these states:

`experiment -> candidate -> validated -> dry-run -> shadow -> live-small -> production -> retired`

Promotion requires evidence appropriate to the stage. At minimum, before dry-run promotion:

- reproducible backtest inputs;
- out-of-sample evaluation;
- walk-forward evaluation;
- lookahead-analysis pass;
- recursive-analysis review;
- acceptable drawdown and minimum trade count;
- documented model/config identifiers.

## Development workflow

1. Read this file first.
2. Read `docs/ai_platform/ARCHITECTURE.md` and `docs/ai_platform/ROADMAP.md` for AI-platform work.
3. Inspect current branch, HEAD, open PRs, and relevant CI before editing.
4. Work on a dedicated feature branch.
5. Keep commits focused and reviewable.
6. Run the narrowest relevant validation first, then broader tests if needed.
7. Open a PR against `develop` unless the repository state explicitly indicates another base.
8. Record important architecture or workflow changes in repository documentation.

## Validation expectations

For Python changes:

- syntax/compile validation;
- Ruff on changed project Python files where applicable;
- targeted tests where test coverage exists.

For strategy changes:

- strategy import/listing validation;
- FreqAI configuration validation;
- backtesting on a declared timerange;
- lookahead-analysis;
- recursive-analysis;
- walk-forward/out-of-sample evaluation before promotion.

A successful backtest alone is not sufficient evidence of a robust strategy.

## AI/ML principles

- FreqAI is the prediction/model lifecycle layer, not an unrestricted execution authority.
- Execution remains behind deterministic strategy and risk rules.
- Prefer a simple baseline model before adding deep learning or reinforcement learning.
- Compare models on out-of-sample trading metrics, not only training metrics.
- Avoid feature explosion and data leakage.
- Version strategy code, FreqAI `identifier`, features, targets, training windows, and evaluation results together.

## Initial baseline

The first baseline lives under `ai_platform/` and is intentionally research-only. It must remain `dry_run` until the validation pipeline defined in the roadmap is implemented and passed.
