from __future__ import annotations

import pytest
from pydantic import TypeAdapter, ValidationError

from ai_platform.portal.contracts.sensitive import OpaqueSensitiveReference


_ADAPTER = TypeAdapter(OpaqueSensitiveReference)


def test_public_opaque_reference_accepts_scheme_free_domain_identifier() -> None:
    assert _ADAPTER.validate_python("exchange-connection-1") == "exchange-connection-1"


@pytest.mark.parametrize(
    "value",
    [
        "vault:tenant-a-exchange",
        "secret:exchange-primary",
        "urn:portal:credential",
    ],
)
def test_public_opaque_reference_rejects_scheme_or_namespace(value: str) -> None:
    with pytest.raises(ValidationError, match="URI scheme or namespace"):
        _ADAPTER.validate_python(value)
