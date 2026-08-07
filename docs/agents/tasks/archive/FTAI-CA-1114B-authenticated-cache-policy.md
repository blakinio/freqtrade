# FTAI-CA-1114B — authenticated Portal response cache policy

```yaml
task_id: FTAI-CA-1114B-authenticated-cache-policy
programme_id: FTAI-20260803-portal-remediation
project_lane: freqtrade-portal
parent_issue: 1114
issue: 1304
status: complete_on_merge
claim_id: ftaica-1304-20260807T075247Z-gpt56sol
owner: repair-worker-1304-20260807T075247Z-gpt56sol
base_branch: develop
original_base_head: 61be1d0d106283aacdf4f5d4cfe4b241006d3cac
branch: repair/1304-authenticated-cache-policy
pull_request: 1308
validated_implementation_head: a588649beb08c7f3fd398297cdf23077c7d061ff
post_dependency_merge_forward_head: ff3db7f9a85420d3b32e777366b9b04ed7ab723b
completion_claim: repository_application_boundary
ownership_release: on_merge
external_acceptance_issue: 1305
live_capital_authorized: false
protected_production_deployment_authorized: false
```

## Delivered outcome

- One canonical helper defines `Cache-Control: private, no-store` for repository-owned dynamic Portal responses.
- Direct Proxy responses apply the cache policy together with nonce CSP and invariant browser-security headers.
- `next.config.ts` applies the same policy to final dynamic Next responses because Next rendering can replace headers placed only on `NextResponse.next()`.
- Application-controlled responses require exact normalized `private, no-store`.
- Framework-generated not-found responses may append only stricter non-cacheable directives; they must retain `private` and `no-store` and may not contain `public`, `immutable`, `s-maxage` or positive `max-age`.
- Next static/image assets retain framework-owned public immutable caching.
- Extension-looking protected routes remain behind the Proxy rather than escaping through a broad file-extension matcher exception.
- All browser back/forward restores force exactly one network reload so the Proxy revalidates current session and tenant state; the reload navigation type prevents recursion.
- Market Evidence and Liquid20 production auth evidence requires the canonical downstream policy.

## Real response and browser evidence

```yaml
focused_runtime:
  exact_head: a588649beb08c7f3fd398297cdf23077c7d061ff
  workflow: AI Platform WickHunter Market Evidence CI
  run: 31161553827
  result: PASS
  portal_job: 92812842006
  portal_checks:
    typecheck_lint_build: PASS
    chromium_browser_tests: PASS
    production_market_evidence_auth: PASS
    production_response_cache_probe: PASS
```

The production response-cache probe starts the real `next start` server with fixture identity disabled and proves:

- login document `200` is private/no-store;
- anonymous protected navigation redirects with private/no-store;
- anonymous protected API returns `401` with private/no-store;
- authenticated nonexistent protected API reaches Next's real `404` through the Proxy and remains fail-closed;
- API mode against intentionally unreachable localhost `127.0.0.1:1` exercises the real BFF `502` path with exact private/no-store and no protected-target access;
- a rendered hashed Next asset retains `public`, positive `max-age` and `immutable`.

Browser coverage additionally proves authenticated success, forbidden, conflict, validation failure, logout, tenant change, extension-looking protected path and back/forward restoration behavior.

## Audit reconciliation

```yaml
prior_findings:
  FTAI-1304-AUD-001: VERIFIED_FIXED
  FTAI-1304-AUD-002: VERIFIED_FIXED
  FTAI-1304-AUD-003: VERIFIED_FIXED
  FTAI-1304-AUD-004: VERIFIED_FIXED
  FTAI-1304-AUD-005: VERIFIED_FIXED
  FTAI-1304-AUD-006: VERIFIED_FIXED
  FTAI-1304-AUD-007: VERIFIED_FIXED
  FTAI-1304-AUD-008: VERIFIED_FIXED
candidate_audit:
  review: 4881212334
  head: a588649beb08c7f3fd398297cdf23077c7d061ff
  result: PASS_ZERO_MATERIAL_FINDINGS
post_dependency_audit:
  review: 4881249609
  head: ff3db7f9a85420d3b32e777366b9b04ed7ab723b
  result: PASS_ZERO_MATERIAL_FINDINGS
material_findings_open: 0
unresolved_review_threads: 0
```

