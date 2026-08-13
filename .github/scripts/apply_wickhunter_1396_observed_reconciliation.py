from __future__ import annotations

from pathlib import Path


path = Path("ai_platform/portal/control_plane/runtime_adoption.py")
text = path.read_text(encoding="utf-8")

old = """    \"\"\"Trusted system reconciliation for a runtime that already exists outside Portal.

    This service never creates, starts, stops, restarts or replaces a runtime. It only
    converges a canonical desired RuntimeGeneration to observed after exact immutable
    identity evidence is supplied by the host-side reconciler.
    \"\"\""""
new = """    \"\"\"Trusted reconciliation for a runtime that already exists outside Portal.

    This service never creates, starts, stops or restarts a runtime. The trusted host-side
    reconciler owns those effects. Portal may move the observed pointer from the currently
    observed generation to the canonical desired generation only when an exact canonical
    rollout links those generations and fresh immutable runtime identity evidence matches
    the desired generation. This preserves RuntimeGeneration as the sole authority while
    allowing an externally managed generation replacement to reconcile truthfully.
    \"\"\""""
if text.count(old) != 1:
    raise SystemExit("runtime adoption docstring anchor mismatch")
text = text.replace(old, new, 1)

old = """            if (
                bot.observed_runtime_generation_id is not None
                and bot.observed_runtime_generation_id != observation.generation_id
            ):
                raise ControlPlaneConflictError(
                    \"bot is already bound to a different observed RuntimeGeneration\"
                )
            generation = self._repository.get_runtime_generation("""
new = """            previous_observed_generation_id = bot.observed_runtime_generation_id
            generation = self._repository.get_runtime_generation("""
if text.count(old) != 1:
    raise SystemExit("observed-generation rejection anchor mismatch")
text = text.replace(old, new, 1)

old = """            if rollout is None:
                raise ControlPlaneConflictError(
                    \"external runtime adoption requires a canonical rollout\"
                )
            if rollout.status == \"SUCCEEDED\":
                if rollout.reason_code != EXTERNAL_ADOPTION_REASON:
                    raise ControlPlaneConflictError(
                        \"successful rollout was not established by external adoption\"
                    )
            elif rollout.status not in _PENDING_ADOPTION_ROLLOUT_STATES:
                raise ControlPlaneConflictError(
                    \"rollout state does not permit external runtime adoption\"
                )
"""
new = """            if rollout is None:
                raise ControlPlaneConflictError(
                    \"external runtime adoption requires a canonical rollout\"
                )
            replacing_observed_generation = (
                previous_observed_generation_id is not None
                and previous_observed_generation_id != generation.generation_id
            )
            if replacing_observed_generation:
                if rollout.from_generation_id != previous_observed_generation_id:
                    raise ControlPlaneConflictError(
                        \"external runtime replacement rollout does not start from \"
                        \"the current observed generation\"
                    )
                previous_generation = self._repository.get_runtime_generation(
                    session,
                    context.tenant_id,
                    previous_observed_generation_id,
                )
                if previous_generation is None or previous_generation.bot_id != bot_id:
                    raise ControlPlaneConflictError(
                        \"current observed RuntimeGeneration does not belong to bot\"
                    )
            if rollout.status == \"SUCCEEDED\":
                if replacing_observed_generation:
                    raise ControlPlaneConflictError(
                        \"successful rollout cannot replace a different current observed generation\"
                    )
                if rollout.reason_code != EXTERNAL_ADOPTION_REASON:
                    raise ControlPlaneConflictError(
                        \"successful rollout was not established by external adoption\"
                    )
            elif rollout.status not in _PENDING_ADOPTION_ROLLOUT_STATES:
                raise ControlPlaneConflictError(
                    \"rollout state does not permit external runtime adoption\"
                )
"""
if text.count(old) != 1:
    raise SystemExit("rollout validation anchor mismatch")
text = text.replace(old, new, 1)

old = """                    details={
                        \"generation_id\": generation.generation_id,
                        \"runtime_instance_id\": observation.runtime_instance_id,
                        \"observation_id\": observation.observation_id,
                        \"evidence_hash\": observation.evidence_hash,
                        \"provenance\": EXTERNAL_ADOPTION_REASON,
                    },
"""
new = """                    details={
                        \"generation_id\": generation.generation_id,
                        \"runtime_instance_id\": observation.runtime_instance_id,
                        \"observation_id\": observation.observation_id,
                        \"evidence_hash\": observation.evidence_hash,
                        \"provenance\": EXTERNAL_ADOPTION_REASON,
                        **(
                            {\"previous_generation_id\": previous_observed_generation_id}
                            if replacing_observed_generation
                            else {}
                        ),
                    },
"""
if text.count(old) != 1:
    raise SystemExit("audit detail anchor mismatch")
path.write_text(text.replace(old, new, 1), encoding="utf-8")
