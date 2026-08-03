# Sensitive Data Classification and Historical Recovery

Status: normative server-side contract for Portal ingress, persistence, publication, observability, support evidence and historical scanning.

## Authority

`ai_platform/portal/security/sensitive_data.py` is the sole normalized sensitive-field and high-confidence sensitive-value classifier. Consumers must use it directly or through these stable boundaries:

- `contracts/payloads.py` for reject-before-persist/publish;
- `observability/redaction.py` for sanitize-before-log/export;
- `contracts/sensitive.py` for approved opaque public references;
- `security/http_validation.py` for API validation responses which never echo rejected input;
- `security/sensitive_scan.py` for persisted test/staging and generated-artifact scanning.

No consumer may maintain a competing alias list.

## Normalized key coverage

Field names are split across acronym, camel-case and non-alphanumeric boundaries, then case-folded. `API-Key`, `api_key`, `apiKey` and `apikey` classify identically. The classifier uses complete tokens, explicit compounds and narrowly bounded compact suffixes instead of broad substring matching.

Protected concepts include:

- authorization and proxy-authorization values;
- cookies and set-cookie values;
- API/client keys, API/client secrets and private keys;
- session identifiers, access/refresh/session/WebSocket tokens;
- credentials, passwords and passphrases;
- DSNs, connection strings and private endpoint/URL fields;
- credential, token, secret and Vault references or paths.

Reference compounds are classified before metadata exemptions. Therefore `credential_ref_name`, `token_ref`, `secret_ref_name` and `vault_path` remain protected. A narrow metadata-only suffix allowlist permits descriptors such as `cookie_policy`, `authorization_status`, `token_count`, `session_id_status`, `dsn_status` and `api_key_name`. Unrelated words such as `monkey`, `tokenizer` and `secretary` are not aliases.

## Value and serialized-structure coverage

High-confidence raw values are rejected/redacted even under a neutral field name when they are recognizable as:

- authorization scheme values;
- JWT-shaped values;
- PEM private keys;
- URLs/DSNs with embedded user information;
- embedded secret assignments.

String fields are byte bounded. Bounded JSON strings, form-encoded bodies and header blocks are decoded and recursively inspected for a maximum number of serialized layers. A hidden alias cannot bypass policy by moving into a JSON string, form body or serialized header object. Oversized/deep strings fail closed.

## Reject-before-persist/publish policy

Audit and domain-event contracts call `reject_sensitive_payload_keys()` before downstream storage or publication. The traversal:

- rejects a sensitive field before inspecting its value;
- supports string-keyed mappings and bounded non-text sequences;
- detects direct and indirect container cycles;
- rejects non-string keys and unsupported containers;
- enforces depth, aggregate-item, string-byte and serialized-layer limits;
- identifies only the field path and classification, never the protected value.

All Portal contract models hide raw inputs in Pydantic error text. The canonical FastAPI application installs a request-validation handler that excludes `input` and sensitive `ctx` data and emits `no-store` responses.

## Redact-before-log/export policy

Observability uses the same classifier through `redact_sensitive()`. Redaction creates a sanitized copy and replaces an entire sensitive subtree with `[REDACTED]` before evaluating or traversing it. Sensitive serialized strings are replaced atomically. Safe-field cycles, unsupported structures and traversal-limit violations fail closed instead of producing a partial unsafe object.

Structured logs, metrics/tracing attributes, error-envelope details, evidence/support exports and fixture/report generators must use the same redaction boundary. No sink may stringify the original object after classification or redaction fails.

## Approved opaque references

A public contract may expose only a dedicated `OpaqueSensitiveReference`, never a raw Vault path, DSN, private endpoint or secret-bearing URL. The type accepts an 8–128 character opaque identifier and forbids path, URL, query, encoding and raw-secret shapes. `BotSpec.exchange_connection_ref` and bot revision contracts use this type.

Ambiguous generic metadata keys such as `credential_ref`, `token_ref`, `secret_ref` and `vault_path` remain rejected. A producer must map a private store location to an approved opaque domain identifier before crossing a public contract.

## Safe fingerprints

Unkeyed hashes of secret values are prohibited because they enable offline verification of low-entropy material. `fingerprint_sensitive_value()` requires a separate key of at least 32 bytes and returns only an HMAC-SHA256 diagnostic fingerprint. The key and input value must never be logged or persisted with the fingerprint. Historical scanning does not fingerprint values at all.

## Historical scanner and remediation procedure

Run:

```bash
python -m ai_platform.portal.security.sensitive_scan \
  ai_platform/portal tests/ai_platform/portal artifacts \
  --report artifacts/sensitive-data-scan.json
```

The scanner reads bounded JSON, JSONL/NDJSON and SQLite files. Its report contains only:

- source file identifier;
- record identity such as document, line number, table and rowid;
- field path;
- classification/finding type.

It never records the rejected value or an unkeyed value fingerprint. Exit code `0` means clean, `1` means findings and `2` means scanning errors.

For a finding:

1. isolate the affected test/staging artifact or database from normal consumers;
2. revoke/rotate the underlying credential or session through its owning authority;
3. delete or rewrite the affected field using an approved opaque reference or safe descriptor;
4. rerun the scanner and bounded API/image negative tests;
5. record only source/record/path, remediation action and rotation authority—never the value;
6. separately assess downstream logs, exports, backups and caches which may have copied the record.

Repository automation scans committed Portal JSON/JSONL/SQLite fixtures and generated evidence roots and uploads the value-free report. The exact control-plane image receives clean and synthetic-negative scanner probes before merge.

## Consumer requirements

- Never stringify or log an object after rejection.
- Never append the original object to an exception, metric, trace, audit, evidence or support report.
- Persist/publish only objects that passed the reject policy.
- Redact before structured logging/export.
- Use dedicated opaque reference types for safe public identifiers.
- Synthetic canaries are the only secret-like test values.
- Extend this classifier and adversarial corpus for new aliases; do not create a local list.
