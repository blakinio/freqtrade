from __future__ import annotations

import hashlib
import hmac
import json
import re
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from enum import StrEnum
from typing import Any
from urllib.parse import parse_qsl, urlsplit


DEFAULT_MAX_DEPTH = 16
DEFAULT_MAX_ITEMS = 256
DEFAULT_MAX_STRING_BYTES = 16_384
DEFAULT_MAX_SERIALIZED_LAYERS = 3
REDACTED_VALUE = "[REDACTED]"

_CAMEL_ACRONYM_BOUNDARY = re.compile(r"([A-Z]+)([A-Z][a-z])")
_CAMEL_WORD_BOUNDARY = re.compile(r"([a-z0-9])([A-Z])")
_NON_ALNUM = re.compile(r"[^A-Za-z0-9]+")
_HEADER_LINE = re.compile(r"^([A-Za-z0-9!#$%&'*+.^_`|~-]+)\s*:\s*(.*)$")
_AUTH_VALUE = re.compile(r"^(?:basic|bearer|digest|token)\s+\S+$", re.IGNORECASE)
_JWT_VALUE = re.compile(r"^[A-Za-z0-9_-]{8,}\.[A-Za-z0-9_-]{8,}\.[A-Za-z0-9_-]{8,}$")
_PRIVATE_KEY_VALUE = re.compile(r"-----BEGIN [A-Z0-9 ]*PRIVATE KEY-----")
_SECRET_ASSIGNMENT = re.compile(
    r"(?:^|[;&\s])(?:api[_-]?key|api[_-]?secret|client[_-]?secret|password|passwd|"
    r"passphrase|refresh[_-]?token|session[_-]?id|token|secret)\s*=\s*[^;&\s]+",
    re.IGNORECASE,
)
_OPAQUE_REFERENCE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]{7,127}$")

# These suffixes describe metadata about a protected field, not its value. Reference
# compounds are checked before this allowlist because their values identify private
# secret stores even when a caller calls them a name or status.
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
    API_SECRET = "api_secret"  # noqa: S105 - classification label, not a credential
    AUTHORIZATION = "authorization"
    CLIENT_KEY = "client_key"
    CLIENT_SECRET = "client_secret"  # noqa: S105 - classification label
    CONNECTION_STRING = "connection_string"
    COOKIE = "cookie"
    CREDENTIAL = "credential"
    CREDENTIAL_REFERENCE = "credential_reference"
    DSN = "dsn"
    PASSWORD = "password"  # noqa: S105 - classification label
    PASSPHRASE = "passphrase"  # noqa: S105 - classification label
    PRIVATE_ENDPOINT = "private_endpoint"
    PRIVATE_KEY = "private_key"
    REFRESH_TOKEN = "refresh_token"  # noqa: S105 - classification label
    SECRET = "secret"  # noqa: S105 - classification label
    SECRET_REFERENCE = "secret_reference"  # noqa: S105 - classification label
    SESSION_ID = "session_id"
    TOKEN = "token"  # noqa: S105 - classification label
    TOKEN_REFERENCE = "token_reference"  # noqa: S105 - classification label
    VAULT_REFERENCE = "vault_reference"


class SensitiveValueKind(StrEnum):
    AUTHORIZATION_VALUE = "authorization_value"
    EMBEDDED_SECRET_ASSIGNMENT = "embedded_secret_assignment"
    JWT = "jwt"
    PRIVATE_KEY = "private_key"
    URL_CREDENTIALS = "url_credentials"


_REFERENCE_COMPOUND_KINDS = (
    (("credential", "ref"), SensitiveFieldKind.CREDENTIAL_REFERENCE),
    (("credential", "reference"), SensitiveFieldKind.CREDENTIAL_REFERENCE),
    (("secret", "ref"), SensitiveFieldKind.SECRET_REFERENCE),
    (("secret", "reference"), SensitiveFieldKind.SECRET_REFERENCE),
    (("token", "ref"), SensitiveFieldKind.TOKEN_REFERENCE),
    (("token", "reference"), SensitiveFieldKind.TOKEN_REFERENCE),
    (("vault", "path"), SensitiveFieldKind.VAULT_REFERENCE),
    (("vault", "ref"), SensitiveFieldKind.VAULT_REFERENCE),
    (("vault", "reference"), SensitiveFieldKind.VAULT_REFERENCE),
)

