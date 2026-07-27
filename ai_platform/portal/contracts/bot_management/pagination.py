from __future__ import annotations

from enum import StrEnum
from typing import Annotated, Self

from pydantic import Field, model_validator

from ai_platform.portal.contracts.common import ContractModel, NonEmptyStr, UtcDateTime
from ai_platform.portal.contracts.environment import Environment


MAX_PAGE_SIZE = 100
PageSize = Annotated[int, Field(ge=1, le=MAX_PAGE_SIZE)]


class SortDirection(StrEnum):
    ASC = "asc"
    DESC = "desc"


class BotManagementSortField(StrEnum):
    CREATED_AT = "created_at"
    UPDATED_AT = "updated_at"
    BOT_ID = "bot_id"
    COMMAND_ID = "command_id"
    OCCURRED_AT = "occurred_at"


class BoundedPagination(ContractModel):
    page_size: PageSize = 50
    cursor: NonEmptyStr | None = None
    sort_field: BotManagementSortField
    sort_direction: SortDirection = SortDirection.ASC


class BotManagementListFilters(ContractModel):
    bot_ids: tuple[NonEmptyStr, ...] = ()
    environments: tuple[Environment, ...] = ()
    states: tuple[NonEmptyStr, ...] = ()
    occurred_from: UtcDateTime | None = None
    occurred_to: UtcDateTime | None = None

    @model_validator(mode="after")
    def validate_filters(self) -> Self:
        for field_name, values in (
            ("bot_ids", self.bot_ids),
            ("environments", tuple(value.value for value in self.environments)),
            ("states", self.states),
        ):
            if len(values) != len(set(values)):
                raise ValueError(f"{field_name} must not contain duplicates")
            if list(values) != sorted(values):
                raise ValueError(f"{field_name} must use deterministic sorted order")
        if self.occurred_from and self.occurred_to and self.occurred_from > self.occurred_to:
            raise ValueError("occurred_from must not be after occurred_to")
        return self


class PageInfo(ContractModel):
    requested_page_size: PageSize
    result_count: Annotated[int, Field(ge=0, le=MAX_PAGE_SIZE)]
    next_cursor: NonEmptyStr | None = None
    has_more: bool

    @model_validator(mode="after")
    def validate_page_info(self) -> Self:
        if self.result_count > self.requested_page_size:
            raise ValueError("result_count must not exceed requested_page_size")
        if self.has_more != (self.next_cursor is not None):
            raise ValueError("has_more and next_cursor must agree")
        return self
