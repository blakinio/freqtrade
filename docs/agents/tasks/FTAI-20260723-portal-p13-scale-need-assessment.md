---
task_id: FTAI-20260723-portal-p13-scale-need-assessment
status: done
branch: docs/portal-p13-scale-no-go-20260723
base_branch: develop
created: 2026-07-23
updated: 2026-07-23
related_pr: "#224"
owned_paths:
  - docs/agents/tasks/FTAI-20260723-portal-p13-scale-need-assessment.md
required_reads:
  - AGENTS.md
  - docs/agents/CONTEXT_HANDOFF.md
  - docs/agents/programs/FTAI_AI_TRADING_PORTAL_PROGRAM.md
  - docs/ai_platform/portal/DELIVERY_ROADMAP.md
  - docs/ai_platform/portal/AGENT_EXECUTION_PLAN.md
  - docs/agents/tasks/FTAI-20260723-portal-p12-autonomous-repair-simulation-first.md
search_first:
  - current develop and open portal PRs
  - measured portal latency, throughput, saturation, capacity or SLO evidence
  - existing P13 tasks or service-extraction decisions
optional_reads: []
---

# AI Trading Portal P13 — Scale Need Assessment

## Goal

Determine whether current repository evidence justifies P13 scale or service extraction work after completion of P12 simulation-first acceptance.

## Decision

P13 is **not declared**. No measured requirement currently justifies Kubernetes scheduling, a dedicated workflow engine, shared inference service, separate trade-intelligence service, partitioned data infrastructure or multi-region design.

## Evidence reviewed

- Current `develop` contains completed P12 simulation-first acceptance and retains P11 as a deliberately deferred real-infrastructure gate.
- No open portal pull requests were found before this assessment PR was opened.
- Repository search found no current portal latency, throughput, saturation, capacity, error-budget or SLO evidence demonstrating a scale bottleneck.
- Repository search found no existing P13 task or approved service-extraction decision.
- The delivery roadmap requires P13 acceptance to be defined prospectively from observed bottlenecks/SLOs and forbids implementation for architectural fashion.

## Reopen conditions

A future P13 declaration requires at least one durable evidence bundle that identifies:

1. the measured bottleneck or unmet SLO;
2. workload and observation window;
3. current architecture baseline;
4. quantified impact;
5. alternatives considered, including no-change and vertical optimization;
6. the smallest justified extraction or scaling change;
7. validation and rollback criteria.

Real P11 infrastructure provisioning by itself is not evidence that P13 is needed.

## Context checkpoint

```yaml
checkpoint_version: 1
updated_at: 2026-07-23T20:12:00+02:00
head: 9026d96f23f1d1715fecfd3a54fbb90c7f45e9da
branch: docs/portal-p13-scale-no-go-20260723
pr: "#224"
status: ready
context_routes:
  - docs/agents/programs/FTAI_AI_TRADING_PORTAL_PROGRAM.md
  - docs/ai_platform/portal/DELIVERY_ROADMAP.md
  - docs/ai_platform/portal/AGENT_EXECUTION_PLAN.md
  - docs/agents/tasks/FTAI-20260723-portal-p12-autonomous-repair-simulation-first.md
owned_paths:
  - docs/agents/tasks/FTAI-20260723-portal-p13-scale-need-assessment.md
proven:
  - P12 simulation-first acceptance is complete on develop.
  - P11 real Cloudflare and protected GitHub staging infrastructure remains intentionally deferred by the owner.
  - No open portal pull requests were found before PR #224 was opened.
  - No repository evidence of portal latency, throughput, saturation, capacity, error-budget or SLO breach was found.
  - No existing P13 task or approved service-extraction decision was found.
  - The delivery roadmap permits P13 only after measured need and rejects architecture-for-fashion implementation.
derived:
  - Starting P13 now would add operational complexity without a demonstrated requirement.
  - The correct bounded action is to preserve the modular monolith and current simulation-first architecture until measured evidence crosses a declared threshold.
unknown:
  - Future production-like staging workload and operational SLO measurements do not yet exist because real P11 infrastructure is deferred.
conflicts: []
first_failure:
  marker: p13-measured-need-absent
  evidence: No durable measurement or SLO breach currently demonstrates that service extraction or scale infrastructure is required.
rejected_hypotheses:
  - Declare Kubernetes because it may be useful later.
  - Extract services solely because P12 is complete.
  - Treat deferred P11 infrastructure work as a scale bottleneck.
  - Infer production capacity needs from deterministic simulation evidence.
changed_paths:
  - docs/agents/tasks/FTAI-20260723-portal-p13-scale-need-assessment.md
validation:
  - command: repository search for open portal PRs
    result: PASS
    evidence: No open portal PR was returned before this assessment PR was opened.
  - command: repository search for P13 tasks and measured portal bottleneck or SLO evidence
    result: PASS
    evidence: No current P13 declaration or qualifying measurement evidence was found.
blockers: []
next_action: Keep P13 undeclared until a durable portal measurement bundle demonstrates a specific bottleneck or unmet SLO, and keep P11 deferred until the owner starts the real infrastructure phase.
```