_COMPOUND_KINDS = (
    (("api", "key"), SensitiveFieldKind.API_KEY),
    (("api", "secret"), SensitiveFieldKind.API_SECRET),
    (("client", "key"), SensitiveFieldKind.CLIENT_KEY),
    (("client", "secret"), SensitiveFieldKind.CLIENT_SECRET),
    (("connection", "string"), SensitiveFieldKind.CONNECTION_STRING),
    (("database", "url"), SensitiveFieldKind.DSN),
    (("database", "uri"), SensitiveFieldKind.DSN),
    (("private", "endpoint"), SensitiveFieldKind.PRIVATE_ENDPOINT),
    (("private", "key"), SensitiveFieldKind.PRIVATE_KEY),
    (("private", "url"), SensitiveFieldKind.PRIVATE_ENDPOINT),
    (("proxy", "authorization"), SensitiveFieldKind.AUTHORIZATION),
    (("refresh", "token"), SensitiveFieldKind.REFRESH_TOKEN),
    (("session", "id"), SensitiveFieldKind.SESSION_ID),
)

_SINGLE_TOKEN_KINDS = {
    "authorization": SensitiveFieldKind.AUTHORIZATION,
    "cookie": SensitiveFieldKind.COOKIE,
    "credential": SensitiveFieldKind.CREDENTIAL,
    "credentials": SensitiveFieldKind.CREDENTIAL,
    "dsn": SensitiveFieldKind.DSN,
    "passwd": SensitiveFieldKind.PASSWORD,
    "password": SensitiveFieldKind.PASSWORD,
    "passphrase": SensitiveFieldKind.PASSPHRASE,
    "secret": SensitiveFieldKind.SECRET,
    "token": SensitiveFieldKind.TOKEN,
}

_COMPACT_KINDS = {
    "accesstoken": SensitiveFieldKind.TOKEN,
    "apikey": SensitiveFieldKind.API_KEY,
    "apisecret": SensitiveFieldKind.API_SECRET,
    "clientkey": SensitiveFieldKind.CLIENT_KEY,
    "clientsecret": SensitiveFieldKind.CLIENT_SECRET,
    "connectionstring": SensitiveFieldKind.CONNECTION_STRING,
    "credentialreference": SensitiveFieldKind.CREDENTIAL_REFERENCE,
    "credentialref": SensitiveFieldKind.CREDENTIAL_REFERENCE,
    "databaseurl": SensitiveFieldKind.DSN,
    "databaseuri": SensitiveFieldKind.DSN,
    "privateendpoint": SensitiveFieldKind.PRIVATE_ENDPOINT,
    "privatekey": SensitiveFieldKind.PRIVATE_KEY,
    "privateurl": SensitiveFieldKind.PRIVATE_ENDPOINT,
    "proxyauthorization": SensitiveFieldKind.AUTHORIZATION,
    "refreshtoken": SensitiveFieldKind.REFRESH_TOKEN,
    "secretreference": SensitiveFieldKind.SECRET_REFERENCE,
    "secretref": SensitiveFieldKind.SECRET_REFERENCE,
    "sessionid": SensitiveFieldKind.SESSION_ID,
    "sessiontoken": SensitiveFieldKind.TOKEN,
    "setcookie": SensitiveFieldKind.COOKIE,
    "tokenreference": SensitiveFieldKind.TOKEN_REFERENCE,
    "tokenref": SensitiveFieldKind.TOKEN_REFERENCE,
    "vaultpath": SensitiveFieldKind.VAULT_REFERENCE,
    "vaultreference": SensitiveFieldKind.VAULT_REFERENCE,
    "vaultref": SensitiveFieldKind.VAULT_REFERENCE,
    "websockettoken": SensitiveFieldKind.TOKEN,
    "wstoken": SensitiveFieldKind.TOKEN,
}

