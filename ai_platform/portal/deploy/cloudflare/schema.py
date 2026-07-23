from __future__ import annotations

import re
from enum import StrEnum
from typing import Literal

from pydantic import BaseModel, ConfigDict, field_validator


_ENV_REF = re.compile(r"^[A-Z][A-Z0-9_]*$")


class AccessSurface(StrEnum):
    ADMIN = "admin"
    RESEARCH = "research"
    MODEL_PROMOTION = "model_promotion"
    INFRASTRUCTURE = "infrastructure"
    E2E = "e2e"


class RateLimitFamily(StrEnum):
    AUTHENTICATION = "authentication"
    PASSWORD_RECOVERY = "password_recovery"
    MFA = "mfa"
    EXCHANGE_CREDENTIALS = "exchange_credentials"
    BOT_LIFECYCLE = "bot_lifecycle"
    TERMINAL_INTENT = "terminal_intent"
    MODEL_PROMOTION = "model_promotion"
    ADMIN = "admin"


class StagingIngressPolicy(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    schema_version: Literal[1] = 1
    environment: Literal["staging"] = "staging"
    tunnel_required: Literal[True] = True
    origin_public_ingress_allowed: Literal[False] = False
    freqtrade_public_ingress_allowed: Literal[False] = False
    execution_mode: Literal["simulated"] = "simulated"
    managed_waf_enabled: Literal[True] = True
    privileged_surfaces: tuple[AccessSurface, ...]
    rate_limit_families: tuple[RateLimitFamily, ...]
    public_base_url_env: str
    privileged_path_env: str
    origin_probe_url_env: str
    freqtrade_probe_url_env: str
    access_client_id_env: str
    access_client_secret_env: str

    @field_validator(
        "public_base_url_env",
        "privileged_path_env",
        "origin_probe_url_env",
        "freqtrade_probe_url_env",
        "access_client_id_env",
        "access_client_secret_env",
    )
    @classmethod
    def validate_env_reference(cls, value: str) -> str:
        if not _ENV_REF.fullmatch(value):
            raise ValueError("staging secret/config references must be environment variable names")
        return value
