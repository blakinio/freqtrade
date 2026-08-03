from __future__ import annotations

from typing import Annotated

from pydantic import AfterValidator

from ai_platform.portal.security.sensitive_data import validate_opaque_sensitive_reference


def validate_public_opaque_sensitive_reference(value: str) -> str:
    """Restrict public references to scheme-free opaque domain identifiers."""

    validated = validate_opaque_sensitive_reference(value)
    if ":" in validated:
        raise ValueError("opaque public reference must not contain a URI scheme or namespace")
    return validated


OpaqueSensitiveReference = Annotated[
    str,
    AfterValidator(validate_public_opaque_sensitive_reference),
]