_COMPACT_SUFFIX_KINDS = (
    ("authorization", SensitiveFieldKind.AUTHORIZATION),
    ("passphrase", SensitiveFieldKind.PASSPHRASE),
    ("password", SensitiveFieldKind.PASSWORD),
    ("credentials", SensitiveFieldKind.CREDENTIAL),
    ("credential", SensitiveFieldKind.CREDENTIAL),
    ("sessionid", SensitiveFieldKind.SESSION_ID),
    ("secret", SensitiveFieldKind.SECRET),
    ("token", SensitiveFieldKind.TOKEN),
    ("cookie", SensitiveFieldKind.COOKIE),
    ("dsn", SensitiveFieldKind.DSN),
)


@dataclass(frozen=True, slots=True)
class SensitiveFieldMatch:
    kind: SensitiveFieldKind
    normalized_key: str


@dataclass(frozen=True, slots=True)
class SensitiveValueMatch:
    kind: SensitiveValueKind


class SensitiveDataError(ValueError):
    """Safe structural error which never embeds a protected field value."""


class SensitiveFieldError(SensitiveDataError):
    def __init__(self, *, path: str, match: SensitiveFieldMatch) -> None:
        super().__init__(
            f"sensitive payload field is forbidden at {path} (classification={match.kind.value})"
        )
        self.path = path
        self.match = match


class SensitiveValueError(SensitiveDataError):
    def __init__(self, *, path: str, match: SensitiveValueMatch) -> None:
        super().__init__(
            f"sensitive payload value is forbidden at {path} (classification={match.kind.value})"
        )
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

    for compound, reference_kind in _REFERENCE_COMPOUND_KINDS:
        if _contains_subsequence(tokens, compound):
            return SensitiveFieldMatch(kind=reference_kind, normalized_key=normalized)

    if len(tokens) > 1 and tokens[-1] in _METADATA_ONLY_SUFFIXES:
        return None

    for compound, compound_kind in _COMPOUND_KINDS:
        if _contains_subsequence(tokens, compound):
            return SensitiveFieldMatch(kind=compound_kind, normalized_key=normalized)

    for token in tokens:
        token_kind = _SINGLE_TOKEN_KINDS.get(token) or _COMPACT_KINDS.get(token)
        if token_kind is not None:
            return SensitiveFieldMatch(kind=token_kind, normalized_key=normalized)
        for suffix, suffix_kind in _COMPACT_SUFFIX_KINDS:
            if len(token) > len(suffix) and token.endswith(suffix):
                return SensitiveFieldMatch(kind=suffix_kind, normalized_key=normalized)

    compact_kind = _COMPACT_KINDS.get("".join(tokens))
    if compact_kind is not None:
        return SensitiveFieldMatch(kind=compact_kind, normalized_key=normalized)
    return None


def classify_sensitive_text(value: str) -> SensitiveValueMatch | None:
    """Return only high-confidence value findings to avoid logging false positives."""

    stripped = value.strip()
    if not stripped:
        return None
    if _PRIVATE_KEY_VALUE.search(stripped):
        return SensitiveValueMatch(SensitiveValueKind.PRIVATE_KEY)
    if _AUTH_VALUE.fullmatch(stripped):
        return SensitiveValueMatch(SensitiveValueKind.AUTHORIZATION_VALUE)
    if _JWT_VALUE.fullmatch(stripped):
        return SensitiveValueMatch(SensitiveValueKind.JWT)
    if _SECRET_ASSIGNMENT.search(stripped):
        return SensitiveValueMatch(SensitiveValueKind.EMBEDDED_SECRET_ASSIGNMENT)
    try:
        parsed = urlsplit(stripped)
    except ValueError:
        return None
    if parsed.scheme and parsed.netloc and (parsed.username is not None or parsed.password is not None):
        return SensitiveValueMatch(SensitiveValueKind.URL_CREDENTIALS)
    return None


