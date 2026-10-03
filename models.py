"""
Data models and schemas for DEVSCOUT.
"""

from typing import Any
from pydantic import BaseModel, Field


class RequirementAnalysis(BaseModel):
    """
    Structured technical requirements extracted from a user's request.
    """
    goal: str = Field(
        ...,
        description="The core technical objective or problem to be solved.",
        min_length=1,
    )
    technologies: list[str] = Field(
        default_factory=list,
        description="Technologies, frameworks, databases, or languages mentioned or required.",
    )
    requirements: list[str] = Field(
        default_factory=list,
        description="Functional and non-functional technical requirements.",
    )
    constraints: list[str] = Field(
        default_factory=list,
        description="Constraints such as budget, scale, licensing, infrastructure, or latency.",
    )
    unknowns: list[str] = Field(
        default_factory=list,
        description="Ambiguities, unstated assumptions, or technical unknowns requiring further research.",
    )

    def to_dict(self) -> dict[str, Any]:
        """Convert the model into a standard Python dictionary."""
        return self.model_dump()
