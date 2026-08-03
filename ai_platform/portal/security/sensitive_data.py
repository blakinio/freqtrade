from __future__ import annotations

import re
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from enum import StrEnum
from typing import Any


DEFAULT_MAX_DEPTH = 16
DEFAULT_MAX_ITEMS = 256
REDACTED_VALUE = "[REDACTED]"

_CAMEL_ACRONYM_BOUNDARY = re.compile(r"([A-Z]+)([A-Z][a-z])")
_CAMEL_WORD_BOUNDARY = re.compile(r"([a-z0-9])([A-Z])")
_NON_ALNUM = re.compile(r"[^A-Za-z0-9]+")

# These suffixes describe metadata about a protected field, not its value. Keep the
# allowlist narrow: authorization_header, secret_ref, and vault_ref remain sensitive.
_METADATA_ONLY_SUFFIXES = frozenset(
    {
        "algorithm",
        "algorithms",
        "configured",
        "count",
        "enabled",
        "expires",
        "expiry",
        "expiration",
        "format",
        "kind",
        "length",
        "name",
        "policy",
        "present",
        "required",
        "scheme",
        "status",
        "ttl",
        "type",
    }
)


class SensitiveFieldKind(StrEnum):
    API_KEY = "api_key"
    API_SECRET = "api_secret"
    AUTHORIZATION = "authorization"
    CLIENT_SECRET = "client_secret"
    COOKIE = "cookie"
    CREDENTIAL = "credential"
    PASSWORD = "password"
    PASSPHRASE = "passphrase"
    PRIVATE_KEY = "private_key"
    REFRESH_TOKEN = "refresh_token"
    SECRET = "secret"
    SECRET_REFERENCE = "secret_reference"
    TOKEN = "token"
    VAULT_REFERENCE = "vault_reference"


_COMPOUND_KINDS = (
    (("api", "key"), SensitiveFieldKind.API_KEY),
    (("api", "secret"), SensitiveFieldKind.API_SECRET),
    (("private", "key"), SensitiveFieldKind.PRIVATE_KEY),
    (("client", "secret"), SensitiveFieldKind.CLIENT_SECRET),
    (("refresh", "token"), SensitiveFieldKind.REFRESH_TOKEN),
    (("secret", "ref"), SensitiveFieldKind.SECRET_REFERENCE),
    (("secret", "reference"), SensitiveFieldKind.SECRET_REFERENCE),
    (("vault", "ref"), SensitiveFieldKind.VAULT_REFERENCE),
    (("vault", "reference"), SensitiveFieldKind.VAULT_REFERENCE),
)

_SINGLE_TOKEN_KINDS = {
    "authorization": SensitiveFieldKind.AUTHORIZATION,
    "cookie": SensitiveFieldKind.COOKIE,
    "credential": SensitiveFieldKind.CREDENTIAL,
    "credentials": SensitiveFieldKind.CREDENTIAL,
    "passwd": SensitiveFieldKind.PASSWORD,
    "password": SensitiveFieldKind.PASSWORD,
    "passphrase": SensitiveFieldKind.PASSPHRASE,
    "secret": SensitiveFieldKind.SECRET,
    "token": SensitiveFieldKind.TOKEN,
}

_COMPACT_KINDS = {
    "apikey": SensitiveFieldKind.API_KEY,
    "apisecret": SensitiveFieldKind.API_SECRET,
    "clientsecret": SensitiveFieldKind.CLIENT_SECRET,
    "privatekey": SensitiveFieldKind.PRIVATE_KEY,
    "refreshtoken": SensitiveFieldKind.REFRESH_TOKEN,
    "secretreference": SensitiveFieldKind.SECRET_REFERENCE,
    "secretref": SensitiveFieldKind.SECRET_REFERENCE,
    "vaultreference": SensitiveFieldKind.VAULT_REFERENCE,
    "vaultref": SensitiveFieldKind.VAULT_REFERENCE,
}


