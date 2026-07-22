from __future__ import annotations

from sqlalchemy import Engine

from ai_platform.portal.control_plane.database import Base


def create_risk_schema(engine: Engine) -> None:
    from ai_platform.portal.control_plane import models as control_plane_models  # noqa: F401
    from ai_platform.portal.risk import models as risk_models  # noqa: F401

    Base.metadata.create_all(engine)
