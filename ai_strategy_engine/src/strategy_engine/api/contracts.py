from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class ValidateStrategyRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    strategy: dict
    generated_by_ai: bool = False


class ValidateStrategyResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    valid: bool
    errors: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)


class SubmitExperimentRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    strategy: dict
    search_space: dict
    dataset_id: str
    budget_trials: int = Field(ge=1, le=100_000)
