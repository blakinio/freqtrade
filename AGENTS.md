# AGENTS.md

## Owner-funded AI and credential budget — highest priority

- Agents MUST NOT invoke Codex, OpenAI API, paid/limited AI review services, or any other mechanism that consumes the repository owner's personal AI quota, credits, tokens, subscription limits, or metered allowance unless the owner gives explicit permission for that specific use.
- Agents MUST NOT use, export, copy, inspect, forward, or authenticate with owner-supplied API keys, access tokens, session tokens, personal credentials, or secrets for AI/model services unless the owner explicitly authorizes that exact credential/service use.
- Availability of a credential, environment variable, CLI login, browser session, connector, MCP/plugin, or previously granted access does NOT constitute permission to consume owner-funded AI resources.
- Prior permission is not standing permission. Authorization must be explicit for the current task/use; if scope, provider, model, or expected consumption materially changes, ask again.
- If a workflow, policy, review gate, script, or tool would normally invoke Codex or another owner-funded AI service, skip that invocation and use a non-owner-funded alternative when one is genuinely available. If the requirement cannot be satisfied without such use, stop and report the exact blocker instead of consuming quota.
- Never weaken, bypass, or falsely mark a review/validation gate as satisfied merely because owner-funded AI use is forbidden.


## Central Spark PR pre-review — standing owner authorization

- The owner explicitly authorizes the central controller in `blakinio/github-projects-control` to perform recurring advisory PR pre-review for this repository using exactly `gpt-5.3-codex-spark` through ChatGPT-managed Codex authentication on its trusted private runner. This is a standing, bounded repository-automation exception to the owner-funded AI restriction above; it does **not** authorize repository agents to invoke Codex, OpenAI API, hosted Code Review, or any other AI service themselves.
- The central controller may inspect only bounded PR metadata/diff text and may post only concrete P0/P1 findings. A clean Spark pass is intentionally silent. Target PR code is not checked out or executed by the Spark runner.
- Keep a PR Draft while implementation is still in progress. Mark it Ready only when this repository's normal readiness rules already permit that transition. The controller considers only eligible ready, internal, non-bot, exact-head, green-CI, bounded changes.
- Do not automatically request `@codex review`, enable hosted Codex Automatic Reviews, invoke Codex CLI, use `OPENAI_API_KEY`, or select another model/provider as a fallback. Any such direct AI use still requires separate explicit owner authorization for the current task/use.
- Spark pre-review is advisory and does not replace self-review, required independent review, required checks, E2E/runtime evidence, branch protection, or any merge gate. Never infer that Spark ran or passed merely because no comment appeared. Do not delay or weaken a repository merge gate solely to manufacture Spark evidence.
- If the central controller posts a P0/P1 finding before merge, treat it as an unresolved material review finding: address or explicitly disposition it under the repository's normal review rules, then rerun any validation invalidated by the resulting change.
- `no-spark-review` opts a PR out of the central controller. `spark-review` may force consideration of an otherwise ignored path class, but it never bypasses draft, fork, bot, CI, exact-head, size, model, or safety fences.

## Purpose

This fork extends upstream Freqtrade with an AI-assisted strategy research and validation platform. The current Portal and WickHunter product are governed by ADR-023 as a private, single-owner Developer Quant Platform working on real public market data, simulation, datasets and local model development, with ADR-024 as the binding runtime/deployment topology overlay.

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

## Current Portal product authority — ADR-023 + ADR-024 runtime overlay

ADR-023 owner decision date: `2026-08-15`.  
ADR-024 runtime-topology decision date: `2026-08-18`.

These rules apply to the entire current Portal, including WickHunter integration, Liquid20/market-data consumption, simulation, datasets, model training/challengers, runtime lifecycle, deployment/operations, CI/E2E and Portal-facing observability.

