from __future__ import annotations

from uuid import UUID

from fastapi import FastAPI
from fastapi.testclient import TestClient

from ai_platform.portal.bot_operations.intent_service import (
    LifecycleCommandIntentService,
    UnavailableBotRuntimeStateProvider,
)
from ai_platform.portal.bot_operations.router import build_router
from ai_platform.portal.bot_operations.service import BotCommandService
from ai_platform.portal.contracts.identity import ActorType, Permission
from ai_platform.portal.control_plane.context import RequestContext
from ai_platform.portal.control_plane.database import (
    build_engine,
    build_session_factory,
    create_schema,
)


def _context() -> RequestContext:
    return RequestContext(
        tenant_id="tenant-a",
        actor_id="actor-a",
        actor_type=ActorType.USER,
        permissions=(Permission.BOT_START,),
        request_id=UUID("11111111-1111-4111-8111-111111111111"),
        correlation_id=UUID("22222222-2222-4222-8222-222222222222"),
    )


def _client() -> TestClient:
    engine = build_engine("sqlite+pysqlite:///:memory:")
    create_schema(engine)
    session_factory = build_session_factory(engine)
    commands = BotCommandService(session_factory)
    intents = LifecycleCommandIntentService(
        commands,
        UnavailableBotRuntimeStateProvider(),
    )
    app = FastAPI()
    app.include_router(build_router(commands, intents, _context))
    return TestClient(app)


def test_lifecycle_intent_api_fails_closed_without_runtime_provider() -> None:
    response = _client().post(
        "/v1/bot-management/commands/lifecycle-intents",
        json={
            "bot_id": "bot-a",
            "action": "START",
            "expected_config_revision": 3,
            "expected_runtime_generation_id": "generation-3",
            "idempotency_key": "intent-a",
        },
    )

    assert response.status_code == 200
    assert response.json() == {
        "contract_version": "v1",
        "command_id": None,
        "bot_id": "bot-a",
        "action": "START",
        "status": "BLOCKED",
        "reason_codes": ["RUNTIME_UNAVAILABLE"],
        "command_persisted": False,
        "execution_submission_performed": False,
    }


def test_lifecycle_intent_api_rejects_browser_supplied_authority_fields() -> None:
    for field, value in (
        ("runtime_generation_id", "browser-generation"),
        ("runtime_id", "browser-runtime"),
        ("runtime_revision", 99),
        ("environment", "production"),
        ("tenant_id", "tenant-b"),
        ("actor_id", "admin"),
    ):
        response = _client().post(
            "/v1/bot-management/commands/lifecycle-intents",
            json={
                "bot_id": "bot-a",
                "action": "START",
                "expected_config_revision": 3,
                "expected_runtime_generation_id": "generation-3",
                "idempotency_key": f"intent-{field}",
                field: value,
            },
        )

        assert response.status_code == 422
