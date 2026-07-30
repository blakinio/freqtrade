# FTAI-20260730 Liquidations Live Telegram monitoring remediation

## Scope

Repair the production portal restart-policy proof mismatch and add GitHub-hosted Telegram alerting, recovery, deduplication, delivery-failure handling and an independent five-minute monitoring watchdog.

## Safety boundary

No collector data, portal authentication, trading configuration, credentials or execution state may be modified. Telegram secrets remain GitHub Actions secrets. Production checks remain fail-closed.

## Context checkpoint

- branch: `fix/liquidations-live-telegram-monitoring-20260730`
- base: `develop@7240762e134d8db42b83030491ae52ec0d02cad6`
- status: implementation
- PROVEN: Issue #751 fails at `production_container_preflight`; PR #755 changed the live portal restart policy to `always`; the proof still requires `unless-stopped`.
- DERIVED: aligning deployment and proof on `always` fixes the real contract mismatch while preserving automatic recovery after Synology restarts.
- UNKNOWN: repository Telegram secrets and true delivery remain unverified until the post-merge bootstrap workflow runs.
- CONFLICT: none
- first_failure: production portal restart-policy contract mismatch
- changed_paths: portal proof/deployment, autostart repair workflow, Telegram notifier/workflow/tests
- validation: local notification unit tests pass
- blockers: Telegram delivery cannot be declared healthy until both required secrets exist and the bootstrap run succeeds.
- next_action: run exact-head CI, review, merge with SHA protection, then validate production health, Issue closure and Telegram delivery.