def decode_serialized_structure(value: str, *, max_items: int) -> tuple[str, Any] | None:
    """Decode bounded JSON, header blocks, or form bodies without returning raw values."""

    stripped = value.strip()
    if not stripped:
        return None
    if stripped[0] in "[{":
        try:
            decoded = json.loads(stripped)
        except (json.JSONDecodeError, RecursionError):
            decoded = None
        if isinstance(decoded, (Mapping, list, tuple)):
            return "json", decoded

    lines = [line for line in stripped.splitlines() if line.strip()]
    if lines:
        headers: dict[str, list[str]] = {}
        for line in lines:
            match = _HEADER_LINE.fullmatch(line)
            if match is None:
                headers = {}
                break
            headers.setdefault(match.group(1), []).append(match.group(2))
            if sum(len(items) for items in headers.values()) > max_items:
                raise SensitiveDataLimitError("serialized header item limit exceeded")
        if headers:
            return "headers", headers

    if "=" in stripped and ("&" in stripped or classify_sensitive_key(stripped.split("=", 1)[0])):
        try:
            pairs = parse_qsl(
                stripped,
                keep_blank_values=True,
                strict_parsing=True,
                max_num_fields=max_items,
            )
        except (ValueError, TypeError):
            pairs = []
        if pairs:
            form: dict[str, list[str]] = {}
            for key, item in pairs:
                form.setdefault(key, []).append(item)
            return "form", form
    return None


def validate_opaque_sensitive_reference(value: str) -> str:
    """Validate a public opaque identifier and reject paths, URLs, or raw secret shapes."""

    if not _OPAQUE_REFERENCE.fullmatch(value):
        raise ValueError("opaque reference must be an 8-128 character identifier")
    if any(marker in value for marker in ("/", "\\", "@", "?", "#", "=", "%")):
        raise ValueError("opaque reference must not contain a path, URL, query, or encoded value")
    if classify_sensitive_text(value) is not None:
        raise ValueError("opaque reference must not contain raw secret material")
    return value


def fingerprint_sensitive_value(value: str | bytes, *, key: bytes) -> str:
    """Create a keyed diagnostic fingerprint; unkeyed secret hashes are prohibited."""

    if len(key) < 32:
        raise ValueError("sensitive fingerprint key must contain at least 32 bytes")
    encoded = value.encode("utf-8") if isinstance(value, str) else bytes(value)
    if len(encoded) > DEFAULT_MAX_STRING_BYTES:
        raise SensitiveDataLimitError("sensitive fingerprint value exceeds the byte limit")
    digest = hmac.new(key, encoded, hashlib.sha256).hexdigest()
    return f"hmac-sha256:{digest}"


def reject_sensitive_data(
    value: Any,
    *,
    path: str = "payload",
    max_depth: int = DEFAULT_MAX_DEPTH,
    max_items: int = DEFAULT_MAX_ITEMS,
    max_string_bytes: int = DEFAULT_MAX_STRING_BYTES,
    max_serialized_layers: int = DEFAULT_MAX_SERIALIZED_LAYERS,
) -> Any:
    """Validate a JSON-like structure before persistence or publication."""

    _validate_limits(
        max_depth=max_depth,
        max_items=max_items,
        max_string_bytes=max_string_bytes,
        max_serialized_layers=max_serialized_layers,
    )
    _reject(
        value,
        path=path,
        depth=0,
        serialized_depth=0,
        max_depth=max_depth,
        max_items=max_items,
        max_string_bytes=max_string_bytes,
        max_serialized_layers=max_serialized_layers,
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
    max_string_bytes: int = DEFAULT_MAX_STRING_BYTES,
    max_serialized_layers: int = DEFAULT_MAX_SERIALIZED_LAYERS,
) -> Any:
    """Return a sanitized JSON-like copy without evaluating sensitive subtrees."""

    _validate_limits(
        max_depth=max_depth,
        max_items=max_items,
        max_string_bytes=max_string_bytes,
        max_serialized_layers=max_serialized_layers,
    )
    return _redact(
        value,
        path=path,
        depth=0,
        serialized_depth=0,
        max_depth=max_depth,
        max_items=max_items,
        max_string_bytes=max_string_bytes,
        max_serialized_layers=max_serialized_layers,
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
        tokens[index : index + width] == candidate for index in range(len(tokens) - width + 1)
    )


