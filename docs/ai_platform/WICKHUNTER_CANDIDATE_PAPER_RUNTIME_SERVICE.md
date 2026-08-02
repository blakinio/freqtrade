# WickHunter candidate PAPER runtime service

The service binds one independently verified candidate package and one immutable WH-09 activation request to the existing WH-07 `ShadowRuntime`.

Each runtime step is committed as a new no-overwrite generation containing the verified runtime state, portal snapshot, canonical `PaperObservation`, full shadow decision evidence, a self-hashed manifest, and a complete checksum index. Recovery scans and verifies the contiguous generation chain before resuming. A stale pointer is repaired from the latest complete generation; incomplete temporary directories are never treated as evidence.

The journal records replay/shadow parity and safety exercises as separate immutable identity-addressed records. WH-09 finalization is refused before the prospective activation window elapses or while any policy blocker remains.

The candidate model, selected parameters, rollback identities, dataset, code SHA, runtime policy, activation policy, bot instance, and PAPER/SHADOW mode remain frozen in the journal identity. Candidate authorization is applied only through the reviewed runtime binding. Credentials, order adapters, execution, orders, automatic promotion, protected-holdout access, and live capital remain absent; `orders_submitted=0`.
