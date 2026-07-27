from __future__ import annotations

from typing import Protocol

from ai_platform.portal.bot_builder.schema import (
    BotConfigurationDraftRevision,
    DraftRevisionRef,
    FinalizedBotConfiguration,
)
from ai_platform.portal.contracts.bot_management.configuration import BotManagementConfiguration


class BotConfigurationRepository(Protocol):
    def get_draft(
        self,
        tenant_id: str,
        draft_id: str,
        revision: int,
    ) -> BotConfigurationDraftRevision | None: ...

    def get_latest_draft(
        self,
        tenant_id: str,
        draft_id: str,
    ) -> BotConfigurationDraftRevision | None: ...

    def save_draft(self, draft: BotConfigurationDraftRevision) -> None: ...

    def get_latest_configuration(
        self,
        tenant_id: str,
        bot_id: str,
    ) -> BotManagementConfiguration | None: ...

    def get_finalization(self, draft_ref: DraftRevisionRef) -> FinalizedBotConfiguration | None: ...

    def save_finalization(self, finalization: FinalizedBotConfiguration) -> None: ...


class InMemoryBotConfigurationRepository:
    def __init__(self) -> None:
        self._drafts: dict[tuple[str, str, int], BotConfigurationDraftRevision] = {}
        self._configurations: dict[tuple[str, str, int], BotManagementConfiguration] = {}
        self._finalizations: dict[tuple[str, str, int], FinalizedBotConfiguration] = {}

    def get_draft(
        self,
        tenant_id: str,
        draft_id: str,
        revision: int,
    ) -> BotConfigurationDraftRevision | None:
        return self._drafts.get((tenant_id, draft_id, revision))

    def get_latest_draft(
        self,
        tenant_id: str,
        draft_id: str,
    ) -> BotConfigurationDraftRevision | None:
        matches = [
            draft
            for (stored_tenant, stored_draft_id, _), draft in self._drafts.items()
            if stored_tenant == tenant_id and stored_draft_id == draft_id
        ]
        if not matches:
            return None
        return max(matches, key=lambda item: item.revision)

    def save_draft(self, draft: BotConfigurationDraftRevision) -> None:
        key = (draft.tenant_id, draft.draft_id, draft.revision)
        if key in self._drafts:
            raise ValueError("draft revision already exists")
        previous = self.get_latest_draft(draft.tenant_id, draft.draft_id)
        if previous is None:
            if draft.revision != 1:
                raise ValueError("first stored draft revision must be 1")
        else:
            if draft.bot_id != previous.bot_id:
                raise ValueError("draft bot identity cannot change across revisions")
            if draft.revision != previous.revision + 1:
                raise ValueError("draft revisions must be contiguous")
        self._drafts[key] = draft

    def get_latest_configuration(
        self,
        tenant_id: str,
        bot_id: str,
    ) -> BotManagementConfiguration | None:
        matches = [
            configuration
            for (stored_tenant, stored_bot_id, _), configuration in self._configurations.items()
            if stored_tenant == tenant_id and stored_bot_id == bot_id
        ]
        if not matches:
            return None
        return max(matches, key=lambda item: item.revision)

    def get_finalization(self, draft_ref: DraftRevisionRef) -> FinalizedBotConfiguration | None:
        return self._finalizations.get(
            (draft_ref.tenant_id, draft_ref.draft_id, draft_ref.revision)
        )

    def save_finalization(self, finalization: FinalizedBotConfiguration) -> None:
        draft_key = (
            finalization.draft_ref.tenant_id,
            finalization.draft_ref.draft_id,
            finalization.draft_ref.revision,
        )
        if draft_key in self._finalizations:
            raise ValueError("draft revision is already finalized")
        configuration = finalization.configuration
        config_key = (configuration.tenant_id, configuration.bot_id, configuration.revision)
        if config_key in self._configurations:
            raise ValueError("configuration revision already exists")
        previous = self.get_latest_configuration(configuration.tenant_id, configuration.bot_id)
        expected_revision = 1 if previous is None else previous.revision + 1
        if configuration.revision != expected_revision:
            raise ValueError("configuration revisions must be contiguous")
        self._configurations[config_key] = configuration
        self._finalizations[draft_key] = finalization
