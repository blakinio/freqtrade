# AI Program Closure — multi-agent prompt pack

This directory contains copy/paste prompts for running the remaining repository closure work in separate ChatGPT/Codex agent chats.

## Why this exists

One chat cannot create or control other chats. Coordination therefore happens through durable repository state:

- `develop`, branches, PRs and exact-head CI;
- `docs/agents/tasks/FTAI-20260730-ai-program-closure-orchestration.md`;
- `docs/ai_platform/PROGRAM_CLOSURE_MATRIX.md`;
- dated child task records under `docs/agents/tasks/`;
- one compact checkpoint per active task.

No chat transcript is a dependency for another agent.

## Launch order

### Step 1 — coordinator only

Open one new agent chat and paste:

- `COORDINATOR-AGENT-PROMPT.md`

The coordinator must complete serialized Gate 0 first. It reconciles the stale backlog, freezes shared contracts and creates only the child tasks classified as `REAL_GAP`.

Do not launch implementation workers before the coordinator records Gate 0 as `PASS` and declares their child task `READY`.

### Step 2 — parallel workers

After Gate 0, open separate chats and paste every worker prompt that the closure matrix marks `READY`:

- `CONTRACTS-AGENT-PROMPT.md`
- `TIME-LEAKAGE-AGENT-PROMPT.md`
- `FEATURE-ENGINE-AGENT-PROMPT.md`
- `SIMULATOR-AGENT-PROMPT.md`
- `RESEARCH-DATA-AGENT-PROMPT.md`
- `AI-ROUTING-RANKING-AGENT-PROMPT.md`
- `UI-SIGNAL-WIZARD-AGENT-PROMPT.md`
- `UI-STRATEGY-CATALOG-AGENT-PROMPT.md`
- `INTEGRATION-E2E-AGENT-PROMPT.md`

The integration/E2E agent may prepare harness work early only when its task record explicitly allows it. Final acceptance waits for all required implementation PRs.

Every worker prompt requires `WORKER-COMMON-RULES.md`; the pasted prompt tells the agent to read it from the repository before editing.

### Optional external lane

Use `EXTERNAL-STAGING-AGENT-PROMPT.md` only after the repository matrix marks it ready and the owner explicitly supplies/authorizes real Cloudflare, protected GitHub, Synology, Authentik, Vault and staging resources.

## Manual operating procedure

1. Paste the coordinator prompt into Chat A.
2. Let Chat A complete Gate 0 and merge its preflight/task-declaration PR.
3. Read the launch table produced in `PROGRAM_CLOSURE_MATRIX.md`.
4. Open one chat per `READY` workstream and paste the matching prompt.
5. Do not reuse the same branch for two chats.
6. Let workers communicate only through task checkpoints, PR state and CI evidence.
7. Keep the coordinator chat available for merge sequencing and bounded contract-change routing.
8. After worker PRs merge, run the integration/E2E prompt if it was not already active.
9. Return to the coordinator prompt/chat for final repository closure and terminal checkpoint.

Launching all worker prompts before Gate 0 is intentionally unsupported: workers will refuse implementation when the matrix, task record or ownership gate is missing.

## Safety

All prompts preserve these boundaries:

- paper/shadow/dry-run only;
- no live-capital authority;
- no exchange secrets;
- no browser-to-Freqtrade, exchange or Vault path;
- no protected holdout reuse;
- no silent reopening of completed ASE/BM packages;
- no force push, history rewrite or CI bypass;
- real external staging evidence is never inferred from fixtures or simulation.
