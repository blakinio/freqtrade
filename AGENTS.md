# AGENTS.md

## Owner-funded AI and credential budget — highest priority

- Agents MUST NOT invoke Codex, OpenAI API, paid/limited AI review services, or any other mechanism that consumes the repository owner's personal AI quota, credits, tokens, subscription limits, or metered allowance unless the owner gives explicit permission for that specific use.
- Agents MUST NOT use, export, copy, inspect, forward, or authenticate with owner-supplied API keys, access tokens, session tokens, personal credentials, or secrets for AI/model services unless the owner explicitly authorizes that exact credential/service use.
- Availability of a credential, environment variable, CLI login, browser session, connector, MCP/plugin, or previously granted access does NOT constitute permission to consume owner-funded AI resources.
- Prior permission is not standing permission. Authorization must be explicit for the current task/use; if scope, provider, model, or expected consumption materially changes, ask again.
- If a workflow, policy, review gate, script, or tool would normally invoke Codex or another owner-funded AI service, skip that invocation and use a non-owner-funded alternative when one is genuinely available. If the requirement cannot be satisfied without such use, stop and report the exact blocker instead of consuming quota.
- Never weaken, bypass, or falsely mark a review/validation gate as satisfied merely because owner-funded AI use is forbidden.

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
- New trading configurations must default to `dry_run: true`; in Quant Platform terminology, a managed Freqtrade dry-run generation is `PAPER` unless a bounded validation package explicitly selects `SHADOW`.
- `PAPER` is the normal and only currently authorized operational trading mode.
- `SHADOW` is optional and temporary. Use it only when research, training, diagnostics, runtime/integration validation, or replay-to-runtime comparison specifically requires observation without simulated order submission.
- `LIVE` must remain unavailable and fail closed in UI, API, configuration generation, runtime materialization, and promotion logic until the owner explicitly approves a separate LIVE architecture and implementation programme.
- No merge, release, deployment, model promotion, strategy promotion, or environment change may implicitly enable `LIVE`.
- Do not enable withdrawals in exchange API credentials.
- Any future live-capital change requires an explicit, separately reviewed owner-approved work package and does not inherit authority from PAPER work.

### Container lifecycle hygiene

- Any temporary container or other Docker resource created by an agent or task must be uniquely attributable to that task through a deterministic name and/or ownership labels.
- The task that creates a temporary Docker resource owns its cleanup. Remove task-owned temporary Docker resources as soon as they are no longer required, including failure and cancellation paths when automation supports unconditional cleanup such as `if: always()` or shell traps.
- One-shot cleanup automation must itself be lifecycle-bounded. A temporary cleanup workflow or script committed solely for an operational cleanup must be constrained to a single authorized invocation and removed or disabled immediately after use; never leave destructive cleanup on a general push or recurring trigger.
- Cleanup must be bounded to resources either proven to be owned by the current task or explicitly covered by the current task's cleanup scope with exact identity and obsolescence evidence. Never use broad destructive cleanup such as `docker system prune`, `docker container prune`, or equivalent host-wide pruning on shared Synology, CI, staging, or production hosts.
- Do not remove persistent/shared deployment containers, databases, runners, portal/control-plane services, bot runtimes, evidence stores, volumes, images, or networks merely because they are stopped or old. Removal requires explicit task scope plus evidence that the exact resource is obsolete.
- If ownership or continued use is uncertain, leave the resource in place and record it as unresolved instead of deleting it.
- Docker-resource cleanup must not implicitly remove persistent data. Do not use volume-removing flags or delete volumes containing persistent/evidence state unless persistent-data deletion is explicitly authorized and separately verified.
- Before cleanup, capture the applicable health signals for protected/current services. After cleanup, verify that every intended authorized resource is gone and that protected/current services did not degrade relative to that baseline; record pre-existing stopped or unhealthy states rather than requiring unrelated cleanup to repair them. Use declared Docker health checks and/or service-level probes where available, because process `running` state alone is not sufficient when a stronger health signal exists. Record exact resource names/IDs and the pre/post health evidence in the task closeout.

### GitHub Actions CI hygiene

