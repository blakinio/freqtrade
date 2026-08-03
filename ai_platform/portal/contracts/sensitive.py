from __future__ import annotations

from typing import Annotated

from pydantic import AfterValidator

from ai_platform.portal.security.sensitive_data import validate_opaque_sensitive_reference


OpaqueSensitiveReference = Annotated[str, AfterValidator(validate_opaque_sensitive_reference)]
