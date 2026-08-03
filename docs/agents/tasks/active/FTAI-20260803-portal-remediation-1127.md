# FTAI-20260803 Portal Remediation — Issue 1127

```yaml
task_id: FTAI-20260803-portal-remediation-1127
programme_id: FTAI-20260803-portal-remediation
issue: 1127
repository: blakinio/freqtrade
lane: freqtrade-portal
task_kind: implementation
phase: validate
status: validating
priority: high
prompting_standard_version: 2.1
execution_policy_version: 2
context_pressure: high
decomposition_decision: single
execution_mode: github_only
run_scope: autonomous_task
continuation_policy: continue_until_real_stop
task_completion_policy: finalize_archive_and_continue
user_communication: terminal_only
feature_scope:
  type: backend_security_foundation
  user_facing: true
  backend_required: true
  frontend_required: false
  integration_required: true
  e2e_required: true
branch: fix/portal-1127-sensitive-data-classifier
base_branch: develop
original_base_head: 9b865a64897ef17004809ccf4973c7a930fe4314
required_integration_base: 947c610842f832786f141c77a38e7f73748e6db6
pr: 1151
pr_state: draft
owned_paths:
  - .github/workflows/ai-platform.yml
  - ai_platform/portal/security/sensitive_data.py
  - ai_platform/portal/security/sensitive_scan.py
  - ai_platform/portal/security/http_validation.py
  - ai_platform/portal/contracts/sensitive.py
  - ai_platform/portal/contracts/payloads.py
  - ai_platform/portal/contracts/common.py
  - ai_platform/portal/contracts/bots.py
  - ai_platform/portal/observability/redaction.py
  - ai_platform/portal/control_plane/api.py
  - tests/ai_platform/portal/test_sensitive_data_classifier.py
  - tests/ai_platform/portal/security/test_sensitive_data_extended.py
  - docs/ai_platform/portal/SENSITIVE_DATA_CLASSIFICATION.md
  - docs/agents/tasks/active/FTAI-20260803-portal-remediation-1127.md
shared_path_leases:
  - mechanism: canonical_sensitive_metadata_classifier
    producer_issue: 1127
    status: held
producer_dependencies:
  - existing Pydantic/FastAPI validation boundaries
  - existing audit and event contract validators
  - exact control-plane image build
consumer_constraints:
  - do not create a new audit writer, event publisher or logging framework
  - do not persist, emit, hash without a key, or log rejected values
  - do not weaken bounded depth, item, string-byte or serialized-layer limits
  - use approved opaque public reference types rather than raw store paths
  - integrate exact post-1126 develop before merge
live_capital_authorized: false
withdrawals_enabled: false
protected_production_deployment_authorized: false
```

## Finding reproduced

The exact original base contained two independent and inconsistent secret-key mechanisms:

- `contracts/payloads.py` used broad lowercase substrings, missing API/client credentials, session identifiers, DSNs/private endpoints and reference/store-path aliases while creating false positives.
- `observability/redaction.py` used a separate exact lowercase-key set, missing case, delimiter, camel/compact and serialized variants.

Neither traversal detected cyclic containers. Neutral string fields could carry secret-shaped values or nested JSON/header/form objects. Raw private store paths could pass through generic reference strings. FastAPI/Pydantic validation could echo rejected input. There was no bounded persisted-artifact scanner or exact-image negative evidence.

## Selected contract

- One normalized key and high-confidence value classifier in `security/sensitive_data.py`.
- Reject-before-persist/publish through `contracts/payloads.py`.
- Redact-before-log/export through `observability/redaction.py`.
- Approved public references use `OpaqueSensitiveReference`; generic secret/store reference aliases remain forbidden.
- API validation responses omit raw `input`/context and use `no-store`.
- Historical scanner reports only source, record identity, path, classification and finding type.
- Secret diagnostics may use keyed HMAC-SHA256 only; unkeyed hashes are prohibited.

## Acceptance inventory

