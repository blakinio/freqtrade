from __future__ import annotations

import json
import re
from collections.abc import Mapping
from datetime import UTC, datetime
from itertools import pairwise
from pathlib import Path
from typing import Any, Literal, Self, cast

import yaml
from pydantic import Field, field_validator, model_validator

from strategy_engine.domain.models import CanonicalModel

_SHA256_PATTERN = r"^[0-9a-f]{64}$"
_TIMERANGE_PATTERN = re.compile(r"^[0-9]{8}-[0-9]{8}$")


class DatasetManifestError(ValueError):
    def __init__(self, reason_code: str, message: str) -> None:
        super().__init__(message)
        self.reason_code = reason_code


def _require_utc(value: datetime) -> datetime:
    if value.tzinfo is None or value.utcoffset() != UTC.utcoffset(value):
        raise ValueError("timestamp must be timezone-aware UTC")
    return value


class DatasetWindow(CanonicalModel):
    start: datetime
    end: datetime

    _utc_start = field_validator("start")(_require_utc)
    _utc_end = field_validator("end")(_require_utc)

    @model_validator(mode="after")
    def validate_order(self) -> Self:
        if self.start >= self.end:
            raise ValueError("dataset window start must precede end")
        return self


class ProtectedFinalHoldout(CanonicalModel):
    timerange: str
    locked: Literal[True] = True
    used: Literal[False] = False
    retuning_allowed: Literal[False] = False

    @field_validator("timerange")
    @classmethod
    def validate_timerange(cls, value: str) -> str:
        if _TIMERANGE_PATTERN.fullmatch(value) is None:
            raise ValueError("final holdout timerange must use YYYYMMDD-YYYYMMDD")
        start_raw, end_raw = value.split("-", maxsplit=1)
        start = datetime.strptime(start_raw, "%Y%m%d").replace(tzinfo=UTC)
        end = datetime.strptime(end_raw, "%Y%m%d").replace(tzinfo=UTC)
        if start > end:
            raise ValueError("final holdout timerange starts after it ends")
        return value


class DatasetHashes(CanonicalModel):
    data_selection_sha256: str = Field(pattern=_SHA256_PATTERN)
    code_sha256: str = Field(pattern=_SHA256_PATTERN)
    config_sha256: str = Field(pattern=_SHA256_PATTERN)


class DatasetManifest(CanonicalModel):
    schema_version: Literal["1.0.0"] = "1.0.0"
    dataset_id: str = Field(min_length=1)
    dataset_version: str = Field(min_length=1)
    immutable: Literal[True] = True
    source: str = Field(min_length=1)
    symbols: tuple[str, ...]
    timeframes: tuple[str, ...]
    training: DatasetWindow
    tuning: DatasetWindow
    validation: DatasetWindow
    final_holdout: ProtectedFinalHoldout
    hashes: DatasetHashes
    manifest_hash: str = Field(pattern=_SHA256_PATTERN)

    @model_validator(mode="after")
    def validate_geometry_and_hash(self) -> Self:
        if not self.symbols or len(self.symbols) != len(set(self.symbols)):
            raise ValueError("symbols must be non-empty and unique")
        if not self.timeframes or len(self.timeframes) != len(set(self.timeframes)):
            raise ValueError("timeframes must be non-empty and unique")
        windows = (self.training, self.tuning, self.validation)
        for left, right in pairwise(windows):
            if left.end >= right.start:
                raise ValueError("dataset windows must be ordered and non-overlapping")
        holdout_start = datetime.strptime(
            self.final_holdout.timerange.split("-", maxsplit=1)[0], "%Y%m%d"
        ).replace(tzinfo=UTC)
        if self.validation.end >= holdout_start:
            raise ValueError("validation window must end before the protected final holdout")
        expected = self.canonical_sha256(exclude={"manifest_hash"})
        if self.manifest_hash != expected:
            raise ValueError("manifest_hash does not match canonical manifest payload")
        return self

    @classmethod
    def create(cls, **values: Any) -> Self:
        payload = dict(values)
        payload.pop("manifest_hash", None)
        normalized = dict(payload)
        normalized["symbols"] = tuple(cast(list[str] | tuple[str, ...], payload["symbols"]))
        normalized["timeframes"] = tuple(
            cast(list[str] | tuple[str, ...], payload["timeframes"])
        )
        normalized["training"] = DatasetWindow.model_validate(payload["training"])
        normalized["tuning"] = DatasetWindow.model_validate(payload["tuning"])
        normalized["validation"] = DatasetWindow.model_validate(payload["validation"])
        normalized["final_holdout"] = ProtectedFinalHoldout.model_validate(
            payload["final_holdout"]
        )
        normalized["hashes"] = DatasetHashes.model_validate(payload["hashes"])
        provisional = cls.model_construct(**normalized, manifest_hash="0" * 64)
        digest = provisional.canonical_sha256(exclude={"manifest_hash"})
        return cls(**normalized, manifest_hash=digest)


def validate_protected_holdout(
    manifest: DatasetManifest,
    declaration: Mapping[str, object],
) -> None:
    final_holdout = declaration.get("final_holdout")
    authorization = declaration.get("authorization")
    if not isinstance(final_holdout, Mapping) or not isinstance(authorization, Mapping):
        raise DatasetManifestError(
            "HOLDOUT_DECLARATION_INVALID",
            "holdout declaration is incomplete",
        )
    if final_holdout.get("timerange") != manifest.final_holdout.timerange:
        raise DatasetManifestError(
            "HOLDOUT_TIMERANGE_MISMATCH",
            "dataset manifest does not match the canonical protected final holdout",
        )
    if final_holdout.get("used") is not False:
        raise DatasetManifestError("HOLDOUT_ALREADY_USED", "protected final holdout is not unused")
    if authorization.get("retuning_allowed") is not False:
        raise DatasetManifestError(
            "HOLDOUT_RETUNING_ALLOWED",
            "holdout declaration permits retuning",
        )


def load_dataset_manifest(
    path: str | Path,
    *,
    protected_declaration_path: str | Path | None = None,
) -> DatasetManifest:
    manifest_path = Path(path)
    try:
        raw = yaml.safe_load(manifest_path.read_text(encoding="utf-8"))
    except (OSError, yaml.YAMLError) as exc:
        raise DatasetManifestError("DATASET_MANIFEST_UNREADABLE", str(exc)) from exc
    if not isinstance(raw, Mapping):
        raise DatasetManifestError("DATASET_MANIFEST_INVALID", "dataset manifest must be a mapping")
    manifest = DatasetManifest.model_validate(dict(cast(Mapping[str, object], raw)))
    if protected_declaration_path is not None:
        declaration_path = Path(protected_declaration_path)
        try:
            declaration_raw = json.loads(declaration_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise DatasetManifestError("HOLDOUT_DECLARATION_UNREADABLE", str(exc)) from exc
        if not isinstance(declaration_raw, Mapping):
            raise DatasetManifestError(
                "HOLDOUT_DECLARATION_INVALID", "holdout declaration must be an object"
            )
        validate_protected_holdout(manifest, cast(Mapping[str, object], declaration_raw))
    return manifest
