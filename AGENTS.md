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

### Integration, release and environment policy

ADR-021 and `docs/agents/BRANCH_POLICY.md` define repository routing. Source branches, deployment environments and bot operating modes are separate control dimensions.

- `develop` is the controlled integration branch and upstream-sync convergence point.
- `main` is the accepted target release branch, but it becomes operational release authority only after the staged migration, protection and CI gates in ADR-021 are proven by exact repository evidence.
- Ordinary task, feature, fix, audit, documentation, migration, runtime, portal, WickHunter, CI and infrastructure work integrates through `develop`.
- After the physical `main` migration is complete, stable release promotion uses a dedicated reviewed `develop -> main` PR; ordinary feature PRs do not target `main`.
- `develop` is not the staging environment and `main` is not the production environment. `dev | staging | production` are deployment environments.
- `SHADOW | PAPER | LIVE` are bot operating modes. Production does not imply LIVE, and LIVE still requires a separate explicit live-capital work package.
- `candidate | stable` are release channels. Deployment uses immutable artifact identity; merging a branch does not itself authorize deployment.
- Until exact repository state proves `main` is created, protected and correctly wired, do not route work to it or claim the two-branch migration is implemented.

1. Read this file first.
2. Read `docs/ai_platform/ARCHITECTURE.md` and `docs/ai_platform/ROADMAP.md` for AI-platform work.
3. For AI Trading Portal/control-plane work, also read `docs/ai_platform/portal/README.md` and the task-relevant documents under `docs/ai_platform/portal/`; use `docs/agents/programs/FTAI_AI_TRADING_PORTAL_PROGRAM.md` as the program boundary.
4. Inspect current branch, HEAD, open PRs, and relevant CI before editing.
5. Work on a dedicated feature branch.
6. Keep commits focused and reviewable.
7. Run the narrowest relevant validation first, then broader tests if needed.
8. Target ordinary repository PRs to `develop`; use `main` only for the dedicated stable release-promotion path after its physical migration is proven complete.
9. Record important architecture or workflow changes in repository documentation.

## Runtime and CI target

- The deployment target for this fork is Linux containers, primarily Docker on Synology or another Linux host.
- Freqtrade and portal build, test, packaging, and deployment workflows must use Linux runners only.
- Do not add or retain native Windows or macOS compilation/test jobs unless the repository owner explicitly authorizes a separate portability work package.
- Keep Linux architecture coverage relevant to deployed containers, including AMD64 and ARM64 where supported by available runners and dependencies.
- Docker is the delivery mechanism; the container runtime remains Linux-based.

## Portal/control-plane safety boundary

- Treat Freqtrade as a private execution engine behind an internal adapter; do not expose its control API or WebSocket directly to the public Internet or browser clients.
- Portal, research, training, execution, and autonomous-validation concerns must remain separated by explicit contracts and credentials.
- AI/post-trade analysis may create evidence, insights, experiments, and model candidates; it must not directly mutate a running production model or bypass deterministic risk controls.
- Autonomous repair agents may prepare regression tests, isolated branches, fixes, and PRs; they may not patch production or bypass CI/promotion gates.
- Cloudflare/Zero Trust may protect ingress and privileged surfaces, but application RBAC, tenant isolation, secret handling, and private Freqtrade networking remain mandatory defense layers.
- Portal implementation must not alter frozen Phase 5 thresholds, consume the protected final holdout iteratively, reopen completed Phase 6, or reinterpret PyTorch/RL evidence as promotion authorization.

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

## GitHub connector routing — mandatory

- For GitHub repository, pull request, issue, review, and remote-file tasks, inspect and use the connected GitHub plugin or connector before falling back to local `git` or `gh`.
- Treat an explicit `@GitHub` selection as a request to use the connected GitHub plugin.
- Local `git` may be used for checkout, worktree, diff, branch, and commit operations. Use `gh` only for operations the connector does not support or when repository policy explicitly requires it.
- A missing local checkout, missing `gh` binary, or unauthenticated local `gh` session is not evidence that the GitHub connector is unavailable.

Before claiming that GitHub access is unavailable:

1. Inspect the available GitHub connector tools.
2. Call `github_get_user_login` or the equivalent authenticated-identity operation.
3. Call `github_get_repo` or `github_list_repositories` for the requested repository scope.
4. Attempt the required read operation through the connector when it is safe to do so.

Report a GitHub access blocker only after an actual connector call returns an authentication or permission error. Include the exact failed operation and error.
