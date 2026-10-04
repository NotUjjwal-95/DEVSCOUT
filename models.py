"""
Data models and schemas for DEVSCOUT.
"""

import hashlib
import re
from typing import Any, Literal
from urllib.parse import urlparse
from pydantic import BaseModel, Field, field_validator, model_validator


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


class GitHubResearchResult(BaseModel):
    """
    Normalized result from a GitHub repository investigation for a specific research task.
    """
    repo_name: str = Field(
        ...,
        description="Full repository name or identifier, e.g. 'owner/repo'.",
        min_length=1,
    )
    url: str = Field(
        ...,
        description="Direct HTTP/HTTPS URL to the repository.",
        min_length=1,
    )
    description: str = Field(
        default="",
        description="Repository description or summary.",
    )
    owner: str = Field(
        ...,
        description="GitHub organization or user login.",
        min_length=1,
    )
    stars: int = Field(
        default=0,
        description="Star count (stargazers_count).",
        ge=0,
    )
    forks: int = Field(
        default=0,
        description="Forks count.",
        ge=0,
    )
    language: str = Field(
        default="",
        description="Primary programming language.",
    )
    open_issues: int = Field(
        default=0,
        description="Open issues count.",
        ge=0,
    )
    last_updated: str = Field(
        default="",
        description="Last updated timestamp.",
    )
    task_question: str = Field(
        ...,
        description="The research task question this repository addresses.",
        min_length=1,
    )
    query: str = Field(
        ...,
        description="The query string executed to find this repository.",
        min_length=1,
    )

    @model_validator(mode="before")
    @classmethod
    def normalize_aliases(cls, data: Any) -> Any:
        if isinstance(data, dict):
            if "repo_name" not in data and "name" in data:
                data["repo_name"] = data["name"]
            elif "repo_name" not in data and "full_name" in data:
                data["repo_name"] = data["full_name"]
            if "last_updated" not in data and "updated_at" in data:
                data["last_updated"] = data["updated_at"]
        return data

    @field_validator("repo_name", "url", "owner", "task_question", "query")
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

    @field_validator("description", "language", "last_updated", mode="before")
    @classmethod
    def normalize_optional_strings(cls, v: Any) -> str:
        if v is None:
            return ""
        return str(v).strip()

    @field_validator("stars", "forks", "open_issues", mode="before")
    @classmethod
    def normalize_int_counts(cls, v: Any) -> int:
        if v is None:
            return 0
        try:
            val = int(v)
            return max(0, val)
        except (ValueError, TypeError):
            return 0

    @property
    def name(self) -> str:
        """Convenience property for repository name."""
        return self.repo_name

    def to_dict(self) -> dict[str, Any]:
        """Convert the result into a standard Python dictionary."""
        return self.model_dump()


class RAGResearchResult(BaseModel):
    """
    Normalized result from a RAG / vector knowledge base investigation for a research task.
    """
    title: str = Field(
        ...,
        description="Title or heading of the retrieved knowledge base document.",
        min_length=1,
    )
    content: str = Field(
        ...,
        description="Relevant text content or passage excerpt from the knowledge base.",
        min_length=1,
    )
    source: str = Field(
        ...,
        description="Originating source name, collection, or file path (e.g. 'internal-wiki', 'docs/arch.md').",
        min_length=1,
    )
    doc_id: str | None = Field(
        default=None,
        description="Unique identifier of the vector/document record if available.",
    )
    score: float | None = Field(
        default=None,
        description="Relevance or similarity score returned by the vector provider.",
    )
    task_question: str = Field(
        ...,
        description="The research task question this knowledge addresses.",
        min_length=1,
    )
    query: str = Field(
        ...,
        description="The query string executed to retrieve this result.",
        min_length=1,
    )

    @model_validator(mode="before")
    @classmethod
    def normalize_aliases(cls, data: Any) -> Any:
        if isinstance(data, dict):
            # Normalize content / snippet alias
            if "content" not in data and "snippet" in data:
                data["content"] = data["snippet"]
            # Normalize doc_id / id / document_id alias
            if "doc_id" not in data and "id" in data:
                data["doc_id"] = data["id"]
            elif "doc_id" not in data and "document_id" in data:
                data["doc_id"] = data["document_id"]
        return data

    @field_validator("title", "content", "source", "task_question", "query")
    @classmethod
    def validate_non_empty(cls, v: str) -> str:
        if not isinstance(v, str) or not v.strip():
            raise ValueError("Field cannot be empty or whitespace only.")
        return v.strip()

    @field_validator("doc_id", mode="before")
    @classmethod
    def validate_doc_id(cls, v: Any) -> str | None:
        if v is None:
            return None
        s = str(v).strip()
        return s if s else None

    @field_validator("score", mode="before")
    @classmethod
    def validate_score(cls, v: Any) -> float | None:
        if v is None:
            return None
        try:
            val = float(v)
            return val
        except (ValueError, TypeError):
            raise ValueError(f"Relevance score must be a valid numeric value, got: {v}")

    @property
    def snippet(self) -> str:
        """Convenience property for content."""
        return self.content

    def to_dict(self) -> dict[str, Any]:
        """Convert the result into a standard Python dictionary."""
        return self.model_dump()


