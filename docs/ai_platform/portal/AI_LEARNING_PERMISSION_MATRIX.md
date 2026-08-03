# AI Intelligence and Learning Permission Matrix

Status: normative application-service authorization matrix for Portal AI/learning evidence.

## Principles

- Backend application services are authoritative. Routers and frontend capability visibility are consumers, not authorization boundaries.
- Tenant equality is necessary but not sufficient.
- The existing versioned permission vocabulary is sufficient for this bounded remediation: `model.read`, `model.train` and the separately governed `model.promote`.
- Permission checks run before repository lookup or mutation so denied callers cannot enumerate tenant resources.
- Permissions are evaluated from the current trusted `RequestContext` on every call; revocation therefore takes effect on the next request.
- Automatic trade-intelligence production requires a tenant-bound `ActorType.SERVICE` context carrying `model.train`. Browser/user contexts cannot act as the producer.
- Candidate registration creates only bounded learning evidence. It never promotes a model, assigns a bot or activates a runtime.

## Service method policy

| Service method | Required permission | Actor policy | Effect |
|---|---|---|---|
| `TradeIntelligenceService.get_analysis` | `model.read` | Any authenticated actor explicitly granted the permission | Read one tenant analysis |
| `TradeIntelligenceService.list_analyses` | `model.read` | Any authenticated actor explicitly granted the permission | Read tenant analyses/insights |
| `TradeIntelligenceService.record_decision_snapshot` | `model.train` | `ActorType.SERVICE` only | Record trusted decision evidence |
| `TradeIntelligenceService.analyze_outcome` | `model.train` | `ActorType.SERVICE` only | Record trusted outcome/diagnosis/insight evidence |
| `LearningService.history` | `model.read` | Any authenticated actor explicitly granted the permission | Read one tenant learning history |
| `LearningService.history_all` | `model.read` | Any authenticated actor explicitly granted the permission | Read tenant learning history |
| `LearningService.create_hypothesis` | `model.train` | Any authenticated actor explicitly granted the permission | Create a bounded hypothesis from existing evidence |
| `LearningService.record_experiment` | `model.train` | Any authenticated actor explicitly granted the permission | Record a bounded experiment |
| `LearningService.register_candidate` | `model.train` | Any authenticated actor explicitly granted the permission | Register a non-promoted, unassigned L4 candidate |

## Built-in role outcome

The canonical built-in role mapping remains in `ai_platform/portal/security/authorization.py`.

| Role | AI/learning reads | Bounded learning writes | Automatic trade-intelligence producer |
|---|---|---|---|
| `user` | allowed (`model.read`) | denied | denied: not a service actor |
| `trader` | allowed (`model.read`) | denied | denied: not a service actor |
| `analyst` | allowed (`model.read`) | allowed (`model.train`) | denied: not a service actor |
| `model_reviewer` | allowed (`model.read`) | denied unless separately granted `model.train` | denied: not a service actor |
| `admin` | allowed | allowed | denied for browser/user context; a distinct trusted service identity is required |
| `service` | denied by default because the built-in role has only `bot.read` | denied by default | allowed only when a dedicated current service membership is explicitly granted `model.train` |
| custom membership | exactly its current explicit permissions | exactly its current explicit permissions | only `ActorType.SERVICE` plus `model.train` |

## Separation from promotion and runtime activation

`model.train` does not grant `model.promote`. Candidate registration persists `promoted=false` and `assigned_to_bot=false`. Model promotion, bot assignment, strategy activation, private runtime composition and live-capital authority remain separate guarded workflows and are not introduced by this matrix.

## Audit and capability consumers

Denied calls use the existing stable `PermissionDeniedError` boundary and disclose no record existence. The future canonical denied-event writer is owned by Issue #1111; this remediation must not create a competing audit authority. Frontend navigation/action projection is owned by Issue #1117 and must mirror, never replace, this backend matrix.
