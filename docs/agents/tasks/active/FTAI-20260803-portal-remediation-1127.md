# FTAI-20260803 Portal Remediation — Issue 1127

```yaml
task_id: FTAI-20260803-portal-remediation-1127
programme_id: FTAI-20260803-portal-remediation
issue: 1127
repository: blakinio/freqtrade
lane: freqtrade-portal
task_kind: implementation
phase: reproduce
status: implementing
priority: high
prompting_standard_version: 2.1
execution_policy_version: 2
context_pressure: medium
decomposition_decision: single
execution_mode: github_only
run_scope: autonomous_task
continuation_policy: continue_until_real_stop
task_completion_policy: finalize_archive_and_continue
user_communication: terminal_only
feature_scope:
  type: backend_security_foundation
  user_facing: false
  backend_required: true
  frontend_required: false
  integration_required: true
  e2e_required: false
branch: fix/portal-1127-sensitive-data-classifier
base_branch: develop
base_head: 9b865a64897ef17004809ccf4973c7a930fe4314
pr: none
owned_paths:
  - ai_platform/portal/security/sensitive_data.py
  - ai_platform/portal/contracts/payloads.py
  - ai_platform/portal/observability/redaction.py
  - ai_platform/portal/contracts/audit.py
  - ai_platform/portal/contracts/events.py
  - tests/ai_platform/portal/**sensitive**
  - tests/ai_platform/portal/**payload**
  - tests/ai_platform/portal/**redaction**
  - docs/ai_platform/portal/SENSITIVE_DATA_CLASSIFICATION.md
  - docs/agents/tasks/active/FTAI-20260803-portal-remediation-1127.md
shared_path_leases:
  - mechanism: canonical_sensitive_metadata_classifier
    producer_issue: 1127
    status: held
producer_dependencies:
  - existing Pydantic contract validators
consumer_constraints:
  - do not create a new audit writer or event publisher
  - do not persist, emit or log rejected values
  - do not weaken bounded payload depth/item limits
  - programme file reconciliation is serialized after issue 1126 closeout
live_capital_authorized: false
withdrawals_enabled: false
protected_production_deployment_authorized: false
```

## Finding reproduced

The exact base contains two independent and inconsistent secret-key mechanisms:

- `contracts/payloads.py` rejects keys when a small substring list appears anywhere in `key.lower()`; this misses important aliases such as API keys, credentials, private keys, passphrases and secret references while producing false positives for unrelated substrings.
- `observability/redaction.py` uses a separate exact lowercase-key set; it misses delimiter/case/suffix variants and has no cycle guard.

Both recursively traverse attacker-controlled metadata without one canonical normalized-key classifier. Payload validation handles mappings and lists but does not detect cycles or unsupported nested containers. Redaction handles mappings/lists/tuples but likewise has no cycle guard. Audit and domain-event contracts depend on payload validation, so incomplete classification can reach persistence/publication boundaries.

## Acceptance inventory

- [ ] One canonical server-side classifier owns normalized sensitive-key recognition for validation and redaction.
- [ ] Normalization is deterministic across case and delimiter variants and uses token/compound-boundary rules rather than unsafe broad substrings.
- [ ] Covered concepts include secret, credential, token, cookie, authorization, API key/secret, private key, password, passphrase, client secret, refresh token, secret reference and Vault reference.
- [ ] Sensitive suffix/prefix compounds are detected without classifying unrelated words such as `monkey`, `tokenizer`, `secretary`, `cookie_policy` or `authorization_status` unless the complete field denotes secret material.
- [ ] Recursive traversal is deterministic for mappings and bounded sequences, rejects unsupported containers, and detects direct/indirect cycles before persistence/publication/logging.
- [ ] Payload guards reject the whole object before any DB insert, event append, audit append or export.
- [ ] Redaction returns only sanitized data, never logs or returns rejected secret values, and replaces sensitive subtrees atomically.
- [ ] Audit and domain-event contracts continue to invoke the canonical payload guard.
- [ ] Tests cover every alias family, case/delimiter variants, nested depth, mappings/sequences, direct/indirect cycles, unsupported types and false positives.
- [ ] Existing payload size/depth limits remain fail closed.
- [ ] Focused tests, full AI Platform CI, exact-head repository CI and fresh changed-path audit pass.
- [ ] PR merges, Issue #1127 closes, task archives and shared classifier lease releases.

## Safety

- Test values use synthetic canaries only.
- Exceptions identify the rejected field path/classification but never include the field value.
- Redaction replaces the entire sensitive value and does not traverse or stringify it.
- No credentials, tokens, cookies, private keys, secret references or protected endpoints are recorded.

## Context checkpoint

```yaml
checkpoint_version: 1
updated_at: 2026-08-03T11:10:00Z
head: 9b865a64897ef17004809ccf4973c7a930fe4314
branch: fix/portal-1127-sensitive-data-classifier
pr: none
status: implementing
context_routes:
  - issue #1127
  - ai_platform/portal/contracts/payloads.py
  - ai_platform/portal/observability/redaction.py
  - ai_platform/portal/contracts/audit.py
  - ai_platform/portal/contracts/events.py
owned_paths:
  - ai_platform/portal/security/sensitive_data.py
  - ai_platform/portal/contracts/payloads.py
  - ai_platform/portal/observability/redaction.py
  - ai_platform/portal/contracts/audit.py
  - ai_platform/portal/contracts/events.py
  - tests/ai_platform/portal/**sensitive**
  - tests/ai_platform/portal/**payload**
  - tests/ai_platform/portal/**redaction**
  - docs/ai_platform/portal/SENSITIVE_DATA_CLASSIFICATION.md
  - docs/agents/tasks/active/FTAI-20260803-portal-remediation-1127.md
proven:
  - payload validation and observability redaction use separate sensitive-key lists and matching rules
  - current payload substring matching misses required aliases and can create false positives
  - current redaction exact-key matching misses normalized variants
  - neither recursive implementation detects cyclic containers
  - audit and domain-event contracts consume validate_payload before their downstream repositories
  - no overlapping branch, task or open PR for issue 1127 was found
  - issue 1126 remains in exact-head CI on non-overlapping product paths
derived:
  - a canonical normalized field classifier can serve both reject and redact policies without creating a new audit/event authority
  - redaction must replace a sensitive subtree before inspecting its value to prevent accidental evaluation/stringification
unknown:
  - complete live consumer/test filename inventory, to resolve through exact-head CI and changed-path inspection
conflicts: []
first_failure:
  marker: divergent-incomplete-sensitive-key-classification
  evidence: contracts/payloads.py versus observability/redaction.py on exact base
rejected_hypotheses:
  - broad substring matching is safe; rejected by false positives and missed compound aliases
  - redaction alone protects persistence; rejected because audit/event payloads must reject before storage/publication
  - recursive traversal can ignore cycles; rejected as availability and fail-open risk
changed_paths:
  - docs/agents/tasks/active/FTAI-20260803-portal-remediation-1127.md
validation:
  - command: static exact-base reproduction
    result: FAIL_EXPECTED
    evidence: divergent classifiers, missed aliases and no cycle guard
blockers:
  - none
next_action: Implement the canonical normalized sensitive-field classifier and cycle-safe reject/redact traversals, then add adversarial corpus tests.
```
