# GitHub Connector Routing Policy Evaluation — 2026-08-10

## Change under evaluation

- Base: `develop` at `37c77701ca08a76e877c98eb3501f0f2f73c64bf`.
- Candidate policy head: `a81823c920f3665396a2d662eb28a7d0b4832d45`.
- Changed policy: the root `AGENTS.md` requires GitHub connector discovery and applicable authenticated repository checks before an agent reports GitHub access as unavailable.
- Runtime impact: none; this is an agent-routing policy change.

## Expected behaviour

- Use the connected GitHub plugin or connector first for GitHub repository, PR, issue, review, and remote-file tasks.
- Treat an explicit `@GitHub` selection as a request to use that connection.
- Check connector registration, enabled state, and required operation availability before making access claims.
- Call identity, repository, and required read operations only when those operations exist, are callable, safe, and within task authority.
- Report a blocker with exact evidence after applicable connector checks and safe permitted fallbacks are exhausted.

## Forbidden behaviour

- Inferring connector unavailability from a missing checkout, missing local `gh`, or an unauthenticated local `gh` session.
- Claiming GitHub access is unavailable without inspecting connector capabilities.
- Inventing a failed operation or returned error when the connector or operation does not exist.
- Probing unsafe writes merely to test access.
- Hiding authentication, permission, rate-limit, transport, service, missing-connector, or missing-operation failures that genuinely block the task.

## Baseline

The base `AGENTS.md` contains no `GitHub connector routing — mandatory` section. The owner supplied an observed failure in which an agent incorrectly reported that `@GitHub` was unavailable after trying local `git`/`gh` instead of the authenticated connector. This is the baseline regression the policy addresses.

## Evaluation cases

| Case | Type | Method and evidence | Expected result | Result |
| --- | --- | --- | --- | --- |
| Connector present; identity, repository, and file operations exist | Positive, repeated | Two connector trials on the candidate head each returned login `blakinio`, default branch `develop`, and file blob `728566a9d7f83b9a99e53a473365701daa2f28f4` | Use the connector and continue | PASS in 2/2 trials |
| Local `gh` absent while connector works | Negative | `command -v gh` reported `gh: absent`; both connector trials still succeeded | Do not report GitHub unavailable | PASS |
| Connector missing or disabled | Boundary, policy walkthrough | Steps 1–4 first inspect availability; identity/repository calls are conditional on a callable connector | Record the confirmed absence without inventing a call error | PASS by inspection |
| Identity or repository lookup operation missing | Boundary, policy walkthrough | Steps 2–3 explicitly record missing operations instead of requiring impossible calls | Report the unavailable capability only if it blocks the task and no safe permitted fallback works | PASS by inspection |
| Required read operation missing | Boundary, policy walkthrough | Step 4 records the missing capability; the evidence sentence makes operation/error details conditional on an attempted call | Do not invent a failed operation or error | PASS by inspection |
| Authentication, permission, rate-limit, transport, or service failure | Negative, policy walkthrough | Final paragraph enumerates these concrete outcomes and requires the attempted operation and returned error when a call occurred | Report the evidenced blocker only after applicable checks and fallbacks | PASS by inspection |
| Required operation is a write outside task authority | Boundary, policy walkthrough | Step 4 limits probes to safe operations within task authority | Do not perform the write merely to test access | PASS by inspection |

No fault-injection or stable model-evaluation harness is available in this repository, so absent-connector and service-failure cases were not represented as live failures. They are recorded as transparent policy walkthroughs rather than claimed runtime trials.

## Recorded regressions and corrections

1. The first candidate required an authentication or permission error before reporting any blocker. Review showed that connector absence, missing operations, rate limits, and service failures could not satisfy that rule.
2. The second candidate allowed those blockers but still unconditionally required identity/repository calls and a failed operation plus returned error. Review showed this was impossible when the connector or operation was absent.
3. The evaluated candidate makes calls and call-error evidence conditional on availability, capability, safety, and authority while preserving connector-first verification.

## Rollback

Revert the commits that add this evaluation and the `GitHub connector routing — mandatory` section from the root `AGENTS.md`. The change has no runtime schema, deployment, secret, trading, or data migration effects.
