from __future__ import annotations

from ai_platform.portal.control_plane.api import create_app
from ai_platform.portal.control_plane.database import (
    build_engine,
    build_session_factory,
    create_schema,
)


def test_external_runtime_adoption_is_not_exposed_as_public_mutation() -> None:
    engine = build_engine("sqlite+pysqlite:///:memory:")
    create_schema(engine)
    app = create_app(build_session_factory(engine))

    paths = app.openapi()["paths"]

    assert "/v1/bots/{bot_id}/runtime-observations/adopt" not in paths
    assert "get" in paths["/v1/bots/{bot_id}/runtime-observations/latest"]
    assert "get" in paths["/v1/bots/{bot_id}/wickhunter-runtime-evidence"]
