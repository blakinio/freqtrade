# Portal audit evidence integrity

## Contract

The retained `Portal Completeness Audit` workflow is a **living exact-head gate**, not an immutable copy of the 2026-08-02 audit. A green run is current classification evidence only when all generated reports identify the exact checked-out commit and the current machine-readable ledger version and digest.

The source of classification truth is:

- `tools/portal_audit/ledger/index.json`

The generator and validation implementation is:

- `tools/portal_audit/audit_ledger.py`
- `tools/portal_audit/deep_inventory.py`
- `tools/portal_audit/classified_matrices.py`
- `tools/portal_audit/navigation_matrix.py`
- `tools/portal_audit/validate_issue_states.py`

## Fail-closed rules

The workflow fails until the ledger receives an explicit disposition when any of these changes:

- backend module inventory;
- FastAPI method/route/source declaration inventory;
- Next.js page inventory;
- same-origin BFF handler inventory;
- canonical left navigation;
- monitored runtime/provider composition evidence;
- a classification references an Issue marked `COMPLETE` in the Portal remediation programme or an Issue already closed on GitHub;
- exact checked-out commit and requested audit head differ;
- generated report metadata does not match the current ledger and head.

A remediation that changes composition without adding or removing a route therefore cannot leave an obsolete status, reason or Issue mapping while CI remains green.

## Updating the ledger

A ledger update is an audit decision, not a mechanical refresh. The author must:

1. inspect the exact source change and its acceptance evidence;
2. update the affected inventory and classification rows together;
3. preserve explicit reasons and Issue or external-boundary mappings;
4. increment `ledger_version`;
5. run the audit-tool regression tests and all four generators on the exact head;
6. independently review the changed product area before accepting the new classification.

Issue #1101 owns canonical product-status reconciliation. This gate only prevents stale or contradictory audit evidence; it does not decide that a product Issue is complete without terminal remediation evidence.

## Reproducibility

Every run generates reports twice and compares them byte-for-byte. The source evidence package is built from a sorted file list with normalized timestamps, ownership, group, mode and gzip metadata. The workflow also publishes a deterministic per-file SHA-256 manifest and verifies a second independently built archive and manifest are identical.

The uploaded evidence contains:

- exact-head JSON and Markdown reports;
- ledger version and SHA-256 in every generated report;
- reproducible source archive and archive digest;
- deterministic source manifest and manifest digest.
