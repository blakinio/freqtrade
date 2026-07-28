from __future__ import annotations

import base64
import binascii
import json
from hashlib import sha256

from ai_platform.portal.bot_catalog.compatibility import (
    BotCatalogCompatibilityEvaluator,
)
from ai_platform.portal.bot_catalog.repository import BotCatalogRepository
from ai_platform.portal.bot_catalog.schema import (
    BotCatalogSnapshot,
    CatalogAccessContext,
    CatalogAccessReasonCode,
    CatalogPageRequest,
    CatalogTemplateEntry,
    CatalogTemplateFilters,
    TemplateCatalogPage,
)
from ai_platform.portal.contracts.bot_management.capabilities import (
    BotManagementCapability,
)
from ai_platform.portal.contracts.bot_management.compatibility import (
    BotCompatibilityDecision,
    CompatibilitySelection,
)
from ai_platform.portal.contracts.bot_management.pagination import PageInfo
from ai_platform.portal.contracts.bot_management.templates import CatalogVersionRef
from ai_platform.portal.contracts.common import UtcDateTime


class BotCatalogServiceError(RuntimeError):
    def __init__(self, reason_code: CatalogAccessReasonCode, message: str) -> None:
        super().__init__(message)
        self.reason_code = reason_code


class BotCatalogService:
    def __init__(
        self,
        repository: BotCatalogRepository,
        evaluator: BotCatalogCompatibilityEvaluator | None = None,
    ) -> None:
        self._repository = repository
        self._evaluator = evaluator or BotCatalogCompatibilityEvaluator()

    def get_snapshot(
        self,
        access: CatalogAccessContext,
        catalog_ref: CatalogVersionRef,
    ) -> BotCatalogSnapshot:
        self._require_capability(access, BotManagementCapability.CATALOG_READ)
        return self._require_snapshot(catalog_ref)

    def list_templates(
        self,
        access: CatalogAccessContext,
        catalog_ref: CatalogVersionRef,
        filters: CatalogTemplateFilters,
        page: CatalogPageRequest,
    ) -> TemplateCatalogPage:
        self._require_capability(access, BotManagementCapability.CATALOG_READ)
        self._require_capability(access, BotManagementCapability.TEMPLATE_READ)
        snapshot = self._require_snapshot(catalog_ref)
        matching = tuple(
            entry for entry in snapshot.templates if self._matches_filters(entry, filters)
        )
        start = self._cursor_start(catalog_ref, filters, page.cursor, len(matching))
        stop = min(start + page.page_size, len(matching))
        items = matching[start:stop]
        next_cursor = None
        if stop < len(matching):
            next_cursor = self._encode_cursor(catalog_ref, filters, stop)
        return TemplateCatalogPage(
            catalog_ref=catalog_ref,
            items=items,
            page_info=PageInfo(
                requested_page_size=page.page_size,
                result_count=len(items),
                next_cursor=next_cursor,
                has_more=next_cursor is not None,
            ),
        )

    def decide_compatibility(
        self,
        access: CatalogAccessContext,
        catalog_ref: CatalogVersionRef,
        selection: CompatibilitySelection,
        decided_at: UtcDateTime,
    ) -> BotCompatibilityDecision:
        self._require_capability(access, BotManagementCapability.CATALOG_READ)
        if access.tenant_id != selection.tenant_id:
            raise BotCatalogServiceError(
                CatalogAccessReasonCode.TENANT_MISMATCH,
                "compatibility selection tenant does not match access context",
            )
        snapshot = self._require_snapshot(catalog_ref)
        return self._evaluator.evaluate(snapshot, selection, decided_at)

    def latest_catalog_ref(
        self,
        access: CatalogAccessContext,
        catalog_id: str,
    ) -> CatalogVersionRef:
        self._require_capability(access, BotManagementCapability.CATALOG_READ)
        snapshot = self._repository.get_latest_snapshot(catalog_id)
        if snapshot is None:
            raise BotCatalogServiceError(
                CatalogAccessReasonCode.CATALOG_NOT_FOUND,
                "catalog does not exist",
            )
        return snapshot.catalog_ref

    def _require_snapshot(self, catalog_ref: CatalogVersionRef) -> BotCatalogSnapshot:
        snapshot = self._repository.get_snapshot(catalog_ref)
        if snapshot is None:
            raise BotCatalogServiceError(
                CatalogAccessReasonCode.CATALOG_NOT_FOUND,
                "catalog revision does not exist",
            )
        return snapshot

    @staticmethod
    def _require_capability(
        access: CatalogAccessContext,
        capability: BotManagementCapability,
    ) -> None:
        if capability not in access.capabilities:
            raise BotCatalogServiceError(
                CatalogAccessReasonCode.CAPABILITY_MISSING,
                f"missing required capability: {capability.value}",
            )

    @staticmethod
    def _matches_filters(
        entry: CatalogTemplateEntry,
        filters: CatalogTemplateFilters,
    ) -> bool:
        template = entry.template
        if entry.state not in filters.states:
            return False
        if filters.bot_families and template.bot_family not in filters.bot_families:
            return False
        if filters.market_types and not set(filters.market_types).issubset(
            template.supported_market_types
        ):
            return False
        if filters.execution_modes and not set(filters.execution_modes).issubset(
            template.supported_execution_modes
        ):
            return False
        if filters.query is not None:
            query = filters.query.casefold()
            if (
                query not in template.template_id.casefold()
                and query not in template.display_name.casefold()
            ):
                return False
        return True

    @classmethod
    def _cursor_start(
        cls,
        catalog_ref: CatalogVersionRef,
        filters: CatalogTemplateFilters,
        cursor: str | None,
        result_count: int,
    ) -> int:
        if cursor is None:
            return 0
        payload = cls._decode_cursor(cursor)
        expected = {
            "catalog_id": catalog_ref.catalog_id,
            "catalog_version": catalog_ref.version,
            "filter_sha256": sha256(filters.canonical_json().encode("utf-8")).hexdigest(),
        }
        if any(payload.get(key) != value for key, value in expected.items()):
            raise BotCatalogServiceError(
                CatalogAccessReasonCode.CURSOR_INVALID,
                "catalog cursor does not match the request",
            )
        offset = payload.get("offset")
        if not isinstance(offset, int) or isinstance(offset, bool) or offset < 0:
            raise BotCatalogServiceError(
                CatalogAccessReasonCode.CURSOR_INVALID,
                "catalog cursor offset is invalid",
            )
        if offset > result_count:
            raise BotCatalogServiceError(
                CatalogAccessReasonCode.CURSOR_INVALID,
                "catalog cursor offset is outside the result set",
            )
        return offset

    @staticmethod
    def _encode_cursor(
        catalog_ref: CatalogVersionRef,
        filters: CatalogTemplateFilters,
        offset: int,
    ) -> str:
        payload = json.dumps(
            {
                "catalog_id": catalog_ref.catalog_id,
                "catalog_version": catalog_ref.version,
                "filter_sha256": sha256(filters.canonical_json().encode("utf-8")).hexdigest(),
                "offset": offset,
            },
            separators=(",", ":"),
            sort_keys=True,
        ).encode("utf-8")
        return base64.urlsafe_b64encode(payload).decode("ascii").rstrip("=")

    @staticmethod
    def _decode_cursor(cursor: str) -> dict[str, object]:
        try:
            padded = cursor + "=" * (-len(cursor) % 4)
            raw = base64.b64decode(padded, altchars=b"-_", validate=True)
            payload = json.loads(raw.decode("utf-8"))
        except (binascii.Error, UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise BotCatalogServiceError(
                CatalogAccessReasonCode.CURSOR_INVALID,
                "catalog cursor cannot be decoded",
            ) from exc
        if not isinstance(payload, dict) or set(payload) != {
            "catalog_id",
            "catalog_version",
            "filter_sha256",
            "offset",
        }:
            raise BotCatalogServiceError(
                CatalogAccessReasonCode.CURSOR_INVALID,
                "catalog cursor shape is invalid",
            )
        return payload
