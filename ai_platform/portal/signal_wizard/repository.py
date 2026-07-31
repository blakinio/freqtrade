from __future__ import annotations

from datetime import datetime

from pydantic import ValidationError
from sqlalchemy import select
from sqlalchemy.orm import Session

from ai_platform.portal.contracts.strategy_closure import (
    SignalWizardPreviewCommand,
    SignalWizardPreviewResult,
    SignalWizardSubmitResult,
)
from ai_platform.portal.signal_wizard.models import (
    SignalWizardPreviewRow,
    SignalWizardSubmissionRow,
)


class CorruptSignalWizardRecordError(RuntimeError):
    pass


class SignalWizardRepository:
    def add_preview(
        self,
        session: Session,
        result: SignalWizardPreviewResult,
        command: SignalWizardPreviewCommand,
        *,
        request_digest: str,
        strategy_version: str,
        created_at: datetime,
    ) -> None:
        session.add(
            SignalWizardPreviewRow(
                tenant_id=result.context.tenant_id,
                preview_hash=result.preview_hash,
                idempotency_key=result.idempotency_key,
                request_digest=request_digest,
                strategy_version=strategy_version,
                created_at=created_at,
                command_json=command.canonical_json(),
                preview_json=result.canonical_json(),
            )
        )

    def get_preview(
        self,
        session: Session,
        tenant_id: str,
        preview_hash: str,
    ) -> tuple[SignalWizardPreviewResult, str, SignalWizardPreviewCommand] | None:
        row = session.get(SignalWizardPreviewRow, (tenant_id, preview_hash))
        if row is None:
            return None
        return self._parse_preview(row), row.strategy_version, self._parse_preview_command(row)

    def get_preview_by_idempotency(
        self,
        session: Session,
        tenant_id: str,
        idempotency_key: str,
    ) -> tuple[SignalWizardPreviewResult, str, str] | None:
        row = session.scalar(
            select(SignalWizardPreviewRow).where(
                SignalWizardPreviewRow.tenant_id == tenant_id,
                SignalWizardPreviewRow.idempotency_key == idempotency_key,
            )
        )
        if row is None:
            return None
        return self._parse_preview(row), row.request_digest, row.strategy_version

    def add_submission(
        self,
        session: Session,
        result: SignalWizardSubmitResult,
        *,
        request_digest: str,
        preview_hash: str,
        command_json: str,
        created_at: datetime,
    ) -> None:
        session.add(
            SignalWizardSubmissionRow(
                tenant_id=result.context.tenant_id,
                experiment_id=result.experiment_id,
                idempotency_key=result.idempotency_key,
                request_digest=request_digest,
                preview_hash=preview_hash,
                created_at=created_at,
                command_json=command_json,
                submission_json=result.canonical_json(),
            )
        )

    def get_submission_by_idempotency(
        self,
        session: Session,
        tenant_id: str,
        idempotency_key: str,
    ) -> tuple[SignalWizardSubmitResult, str] | None:
        row = session.scalar(
            select(SignalWizardSubmissionRow).where(
                SignalWizardSubmissionRow.tenant_id == tenant_id,
                SignalWizardSubmissionRow.idempotency_key == idempotency_key,
            )
        )
        if row is None:
            return None
        return self._parse_submission(row), row.request_digest

    @staticmethod
    def _parse_preview(row: SignalWizardPreviewRow) -> SignalWizardPreviewResult:
        try:
            return SignalWizardPreviewResult.model_validate_json(row.preview_json)
        except (ValidationError, ValueError) as exc:
            raise CorruptSignalWizardRecordError("corrupt Signal Wizard preview record") from exc

    @staticmethod
    def _parse_preview_command(row: SignalWizardPreviewRow) -> SignalWizardPreviewCommand:
        if row.command_json is None:
            raise CorruptSignalWizardRecordError(
                "Signal Wizard preview record predates canonical command persistence"
            )
        try:
            return SignalWizardPreviewCommand.model_validate_json(row.command_json)
        except (ValidationError, ValueError) as exc:
            raise CorruptSignalWizardRecordError(
                "corrupt Signal Wizard preview command record"
            ) from exc

    @staticmethod
    def _parse_submission(row: SignalWizardSubmissionRow) -> SignalWizardSubmitResult:
        try:
            return SignalWizardSubmitResult.model_validate_json(row.submission_json)
        except (ValidationError, ValueError) as exc:
            raise CorruptSignalWizardRecordError(
                "corrupt Signal Wizard submission record"
            ) from exc
