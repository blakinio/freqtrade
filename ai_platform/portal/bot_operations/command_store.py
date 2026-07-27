from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.orm import Session

from ai_platform.portal.bot_operations.models import (
    BotCommandHistoryRow,
    BotCommandIdempotencyConflictRow,
    BotCommandRow,
)
from ai_platform.portal.bot_operations.schema import (
    BotOperationCommand,
    BotOperationCommandKind,
    CommandHistoryEntry,
    IdempotencyConflictRecord,
)
from ai_platform.portal.contracts.bot_management.commands import (
    BotLifecycleCommand,
    OrderCommand,
    PositionCommand,
)


@dataclass(frozen=True)
class StoredCommand:
    scope_tenant_id: str
    kind: BotOperationCommandKind
    command: BotOperationCommand
    command_digest: str


class BotCommandStore:
    def get_command(
        self,
        session: Session,
        scope_tenant_id: str,
        command_id: str,
    ) -> StoredCommand | None:
        row = session.get(BotCommandRow, (scope_tenant_id, command_id))
        return self._stored_from_row(row) if row is not None else None

    def get_by_idempotency_key(
        self,
        session: Session,
        scope_tenant_id: str,
        idempotency_key: str,
    ) -> StoredCommand | None:
        row = session.scalar(
            select(BotCommandRow).where(
                BotCommandRow.scope_tenant_id == scope_tenant_id,
                BotCommandRow.idempotency_key == idempotency_key,
            )
        )
        return self._stored_from_row(row) if row is not None else None

    def add_command(
        self,
        session: Session,
        scope_tenant_id: str,
        kind: BotOperationCommandKind,
        command: BotOperationCommand,
        command_digest: str,
        history_entry: CommandHistoryEntry,
    ) -> None:
        session.add(
            BotCommandRow(
                scope_tenant_id=scope_tenant_id,
                command_id=command.command_id,
                idempotency_key=command.idempotency_key,
                command_kind=kind.value,
                command_digest=command_digest,
                command_json=command.canonical_json(),
                created_at=command.submitted_at,
            )
        )
        self.append_history(session, scope_tenant_id, history_entry)

    def append_history(
        self,
        session: Session,
        scope_tenant_id: str,
        entry: CommandHistoryEntry,
    ) -> None:
        session.add(
            BotCommandHistoryRow(
                history_id=str(entry.history_id),
                scope_tenant_id=scope_tenant_id,
                command_id=entry.command.command_id,
                sequence=entry.sequence,
                entry_json=entry.canonical_json(),
                recorded_at=entry.recorded_at,
            )
        )

    def list_history(
        self,
        session: Session,
        scope_tenant_id: str,
        command_id: str,
    ) -> tuple[CommandHistoryEntry, ...]:
        rows = session.scalars(
            select(BotCommandHistoryRow)
            .where(
                BotCommandHistoryRow.scope_tenant_id == scope_tenant_id,
                BotCommandHistoryRow.command_id == command_id,
            )
            .order_by(BotCommandHistoryRow.sequence)
        ).all()
        return tuple(CommandHistoryEntry.model_validate_json(row.entry_json) for row in rows)

    def add_idempotency_conflict(
        self,
        session: Session,
        conflict: IdempotencyConflictRecord,
    ) -> None:
        session.add(
            BotCommandIdempotencyConflictRow(
                conflict_id=str(conflict.conflict_id),
                scope_tenant_id=conflict.scope_tenant_id,
                idempotency_key=conflict.idempotency_key,
                existing_command_id=conflict.existing_command_id,
                attempted_command_id=conflict.attempted_command.command_id,
                conflict_json=conflict.canonical_json(),
                recorded_at=conflict.recorded_at,
            )
        )

    def list_idempotency_conflicts(
        self,
        session: Session,
        scope_tenant_id: str,
        idempotency_key: str | None = None,
    ) -> tuple[IdempotencyConflictRecord, ...]:
        statement = select(BotCommandIdempotencyConflictRow).where(
            BotCommandIdempotencyConflictRow.scope_tenant_id == scope_tenant_id
        )
        if idempotency_key is not None:
            statement = statement.where(
                BotCommandIdempotencyConflictRow.idempotency_key == idempotency_key
            )
        rows = session.scalars(
            statement.order_by(
                BotCommandIdempotencyConflictRow.recorded_at,
                BotCommandIdempotencyConflictRow.conflict_id,
            )
        ).all()
        return tuple(
            IdempotencyConflictRecord.model_validate_json(row.conflict_json) for row in rows
        )

    @staticmethod
    def _stored_from_row(row: BotCommandRow) -> StoredCommand:
        kind = BotOperationCommandKind(row.command_kind)
        if kind == BotOperationCommandKind.LIFECYCLE:
            command: BotOperationCommand = BotLifecycleCommand.model_validate_json(row.command_json)
        elif kind == BotOperationCommandKind.POSITION:
            command = PositionCommand.model_validate_json(row.command_json)
        else:
            command = OrderCommand.model_validate_json(row.command_json)
        return StoredCommand(
            scope_tenant_id=row.scope_tenant_id,
            kind=kind,
            command=command,
            command_digest=row.command_digest,
        )
