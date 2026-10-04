"""
Data models and schemas for DEVSCOUT.
"""

from typing import Any, Literal
from urllib.parse import urlparse
from pydantic import BaseModel, Field, field_validator


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


SourceType = Literal["web", "github", "rag"]
PriorityLevel = Literal["high", "medium", "low"]


class ResearchQuestion(BaseModel):
    """
    An individual research question to investigate before making an engineering decision.
    """
    question: str = Field(
        ...,
        description="The specific research question to be answered.",
        min_length=5,
    )
    priority: PriorityLevel = Field(
        ...,
        description="Importance ranking of the question: 'high', 'medium', or 'low'.",
    )
    source_types: list[SourceType] = Field(
        ...,
        description="Information sources suited for this question ('web', 'github', 'rag').",
        min_length=1,
    )
    rationale: str = Field(
        ...,
        description="Brief explanation of why this research question matters to the technical decision.",
        min_length=1,
    )

    @field_validator("priority", mode="before")
    @classmethod
    def normalize_priority(cls, v: Any) -> Any:
        if isinstance(v, str):
            return v.strip().lower()
        return v

    @field_validator("source_types", mode="before")
    @classmethod
    def normalize_source_types(cls, v: Any) -> Any:
        if isinstance(v, list):
            return [item.strip().lower() if isinstance(item, str) else item for item in v]
        return v


class ResearchPlan(BaseModel):
    """
    Structured research plan generated from technical requirements.
    """
    research_questions: list[ResearchQuestion] = Field(
        ...,
        description="Prioritized list of research questions to investigate.",
        min_length=1,
    )
    technologies_to_investigate: list[str] = Field(
        default_factory=list,
        description="Explicit and implied technologies, libraries, or concepts to research.",
    )

    def to_dict(self) -> dict[str, Any]:
        """Convert the plan into a standard Python dictionary."""
        return self.model_dump()

    def get_questions_by_priority(self, priority: PriorityLevel) -> list[ResearchQuestion]:
        """Filter research questions by priority level."""
        return [q for q in self.research_questions if q.priority == priority]

    def get_questions_by_source(self, source: SourceType) -> list[ResearchQuestion]:
        """Filter research questions by source type."""
        return [q for q in self.research_questions if source in q.source_types]


class ResearchTask(BaseModel):
    """
    An atomic, executable research task targeted at a specific connector (web, github, rag).
    """
    question: str = Field(
        ...,
        description="Specific question to be answered by the research connector.",
        min_length=1,
    )
    source_type: SourceType = Field(
        ...,
        description="Target research connector: 'web', 'github', or 'rag'.",
    )
    priority: PriorityLevel = Field(
        ...,
        description="Importance ranking of the task: 'high', 'medium', or 'low'.",
    )
    target: str = Field(
        ...,
        description="Technology, library, architecture, or concept being investigated.",
        min_length=1,
    )
    purpose: str = Field(
        ...,
        description="Why this investigation matters to the technical decision.",
        min_length=1,
    )

    @field_validator("source_type", mode="before")
    @classmethod
    def normalize_source_type(cls, v: Any) -> Any:
        if isinstance(v, str):
            return v.strip().lower()
        return v

    @field_validator("priority", mode="before")
    @classmethod
    def normalize_priority(cls, v: Any) -> Any:
        if isinstance(v, str):
            return v.strip().lower()
        return v

    @field_validator("question", "target", "purpose")
    @classmethod
    def validate_non_empty(cls, v: str) -> str:
        if not isinstance(v, str) or not v.strip():
            raise ValueError("Field cannot be empty or whitespace only.")
        return v.strip()

    def to_dict(self) -> dict[str, Any]:
        """Convert the task into a standard Python dictionary."""
        return self.model_dump()


class WebResearchResult(BaseModel):
    """
    Normalized result from a web research investigation for a specific research task.
    """
    title: str = Field(
        ...,
        description="Title of the web resource or article.",
        min_length=1,
    )
    url: str = Field(
        ...,
        description="Direct URL to the web resource.",
        min_length=1,
    )
    source: str = Field(
        ...,
        description="Domain or publishing source name (e.g. 'github.com', 'dev.to', 'timescale.com').",
        min_length=1,
    )
    snippet: str = Field(
        default="",
        description="Relevant content excerpt or summary from the web resource.",
    )
    task_question: str = Field(
        ...,
        description="The research task question this result addresses.",
        min_length=1,
    )
    query: str = Field(
        ...,
        description="The query string executed to find this result.",
        min_length=1,
    )

    @field_validator("title", "url", "source", "task_question", "query")
    @classmethod
    def validate_non_empty(cls, v: str) -> str:
        if not isinstance(v, str) or not v.strip():
            raise ValueError("Field cannot be empty or whitespace only.")
        return v.strip()

    @field_validator("url")
    @classmethod
    def validate_http_url(cls, v: str) -> str:
        parsed = urlparse(v)
        if parsed.scheme.lower() not in ("http", "https") or not parsed.netloc:
            raise ValueError(f"URL must have a valid http or https scheme and host: '{v}'")
        return v

    def to_dict(self) -> dict[str, Any]:
        """Convert the result into a standard Python dictionary."""
        return self.model_dump()