- A task owns the temporary GitHub Actions resources it creates: diagnostic/request workflows, request files, short-lived CI branches, request-only PRs, task-specific caches, and non-durable artifacts. Close or remove them at terminal task closeout unless an explicit evidence requirement requires retention.
- Temporary or diagnostic workflow files must be single-purpose and lifecycle-bounded. Remove them from the final delivery as soon as their terminal evidence is captured; never leave a one-shot diagnostic or destructive workflow active on a general push, pull-request, schedule, or recurring trigger.
- Request-only CI/deployment PRs must be closed without merge after their workflow reaches a terminal result when their contract says they are non-mergeable. Delete their short-lived branch after closeout unless a documented evidence dependency requires the ref to remain. Ordinary merged task branches should rely on repository auto-delete and verify the branch is actually gone.
- Do not upload an Actions artifact when the same bounded evidence is already sufficient in the job summary or logs. Every new or materially modified `actions/upload-artifact` use must set an explicit `retention-days` appropriate to the evidence class; prefer 1 day for disposable diagnostics, 7 days for routine CI evidence, and at most 14 days for acceptance/audit evidence unless a documented requirement justifies longer retention.
- GitHub Actions artifacts are not the long-term system of record. Evidence that must outlive its Actions retention must be promoted before expiry to a durable repository record or approved durable evidence store with exact run/artifact identity and digest. Do not extend artifact retention merely to avoid durable publication.
- Treat Actions caches as disposable performance data, never as acceptance evidence. Cache keys must be bounded in cardinality and based on reusable dependency/toolchain inputs; do not add run IDs, timestamps, or commit SHAs to cache keys unless a specific isolation requirement is documented. A temporary workflow that creates a dedicated cache family owns deletion of that cache family at closeout when the GitHub capability is available.
- When performing CI hygiene, delete caches only when they are safely reconstructible and their scope is proven obsolete, such as caches bound to closed PR refs, deleted branches, or an explicitly retired temporary cache family. Do not broadly delete active default-branch caches merely to reduce storage without measuring the CI-performance impact.
- Do not delete workflow runs, logs, artifacts, branches, PRs, or refs that are cited as the only surviving acceptance, audit, deployment, security, rollback, or incident evidence. Preserve the evidence or first promote the required facts and digests to durable storage.
- Before adding a new artifact or cache family, inspect existing CI storage/cardinality when the task materially affects Actions storage. Prefer reusing a stable cache family and bounded artifact set over creating per-run or per-SHA families that grow without bound.
- At closeout, verify GitHub CI hygiene: temporary workflows/request files removed, request-only PRs terminal, disposable branches deleted, task-specific caches/artifacts either deleted or covered by explicit bounded retention, and durable evidence promoted when required. Record any cleanup blocked by GitHub permissions/API capability instead of silently leaking resources.

## Strategy lifecycle

Strategies use the PAPER-first lifecycle:

`experiment -> candidate -> validated -> paper-eligible -> paper -> paper-suspended | retired`

An optional validation side lane may be used when specifically required:

`candidate | validated -> shadow-validation -> validated`

`SHADOW` is not a mandatory promotion stage. There is no reachable `LIVE` transition in the currently authorized lifecycle.

Promotion requires evidence appropriate to the stage. At minimum, before `paper-eligible` promotion:

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
- `SHADOW | PAPER | LIVE` are bot-mode vocabulary under ADR-021/ADR-022. `PAPER` is the default and only currently authorized operational mode, `SHADOW` is optional validation-only, and `LIVE` is reserved but unreachable until a separate explicit owner decision and programme.
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

The first baseline lives under `ai_platform/` and is intentionally research-only. It may use bounded `SHADOW` validation when technically necessary, but it must not become `PAPER_ELIGIBLE` or run as a managed PAPER generation until the validation pipeline defined in the roadmap is implemented and passed. It has no reachable LIVE path.

## GitHub connector routing — mandatory

- For GitHub repository, pull request, issue, review, and remote-file tasks, inspect and use the connected GitHub plugin or connector before falling back to local `git` or `gh`.
- Treat an explicit `@GitHub` selection as a request to use the connected GitHub plugin.
- Local `git` may be used for checkout, worktree, diff, branch, and commit operations. Use `gh` only for operations the connector does not support or when repository policy explicitly requires it.
- A missing local checkout, missing `gh` binary, or unauthenticated local `gh` session is not evidence that the GitHub connector is unavailable.

Before claiming that GitHub access is unavailable:

1. Inspect the available GitHub connector tools and determine whether the connector is registered and enabled and whether the required operations exist.
2. If an authenticated-identity operation exists and the connector is callable, call `github_get_user_login` or its equivalent; otherwise record the confirmed missing or disabled connector or missing identity operation.
3. If a repository lookup or listing operation exists and the connector is callable, call `github_get_repo` or `github_list_repositories` for the requested repository scope; otherwise record the missing capability.
4. If the required read operation exists and is callable, attempt it through the connector when it is safe and within the task's authority; otherwise record the unavailable capability.

Report a GitHub access blocker only after the applicable availability and capability checks above and, when an applicable operation exists and is safe to attempt, an actual connector call. Authentication or permission errors, a confirmed missing or disabled connector, a missing required operation, rate limiting, and transport or service failures are valid blockers when they prevent the task and no safe permitted connector, local `git`, or `gh` fallback can complete it. Include the exact availability and capability verification performed. When a call was attempted, include the failed operation and returned error; when no call was possible, identify the missing or disabled connector or unavailable operation instead.
