# Sensitive Data Classification

Status: normative server-side classification and traversal contract for Portal metadata, audit/event payloads and observability redaction.

## Authority

`ai_platform/portal/security/sensitive_data.py` is the sole normalized sensitive-field classifier. Consumers must call it directly or through the stable wrappers in `contracts/payloads.py` and `observability/redaction.py`. No consumer may maintain a competing alias list.

## Normalization

Field names are split across acronym, camel-case and non-alphanumeric boundaries, then case-folded. Examples such as `API-Key`, `api_key`, `apiKey` and `apikey` classify identically. Classification uses complete normalized tokens and explicit compound aliases rather than broad substring matching.

Protected concepts include:

- secret and credential values;
- token, cookie and authorization values;
- API keys and API secrets;
- private keys, passwords and passphrases;
- client secrets and refresh tokens;
- secret references and Vault references.

A narrow metadata-only suffix allowlist prevents documented false positives such as `cookie_policy`, `authorization_status`, `token_count` and `api_key_name`. Unrelated words such as `monkey`, `tokenizer` and `secretary` are not sensitive aliases. An authorization header, secret reference or Vault reference remains sensitive.

## Reject policy

Audit and domain-event contracts call `reject_sensitive_payload_keys()` before downstream persistence or publication. The traversal:

- rejects a sensitive field before inspecting its value;
- supports string-keyed mappings and bounded non-text sequences;
- detects direct and indirect container cycles;
- rejects non-string mapping keys and unsupported containers;
- enforces depth and aggregate-item limits;
- reports only the field path and classification, never the protected value.

All Portal contract models hide raw input values in validation error text so rejected metadata cannot be copied into logs or responses through Pydantic diagnostics.

## Redact policy

Observability calls the same classifier through `redact_sensitive()`. Redaction creates a sanitized copy and replaces an entire sensitive subtree with `[REDACTED]` before evaluating or traversing it. Safe-field cycles, unsupported structures and traversal-limit violations fail closed instead of returning an unsafe partial object.

## Consumer requirements

- Never stringify or log an object after rejection.
- Never catch a sensitive-data exception and append the original object to diagnostics.
- Persist and publish only objects that passed the reject policy.
- Redact before structured logging or support export.
- Synthetic canaries are the only secret-like values permitted in tests.
- New alias families must extend the canonical classifier and adversarial corpus, not a local consumer list.