def generate_stable_identifier(
    source_type: str,
    url: str | None = None,
    doc_id: str | None = None,
    repo_name: str | None = None,
    title: str = "",
    content: str = "",
) -> str:
    """
    Generate a deterministic, canonical identifier for an evidence item.
    """
    st = (source_type or "unknown").strip().lower()
    if st == "github":
        if repo_name and repo_name.strip():
            return f"github:{repo_name.strip().lower()}"
        if url and url.strip():
            clean_url = url.strip().lower().rstrip("/")
            parsed = urlparse(clean_url)
            path = parsed.path.strip("/")
            if path:
                return f"github:{path}"
            return f"github:{clean_url}"
    elif st == "web":
        if url and url.strip():
            clean_url = url.strip().lower().rstrip("/")
            return f"web:{clean_url}"
    elif st == "rag":
        if doc_id and doc_id.strip():
            return f"rag:{doc_id.strip().lower()}"
        if url and url.strip():
            return f"rag:{url.strip().lower().rstrip('/')}"

    norm_content = re.sub(r"\s+", " ", f"{title} {content[:200]}").strip().lower()
    content_hash = hashlib.sha256(norm_content.encode("utf-8")).hexdigest()[:16]
    return f"{st}:{content_hash}"


class Evidence(BaseModel):
    """
    Canonical representation of a piece of research evidence collected from
    Web, GitHub, or RAG sources, preserving provenance and supporting ranking.
    """
    source_type: SourceType = Field(
        ...,
        description="Source connector that gathered this evidence: 'web', 'github', or 'rag'.",
    )
    title: str = Field(
        ...,
        description="Title, headline, or repository identifier of the evidence.",
        min_length=1,
    )
    content: str = Field(
        ...,
        description="Substantive text content, excerpt, description, or snippet.",
        min_length=1,
    )
    url: str | None = Field(
        default=None,
        description="Canonical URL or web link to the evidence if applicable.",
    )
    source: str = Field(
        ...,
        description="Originating source identifier (e.g. domain name, repository owner/name, document collection).",
        min_length=1,
    )
    identifier: str = Field(
        default="",
        description="Deterministic, unique identifier for deduplication (e.g. 'web:url', 'github:owner/repo', 'rag:doc-id').",
    )
    task_question: str = Field(
        ...,
        description="The research task question this evidence directly addresses.",
        min_length=1,
    )
    task_priority: PriorityLevel = Field(
        default="medium",
        description="Priority level of the originating research task ('high', 'medium', 'low').",
    )
    query: str = Field(
        ...,
        description="The exact query executed that produced this evidence item.",
        min_length=1,
    )
    relevance_score: float | None = Field(
        default=None,
        description="Explicit relevance or similarity score from the underlying retrieval provider if available.",
    )
    rank_score: float = Field(
        default=0.0,
        description="Deterministic composite rank score calculated by the Evidence Layer.",
    )
    metadata: dict[str, Any] = Field(
        default_factory=dict,
        description="Source-specific metadata attributes (e.g. stars, forks, language, doc_id).",
    )

    @model_validator(mode="before")
    @classmethod
    def normalize_evidence_data(cls, data: Any) -> Any:
        if isinstance(data, dict):
            # Normalize source_type
            if "source_type" in data and isinstance(data["source_type"], str):
                data["source_type"] = data["source_type"].strip().lower()
            # Normalize task_priority
            if "task_priority" in data and isinstance(data["task_priority"], str):
                data["task_priority"] = data["task_priority"].strip().lower()
            # Normalize content from aliases
            if "content" not in data or not data["content"]:
                if "description" in data and data["description"]:
                    data["content"] = str(data["description"]).strip()
                elif "snippet" in data and data["snippet"]:
                    data["content"] = str(data["snippet"]).strip()
            # Auto-infer source if missing
            if "source" not in data or not data["source"]:
                st = data.get("source_type")
                if st == "github":
                    data["source"] = data.get("metadata", {}).get("repo_name") or "github.com"
                elif st == "web" and data.get("url"):
                    data["source"] = urlparse(data["url"]).netloc or "web"
                elif st == "rag":
                    data["source"] = "rag-knowledge-base"
                else:
                    data["source"] = "unknown"
            # Auto-infer identifier if missing or empty
            if "identifier" not in data or not data["identifier"]:
                data["identifier"] = generate_stable_identifier(
                    source_type=data.get("source_type", "unknown"),
                    url=data.get("url"),
                    doc_id=data.get("metadata", {}).get("doc_id"),
                    repo_name=data.get("metadata", {}).get("repo_name"),
                    title=str(data.get("title", "")),
                    content=str(data.get("content", "")),
                )
        return data

    @field_validator("title", "content", "source", "identifier", "task_question", "query")
    @classmethod
    def validate_non_empty(cls, v: str) -> str:
        if not isinstance(v, str) or not v.strip():
            raise ValueError("Field cannot be empty or whitespace only.")
        return v.strip()

    @field_validator("url")
    @classmethod
    def validate_url_if_present(cls, v: str | None) -> str | None:
        if v is None:
            return None
        v_clean = v.strip()
        if not v_clean:
            return None
        parsed = urlparse(v_clean)
        if parsed.scheme.lower() not in ("http", "https") or not parsed.netloc:
            raise ValueError(f"URL must have a valid http or https scheme and host: '{v}'")
        return v_clean

    @field_validator("relevance_score", "rank_score", mode="before")
    @classmethod
    def normalize_scores(cls, v: Any) -> float | None:
        if v is None:
            return None
        try:
            return float(v)
        except (ValueError, TypeError):
            raise ValueError(f"Score must be a valid numeric value, got: {v}")

    @property
    def description(self) -> str:
        """Alias property for content."""
        return self.content

    @property
    def snippet(self) -> str:
        """Alias property for content."""
        return self.content

    def to_dict(self) -> dict[str, Any]:
        """Convert the model into a standard Python dictionary."""
        return self.model_dump()


