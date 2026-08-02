from __future__ import annotations

import hashlib
import json
import os
import shutil
import tempfile
from collections.abc import Sequence
from dataclasses import dataclass, replace
from pathlib import Path
from typing import Any

from ai_platform.wickhunter.candidate_runtime_binding import CandidatePaperRuntimeBinding
from ai_platform.wickhunter.canonical import canonical_json, canonical_sha256
from ai_platform.wickhunter.contracts import ShadowDecisionEvidence
from ai_platform.wickhunter.paper_validation import (
    PaperObservation,
    PaperValidationError,
    PaperValidationOutcome,
    PaperValidationResult,
    SafetyExerciseEvidence,
    _exercise_from_payload,
    _observation_from_payload,
    _parity_from_payload,
    evaluate_paper_observations,
    observation_from_snapshot,
    publish_paper_observation_package,
)
from ai_platform.wickhunter.shadow_runtime import (
    ReplayShadowParityEvidence,
    ShadowRuntime,
    ShadowRuntimeError,
    ShadowRuntimePolicy,
    ShadowRuntimeState,
    ShadowRuntimeStepResult,
    ShadowRuntimeStore,
    ShadowRuntimeTick,
)


JOURNAL_SCHEMA_VERSION = "wickhunter-candidate-paper-runtime-journal-v1"
GENERATION_SCHEMA_VERSION = "wickhunter-candidate-paper-runtime-generation-v1"
POINTER_SCHEMA_VERSION = "wickhunter-candidate-paper-runtime-pointer-v1"
IDENTITY_NAME = "identity.json"
POINTER_NAME = "active-generation.json"
GENERATIONS_DIR = "generations"
PARITY_DIR = "parity"
EXERCISES_DIR = "exercises"
OBSERVATION_NAME = "paper-observation.json"
DECISIONS_NAME = "shadow-decisions.jsonl"
MANIFEST_NAME = "manifest.json"
CHECKSUM_NAME = "artifact-sha256.txt"
RUNTIME_DIR = "runtime"


class CandidatePaperRuntimeServiceError(RuntimeError):
    """Raised when candidate PAPER evidence cannot be persisted or recovered safely."""


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _read_json(path: Path, *, field: str) -> dict[str, Any]:
    if path.is_symlink() or not path.is_file():
        raise CandidatePaperRuntimeServiceError(f"{field} must be a regular file")
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise CandidatePaperRuntimeServiceError(f"unable to read {field}") from exc
    if not isinstance(payload, dict):
        raise CandidatePaperRuntimeServiceError(f"{field} must contain an object")
    return payload


