from __future__ import annotations

from uuid import uuid4

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


def test_default_lifecycle_intent_router_fails_closed_without_runtime_evidence() -> None:
    engine = build_engine("sqlite+pysqlite:///:memory:")
    create_schema(engine)
    session_factory = build_session_factory(engine)
    commands = BotCommandService(session_factory)
    intents = LifecycleCommandIntentService(
        commands,
        UnavailableBotRuntimeStateProvider(),
    )
    context = RequestContext(
        tenant_id="tenant-a",
        actor_id="actor-a",
        actor_type=ActorType.USER,
        permissions=(Permission.BOT_START,),
        request_id=uuid4(),
        correlation_id=uuid4(),
    )
    app = FastAPI()
    app.include_router(build_router(commands, intents, lambda: context))
    client = TestClient(app)

    response = client.post(
        "/v1/bot-management/commands/lifecycle-intents",
        json={
            "bot_id": "bot-a",
            "action": "START",
            "expected_config_revision": 1,
            "idempotency_key": "start-bot-a-r1",
        },
    )

    assert response.status_code == 200
    assert response.json() == {
        "command_id": None,
        "bot_id": "bot-a",
        "action": "START",
        "status": "BLOCKED",
        "reason_codes": ["RUNTIME_UNAVAILABLE"],
        "command_persisted": False,
        "execution_submission_performed": False,
    }
