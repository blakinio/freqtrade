from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
from uuid import UUID

import pytest
from fastapi.testclient import TestClient

from ai_platform.portal.contracts.common import CorrelationContext
from ai_platform.portal.contracts.environment import Environment, ExecutionMode
from ai_platform.portal.contracts.identity import ActorType, Permission
from ai_platform.portal.contracts.strategy_closure import (
    CapabilityRequirement,
    ClosureRequestContext,
    PublicContractProvenance,
    SignalWizardFeatureSelection,
    SignalWizardParameterConstraint,
    SignalWizardPreviewCommand,
    SignalWizardSubmitCommand,
    StrategyCapability,
)
from ai_platform.portal.control_plane.api import create_app
from ai_platform.portal.control_plane.context import RequestContext
from ai_platform.portal.control_plane.database import (
    build_engine,
    build_session_factory,
    create_schema,
)
from ai_platform.portal.signal_wizard.models import SignalWizardPreviewRow
from ai_platform.portal.signal_wizard.repository import SignalWizardRepository
from ai_platform.portal.signal_wizard.service import (
    SignalWizardConflictError,
    SignalWizardService,
    SignalWizardValidationError,
)


REQUEST_ID = UUID("20000000-0000-0000-0000-000000000001")
CORRELATION_ID = UUID("20000000-0000-0000-0000-000000000002")
NOW = datetime(2026, 7, 31, 8, 0, tzinfo=UTC)


def _trusted_context(
    *,
    actor_id: str = "analyst-a",
    tenant_id: str = "tenant-a",
) -> RequestContext:
    return RequestContext(
        tenant_id=tenant_id,
        actor_id=actor_id,
        actor_type=ActorType.USER,
        permissions=(Permission.MODEL_READ, Permission.MODEL_TRAIN),
        request_id=REQUEST_ID,
        correlation_id=CORRELATION_ID,
    )


def _command_context(
    *,
    actor_id: str = "analyst-a",
    tenant_id: str = "tenant-a",
    resource_type: str = "strategy",
    resource_id: str = "strategy-a",
    environment: Environment = Environment.RESEARCH,
    execution_mode: ExecutionMode = ExecutionMode.SIMULATED,
) -> ClosureRequestContext:
    return ClosureRequestContext(
        tenant_id=tenant_id,
        actor_id=actor_id,
        actor_type=ActorType.USER,
        resource_type=resource_type,
        resource_id=resource_id,
        environment=environment,
        execution_mode=execution_mode,
        correlation=CorrelationContext(
            request_id=REQUEST_ID,
            correlation_id=CORRELATION_ID,
        ),
        provenance=PublicContractProvenance(
            producer="signal-wizard-semantic-test",
            artifact_id="semantic-artifact",
            created_at=NOW,
            source_refs=("feature-registry:1.0.0",),
        ),
    )


def _capability(value: StrategyCapability) -> CapabilityRequirement:
    return CapabilityRequirement(
        capability=value,
        authorization_decision_ref=f"semantic:{value.value}",
    )


def _preview_command(
    *,
    context: ClosureRequestContext | None = None,
    idempotency_key: str = "preview-semantic-1",
    base_strategy_version: str | None = "strategy-a:v1",
    selections: tuple[SignalWizardFeatureSelection, ...] | None = None,
    constraints: tuple[SignalWizardParameterConstraint, ...] = (),
    condition_feature: str = "atr.v1",
) -> SignalWizardPreviewCommand:
    selected = selections or (
        SignalWizardFeatureSelection(
            feature_id="atr.v1",
            timeframe="5m",
            parameters={"period": 14},
        ),
    )
    return SignalWizardPreviewCommand(
        context=context or _command_context(),
        idempotency_key=idempotency_key,
        strategy_id="strategy-a",
        base_strategy_version=base_strategy_version,
        feature_selections=selected,
        parameter_constraints=constraints,
        condition_ast={"all": [{"feature": condition_feature, "op": "gt", "value": 0}]},
        capability=_capability(StrategyCapability.STRATEGY_RESEARCH),
    )


def _submit_command(
    preview_hash: str,
    expected_version: str,
    *,
    context: ClosureRequestContext | None = None,
    idempotency_key: str = "submit-semantic-1",
) -> SignalWizardSubmitCommand:
    return SignalWizardSubmitCommand(
        context=context or _command_context(),
        idempotency_key=idempotency_key,
        preview_hash=preview_hash,
        experiment_name="Semantic hardening candidate",
        expected_strategy_version=expected_version,
        capability=_capability(StrategyCapability.EXPERIMENT_SUBMIT),
    )


