from __future__ import annotations

from sqlalchemy import Engine

from ai_platform.portal.database.schema import migrate_database


def create_learning_schema(engine: Engine) -> None:
    migrate_database(engine)
