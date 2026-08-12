# Evidence Workbench producer

This package evaluates an exact immutable evidence tuple against an explicit policy and emits a
deterministic PAPER eligibility decision. It is fail-closed: missing, stale, invalid, conflicting,
foreign-identity, incomplete, unsupported-realism, or insufficiently-provenanced evidence cannot
produce eligibility.

It is an isolated `partial_producer`. Future work must bind the read-only ports to G4
reconciliation, `PaperExecutionProfile`, Portfolio Risk, RuntimeGeneration/run evidence, durable
persistence, and Portal API/UI consumers. SHADOW remains distinct, LIVE is rejected, and neither AI
suggestions nor this package grant exchange, order, credential, withdrawal, deployment, promotion,
or runtime authority.