@dataclass(frozen=True, slots=True)
class SensitiveFieldMatch:
    kind: SensitiveFieldKind
    normalized_key: str


class SensitiveDataError(ValueError):
    """Safe structural error which never embeds a protected field value."""


class SensitiveFieldError(SensitiveDataError):
    def __init__(self, *, path: str, match: SensitiveFieldMatch) -> None:
        super().__init__(f"sensitive {match.kind.value} field is forbidden at {path}")
        self.path = path
        self.match = match


class SensitiveDataCycleError(SensitiveDataError):
    def __init__(self, *, path: str) -> None:
        super().__init__(f"cyclic sensitive-data container is forbidden at {path}")
        self.path = path


class SensitiveDataLimitError(SensitiveDataError):
    pass


class UnsupportedSensitiveDataTypeError(SensitiveDataError):
    def __init__(self, *, path: str, value: Any) -> None:
        super().__init__(
            f"unsupported sensitive-data container type at {path}: {type(value).__name__}"
        )
        self.path = path


def classify_sensitive_key(key: str) -> SensitiveFieldMatch | None:
    """Classify a field after case, delimiter, acronym, and camel-case normalization."""

    tokens = _key_tokens(key)
    if not tokens:
        return None
    normalized = "_".join(tokens)

    if len(tokens) > 1 and tokens[-1] in _METADATA_ONLY_SUFFIXES:
        return None

    for compound, kind in _COMPOUND_KINDS:
        if _contains_subsequence(tokens, compound):
            return SensitiveFieldMatch(kind=kind, normalized_key=normalized)

    for token in tokens:
        kind = _SINGLE_TOKEN_KINDS.get(token) or _COMPACT_KINDS.get(token)
        if kind is not None:
            return SensitiveFieldMatch(kind=kind, normalized_key=normalized)

    compact_kind = _COMPACT_KINDS.get("".join(tokens))
    if compact_kind is not None:
        return SensitiveFieldMatch(kind=compact_kind, normalized_key=normalized)
    return None


def reject_sensitive_data(
    value: Any,
    *,
    path: str = "payload",
    max_depth: int = DEFAULT_MAX_DEPTH,
    max_items: int = DEFAULT_MAX_ITEMS,
) -> Any:
    """Validate a JSON-like structure before persistence or publication."""

    _validate_limits(max_depth=max_depth, max_items=max_items)
    _reject(
        value,
        path=path,
        depth=0,
        max_depth=max_depth,
        max_items=max_items,
        budget=[0],
        active=set(),
    )
    return value


def redact_sensitive_data(
    value: Any,
    *,
    path: str = "value",
    replacement: str = REDACTED_VALUE,
    max_depth: int = DEFAULT_MAX_DEPTH,
    max_items: int = DEFAULT_MAX_ITEMS,
) -> Any:
    """Return a sanitized JSON-like copy without evaluating sensitive subtrees."""

    _validate_limits(max_depth=max_depth, max_items=max_items)
    return _redact(
        value,
        path=path,
        depth=0,
        max_depth=max_depth,
        max_items=max_items,
        budget=[0],
        active=set(),
        replacement=replacement,
    )


def _key_tokens(key: str) -> tuple[str, ...]:
    acronym_split = _CAMEL_ACRONYM_BOUNDARY.sub(r"\1_\2", key.strip())
    camel_split = _CAMEL_WORD_BOUNDARY.sub(r"\1_\2", acronym_split)
    return tuple(part.casefold() for part in _NON_ALNUM.split(camel_split) if part)


def _contains_subsequence(tokens: tuple[str, ...], candidate: tuple[str, ...]) -> bool:
    width = len(candidate)
    return any(
        tokens[index : index + width] == candidate
        for index in range(len(tokens) - width + 1)
    )


def _validate_limits(*, max_depth: int, max_items: int) -> None:
    if max_depth < 0:
        raise ValueError("max_depth must be non-negative")
    if max_items < 1:
        raise ValueError("max_items must be positive")


