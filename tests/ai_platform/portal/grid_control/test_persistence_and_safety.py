from decimal import Decimal

import pytest

from ai_platform.portal.contracts.bot_management.capabilities import BotManagementCapability
from ai_platform.portal.contracts.environment import ExecutionMode
from ai_platform.portal.grid_control.repository import InMemoryGridControlRepository
from ai_platform.portal.grid_control.schema import (
    GridControlReasonCode,
    PersistGridPolicyRequest,
)
from ai_platform.portal.grid_control.service import GridControlService, GridControlServiceError
from tests.ai_platform.portal.grid_control.support import (
    clock,
    context,
    exchange,
    request,
    template,
)


def _service_and_preview() -> tuple[GridControlService, object]:
    grid_service = GridControlService(InMemoryGridControlRepository(), clock=clock)
    preview = grid_service.preview(context(), request(), template(), exchange())
    return grid_service, preview


def test_first_persisted_revision_is_one_and_dry_run() -> None:
    grid_service, preview = _service_and_preview()
    revision = grid_service.persist(
        context(),
        PersistGridPolicyRequest(preview=preview, expected_revision=0),
    )
    assert revision.revision == 1
    assert revision.supersedes_revision is None
    assert revision.execution_mode == ExecutionMode.DRY_RUN
    assert revision.immutable is True
    assert revision.order_submission_performed is False


def test_second_revision_supersedes_first() -> None:
    repository = InMemoryGridControlRepository()
    grid_service = GridControlService(repository, clock=clock)
    first_preview = grid_service.preview(context(), request(), template(), exchange())
    first = grid_service.persist(
        context(), PersistGridPolicyRequest(preview=first_preview, expected_revision=0)
    )
    second_request = request().model_copy(
        update={
            "config_revision": 8,
            "policy": request().policy.model_copy(
                update={"revision": 2, "total_quote_allocation": Decimal("350")}
            ),
        }
    )
    second_preview = grid_service.preview(context(), second_request, template(), exchange())
    second = grid_service.persist(
        context(), PersistGridPolicyRequest(preview=second_preview, expected_revision=1)
    )
    assert first.revision == 1
    assert second.revision == 2
    assert second.supersedes_revision == 1
    assert repository.list_revisions("tenant-a", "bot-1") == (first, second)


def test_stale_expected_revision_is_rejected() -> None:
    grid_service, preview = _service_and_preview()
    grid_service.persist(
        context(), PersistGridPolicyRequest(preview=preview, expected_revision=0)
    )
    with pytest.raises(GridControlServiceError) as error:
        grid_service.persist(
            context(), PersistGridPolicyRequest(preview=preview, expected_revision=0)
        )
    assert error.value.reason_codes == (GridControlReasonCode.REVISION_CONFLICT,)


def test_rejected_preview_cannot_be_persisted() -> None:
    repository = InMemoryGridControlRepository()
    grid_service = GridControlService(repository, clock=clock)
    rejected = grid_service.preview(
        context(),
        request().model_copy(update={"available_quote": Decimal("1")}),
        template(),
        exchange(),
    )
    with pytest.raises(GridControlServiceError) as error:
        grid_service.persist(
            context(), PersistGridPolicyRequest(preview=rejected, expected_revision=0)
        )
    assert error.value.reason_codes == (GridControlReasonCode.PREVIEW_REJECTED,)
    assert repository.list_revisions("tenant-a", "bot-1") == ()


def test_missing_capability_cannot_persist() -> None:
    grid_service, preview = _service_and_preview()
    denied = context().model_copy(update={"capabilities": ()})
    with pytest.raises(GridControlServiceError) as error:
        grid_service.persist(
            denied, PersistGridPolicyRequest(preview=preview, expected_revision=0)
        )
    assert error.value.reason_codes == (GridControlReasonCode.CAPABILITY_MISSING,)


def test_unrelated_capability_cannot_persist() -> None:
    grid_service, preview = _service_and_preview()
    denied = context().model_copy(
        update={"capabilities": (BotManagementCapability.BOT_CREATE,)}
    )
    with pytest.raises(GridControlServiceError) as error:
        grid_service.persist(
            denied, PersistGridPolicyRequest(preview=preview, expected_revision=0)
        )
    assert error.value.reason_codes == (GridControlReasonCode.CAPABILITY_MISSING,)


def test_foreign_tenant_preview_cannot_persist() -> None:
    grid_service, preview = _service_and_preview()
    foreign = preview.model_copy(update={"tenant_id": "tenant-b"})
    with pytest.raises(GridControlServiceError) as error:
        grid_service.persist(
            context(), PersistGridPolicyRequest(preview=foreign, expected_revision=0)
        )
    assert error.value.reason_codes == (GridControlReasonCode.TENANT_MISMATCH,)


def test_revision_identity_is_deterministic_for_same_inputs() -> None:
    first_service, first_preview = _service_and_preview()
    first = first_service.persist(
        context(), PersistGridPolicyRequest(preview=first_preview, expected_revision=0)
    )
    second_service, second_preview = _service_and_preview()
    second = second_service.persist(
        context(), PersistGridPolicyRequest(preview=second_preview, expected_revision=0)
    )
    assert first.policy_revision_id == second.policy_revision_id


def test_repository_rejects_duplicate_revision_identity() -> None:
    repository = InMemoryGridControlRepository()
    grid_service = GridControlService(repository, clock=clock)
    preview = grid_service.preview(context(), request(), template(), exchange())
    revision = grid_service.persist(
        context(), PersistGridPolicyRequest(preview=preview, expected_revision=0)
    )
    with pytest.raises(ValueError, match="already exists"):
        repository.save_revision(revision)


def test_repository_rejects_non_contiguous_first_revision() -> None:
    grid_service, preview = _service_and_preview()
    revision = grid_service.persist(
        context(), PersistGridPolicyRequest(preview=preview, expected_revision=0)
    )
    invalid = revision.model_copy(update={"revision": 3, "supersedes_revision": 2})
    repository = InMemoryGridControlRepository()
    with pytest.raises(ValueError, match="first grid policy revision must be 1"):
        repository.save_revision(invalid)


def test_repository_get_revision_is_tenant_scoped() -> None:
    repository = InMemoryGridControlRepository()
    grid_service = GridControlService(repository, clock=clock)
    preview = grid_service.preview(context(), request(), template(), exchange())
    revision = grid_service.persist(
        context(), PersistGridPolicyRequest(preview=preview, expected_revision=0)
    )
    assert repository.get_revision("tenant-a", "bot-1", 1) == revision
    assert repository.get_revision("tenant-b", "bot-1", 1) is None


def test_persisted_levels_are_exact_preview_evidence() -> None:
    grid_service, preview = _service_and_preview()
    revision = grid_service.persist(
        context(), PersistGridPolicyRequest(preview=preview, expected_revision=0)
    )
    assert revision.levels == preview.levels
    assert revision.total_quote_allocation == preview.total_quote_allocation


def test_service_has_no_order_submission_surface() -> None:
    grid_service, _ = _service_and_preview()
    assert not hasattr(grid_service, "submit_order")
    assert not hasattr(grid_service, "execute")
    assert not hasattr(grid_service, "place_order")
