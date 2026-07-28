from __future__ import annotations

import hashlib
from dataclasses import dataclass
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from ai_platform.portal.control_plane.database import SessionFactory
from ai_platform.portal.execution_submission.errors import (
    SubmissionIdempotencyConflictError,
    SubmissionNotFoundError,
)
from ai_platform.portal.execution_submission.models import ExecutionSubmissionRow
from ai_platform.portal.execution_submission.schema import (
    PrivateDryRunSubmission,
    PrivateSubmissionReceipt,
)


@dataclass(frozen=True)
class StoredSubmission:
    submission: PrivateDryRunSubmission
    receipt: PrivateSubmissionReceipt
    digest: str


class ExecutionSubmissionStore:
    def __init__(self, session_factory: SessionFactory) -> None:
        self._session_factory = session_factory

    @staticmethod
    def digest(submission: PrivateDryRunSubmission) -> str:
        return hashlib.sha256(submission.canonical_json().encode()).hexdigest()

    def reserve(
        self,
        submission: PrivateDryRunSubmission,
        receipt: PrivateSubmissionReceipt,
    ) -> tuple[StoredSubmission, bool]:
        digest = self.digest(submission)
        with self._session_factory() as session, session.begin():
            existing = self._find_by_key(
                session,
                submission.binding.tenant_id,
                submission.binding.idempotency_key,
            )
            if existing is not None:
                stored = self._decode(existing)
                if stored.digest != digest:
                    raise SubmissionIdempotencyConflictError()
                return stored, False

            row = ExecutionSubmissionRow(
                tenant_id=submission.binding.tenant_id,
                attempt_id=receipt.attempt.attempt_id,
                idempotency_key=submission.binding.idempotency_key,
                command_id=submission.command_id,
                execution_intent_id=str(submission.intent.execution_intent_id),
                submission_digest=digest,
                submission_json=submission.canonical_json(),
                receipt_json=receipt.canonical_json(),
                created_at=receipt.attempt.started_at,
                updated_at=receipt.attempt.started_at,
            )
            session.add(row)
            try:
                session.flush()
            except IntegrityError:
                session.rollback()
                return self._resolve_reservation_race(submission, digest), False
        return StoredSubmission(submission=submission, receipt=receipt, digest=digest), True

    def update_receipt(
        self,
        tenant_id: str,
        attempt_id: str,
        receipt: PrivateSubmissionReceipt,
    ) -> StoredSubmission:
        with self._session_factory() as session, session.begin():
            row = session.get(ExecutionSubmissionRow, (tenant_id, attempt_id))
            if row is None:
                raise SubmissionNotFoundError("execution submission not found")
            row.receipt_json = receipt.canonical_json()
            row.updated_at = datetime.now(UTC)
            session.flush()
            return self._decode(row)

    def get_by_attempt(self, tenant_id: str, attempt_id: str) -> StoredSubmission:
        with self._session_factory() as session:
            row = session.get(ExecutionSubmissionRow, (tenant_id, attempt_id))
            if row is None:
                raise SubmissionNotFoundError("execution submission not found")
            return self._decode(row)

    def get_by_idempotency_key(
        self,
        tenant_id: str,
        idempotency_key: str,
    ) -> StoredSubmission:
        with self._session_factory() as session:
            row = self._find_by_key(session, tenant_id, idempotency_key)
            if row is None:
                raise SubmissionNotFoundError("execution submission not found")
            return self._decode(row)

    def _resolve_reservation_race(
        self,
        submission: PrivateDryRunSubmission,
        digest: str,
    ) -> StoredSubmission:
        with self._session_factory() as session:
            row = self._find_by_key(
                session,
                submission.binding.tenant_id,
                submission.binding.idempotency_key,
            )
            if row is None:
                raise SubmissionIdempotencyConflictError() from None
            stored = self._decode(row)
            if stored.digest != digest:
                raise SubmissionIdempotencyConflictError() from None
            return stored

    @staticmethod
    def _find_by_key(
        session: Session,
        tenant_id: str,
        idempotency_key: str,
    ) -> ExecutionSubmissionRow | None:
        return session.scalar(
            select(ExecutionSubmissionRow).where(
                ExecutionSubmissionRow.tenant_id == tenant_id,
                ExecutionSubmissionRow.idempotency_key == idempotency_key,
            )
        )

    @staticmethod
    def _decode(row: ExecutionSubmissionRow) -> StoredSubmission:
        return StoredSubmission(
            submission=PrivateDryRunSubmission.model_validate_json(row.submission_json),
            receipt=PrivateSubmissionReceipt.model_validate_json(row.receipt_json),
            digest=row.submission_digest,
        )