def _enter_container(value: Any, *, path: str, active: set[int]) -> int:
    identity = id(value)
    if identity in active:
        raise SensitiveDataCycleError(path=path)
    active.add(identity)
    return identity


def _consume(*, path: str, budget: list[int], max_items: int) -> None:
    budget[0] += 1
    if budget[0] > max_items:
        raise SensitiveDataLimitError(f"sensitive-data item limit exceeded at {path}")


def _reject(
    value: Any,
    *,
    path: str,
    depth: int,
    max_depth: int,
    max_items: int,
    budget: list[int],
    active: set[int],
) -> None:
    if depth > max_depth:
        raise SensitiveDataLimitError(f"sensitive-data depth limit exceeded at {path}")

    if isinstance(value, Mapping):
        identity = _enter_container(value, path=path, active=active)
        try:
            for key, child in value.items():
                if not isinstance(key, str):
                    raise UnsupportedSensitiveDataTypeError(path=path, value=key)
                child_path = f"{path}.{key}"
                _consume(path=child_path, budget=budget, max_items=max_items)
                match = classify_sensitive_key(key)
                if match is not None:
                    raise SensitiveFieldError(path=child_path, match=match)
                _reject(
                    child,
                    path=child_path,
                    depth=depth + 1,
                    max_depth=max_depth,
                    max_items=max_items,
                    budget=budget,
                    active=active,
                )
        finally:
            active.remove(identity)
        return

    if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        identity = _enter_container(value, path=path, active=active)
        try:
            for index, child in enumerate(value):
                child_path = f"{path}[{index}]"
                _consume(path=child_path, budget=budget, max_items=max_items)
                _reject(
                    child,
                    path=child_path,
                    depth=depth + 1,
                    max_depth=max_depth,
                    max_items=max_items,
                    budget=budget,
                    active=active,
                )
        finally:
            active.remove(identity)
        return

    if isinstance(value, (set, frozenset, bytearray)):
        raise UnsupportedSensitiveDataTypeError(path=path, value=value)


def _redact(
    value: Any,
    *,
    path: str,
    depth: int,
    max_depth: int,
    max_items: int,
    budget: list[int],
    active: set[int],
    replacement: str,
) -> Any:
    if depth > max_depth:
        raise SensitiveDataLimitError(f"sensitive-data depth limit exceeded at {path}")

    if isinstance(value, Mapping):
        identity = _enter_container(value, path=path, active=active)
        try:
            redacted: dict[str, Any] = {}
            for key, child in value.items():
                if not isinstance(key, str):
                    raise UnsupportedSensitiveDataTypeError(path=path, value=key)
                child_path = f"{path}.{key}"
                _consume(path=child_path, budget=budget, max_items=max_items)
                if classify_sensitive_key(key) is not None:
                    redacted[key] = replacement
                else:
                    redacted[key] = _redact(
                        child,
                        path=child_path,
                        depth=depth + 1,
                        max_depth=max_depth,
                        max_items=max_items,
                        budget=budget,
                        active=active,
                        replacement=replacement,
                    )
            return redacted
        finally:
            active.remove(identity)

    if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        identity = _enter_container(value, path=path, active=active)
        try:
            redacted_sequence: list[Any] = []
            for index, child in enumerate(value):
                child_path = f"{path}[{index}]"
                _consume(path=child_path, budget=budget, max_items=max_items)
                redacted_sequence.append(
                    _redact(
                        child,
                        path=child_path,
                        depth=depth + 1,
                        max_depth=max_depth,
                        max_items=max_items,
                        budget=budget,
                        active=active,
                        replacement=replacement,
                    )
                )
            return redacted_sequence
        finally:
            active.remove(identity)

    if isinstance(value, (set, frozenset, bytearray)):
        raise UnsupportedSensitiveDataTypeError(path=path, value=value)
    return value