def _validate_limits(
    *,
    max_depth: int,
    max_items: int,
    max_string_bytes: int,
    max_serialized_layers: int,
) -> None:
    if max_depth < 0:
        raise ValueError("max_depth must be non-negative")
    if max_items < 1:
        raise ValueError("max_items must be positive")
    if max_string_bytes < 1:
        raise ValueError("max_string_bytes must be positive")
    if max_serialized_layers < 0:
        raise ValueError("max_serialized_layers must be non-negative")


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
    serialized_depth: int,
    max_depth: int,
    max_items: int,
    max_string_bytes: int,
    max_serialized_layers: int,
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
                field_match = classify_sensitive_key(key)
                if field_match is not None:
                    raise SensitiveFieldError(path=child_path, match=field_match)
                _reject(
                    child,
                    path=child_path,
                    depth=depth + 1,
                    serialized_depth=serialized_depth,
                    max_depth=max_depth,
                    max_items=max_items,
                    max_string_bytes=max_string_bytes,
                    max_serialized_layers=max_serialized_layers,
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
                    serialized_depth=serialized_depth,
                    max_depth=max_depth,
                    max_items=max_items,
                    max_string_bytes=max_string_bytes,
                    max_serialized_layers=max_serialized_layers,
                    budget=budget,
                    active=active,
                )
        finally:
            active.remove(identity)
        return

    if isinstance(value, str):
        if len(value.encode("utf-8")) > max_string_bytes:
            raise SensitiveDataLimitError(f"sensitive-data string byte limit exceeded at {path}")
        value_match = classify_sensitive_text(value)
        if value_match is not None:
            raise SensitiveValueError(path=path, match=value_match)
        if serialized_depth < max_serialized_layers:
            decoded = decode_serialized_structure(value, max_items=max_items)
            if decoded is not None:
                encoding, structured = decoded
                _reject(
                    structured,
                    path=f"{path}#{encoding}",
                    depth=depth + 1,
                    serialized_depth=serialized_depth + 1,
                    max_depth=max_depth,
                    max_items=max_items,
                    max_string_bytes=max_string_bytes,
                    max_serialized_layers=max_serialized_layers,
                    budget=budget,
                    active=active,
                )
        return

    if isinstance(value, (set, frozenset, bytes, bytearray)):
        raise UnsupportedSensitiveDataTypeError(path=path, value=value)


def _redact(
    value: Any,
    *,
    path: str,
    depth: int,
    serialized_depth: int,
    max_depth: int,
    max_items: int,
    max_string_bytes: int,
    max_serialized_layers: int,
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
                        serialized_depth=serialized_depth,
                        max_depth=max_depth,
                        max_items=max_items,
                        max_string_bytes=max_string_bytes,
                        max_serialized_layers=max_serialized_layers,
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
            return [
                _redact(
                    child,
                    path=f"{path}[{index}]",
                    depth=depth + 1,
                    serialized_depth=serialized_depth,
                    max_depth=max_depth,
                    max_items=max_items,
                    max_string_bytes=max_string_bytes,
                    max_serialized_layers=max_serialized_layers,
                    budget=budget,
                    active=active,
                    replacement=replacement,
                )
                for index, child in enumerate(value)
                if not _consume_and_keep(
                    path=f"{path}[{index}]", budget=budget, max_items=max_items
                )
            ]
        finally:
            active.remove(identity)

    if isinstance(value, str):
        if len(value.encode("utf-8")) > max_string_bytes:
            raise SensitiveDataLimitError(f"sensitive-data string byte limit exceeded at {path}")
        if classify_sensitive_text(value) is not None:
            return replacement
        if serialized_depth < max_serialized_layers:
            decoded = decode_serialized_structure(value, max_items=max_items)
            if decoded is not None:
                encoding, structured = decoded
                try:
                    _reject(
                        structured,
                        path=f"{path}#{encoding}",
                        depth=depth + 1,
                        serialized_depth=serialized_depth + 1,
                        max_depth=max_depth,
                        max_items=max_items,
                        max_string_bytes=max_string_bytes,
                        max_serialized_layers=max_serialized_layers,
                        budget=budget,
                        active=active,
                    )
                except (SensitiveFieldError, SensitiveValueError):
                    return replacement
        return value

    if isinstance(value, (set, frozenset, bytes, bytearray)):
        raise UnsupportedSensitiveDataTypeError(path=path, value=value)
    return value


def _consume_and_keep(*, path: str, budget: list[int], max_items: int) -> bool:
    _consume(path=path, budget=budget, max_items=max_items)
    return False