- The current Portal is a private, single-owner developer/quant/research platform, not a multi-tenant production trading control plane.
- Current data-source vocabulary is `REALTIME_PUBLIC | REPLAY`.
- Current target runtime-location vocabulary is `LOCAL | DEDICATED_LINUX`; current storage-provider vocabulary is `LOCAL | SYNOLOGY`. Existing Synology-hosted application services are transitional implementation state until individually migrated and proven.
- Simulated positions, fees, slippage, PnL and outcomes are normal developer-platform capabilities; they do not constitute a separate trading-authority mode.
- Current model lifecycle is `BASELINE | CHALLENGER | ACTIVE | ARCHIVED`. Training may create challengers; activation remains deliberate and attributable.
- `SHADOW`, `PAPER`, `LIVE`, `PAPER_ELIGIBLE` and similar mode vocabulary may remain only in historical evidence, legacy compatibility schemas or migration code. Do not introduce or require them as current Portal product states.
- When legacy Freqtrade compatibility requires an executable configuration, it MUST remain `dry_run: true`; this is a technical simulation safeguard, not a Portal product-mode ceremony.
- Real-money exchange execution, private trading credentials for order submission, withdrawals and capital authority are outside the current Portal product. If ever requested, they require a separate owner-approved Execution/Capital Gateway architecture and implementation programme.
- `quant.molehill.cloud` is the persistent Developer Quant Portal endpoint. Historical use of `production` for that host or Synology deployment does not turn the current product into a real-money production trading system.
- Existing RuntimeGeneration, Runtime Supervisor, Gateway, risk, evidence and isolation components may be reused where they solve a concrete current problem. They are not universal completion prerequisites unless the current workflow actually needs them.
- Open Portal/WickHunter work created under the superseded PAPER-first or production-like target must be reclassified `KEEP_NOW | SIMPLIFY | DEFER | OBSOLETE` before further mode-driven implementation.

Current Portal completion is user-workflow based:

`real public data -> bot/model decisions including NO_TRADE -> simulated positions/outcomes -> durable dataset growth -> local challenger training -> active/challenger comparison -> deliberate owner activation -> restart-safe continued observation`

## Safety rules

- Never commit exchange API keys, secrets, tokens, wallet credentials, private endpoints or browser-readable secret material.
- Current Portal data acquisition uses public market-data interfaces. Do not add private/account/order endpoints merely to satisfy a former trading-mode contract.
- No current Portal code may submit a real exchange order, enable withdrawals, allocate live capital or silently activate private trading credentials.
- No merge, release, deployment, model activation, strategy activation or environment change may introduce real-money execution authority.
- Keep authentication, same-origin browser boundaries, secret exclusion, bounded input handling, durable state, restart recovery and proportionate container/process hardening.
- Do not add broad privileged/container-engine access when a narrower boundary suffices. Existing Supervisor/Gateway isolation may be retained when materially useful.
- Historical research integrity remains protected: no Portal migration may rewrite frozen evidence, use protected holdout iteratively or convert past evidence into a stronger claim than it originally supported.

### Container lifecycle hygiene

- Any temporary container or other Docker resource created by an agent or task must be uniquely attributable to that task through a deterministic name and/or ownership labels.
- The task that creates a temporary Docker resource owns its cleanup. Remove task-owned temporary Docker resources as soon as they are no longer required, including failure and cancellation paths when automation supports unconditional cleanup such as `if: always()` or shell traps.
- One-shot cleanup automation must itself be lifecycle-bounded. A temporary cleanup workflow or script committed solely for an operational cleanup must be constrained to a single authorized invocation and removed or disabled immediately after use; never leave destructive cleanup on a general push or recurring trigger.
- Cleanup must be bounded to resources either proven to be owned by the current task or explicitly covered by the current task's cleanup scope with exact identity and obsolescence evidence. Never use broad destructive cleanup such as `docker system prune`, `docker container prune`, or equivalent host-wide pruning on shared Synology or CI hosts.
- Do not remove persistent/shared deployment containers, databases, runners, portal services, bot runtimes, datasets, evidence stores, volumes, images, or networks merely because they are stopped or old. Removal requires explicit task scope plus evidence that the exact resource is obsolete.
- If ownership or continued use is uncertain, leave the resource in place and record it as unresolved instead of deleting it.
- Docker-resource cleanup must not implicitly remove persistent data. Do not use volume-removing flags or delete volumes containing persistent/evidence state unless persistent-data deletion is explicitly authorized and separately verified.
- Before cleanup, capture the applicable health signals for protected/current services. After cleanup, verify that every intended authorized resource is gone and that current services did not degrade relative to that baseline.