def _write_new(path: Path, content: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists() or path.is_symlink():
        raise CandidatePaperRuntimeServiceError(f"refusing to overwrite {path}")
    with path.open("xb") as handle:
        handle.write(content)
        handle.flush()
        os.fsync(handle.fileno())


def _write_json_new(path: Path, payload: object) -> None:
    _write_new(path, canonical_json(payload).encode("utf-8") + b"\n")


def _atomic_json(path: Path, payload: object) -> None:
    if path.is_symlink():
        raise CandidatePaperRuntimeServiceError("atomic destination cannot be a symlink")
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(
        prefix=f".{path.name}.",
        suffix=".tmp",
        dir=path.parent,
    )
    temporary = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
            handle.write(canonical_json(payload) + "\n")
            handle.flush()
            os.fsync(handle.fileno())
        temporary.replace(path)
    except Exception:
        temporary.unlink(missing_ok=True)
        raise


def _self_hashed(schema_version: str, payload: dict[str, object], field: str) -> dict[str, object]:
    value: dict[str, object] = {"schema_version": schema_version, **payload}
    value[field] = canonical_sha256({"schema_version": schema_version, "payload": payload})
    return value


def _verify_self_hash(
    payload: dict[str, Any],
    *,
    schema_version: str,
    field: str,
    label: str,
) -> None:
    if payload.get("schema_version") != schema_version:
        raise CandidatePaperRuntimeServiceError(f"{label} schema mismatch")
    claimed = payload.get(field)
    body = {key: value for key, value in payload.items() if key not in {"schema_version", field}}
    expected = canonical_sha256({"schema_version": schema_version, "payload": body})
    if claimed != expected:
        raise CandidatePaperRuntimeServiceError(f"{label} self-hash mismatch")


def _assert_zero_authority(payload: dict[str, Any], *, field: str) -> None:
    unsafe = (
        payload.get("protected_holdout_accessed") is not False
        or payload.get("automatic_promotion_enabled") is not False
        or payload.get("trading_credentials_present") is not False
        or payload.get("order_adapter_present") is not False
        or payload.get("execution_enabled") is not False
        or payload.get("live_capital_authorized") is not False
        or payload.get("orders_submitted") != 0
    )
    if unsafe:
        raise CandidatePaperRuntimeServiceError(f"{field} contains forbidden authority")


def _write_jsonl(path: Path, values: Sequence[object]) -> None:
    content = b"".join(canonical_json(value).encode("utf-8") + b"\n" for value in values)
    _write_new(path, content)


def _read_jsonl(path: Path, *, field: str) -> tuple[dict[str, Any], ...]:
    if path.is_symlink() or not path.is_file():
        raise CandidatePaperRuntimeServiceError(f"{field} must be a regular file")
    rows: list[dict[str, Any]] = []
    try:
        for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            payload = json.loads(line)
            if not isinstance(payload, dict):
                raise CandidatePaperRuntimeServiceError(
                    f"{field} row {line_number} must contain an object"
                )
            rows.append(payload)
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise CandidatePaperRuntimeServiceError(f"unable to read {field}") from exc
    return tuple(rows)


def _decision_ids(decisions: Sequence[ShadowDecisionEvidence]) -> tuple[str, ...]:
    values = tuple(sorted(item.shadow_decision_id for item in decisions))
    if len(values) != len(set(values)):
        raise CandidatePaperRuntimeServiceError("runtime result contains duplicate decisions")
    return values


@dataclass(frozen=True, slots=True)
class CandidatePaperRuntimeJournal:
    root: Path
    binding: CandidatePaperRuntimeBinding

    def __post_init__(self) -> None:
        if not self.root.is_absolute():
            raise CandidatePaperRuntimeServiceError("journal root must be absolute")
        if self.root.is_symlink():
            raise CandidatePaperRuntimeServiceError("journal root cannot be a symlink")
        self.root.mkdir(parents=True, exist_ok=True)
        for name in (GENERATIONS_DIR, PARITY_DIR, EXERCISES_DIR):
            directory = self.root / name
            if directory.is_symlink():
                raise CandidatePaperRuntimeServiceError("journal directory cannot be a symlink")
            directory.mkdir(exist_ok=True)
        self._write_or_verify_identity()

    def _identity_payload(self) -> dict[str, object]:
        return {
            "binding_id": self.binding.binding_id,
            "run_id": self.binding.request.run_id,
            "candidate_package_id": self.binding.identity.package_id,
            "candidate_manifest_sha256": self.binding.identity.manifest_sha256,
            "model_hash": self.binding.request.model_hash,
            "parameter_hash": self.binding.request.parameter_hash,
            "rollback_model_hash": self.binding.request.rollback_model_hash,
            "rollback_parameter_hash": self.binding.request.rollback_parameter_hash,
            "dataset_hash": self.binding.request.dataset_hash,
            "code_sha": self.binding.request.code_sha,
            "policy_sha256": self.binding.policy.policy_sha256,
            "protected_holdout_accessed": False,
            "automatic_promotion_enabled": False,
            "trading_credentials_present": False,
            "order_adapter_present": False,
            "execution_enabled": False,
            "orders_submitted": 0,
            "live_capital_authorized": False,
        }

    def _write_or_verify_identity(self) -> None:
        path = self.root / IDENTITY_NAME
        expected = _self_hashed(
            JOURNAL_SCHEMA_VERSION,
            self._identity_payload(),
            "identity_sha256",
        )
        if path.exists() or path.is_symlink():
            actual = _read_json(path, field="journal identity")
            _verify_self_hash(
                actual,
                schema_version=JOURNAL_SCHEMA_VERSION,
                field="identity_sha256",
                label="journal identity",
            )
            _assert_zero_authority(actual, field="journal identity")
            if actual != expected:
                raise CandidatePaperRuntimeServiceError("journal identity does not match binding")
            return
        _write_json_new(path, expected)

    def _generation_paths(self) -> tuple[Path, ...]:
        generations = self.root / GENERATIONS_DIR
        paths = tuple(
            sorted(
                (
                    path
                    for path in generations.iterdir()
                    if path.is_dir() and not path.is_symlink() and path.name.isdigit()
                ),
                key=lambda path: int(path.name),
            )
        )
        expected = list(range(1, len(paths) + 1))
        actual = [int(path.name) for path in paths]
        if actual != expected:
            raise CandidatePaperRuntimeServiceError("journal generations are not contiguous")
        return paths

    def _artifact_paths(self, generation_root: Path) -> tuple[str, ...]:
        return (
            f"{RUNTIME_DIR}/state.json",
            f"{RUNTIME_DIR}/portal-observability-snapshot.json",
            OBSERVATION_NAME,
            DECISIONS_NAME,
        )

    def _verify_generation(
        self,
        generation_root: Path,
    ) -> tuple[ShadowRuntimeState, PaperObservation, tuple[str, ...], str]:
        expected_entries = {
            RUNTIME_DIR,
            OBSERVATION_NAME,
            DECISIONS_NAME,
            MANIFEST_NAME,
            CHECKSUM_NAME,
        }
        if {item.name for item in generation_root.iterdir()} != expected_entries:
            raise CandidatePaperRuntimeServiceError("generation file set mismatch")
        runtime_root = generation_root / RUNTIME_DIR
        if runtime_root.is_symlink() or not runtime_root.is_dir():
            raise CandidatePaperRuntimeServiceError("generation runtime root is invalid")
        manifest = _read_json(generation_root / MANIFEST_NAME, field="generation manifest")
        _verify_self_hash(
            manifest,
            schema_version=GENERATION_SCHEMA_VERSION,
            field="manifest_sha256",
            label="generation manifest",
        )
        _assert_zero_authority(manifest, field="generation manifest")
        generation = int(generation_root.name)
        if manifest.get("generation") != generation:
            raise CandidatePaperRuntimeServiceError("generation identity mismatch")
        if manifest.get("binding_id") != self.binding.binding_id:
            raise CandidatePaperRuntimeServiceError("generation binding mismatch")
        if manifest.get("run_id") != self.binding.request.run_id:
            raise CandidatePaperRuntimeServiceError("generation run mismatch")

        index_path = generation_root / CHECKSUM_NAME
        entries: dict[str, str] = {}
        for line in index_path.read_text(encoding="utf-8").splitlines():
            digest, separator, name = line.partition("  ")
            if not separator or name in entries:
                raise CandidatePaperRuntimeServiceError("generation checksum index is malformed")
            entries[name] = digest
        expected_artifacts = {*self._artifact_paths(generation_root), MANIFEST_NAME}
        if set(entries) != expected_artifacts:
            raise CandidatePaperRuntimeServiceError("generation checksum file set mismatch")
        for name, digest in entries.items():
            path = generation_root / name
            if path.is_symlink() or not path.is_file() or _sha256_file(path) != digest:
                raise CandidatePaperRuntimeServiceError(f"generation checksum mismatch: {name}")

        state = ShadowRuntimeStore(runtime_root).load()
        if state is None or state.generation != generation:
            raise CandidatePaperRuntimeServiceError("generation runtime state is missing")
        if manifest.get("runtime_state_sha256") != state.state_sha256:
            raise CandidatePaperRuntimeServiceError("generation runtime state identity mismatch")
        observation_payload = _read_json(
            generation_root / OBSERVATION_NAME,
            field="paper observation",
        )
        try:
            observation = _observation_from_payload(observation_payload)
        except PaperValidationError as exc:
            raise CandidatePaperRuntimeServiceError("paper observation is invalid") from exc
        if observation.snapshot_id != manifest.get("snapshot_id"):
            raise CandidatePaperRuntimeServiceError("generation snapshot identity mismatch")
        decision_payloads = _read_jsonl(
            generation_root / DECISIONS_NAME,
            field="shadow decisions",
        )
        decision_ids = tuple(sorted(str(item.get("shadow_decision_id", "")) for item in decision_payloads))
        if not decision_ids or len(decision_ids) != len(set(decision_ids)):
            raise CandidatePaperRuntimeServiceError("generation decision identities are invalid")
        if list(decision_ids) != manifest.get("decision_ids"):
            raise CandidatePaperRuntimeServiceError("generation decision manifest mismatch")
        return state, observation, decision_ids, str(manifest["manifest_sha256"])

    def latest_state(self) -> ShadowRuntimeState | None:
        paths = self._generation_paths()
        if not paths:
            return None
        latest_state: ShadowRuntimeState | None = None
        latest_observation: PaperObservation | None = None
        latest_manifest = ""
        for path in paths:
            latest_state, latest_observation, _decision_ids_value, latest_manifest = (
                self._verify_generation(path)
            )
        if latest_state is None or latest_observation is None:
            raise CandidatePaperRuntimeServiceError("latest generation is unavailable")
        self._write_pointer(
            generation=latest_state.generation,
            manifest_sha256=latest_manifest,
            runtime_state_sha256=latest_state.state_sha256,
            snapshot_id=latest_observation.snapshot_id,
        )
        return latest_state

    def _write_pointer(
        self,
        *,
        generation: int,
        manifest_sha256: str,
        runtime_state_sha256: str,
        snapshot_id: str,
    ) -> None:
        payload = _self_hashed(
            POINTER_SCHEMA_VERSION,
            {
                "generation": generation,
                "generation_directory": f"{generation:020d}",
                "manifest_sha256": manifest_sha256,
                "runtime_state_sha256": runtime_state_sha256,
                "snapshot_id": snapshot_id,
                "binding_id": self.binding.binding_id,
                "run_id": self.binding.request.run_id,
                "protected_holdout_accessed": False,
                "automatic_promotion_enabled": False,
                "trading_credentials_present": False,
                "order_adapter_present": False,
                "execution_enabled": False,
                "orders_submitted": 0,
                "live_capital_authorized": False,
            },
            "pointer_sha256",
        )
        _atomic_json(self.root / POINTER_NAME, payload)

    def commit(self, result: ShadowRuntimeStepResult) -> PaperObservation:
        generation = result.state.generation
        if generation < 1:
            raise CandidatePaperRuntimeServiceError("runtime generation must be positive")
        previous = self._generation_paths()
        if generation != len(previous) + 1:
            raise CandidatePaperRuntimeServiceError("runtime generation is not the next journal entry")
        observation = observation_from_snapshot(result.snapshot)
        observation_ids = tuple(
            sorted(
                (
                    *observation.allowed_decision_ids,
                    *observation.risk_rejection_decision_ids,
                    *observation.ignored_decision_ids,
                )
            )
        )
        decision_ids = _decision_ids(result.decisions)
        if observation_ids != decision_ids:
            raise CandidatePaperRuntimeServiceError(
                "snapshot decision summaries do not match runtime evidence"
            )
        generations = self.root / GENERATIONS_DIR
        destination = generations / f"{generation:020d}"
        temporary = Path(tempfile.mkdtemp(prefix=f".{generation:020d}.", dir=generations))
        try:
            runtime_root = temporary / RUNTIME_DIR
            ShadowRuntimeStore(runtime_root).save(result.state, result.snapshot)
            _write_json_new(temporary / OBSERVATION_NAME, observation)
            _write_jsonl(temporary / DECISIONS_NAME, result.decisions)
            artifact_names = self._artifact_paths(temporary)
            artifacts = tuple(
                (name, _sha256_file(temporary / name)) for name in artifact_names
            )
            previous_manifest = (
                None
                if not previous
                else self._verify_generation(previous[-1])[3]
            )
            manifest = _self_hashed(
                GENERATION_SCHEMA_VERSION,
                {
                    "generation": generation,
                    "previous_manifest_sha256": previous_manifest,
                    "binding_id": self.binding.binding_id,
                    "run_id": self.binding.request.run_id,
                    "runtime_state_sha256": result.state.state_sha256,
                    "snapshot_id": observation.snapshot_id,
                    "observation_sha256": canonical_sha256(observation),
                    "decision_ids": list(decision_ids),
                    "artifacts": [list(item) for item in artifacts],
                    "protected_holdout_accessed": False,
                    "automatic_promotion_enabled": False,
                    "trading_credentials_present": False,
                    "order_adapter_present": False,
                    "execution_enabled": False,
                    "orders_submitted": 0,
                    "live_capital_authorized": False,
                },
                "manifest_sha256",
            )
            _write_json_new(temporary / MANIFEST_NAME, manifest)
            checksum_names = (*artifact_names, MANIFEST_NAME)
            _write_new(
                temporary / CHECKSUM_NAME,
                "".join(
                    f"{_sha256_file(temporary / name)}  {name}\n" for name in checksum_names
                ).encode("utf-8"),
            )
            if destination.exists() or destination.is_symlink():
                raise CandidatePaperRuntimeServiceError("journal generation already exists")
            temporary.replace(destination)
        except Exception:
            shutil.rmtree(temporary, ignore_errors=True)
            raise
        self._verify_generation(destination)
        self._write_pointer(
            generation=generation,
            manifest_sha256=str(manifest["manifest_sha256"]),
            runtime_state_sha256=result.state.state_sha256,
            snapshot_id=observation.snapshot_id,
        )
        return observation

    def observations(self) -> tuple[PaperObservation, ...]:
        return tuple(self._verify_generation(path)[1] for path in self._generation_paths())

    def _write_idempotent_record(self, path: Path, value: object, *, field: str) -> None:
        content = canonical_json(value) + "\n"
        if path.exists() or path.is_symlink():
            if path.is_symlink() or not path.is_file():
                raise CandidatePaperRuntimeServiceError(f"{field} path is invalid")
            if path.read_text(encoding="utf-8") != content:
                raise CandidatePaperRuntimeServiceError(f"{field} identity collision")
            return
        _write_new(path, content.encode("utf-8"))

    def record_parity(self, evidence: ReplayShadowParityEvidence) -> None:
        allowed_ids = {
            decision_id
            for observation in self.observations()
            for decision_id in observation.allowed_decision_ids
        }
        if evidence.shadow_decision_id not in allowed_ids:
            raise CandidatePaperRuntimeServiceError("parity does not bind a journaled allowed decision")
        if (
            evidence.dataset_hash != self.binding.request.dataset_hash
            or evidence.code_sha != self.binding.request.code_sha
        ):
            raise CandidatePaperRuntimeServiceError("parity identity does not match activation")
        self._write_idempotent_record(
            self.root / PARITY_DIR / f"{evidence.parity_id}.json",
            evidence,
            field="parity",
        )

    def record_exercise(self, evidence: SafetyExerciseEvidence) -> None:
        snapshot_ids = {item.snapshot_id for item in self.observations()}
        if evidence.run_id != self.binding.request.run_id:
            raise CandidatePaperRuntimeServiceError("exercise run identity mismatch")
        if evidence.source_snapshot_id not in snapshot_ids:
            raise CandidatePaperRuntimeServiceError("exercise snapshot is not journaled")
        self._write_idempotent_record(
            self.root / EXERCISES_DIR / f"{evidence.exercise_id}.json",
            evidence,
            field="safety exercise",
        )

    def parity_evidence(self) -> tuple[ReplayShadowParityEvidence, ...]:
        values: list[ReplayShadowParityEvidence] = []
        for path in sorted((self.root / PARITY_DIR).glob("*.json")):
            try:
                values.append(_parity_from_payload(_read_json(path, field="parity")))
            except PaperValidationError as exc:
                raise CandidatePaperRuntimeServiceError("journal parity is invalid") from exc
        return tuple(values)

    def safety_exercises(self) -> tuple[SafetyExerciseEvidence, ...]:
        values: list[SafetyExerciseEvidence] = []
        for path in sorted((self.root / EXERCISES_DIR).glob("*.json")):
            try:
                values.append(_exercise_from_payload(_read_json(path, field="exercise")))
            except PaperValidationError as exc:
                raise CandidatePaperRuntimeServiceError("journal exercise is invalid") from exc
        return tuple(values)

    def evaluate(self) -> PaperValidationResult:
        return evaluate_paper_observations(
            request=self.binding.request,
            policy=self.binding.policy,
            observations=self.observations(),
            parity_evidence=self.parity_evidence(),
            safety_exercises=self.safety_exercises(),
        )

    def finalize(self, destination: Path, *, finalized_at_ms: int) -> PaperValidationResult:
        if finalized_at_ms < self.binding.request.window_end_ms:
            raise CandidatePaperRuntimeServiceError("paper window has not elapsed")
        result = self.evaluate()
        if result.report.outcome is not PaperValidationOutcome.READY_FOR_OWNER_REVIEW:
            blockers = ",".join(result.report.blocker_codes)
            raise CandidatePaperRuntimeServiceError(
                f"paper evidence is not ready for owner review: {blockers}"
            )
        return publish_paper_observation_package(
            destination,
            request=self.binding.request,
            policy=self.binding.policy,
            observations=result.observations,
            parity_evidence=self.parity_evidence(),
            safety_exercises=self.safety_exercises(),
        )


class CandidatePaperRuntimeService:
    def __init__(
        self,
        *,
        binding: CandidatePaperRuntimeBinding,
        runtime_policy: ShadowRuntimePolicy,
        journal_root: Path,
    ) -> None:
        if runtime_policy.maximum_drawdown_ratio > binding.policy.maximum_drawdown_ratio:
            raise CandidatePaperRuntimeServiceError(
                "runtime drawdown policy is weaker than paper validation policy"
            )
        self.binding = binding
        self.journal = CandidatePaperRuntimeJournal(journal_root, binding)
        self.runtime = ShadowRuntime(
            bot_instance=binding.request.bot_instance,
            mode=binding.request.mode,
            policy=runtime_policy,
            store=None,
        )
        recovered = self.journal.latest_state()
        if recovered is None:
            self.runtime.state = replace(
                self.runtime.state,
                model_version=binding.request.model_version,
                model_hash=binding.request.model_hash,
                parameter_version=binding.request.parameter_version,
                parameter_hash=binding.request.parameter_hash,
                dataset_hash=binding.request.dataset_hash,
                code_sha=binding.request.code_sha,
            )
        else:
            expected = (
                binding.request.model_version,
                binding.request.model_hash,
                binding.request.parameter_version,
                binding.request.parameter_hash,
                binding.request.dataset_hash,
                binding.request.code_sha,
            )
            actual = (
                recovered.model_version,
                recovered.model_hash,
                recovered.parameter_version,
                recovered.parameter_hash,
                recovered.dataset_hash,
                recovered.code_sha,
            )
            if actual != expected:
                raise CandidatePaperRuntimeServiceError(
                    "recovered runtime identity does not match activation"
                )
            self.runtime.state = recovered

    def step(self, tick: ShadowRuntimeTick) -> ShadowRuntimeStepResult:
        request = self.binding.request
        if not request.window_start_ms <= tick.observed_at_ms < request.window_end_ms:
            raise CandidatePaperRuntimeServiceError("runtime tick is outside activation window")
        bound_tick = replace(
            tick,
            decision_requests=tuple(
                self.binding.bind_request(item) for item in tick.decision_requests
            ),
        )
        previous_state = self.runtime.state
        try:
            result = self.runtime.step(bound_tick)
            self.journal.commit(result)
        except (ShadowRuntimeError, PaperValidationError, OSError, ValueError) as exc:
            self.runtime.state = previous_state
            if isinstance(exc, CandidatePaperRuntimeServiceError):
                raise
            raise CandidatePaperRuntimeServiceError("candidate PAPER runtime step failed") from exc
        except Exception:
            self.runtime.state = previous_state
            raise
        return result
