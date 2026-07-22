from sqlalchemy import Engine

from ai_platform.portal.control_plane.database import Base


def create_event_schema(engine: Engine) -> None:
    from ai_platform.portal.events import models  # noqa: F401

    Base.metadata.create_all(engine)
