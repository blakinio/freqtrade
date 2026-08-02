# WickHunter candidate paper activation

`ai_platform.wickhunter.candidate_activation` is the fail-closed boundary between an immutable candidate-materialization package and the WH-09 paper-validation request.

The verifier requires the exact package file set, checksum index, manifest self-hash, per-file hashes and sizes, validation-only selection, test-descriptive evidence, model text/hash/artifact identity, selected parameter identity, rollback binding and zero execution authority. Coordinated rewrites of checksums and the manifest do not make semantically altered model or parameter evidence acceptable.

Activation publishes the existing immutable WH-09 `PaperRunRequest` and `PaperValidationPolicy`, then writes a separate candidate binding containing the package and manifest identities. The resulting run is paper/shadow only. Protected-holdout access, automatic promotion, credentials, order adapters, order submission, execution and live capital remain disabled.

Candidate activation is not model promotion and is not authorization for production trading. A completed 24-hour WH-09 evidence package still requires explicit owner review.