### GitHub Actions CI hygiene

- A task owns the temporary GitHub Actions resources it creates: diagnostic/request workflows, request files, short-lived CI branches, request-only PRs, task-specific caches, and non-durable artifacts. Close or remove them at terminal task closeout unless an explicit evidence requirement requires retention.
- Temporary or diagnostic workflow files must be single-purpose and lifecycle-bounded. Remove them from the final delivery as soon as their terminal evidence is captured; never leave a one-shot diagnostic or destructive workflow active on a general push, pull-request, schedule, or recurring trigger.
- Request-only CI/deployment PRs must be closed without merge after their workflow reaches a terminal result when their contract says they are non-mergeable. Delete their short-lived branch after closeout unless a documented evidence dependency requires the ref to remain.
- Do not upload an Actions artifact when the same bounded evidence is already sufficient in the job summary or logs. Every new or materially modified `actions/upload-artifact` use must set an explicit `retention-days` appropriate to the evidence class.
- GitHub Actions artifacts are not the long-term system of record. Evidence that must outlive its Actions retention must be promoted before expiry to a durable repository record or approved durable evidence store with exact run/artifact identity and digest.
- Treat Actions caches as disposable performance data, never as acceptance evidence.
- Do not delete workflow runs, logs, artifacts, branches, PRs, or refs that are cited as the only surviving acceptance, audit, deployment, security, rollback, or incident evidence.
- At closeout, verify GitHub CI hygiene: temporary workflows/request files removed, request-only PRs terminal, disposable branches deleted, task-specific caches/artifacts either deleted or covered by explicit bounded retention, and durable evidence promoted when required.

## Model and strategy lifecycle

For the current Developer Quant Portal:

`experiment -> baseline | challenger -> active | archived`

- Training/retraining may create a `CHALLENGER` automatically when its dataset, feature schema, model parameters and code identity are recorded.
- Training MUST NOT silently replace the `ACTIVE` model. Activation is a deliberate owner action and must remain attributable/reversible.
- `ACTIVE` means active for the current developer inference/simulation workflow; it grants no real-money execution authority.
- Compare candidates on out-of-sample/replay and accumulated realtime-public evidence appropriate to the strategy/model. Avoid leakage and repeated tuning on a protected holdout.
- A successful backtest alone is not sufficient evidence of a robust model or strategy.

## Development workflow

### Integration, release and environment policy

ADR-021 and `docs/agents/BRANCH_POLICY.md` may continue to define repository integration/release routing where independently applicable. ADR-023 supersedes ADR-021/ADR-022 bot-mode semantics for the current Portal; ADR-024 supersedes conflicting Synology-as-target-runtime guidance.

- `develop` is the controlled integration branch and upstream-sync convergence point.
- `main` is only a target release branch until exact repository evidence proves its physical migration, protection and workflow routing are complete.
- Ordinary task, feature, fix, audit, documentation, migration, runtime, Portal, WickHunter, CI and infrastructure work integrates through `develop`.
- Source branches/release channels are not runtime locations. `LOCAL | DEDICATED_LINUX` describes current target runtime location; `SYNOLOGY` is a durable-storage provider and may remain transitional compute only until service-level cutover is proven.
- Do not use `dev | staging | production` or `SHADOW | PAPER | LIVE` as current Portal product-mode vocabulary.
- Deployment uses attributable artifacts and durable state, but ordinary developer deployment does not require production-trading certification ceremony.

