from __future__ import annotations

from collections.abc import Callable

from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker
from sqlalchemy.pool import StaticPool


class Base(DeclarativeBase):
    pass


SessionFactory = Callable[[], Session]


def build_engine(database_url: str) -> Engine:
    if database_url == "sqlite+pysqlite:///:memory:":
        return create_engine(
            database_url,
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )
    return create_engine(database_url, pool_pre_ping=True)


def build_session_factory(engine: Engine) -> sessionmaker[Session]:
    return sessionmaker(bind=engine, expire_on_commit=False)


def create_schema(engine: Engine) -> None:
    # Import every portal module that contributes SQLAlchemy tables to the shared
    # metadata before creating the development/test schema. Production continues
    # to use the versioned migrations owned by each module.
    from ai_platform.portal.control_plane import models as control_plane_models  # noqa: F401
    from ai_platform.portal.intelligence import models as intelligence_models  # noqa: F401
    from ai_platform.portal.learning import models as learning_models  # noqa: F401
    from ai_platform.portal.model_control import models as model_control_models  # noqa: F401
    from ai_platform.portal.operations import models as operations_models  # noqa: F401
    from ai_platform.portal.risk import models as risk_models  # noqa: F401

    Base.metadata.create_all(engine)
