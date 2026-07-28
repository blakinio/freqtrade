from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
from typing import TypeVar

from ai_platform.portal.credentials.errors import CredentialPolicyError
from ai_platform.portal.credentials.schema import CredentialLeaseEvidence


T = TypeVar("T")


def _to_buffer(value: str | None) -> bytearray | None:
    if value is None:
        return None
    return bytearray(value.encode("utf-8"))


def _clear(buffer: bytearray | None) -> None:
    if buffer is None:
        return
    for index in range(len(buffer)):
        buffer[index] = 0


@dataclass
class CredentialMaterial:
    exchange_api_key: bytearray = field(repr=False)
    exchange_api_secret: bytearray = field(repr=False)
    exchange_passphrase: bytearray | None = field(default=None, repr=False)
    runtime_api_username: bytearray = field(default_factory=bytearray, repr=False)
    runtime_api_password: bytearray = field(default_factory=bytearray, repr=False)
    _closed: bool = field(default=False, init=False, repr=False)

    @classmethod
    def from_values(
        cls,
        *,
        exchange_api_key: str,
        exchange_api_secret: str,
        exchange_passphrase: str | None,
        runtime_api_username: str,
        runtime_api_password: str,
    ) -> CredentialMaterial:
        return cls(
            exchange_api_key=_to_buffer(exchange_api_key) or bytearray(),
            exchange_api_secret=_to_buffer(exchange_api_secret) or bytearray(),
            exchange_passphrase=_to_buffer(exchange_passphrase),
            runtime_api_username=_to_buffer(runtime_api_username) or bytearray(),
            runtime_api_password=_to_buffer(runtime_api_password) or bytearray(),
        )

    def use_exchange(
        self,
        consumer: Callable[[bytes, bytes, bytes | None], T],
    ) -> T:
        self._require_open()
        passphrase = bytes(self.exchange_passphrase) if self.exchange_passphrase else None
        return consumer(
            bytes(self.exchange_api_key),
            bytes(self.exchange_api_secret),
            passphrase,
        )

    def use_runtime_api(self, consumer: Callable[[bytes, bytes], T]) -> T:
        self._require_open()
        return consumer(bytes(self.runtime_api_username), bytes(self.runtime_api_password))

    def clear(self) -> None:
        if self._closed:
            return
        for buffer in (
            self.exchange_api_key,
            self.exchange_api_secret,
            self.exchange_passphrase,
            self.runtime_api_username,
            self.runtime_api_password,
        ):
            _clear(buffer)
        self._closed = True

    @property
    def closed(self) -> bool:
        return self._closed

    def _require_open(self) -> None:
        if self._closed:
            raise CredentialPolicyError("CREDENTIAL_LEASE_CLOSED")

    def __del__(self) -> None:
        self.clear()


@dataclass
class ResolvedCredentialLease:
    evidence: CredentialLeaseEvidence
    _material: CredentialMaterial = field(repr=False)
    _closed: bool = field(default=False, init=False, repr=False)

    def use_exchange(
        self,
        consumer: Callable[[bytes, bytes, bytes | None], T],
    ) -> T:
        self._require_open()
        return self._material.use_exchange(consumer)

    def use_runtime_api(self, consumer: Callable[[bytes, bytes], T]) -> T:
        self._require_open()
        return self._material.use_runtime_api(consumer)

    def close(self) -> None:
        if self._closed:
            return
        self._material.clear()
        self._closed = True

    @property
    def closed(self) -> bool:
        return self._closed

    def _require_open(self) -> None:
        if self._closed:
            raise CredentialPolicyError("CREDENTIAL_LEASE_CLOSED")

    def __enter__(self) -> ResolvedCredentialLease:
        self._require_open()
        return self

    def __exit__(self, exc_type: object, exc: object, traceback: object) -> None:
        self.close()

    def __del__(self) -> None:
        self.close()