def _service(database_url: str = "sqlite+pysqlite:///:memory:") -> tuple[SignalWizardService, object]:
    engine = build_engine(database_url)
    create_schema(engine)
    factory = build_session_factory(engine)
    return SignalWizardService(factory), factory


def test_disabled_feature_identity_is_validated_and_preserved() -> None:
    service, _factory = _service()
    context = _trusted_context()
    command = _preview_command(
        selections=(
            SignalWizardFeatureSelection(
                feature_id="atr.v1",
                timeframe="5m",
                parameters={"period": 14},
            ),
            SignalWizardFeatureSelection(
                feature_id="rsi.v1",
                timeframe="1h",
                parameters={"period": 21},
                enabled=False,
            ),
        )
    )

    preview = service.preview(context, command)

    assert preview.strategy_definition["features"] == [
        {
            "id": "atr.v1",
            "enabled": True,
            "params": {"period": 14, "ma_type": "rma"},
            "timeframe": "5m",
            "confirmation": "closed_bar",
            "definition_sha256": preview.strategy_definition["features"][0][
                "definition_sha256"
            ],
        },
        {
            "id": "rsi.v1",
            "enabled": False,
            "params": {"period": 21, "ma_type": "rma"},
            "timeframe": "1h",
            "confirmation": "closed_bar",
            "definition_sha256": preview.strategy_definition["features"][1][
                "definition_sha256"
            ],
        },
    ]

    with pytest.raises(SignalWizardValidationError) as rejected:
        service.preview(
            context,
            _preview_command(
                idempotency_key="preview-disabled-unapproved",
                selections=(
                    SignalWizardFeatureSelection(
                        feature_id="atr.v1",
                        timeframe="5m",
                        parameters={"period": 14},
                    ),
                    SignalWizardFeatureSelection(
                        feature_id="squeeze_ratio.v1",
                        timeframe="5m",
                        enabled=False,
                    ),
                ),
            ),
        )
    assert rejected.value.reason_code == "FEATURE_NOT_APPROVED_FOR_AI"


def test_disabled_feature_cannot_satisfy_condition_identity() -> None:
    service, _factory = _service()
    with pytest.raises(SignalWizardValidationError) as rejected:
        service.preview(
            _trusted_context(),
            _preview_command(
                idempotency_key="preview-disabled-condition",
                selections=(
                    SignalWizardFeatureSelection(
                        feature_id="atr.v1",
                        timeframe="5m",
                        parameters={"period": 14},
                    ),
                    SignalWizardFeatureSelection(
                        feature_id="rsi.v1",
                        timeframe="5m",
                        parameters={"period": 14},
                        enabled=False,
                    ),
                ),
                condition_feature="rsi.v1",
            ),
        )
    assert rejected.value.reason_code == "FEATURE_NOT_DECLARED"


def test_preview_derives_new_research_draft_and_removes_fabricated_risk() -> None:
    service, _factory = _service()
    preview = service.preview(_trusted_context(), _preview_command())

    version = preview.strategy_definition["version"]
    assert isinstance(version, str)
    assert version.startswith("strategy-a:wizard:")
    assert version != "strategy-a:v1"
    assert preview.strategy_definition["base_strategy_version"] == "strategy-a:v1"
    assert preview.strategy_definition["lifecycle_state"] == "research_draft"
    assert "risk" not in preview.strategy_definition
    assert preview.strategy_definition["draft_authority"] == {
        "research_only": True,
        "use_closed_bars_only": True,
        "execution_authority": False,
        "promotion_authority": False,
        "live_capital_authority": False,
    }


def test_preview_command_and_result_survive_service_restart(tmp_path: Path) -> None:
    database = tmp_path / "signal-wizard.sqlite"
    database_url = f"sqlite+pysqlite:///{database}"
    first_service, factory = _service(database_url)
    context = _trusted_context()
    command = _preview_command()
    preview = first_service.preview(context, command)

    restarted = SignalWizardService(factory)
    retried = restarted.preview(context, command)
    assert retried == preview

    with factory() as session:
        stored = SignalWizardRepository().get_preview(
            session,
            context.tenant_id,
            preview.preview_hash,
        )
        row = session.get(
            SignalWizardPreviewRow,
            (context.tenant_id, preview.preview_hash),
        )
    assert stored is not None
    stored_result, stored_version, stored_command = stored
    assert stored_result == preview
    assert stored_version == preview.strategy_definition["version"]
    assert stored_command == command
    assert row is not None
    assert row.command_json == command.canonical_json()
    assert row.preview_json == preview.canonical_json()


