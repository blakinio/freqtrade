from __future__ import annotations

from sqlalchemy import Engine

from ai_platform.portal.control_plane.database import Base


def create_intelligence_schema(engine: Engine) -> None:
    from ai_platform.portal.intelligence import models as intelligence_models  # noqa: F401

    Base.metadata.create_all(engine)