- [x] One canonical server-side classifier owns normalized key and high-confidence value recognition.
- [x] Case, acronym, camel-case, delimiter and compact variants normalize deterministically.
- [x] Coverage includes authorization/proxy authorization, cookies/set-cookie, API/client keys and secrets, private keys, credentials, passwords/passphrases, session IDs, access/refresh/session/WebSocket tokens, DSNs, connection strings, private endpoints and credential/token/secret/Vault references.
- [x] Reference compounds are checked before metadata exemptions; `credential_ref`, `token_ref`, `secret_ref` and `vault_path` are rejected.
- [x] Documented metadata descriptors and unrelated words remain safe.
- [x] Neutral strings are inspected for authorization values, JWTs, PEM private keys, URL credentials and embedded secret assignments.
- [x] Bounded JSON strings, form bodies and header blocks are recursively inspected.
- [x] Mapping/sequence traversal detects cycles, unsupported structures, depth, item, string-byte and serialized-layer limits.
- [x] Sensitive subtrees are replaced atomically before traversal or serialization.
- [x] Audit and domain-event contracts continue to reject through the canonical payload guard before downstream consumers.
- [x] Canonical API validation errors omit rejected input values and use `no-store`.
- [x] Bot exchange references use an approved opaque domain identifier and reject raw Vault paths, URLs and encoded values.
- [x] Safe diagnostics use keyed HMAC-SHA256 and never return raw values.
- [x] Structured logging imports the canonical redaction boundary and has an extended-alias/serialized-value negative test.
- [x] A bounded JSON/JSONL/SQLite scanner emits value-free source/record/path/classification findings and a remediation runbook.
- [x] CI scans committed Portal artifacts and uploads a value-free report.
- [x] Exact control-plane image CI includes clean and synthetic-negative scanner probes and removes synthetic input before evidence upload.
- [x] Tests use synthetic canaries and assert no canary appears in errors, API responses, logs or scan reports.
- [ ] Incorporate exact `develop@947c610842f832786f141c77a38e7f73748e6db6` after Issue #1126 merge and resolve any integration conflict.
- [ ] Focused tests, full AI Platform CI, exact-image probes, repository CI and fresh changed-path audit pass on the exact integrated final head.
- [ ] PR becomes ready, all threads resolve, merges, Issue #1127 closes, task archives and classifier lease releases.

## Validation history

1. Head `a67f0eb831d232329a9920f73bf3c2927015dbb5`, AI Platform run `30809368889`: `1118` passed and four legacy error-contract tests failed. Root cause was a changed safe error phrase and missed compact aliases. The classifier was corrected without value disclosure.
2. Head `034349cadc65700c50fad39b50ab15f40f2f0145`, AI Platform run `30809551386`: `1122` passed; Ruff identified classification enum labels as false-positive hardcoded secrets. Explicit classification-only annotations were added.
3. Head `c9ef785cc90c97f1f7707edf7ebadeb87010ec25`, AI Platform run `30809687419`: tests passed; Ruff format found one formatting-only defect. Canonical formatting was applied.
4. Issue-body reconciliation proved the initial scope was incomplete. The same task/PR was expanded to cover value recognition, serialized structures, session/DSN/private endpoint/reference aliases, safe opaque references, keyed fingerprints, safe API errors, structured logs, historical scanning and exact-image evidence. Prior green results are not final acceptance evidence.

## Safety

- Synthetic canaries only.
- Exceptions and reports include field path/classification, never field value.
- Redaction replaces an entire sensitive subtree before evaluating it.
- Scanner reports never contain values or unkeyed fingerprints.
- Exact-image evidence uploads reports only; synthetic input files are deleted first.
- No real credential, token, cookie, key, Vault path, protected endpoint, production deployment, trading mutation, withdrawal or live-capital effect is authorized or recorded.

## Context checkpoint

