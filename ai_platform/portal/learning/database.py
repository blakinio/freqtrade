from __future__ import annotations

from sqlalchemy import Engine

from ai_platform.portal.control_plane.database import Base


def create_learning_schema(engine: Engine) -> None:
    from ai_platform.portal.learning import models as learning_models  # noqa: F401

    Base.metadata.create_all(engine)