class EvidenceGroup(BaseModel):
    """
    Collection of normalized evidence items grouped under a specific research question.
    """
    task_question: str = Field(
        ...,
        description="The research question grouping these evidence items.",
        min_length=1,
    )
    items: list[Evidence] = Field(
        default_factory=list,
        description="List of evidence items addressing this question.",
    )

    @field_validator("task_question")
    @classmethod
    def validate_task_question(cls, v: str) -> str:
        if not isinstance(v, str) or not v.strip():
            raise ValueError("task_question cannot be empty.")
        return v.strip()

    @property
    def total_count(self) -> int:
        return len(self.items)

    @property
    def web_count(self) -> int:
        return sum(1 for e in self.items if e.source_type == "web")

    @property
    def github_count(self) -> int:
        return sum(1 for e in self.items if e.source_type == "github")

    @property
    def rag_count(self) -> int:
        return sum(1 for e in self.items if e.source_type == "rag")

    def by_source_type(self) -> dict[SourceType, list[Evidence]]:
        """Return evidence items partitioned by source type."""
        grouped: dict[SourceType, list[Evidence]] = {"web": [], "github": [], "rag": []}
        for item in self.items:
            grouped[item.source_type].append(item)
        return grouped

    def to_dict(self) -> dict[str, Any]:
        """Convert the group into a standard Python dictionary."""
        return self.model_dump()