PR #1310 / Issue #1309 was merged into `develop` as `7e40b5b0b45b26e2127c06002dec3bd277645f5c`; #1308 was then non-force merge-forwarded. The #1304 product diff remained 12 intended paths and the four #1309 CI-governance paths became base state rather than #1304 changes.

## Completeness ledger reconciliation

```yaml
ledger_authority: docs/ai_platform/portal/FEATURE_COMPLETENESS_LEDGER.json
record: CONTROL-BROWSER-HEADERS
result: NO_STATUS_CHANGE_REQUIRED
repository_component: COMPLETE
runtime_composition: COMPLETE
api_mode_e2e: PARTIAL
deployment_package: PARTIAL
protected_target_acceptance: EXTERNAL_ACCEPTANCE_REQUIRED
parent_finding_remaining_open: 1114
external_child_remaining: 1305
protected_acceptance_inferred: false
```

No ledger status elevation is truthful from #1304 alone. The authoritative ledger already includes Issue #1304 and `BROWSER_SECURITY_HEADER_POLICY.md` in its source-evidence contract, while `CONTROL-BROWSER-HEADERS` already records repository/runtime completion. API-mode completeness remains constrained by #1098 and the parent browser-boundary finding, and deployment/protected-target evidence remains external under #1305. Therefore closeout intentionally records reconciliation without mutating the ledger or claiming HSTS/public-edge acceptance.

## Acceptance reconciliation

```yaml
acceptance:
  canonical_helper_and_consistent_policy: PASS
  success_401_403_404_conflict_5xx_real_response_evidence: PASS
  login_callback_session_logout_and_sensitive_redirects_not_shared_cacheable: PASS
  logout_tenant_switch_and_history_do_not_restore_prior_protected_state: PASS
  public_immutable_next_assets_not_degraded: PASS
  direct_origin_and_browser_regressions_fail_closed: PASS
  focused_production_build_and_chromium: PASS
  independent_final_audit_before_archive: PASS_ZERO_MATERIAL_FINDINGS
  dependency_1309_terminal_and_merged: PASS
  ledger_reconciled_without_external_overclaim: PASS_NO_STATUS_CHANGE_REQUIRED
  exact_archive_head_required_ci: PENDING
  squash_merge_and_issue_close: PENDING
```

## Recovery checkpoint

```yaml
recovery:
  policy_version: 1
  generation: archive-final
  session_id: repair-worker-1304-20260807T075247Z-gpt56sol
  session_started_at: 2026-08-07T07:52:47Z
  checkpointed_at: 2026-08-07T08:35:00Z
  last_progress_at: 2026-08-07T08:35:00Z
  phase: close
  exact_head: SELF_AFTER_ARCHIVE_TRANSITION
  pull_request: 1308
  active_operation: final exact-head CI and merge closeout
  check_generation: archive-final
  checks_used: 0
  status: ready
  safe_to_resume: true
  next_action: perform a fresh proportionate audit of the archive-transition diff and zero review threads, then observe Freqtrade CI, risk-aware component CI, WickHunter Market Evidence CI, CodeQL and zizmor on the exact unchanged archive head; squash-merge only after every required gate passes
```

## Closeout contract

This archive transition changes PR #1308 after the audited implementation/merge-forward head. PR #1308 may merge only after a fresh final audit of the complete archive-transition diff, zero unresolved review threads and all required checks pass on the exact archive-transition head. Merge closes #1304 and releases the claim. Parent #1114 remains open because #1305 protected public-edge/HSTS acceptance is separately owner-authorized work and is not inferred from repository completion.

## Safety boundary

No protected Cloudflare/Synology mutation, production deployment, credentials, private target, trading, withdrawal, strategy/model promotion or live-capital authority is exercised or granted by this repair.
