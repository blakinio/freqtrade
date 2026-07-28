from ai_platform.portal.contracts.bot_management.commands import LifecycleAction, PositionAction
from ai_platform.portal.contracts.bot_management.policies import SignalAuthority, SignalCommand
from ai_platform.portal.signal_control.schema import (
    SIGNAL_PAYLOAD_SCHEMA_V1,
    MappedCommandVocabulary,
    SignalMappingStatus,
    SignalProcessingMode,
)
from tests.ai_platform.portal.signal_control.support import (
    context,
    endpoint_request,
    processing_request,
    service_with_endpoint,
    target,
)


def test_advisory_signal_never_creates_or_executes_command() -> None:
    service, _ = service_with_endpoint(authority=SignalAuthority.ADVISORY_ONLY)
    result = service.process(context(), processing_request(), signature=b"x", target=target())
    assert result.mapping.status == SignalMappingStatus.ADVISORY_RECORDED
    assert result.command_intent is None
    assert result.execution_performed is False


def test_execution_authorized_signal_creates_intent_only() -> None:
    service, _ = service_with_endpoint(authority=SignalAuthority.EXECUTION_AUTHORIZED)
    result = service.process(context(), processing_request(), signature=b"x", target=target())
    assert result.mapping.status == SignalMappingStatus.COMMAND_INTENT_CREATED
    assert result.command_intent is not None
    assert result.command_intent.execution_performed is False
    assert result.command_intent.requires_risk_approval is True


def test_open_and_dca_map_to_bm00_trade_intent_vocabulary() -> None:
    for command in (SignalCommand.OPEN, SignalCommand.DCA):
        service, _ = service_with_endpoint(authority=SignalAuthority.EXECUTION_AUTHORIZED)
        result = service.process(
            context(), processing_request(command), signature=b"x", target=target()
        )
        assert result.command_intent is not None
        assert result.command_intent.vocabulary == MappedCommandVocabulary.BM00_SIGNAL
        assert result.command_intent.action == command.value


def test_close_and_take_profit_map_to_bm03_position_vocabulary() -> None:
    expected = {
        SignalCommand.CLOSE_POSITION: PositionAction.CLOSE_POSITION.value,
        SignalCommand.TAKE_PROFIT: PositionAction.FORCE_TAKE_PROFIT.value,
    }
    for command, action in expected.items():
        service, _ = service_with_endpoint(authority=SignalAuthority.EXECUTION_AUTHORIZED)
        result = service.process(
            context(), processing_request(command), signature=b"x", target=target()
        )
        assert result.command_intent is not None
        assert result.command_intent.vocabulary == MappedCommandVocabulary.BM03_POSITION
        assert result.command_intent.action == action


def test_close_all_maps_to_bm03_position_close_all() -> None:
    service, _ = service_with_endpoint(authority=SignalAuthority.EXECUTION_AUTHORIZED)
    result = service.process(
        context(), processing_request(SignalCommand.CLOSE_ALL), signature=b"x", target=target()
    )
    assert result.command_intent is not None
    assert result.command_intent.action == PositionAction.CLOSE_ALL.value


def test_enable_pause_and_stop_map_to_bm03_lifecycle_actions() -> None:
    expected = {
        SignalCommand.ENABLE_BOT: LifecycleAction.START.value,
        SignalCommand.PAUSE_BOT: LifecycleAction.PAUSE_NEW_ENTRIES.value,
        SignalCommand.STOP_BOT: LifecycleAction.STOP_KEEP_POSITIONS.value,
    }
    for command, action in expected.items():
        service, _ = service_with_endpoint(authority=SignalAuthority.EXECUTION_AUTHORIZED)
        result = service.process(
            context(), processing_request(command), signature=b"x", target=target()
        )
        assert result.command_intent is not None
        assert result.command_intent.vocabulary == MappedCommandVocabulary.BM03_LIFECYCLE
        assert result.command_intent.action == action


def test_preview_is_not_persisted_and_marks_intent_preview_only() -> None:
    service, repository = service_with_endpoint(authority=SignalAuthority.EXECUTION_AUTHORIZED)
    result = service.preview(context(), processing_request(), signature=b"x", target=target())
    assert result.mode == SignalProcessingMode.PREVIEW
    assert result.persisted is False
    assert result.command_intent is not None
    assert result.command_intent.preview_only is True
    assert repository.list_processing("tenant-a") == ()


def test_preview_does_not_consume_nonce_or_idempotency() -> None:
    service, _ = service_with_endpoint(authority=SignalAuthority.EXECUTION_AUTHORIZED)
    preview = service.preview(context(), processing_request(), signature=b"x", target=target())
    accepted = service.process(context(), processing_request(), signature=b"x", target=target())
    assert preview.validation.reason_codes == ()
    assert accepted.validation.reason_codes == ()
    assert accepted.command_intent is not None
    assert accepted.command_intent.preview_only is False


def test_serialization_is_deterministic() -> None:
    service, _ = service_with_endpoint(authority=SignalAuthority.EXECUTION_AUTHORIZED)
    result = service.process(context(), processing_request(), signature=b"x", target=target())
    assert result.canonical_json() == result.canonical_json()
    assert (
        result.processing_id
        == service.process(
            context(), processing_request(), signature=b"x", target=target()
        ).processing_id
    )


def test_reason_codes_are_deterministically_sorted() -> None:
    service, _ = service_with_endpoint(supported_commands=(SignalCommand.OPEN,))
    result = service.process(
        context(),
        processing_request(
            SignalCommand.DCA,
            tenant_id="tenant-b",
            bot_revision=3,
            config_revision=6,
            runtime_revision=2,
        ),
        signature=b"x",
        target=target(),
    )
    values = [reason.value for reason in result.validation.reason_codes]
    assert values == sorted(values)
    assert set(result.mapping.reason_codes) == set(result.validation.reason_codes)


def test_every_serialized_model_excludes_secret_material() -> None:
    service, _ = service_with_endpoint(authority=SignalAuthority.EXECUTION_AUTHORIZED)
    result = service.process(
        context(), processing_request(), signature=b"top-secret", target=target()
    )
    models = (
        endpoint_request(),
        SIGNAL_PAYLOAD_SCHEMA_V1,
        result,
        result.validation,
        result.mapping,
        result.command_intent,
    )
    for model in models:
        assert model is not None
        serialized = model.canonical_json()
        assert "top-secret" not in serialized
        assert "resolved/secret/store" not in serialized
        assert "provider-internal" not in serialized


def test_schema_definition_is_versioned_and_deterministic() -> None:
    assert SIGNAL_PAYLOAD_SCHEMA_V1.schema_id == "signal.v1"
    assert SIGNAL_PAYLOAD_SCHEMA_V1.revision == 1
    assert list(SIGNAL_PAYLOAD_SCHEMA_V1.field_names) == sorted(
        SIGNAL_PAYLOAD_SCHEMA_V1.field_names
    )
    forbidden = {"api_key", "secret", "token", "passphrase", "secret_store_path"}
    assert forbidden.isdisjoint(SIGNAL_PAYLOAD_SCHEMA_V1.field_names)
