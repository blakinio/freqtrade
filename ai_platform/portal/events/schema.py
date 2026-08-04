from sqlalchemy import Engine

from ai_platform.portal.database.schema import migrate_database


def create_event_schema(engine: Engine) -> None:
    migrate_database(engine)
