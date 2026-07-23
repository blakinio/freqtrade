from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from ai_platform.portal.product.models import (
    GridBotConfigRow,
    NotificationPreferenceRow,
    SignalEventRow,
)
from ai_platform.portal.product.schema import (
    GridBotConfig,
    NotificationPreference,
    SignalEvent,
)


class ProductCapabilityRepository:
    def add_signal(self, session: Session, signal: SignalEvent) -> None:
        session.add(
            SignalEventRow(
                tenant_id=signal.tenant_id,
                signal_id=str(signal.signal_id),
                bot_id=signal.bot_id,
                occurred_at=signal.occurred_at,
                signal_json=signal.canonical_json(),
            )
        )

    def list_signals(
        self,
        session: Session,
        tenant_id: str,
    ) -> tuple[SignalEvent, ...]:
        rows = session.scalars(
            select(SignalEventRow)
            .where(SignalEventRow.tenant_id == tenant_id)
            .order_by(
                SignalEventRow.occurred_at.desc(),
                SignalEventRow.signal_id.desc(),
            )
        ).all()
        return tuple(SignalEvent.model_validate_json(row.signal_json) for row in rows)

    def add_grid_config(self, session: Session, config: GridBotConfig) -> None:
        session.add(
            GridBotConfigRow(
                tenant_id=config.tenant_id,
                grid_config_id=str(config.grid_config_id),
                bot_id=config.bot_id,
                created_at=config.created_at,
                config_json=config.canonical_json(),
            )
        )

    def list_grid_configs(
        self,
        session: Session,
        tenant_id: str,
    ) -> tuple[GridBotConfig, ...]:
        rows = session.scalars(
            select(GridBotConfigRow)
            .where(GridBotConfigRow.tenant_id == tenant_id)
            .order_by(
                GridBotConfigRow.created_at.desc(),
                GridBotConfigRow.grid_config_id.desc(),
            )
        ).all()
        return tuple(GridBotConfig.model_validate_json(row.config_json) for row in rows)

    def get_notification_preference(
        self,
        session: Session,
        tenant_id: str,
        actor_id: str,
    ) -> NotificationPreference | None:
        row = session.get(NotificationPreferenceRow, (tenant_id, actor_id))
        return (
            NotificationPreference.model_validate_json(row.preference_json)
            if row is not None
            else None
        )

    def upsert_notification_preference(
        self,
        session: Session,
        preference: NotificationPreference,
    ) -> None:
        row = session.get(
            NotificationPreferenceRow,
            (preference.tenant_id, preference.actor_id),
        )
        if row is None:
            session.add(
                NotificationPreferenceRow(
                    tenant_id=preference.tenant_id,
                    actor_id=preference.actor_id,
                    in_app_enabled=preference.in_app_enabled,
                    signal_events=preference.signal_events,
                    risk_events=preference.risk_events,
                    execution_events=preference.execution_events,
                    updated_at=preference.updated_at,
                    preference_json=preference.canonical_json(),
                    revision=1,
                )
            )
            return
        row.in_app_enabled = preference.in_app_enabled
        row.signal_events = preference.signal_events
        row.risk_events = preference.risk_events
        row.execution_events = preference.execution_events
        row.updated_at = preference.updated_at
        row.preference_json = preference.canonical_json()
        row.revision += 1