def test_submit_binds_full_persisted_identity_with_distinct_reason_codes() -> None:
    service, _factory = _service()
    trusted = _trusted_context()
    preview = service.preview(trusted, _preview_command())
    version = str(preview.strategy_definition["version"])

    cases = (
        (
            _command_context(actor_id="analyst-b"),
            _trusted_context(actor_id="analyst-b"),
            "SIGNAL_WIZARD_ACTOR_MISMATCH",
        ),
        (
            _command_context(resource_id="strategy-b"),
            trusted,
            "SIGNAL_WIZARD_TARGET_MISMATCH",
        ),
        (
            _command_context(environment=Environment.TEST),
            trusted,
            "SIGNAL_WIZARD_ENVIRONMENT_MISMATCH",
        ),
        (
            _command_context(execution_mode=ExecutionMode.DRY_RUN),
            trusted,
            "SIGNAL_WIZARD_EXECUTION_MODE_MISMATCH",
        ),
    )
    for index, (command_context, request_context, reason_code) in enumerate(cases):
        with pytest.raises(SignalWizardConflictError) as rejected:
            service.submit(
                request_context,
                _submit_command(
                    preview.preview_hash,
                    version,
                    context=command_context,
                    idempotency_key=f"submit-binding-{index}",
                ),
            )
        assert rejected.value.reason_code == reason_code

    with pytest.raises(SignalWizardConflictError) as version_rejected:
        service.submit(
            trusted,
            _submit_command(
                preview.preview_hash,
                "strategy-a:wizard:wrong",
                idempotency_key="submit-version-mismatch",
            ),
        )
    assert version_rejected.value.reason_code == "SIGNAL_WIZARD_VERSION_MISMATCH"


def test_numeric_constraint_rejects_nonnumeric_parameter() -> None:
    service, _factory = _service()
    with pytest.raises(SignalWizardValidationError) as rejected:
        service.preview(
            _trusted_context(),
            _preview_command(
                idempotency_key="preview-nonnumeric-constraint",
                selections=(
                    SignalWizardFeatureSelection(
                        feature_id="macd.v1",
                        timeframe="5m",
                        parameters={"signal_ma_type": "ema"},
                    ),
                ),
                constraints=(
                    SignalWizardParameterConstraint(
                        parameter="signal_ma_type",
                        minimum=1,
                        reason_code="CUSTOM_NUMERIC_MINIMUM",
                    ),
                ),
                condition_feature="macd.v1",
            ),
        )
    assert rejected.value.reason_code == "PARAMETER_CONSTRAINT_TYPE_INVALID"


def test_router_returns_stable_bounded_conflict_without_raw_input() -> None:
    engine = build_engine("sqlite+pysqlite:///:memory:")
    create_schema(engine)
    factory = build_session_factory(engine)
    context = _trusted_context()
    client = TestClient(create_app(factory, lambda: context))
    command = _preview_command(idempotency_key="router-conflict")

    first = client.post(
        "/v1/signal-wizard/preview",
        json=command.model_dump(mode="json"),
    )
    changed = command.model_copy(update={"strategy_id": "private-endpoint-secret-value"})
    conflict = client.post(
        "/v1/signal-wizard/preview",
        json=changed.model_dump(mode="json"),
    )

    assert first.status_code == 200
    assert conflict.status_code == 409
    assert conflict.json() == {
        "detail": {
            "reason_code": "SIGNAL_WIZARD_PREVIEW_IDEMPOTENCY_CONFLICT",
            "message": "The preview idempotency key is already bound to another request.",
        }
    }
    assert "private-endpoint-secret-value" not in conflict.text


def test_forward_migration_adds_nullable_preview_command_column() -> None:
    migration = Path(
        "ai_platform/portal/signal_wizard/migrations/0002_semantic_hardening.sql"
    ).read_text(encoding="utf-8")
    assert "ALTER TABLE portal_signal_wizard_previews" in migration
    assert "ADD COLUMN command_json TEXT" in migration
    assert "DROP" not in migration.upper()
