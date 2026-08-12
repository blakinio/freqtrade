# PAPER reconciliation producer

This package is the dependency-independent G4 command/reconciliation state-machine producer. It
does not bind to the Runtime Supervisor or Gateway and does not define another RuntimeGeneration
authority. `SupervisorLifecycleObservationPort` is observation-only; `GatewayAuthoritativeReadPort`
is the future source of execution truth. A transport acknowledgement only reaches
`acknowledged_but_unreconciled`.

`InMemorySnapshotStore` is a deterministic test/restart codec, not production persistence. The G4
coordinator must supply one PostgreSQL adapter implementing atomic create and compare-and-swap for
the complete canonical `ReconciliationRecord`, keyed by `(tenant_id, command_id)`, plus an index for
non-terminal retry work. That migration must be added only by the single integration owner after G3
contracts settle; this producer intentionally creates no shared migration chain.

Missing consumers: Supervisor lifecycle observation, Gateway authoritative reads, PostgreSQL
adapter, worker scheduling, API/UI/audit exposure, valuation composition and real runtime E2E.