```yaml
checkpoint_version: 2
updated_at: 2026-08-03T11:38:00Z
head: 8c50a2441631b3640840ad88eb34fefa55c57488
branch: fix/portal-1127-sensitive-data-classifier
pr: 1151
status: validating
context_routes:
  - issue #1127
  - ai_platform/portal/security/sensitive_data.py
  - ai_platform/portal/security/sensitive_scan.py
  - ai_platform/portal/security/http_validation.py
  - ai_platform/portal/contracts/sensitive.py
  - ai_platform/portal/contracts/payloads.py
  - ai_platform/portal/observability/redaction.py
  - .github/workflows/ai-platform.yml
owned_paths:
  - .github/workflows/ai-platform.yml
  - ai_platform/portal/security/sensitive_data.py
  - ai_platform/portal/security/sensitive_scan.py
  - ai_platform/portal/security/http_validation.py
  - ai_platform/portal/contracts/sensitive.py
  - ai_platform/portal/contracts/payloads.py
  - ai_platform/portal/contracts/common.py
  - ai_platform/portal/contracts/bots.py
  - ai_platform/portal/observability/redaction.py
  - ai_platform/portal/control_plane/api.py
  - tests/ai_platform/portal/test_sensitive_data_classifier.py
  - tests/ai_platform/portal/security/test_sensitive_data_extended.py
  - docs/ai_platform/portal/SENSITIVE_DATA_CLASSIFICATION.md
  - docs/agents/tasks/active/FTAI-20260803-portal-remediation-1127.md
proven:
  - original payload and redaction classifiers diverged and missed authorized Issue aliases
  - original traversals lacked cycle guards and serialized-structure inspection
  - generic strings could expose raw store paths and FastAPI validation could echo rejected input
  - audit and event contracts validate payloads before downstream repositories
  - canonical structured_log already consumes observability redaction
  - issue #1126 is merged into develop at 947c610842f832786f141c77a38e7f73748e6db6
  - PR #1151 is draft and currently diverged by one develop commit
  - no competing sensitive-classifier task or producer exists
derived:
  - branch integration must preserve the current #1127 tree while adding the exact #1126 develop parent
  - exact-image probes are required because the classifier/scanner must be present and executable in the shipped control-plane image
unknown:
  - exact integrated-head test, historical-scan and image-probe outcomes
conflicts:
  - PR #1151 must incorporate post-#1126 develop before it can be mergeable
first_failure:
  marker: divergent-incomplete-sensitive-classification-and-sinks
  evidence: issue #1127 plus exact original payload/redaction implementations
rejected_hypotheses:
  - key-only classification is complete; rejected by serialized/value acceptance criteria
  - broad substring matching is safe; rejected by false positives and missed aliases
  - redaction alone protects persistence; rejected because audit/events must reject before storage/publication
  - raw Vault/store paths are safe public references; rejected
  - unkeyed secret hashes are safe diagnostics; rejected
  - prior narrow green tests prove Issue acceptance; rejected after complete Issue-body reconciliation
changed_paths:
  - .github/workflows/ai-platform.yml
  - ai_platform/portal/security/sensitive_data.py
  - ai_platform/portal/security/sensitive_scan.py
  - ai_platform/portal/security/http_validation.py
  - ai_platform/portal/contracts/sensitive.py
  - ai_platform/portal/contracts/payloads.py
  - ai_platform/portal/contracts/common.py
  - ai_platform/portal/contracts/bots.py
  - ai_platform/portal/observability/redaction.py
  - ai_platform/portal/control_plane/api.py
  - tests/ai_platform/portal/test_sensitive_data_classifier.py
  - tests/ai_platform/portal/security/test_sensitive_data_extended.py
  - docs/ai_platform/portal/SENSITIVE_DATA_CLASSIFICATION.md
  - docs/agents/tasks/active/FTAI-20260803-portal-remediation-1127.md
validation:
  - command: AI Platform CI 30809368889
    tested_sha: a67f0eb831d232329a9920f73bf3c2927015dbb5
    result: FAIL_ISOLATED
    evidence: 1118 passed; four safe error-contract/compact-alias defects
  - command: AI Platform CI 30809551386
    tested_sha: 034349cadc65700c50fad39b50ab15f40f2f0145
    result: FAIL_ISOLATED
    evidence: 1122 passed; Ruff S105 false positives on classifier labels
  - command: AI Platform CI 30809687419
    tested_sha: c9ef785cc90c97f1f7707edf7ebadeb87010ec25
    result: FAIL_ISOLATED
    evidence: tests passed; one Ruff formatting-only defect
blockers:
  - none
next_action: Incorporate exact develop 947c610842f832786f141c77a38e7f73748e6db6 into PR #1151 without losing the current #1127 tree, then run the expanded focused/full/image validation and isolate the first relevant failure.
```