1. Read this file first.
2. Read `ARCHITECTURE_REGISTRY.yaml` and the current accepted Portal decisions (`ADR-023` plus the `ADR-024` runtime overlay) before Portal/WickHunter/runtime work.
3. For Portal work, read `docs/ai_platform/portal/README.md`, `docs/ai_platform/portal/DEVELOPER_QUANT_PORTAL_ARCHITECTURE.md` and the task-relevant documents; use `docs/agents/programs/FTAI_AI_TRADING_PORTAL_PROGRAM.md` as the current programme boundary.
4. Inspect current branch, HEAD, open PRs, and relevant CI before editing.
5. Work on a dedicated feature branch.
6. Keep commits focused and reviewable.
7. Run the narrowest relevant validation first, then broader tests when they materially protect the changed workflow.
8. Target ordinary repository PRs to `develop`; do not invent `main` state.
9. Record important architecture or workflow changes in repository documentation.

## Runtime and CI target

- The persistent application-compute target for this fork is Linux containers on a dedicated Linux runtime host. Synology is the target durable storage/evidence/backup provider, while existing Synology-hosted application services remain transitional current state until individually migrated.
- Freqtrade and Portal build, test, packaging, security analysis and immutable image builds use GitHub-hosted Linux runners by default when compatible with the task. GitHub-hosted runners are not persistent application runtime hosts.
- A self-hosted GitHub runner on the dedicated runtime host or Synology, when retained, must be `deploy-only` or otherwise narrowly scoped; do not use privileged runtime/storage hosts as the normal repository-wide CI or model-training environment.
- Local Linux-compatible developer processes/workers and local model training remain permitted where the workflow calls for `LOCAL` execution.
- Keep Linux architecture coverage relevant to deployed containers, including AMD64 and ARM64 where supported by available runners and dependencies.
- Docker is a delivery mechanism, not product authority.

## Portal/control-plane safety boundary

- Treat Freqtrade as an internal engine when it is used; do not expose its control API or WebSocket directly to the public Internet or browser clients.
- Browser requests terminate at the Portal same-origin boundary. Server-side components may consume public exchange/market-data APIs directly when required by the current workflow.
- The current Portal is single-owner. Existing tenant/RBAC fields may remain for compatibility or defense in depth, but multi-tenancy and enterprise role matrices are not completion prerequisites unless a later owner decision reintroduces them.
- Research/training and active-model assignment remain separate: training produces challengers; activation is explicit.
- Autonomous repair agents may prepare regression tests, isolated branches, fixes, and PRs; they may not bypass CI or perform destructive shared-host actions outside task scope.
- Cloudflare/Tunnel/Auth may protect the endpoint, but protected-target ceremony is required only when a concrete current security/reliability risk makes it relevant to the workflow being delivered.
- Portal implementation must not alter frozen historical research thresholds/evidence or iteratively consume protected holdout data unless a separate research decision explicitly authorizes it.

## Validation expectations

For Python changes:

- syntax/compile validation;
- Ruff on changed project Python files where applicable;
- targeted tests where test coverage exists.

For strategy/model changes:

- import/config validation;
- declared replay/backtest inputs;
- lookahead/leakage checks appropriate to the feature pipeline;
- out-of-sample or walk-forward evaluation where selection is involved;
- versioned model, feature, dataset and parameter identities.

## AI/ML principles

- FreqAI or another model layer predicts/scores; it does not grant real-money authority.
- Prefer a simple baseline before adding deep learning or reinforcement learning.
- Compare challengers on out-of-sample and accumulated realtime-public evidence, not only training metrics.
- Avoid feature explosion and data leakage.
- Version strategy/model code, features, targets, training windows, datasets and evaluation results together.
- Periodic local challenger training is allowed once the data/provenance path is proven; promotion/activation remains a separate deliberate action.

## Initial baseline

The initial baseline under `ai_platform/` remains historical/research evidence. Current Portal migration may reuse it for observation, replay and simulation when exact compatibility is known. It does not need a PAPER/SHADOW mode transition to participate in the Developer Quant workflow, and it grants no real-money execution authority.

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