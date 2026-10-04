"""
Data models and schemas for DEVSCOUT.
"""

import hashlib
import re
from typing import Any, Literal, Sequence
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
    ev_id: str | None = Field(
        default=None,
        description="Reasoning-facing reference identifier (e.g. 'EV-001') assigned within an EvidenceContext.",
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

    @field_validator("ev_id")
    @classmethod
    def validate_ev_id_format(cls, v: str | None) -> str | None:
        if v is None:
            return None
        v_clean = v.strip().upper()
        if not re.match(r"^EV-\d{3,}$", v_clean):
            raise ValueError(
                f"Invalid evidence reference ID format '{v}'. Expected pattern 'EV-xxx' (e.g. 'EV-001')."
            )
        return v_clean

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

    @property
    def evidence_ids(self) -> list[str]:
        """Return the list of reasoning-facing EV reference IDs for items in this group."""
        return [e.ev_id for e in self.items if e.ev_id]

    def to_dict(self) -> dict[str, Any]:
        """Convert the group into a standard Python dictionary."""
        return self.model_dump()


class EvidenceReferenceError(KeyError):
    """Raised when an evidence reference ID (e.g. 'EV-007') cannot be found or resolved in an EvidenceContext."""
    pass


class EvidenceContext(BaseModel):
    """
    Validated research context packaging the original request, requirement analysis,
    plan, atomic tasks, and grouped evidence with reasoning-facing EV reference IDs.
    Establishes the deterministic contract consumed by the future Reasoning Engine.
    """
    user_request: str = Field(
        ...,
        description="The original, raw technical request submitted by the user.",
        min_length=1,
    )
    requirements: RequirementAnalysis = Field(
        ...,
        description="Validated technical requirements extracted from the user request.",
    )
    plan: ResearchPlan = Field(
        ...,
        description="Validated research plan containing prioritized questions.",
    )
    tasks: list[ResearchTask] = Field(
        ...,
        description="List of atomic, executable research tasks across connectors.",
        min_length=1,
    )
    evidence_groups: list[EvidenceGroup] = Field(
        default_factory=list,
        description="Evidence items grouped under their corresponding research questions.",
    )
    evidence_map: dict[str, Evidence] = Field(
        default_factory=dict,
        description="Lookup map resolving reasoning-facing references ('EV-001') to Evidence objects.",
    )

    @field_validator("user_request")
    @classmethod
    def validate_user_request(cls, v: str) -> str:
        if not isinstance(v, str) or not v.strip():
            raise ValueError("user_request cannot be empty or whitespace only.")
        return v.strip()

    @field_validator("tasks")
    @classmethod
    def validate_tasks_list(cls, v: list[ResearchTask]) -> list[ResearchTask]:
        if not v:
            raise ValueError("EvidenceContext requires at least one ResearchTask.")
        for idx, task in enumerate(v):
            if not isinstance(task, ResearchTask):
                raise ValueError(f"Task at index {idx} is not a ResearchTask instance.")
        return v

    @model_validator(mode="before")
    @classmethod
    def auto_index_evidence(cls, data: Any) -> Any:
        if not isinstance(data, dict):
            return data

        groups = data.get("evidence_groups") or []
        evidence_map = data.get("evidence_map") or {}

        # Mappings for tracking and conflict detection
        ev_id_to_ident: dict[str, str] = {}  # uppercase EV-xxx -> canonical lowercase identifier
        ident_to_ev_id: dict[str, str] = {}  # canonical lowercase identifier -> uppercase EV-xxx
        ev_id_to_item: dict[str, Any] = {}   # uppercase EV-xxx -> Evidence object or dict

        def _get_ident(item: Any) -> str:
            if hasattr(item, "identifier") and item.identifier:
                return str(item.identifier).strip().lower()
            if isinstance(item, dict):
                if item.get("identifier"):
                    return str(item["identifier"]).strip().lower()
                ident = generate_stable_identifier(
                    source_type=item.get("source_type", "unknown"),
                    url=item.get("url"),
                    doc_id=item.get("metadata", {}).get("doc_id") if isinstance(item.get("metadata"), dict) else None,
                    repo_name=item.get("metadata", {}).get("repo_name") if isinstance(item.get("metadata"), dict) else None,
                    title=str(item.get("title", "")),
                    content=str(item.get("content", "")),
                )
                item["identifier"] = ident
                return ident.strip().lower()
            return ""

        def _get_ev_id(item: Any) -> str | None:
            if hasattr(item, "ev_id"):
                return str(item.ev_id).strip() if item.ev_id else None
            if isinstance(item, dict):
                v = item.get("ev_id")
                return str(v).strip() if v else None
            return None

        def _set_ev_id(item: Any, val: str) -> None:
            if hasattr(item, "ev_id"):
                item.ev_id = val
            elif isinstance(item, dict):
                item["ev_id"] = val

        # Step 1: Inspect and register evidence_map if provided
        if evidence_map and isinstance(evidence_map, dict):
            for ref_id, item in list(evidence_map.items()):
                ref_clean = str(ref_id).strip().upper()
                if not re.match(r"^EV-\d{3,}$", ref_clean):
                    raise ValueError(
                        f"Invalid evidence reference key '{ref_id}' in evidence_map. Expected pattern 'EV-xxx' (e.g. 'EV-001')."
                    )

                ident = _get_ident(item)
                if not ident:
                    raise ValueError(f"Evidence item for '{ref_id}' in evidence_map lacks a valid identifier.")

                item_ev_id = _get_ev_id(item)
                if item_ev_id:
                    item_ev_id_clean = item_ev_id.upper()
                    if not re.match(r"^EV-\d{3,}$", item_ev_id_clean):
                        raise ValueError(
                            f"Invalid evidence reference ID format '{item_ev_id}' on Evidence object. Expected pattern 'EV-xxx'."
                        )
                    if item_ev_id_clean != ref_clean:
                        raise ValueError(
                            f"Mismatched evidence reference: key is '{ref_id}' but Evidence item has ev_id='{item_ev_id}'."
                        )
                _set_ev_id(item, ref_clean)

                # Conflict Check 1: Duplicate EV ID claimed by different evidence
                if ref_clean in ev_id_to_ident:
                    if ev_id_to_ident[ref_clean] != ident:
                        raise ValueError(
                            f"Conflicting EV ID '{ref_clean}': assigned to both '{ev_id_to_ident[ref_clean]}' and '{ident}'. "
                            f"No two different Evidence objects can claim the same EV ID."
                        )
                else:
                    ev_id_to_ident[ref_clean] = ident

                # Conflict Check 2: Same evidence claiming multiple EV IDs
                if ident in ident_to_ev_id:
                    if ident_to_ev_id[ident] != ref_clean:
                        raise ValueError(
                            f"Conflicting EV ID for evidence '{ident}': already assigned '{ident_to_ev_id[ident]}', "
                            f"cannot also claim '{ref_clean}'. An Evidence item cannot have multiple EV IDs."
                        )
                else:
                    ident_to_ev_id[ident] = ref_clean

                ev_id_to_item[ref_clean] = item

        # Collect all items from evidence_groups
        group_items: list[Any] = []
        if groups:
            for group in groups:
                items = group.items if hasattr(group, "items") else (group.get("items", []) if isinstance(group, dict) else [])
                for item in items:
                    group_items.append(item)

        # Step 2: Pass 1 on group_items - Validate & register all pre-existing ev_id values
        for item in group_items:
            existing_id = _get_ev_id(item)
            if not existing_id:
                continue

            norm_id = existing_id.upper()
            if not re.match(r"^EV-\d{3,}$", norm_id):
                raise ValueError(
                    f"Invalid evidence reference ID format '{existing_id}'. Expected pattern 'EV-xxx' (e.g. 'EV-001')."
                )

            ident = _get_ident(item)
            if not ident:
                continue

            # Conflict Check 1: Duplicate EV ID claimed by different evidence
            if norm_id in ev_id_to_ident:
                if ev_id_to_ident[norm_id] != ident:
                    raise ValueError(
                        f"Conflicting EV ID '{norm_id}': assigned to both '{ev_id_to_ident[norm_id]}' and '{ident}'. "
                        f"No two different Evidence objects can claim the same EV ID."
                    )
            else:
                ev_id_to_ident[norm_id] = ident

            # Conflict Check 2: Same evidence claiming multiple EV IDs
            if ident in ident_to_ev_id:
                if ident_to_ev_id[ident] != norm_id:
                    raise ValueError(
                        f"Conflicting EV ID for evidence '{ident}': already assigned '{ident_to_ev_id[ident]}', "
                        f"cannot also claim '{norm_id}'. An Evidence item cannot have multiple EV IDs."
                    )
            else:
                ident_to_ev_id[ident] = norm_id

            _set_ev_id(item, norm_id)
            if norm_id not in ev_id_to_item:
                ev_id_to_item[norm_id] = item

        # Step 3: Pass 2 on group_items - Auto-assign EV IDs for items where ev_id is None
        next_counter = 1
        for item in group_items:
            ident = _get_ident(item)
            if not ident:
                continue

            existing_id = _get_ev_id(item)
            if existing_id:
                # Already registered in Pass 1, ensure assigned ID is consistent
                assigned_id = ident_to_ev_id[ident]
                _set_ev_id(item, assigned_id)
                continue

            # If this identifier was already assigned an EV ID (e.g. from Pass 1 or another group)
            if ident in ident_to_ev_id:
                assigned_id = ident_to_ev_id[ident]
                _set_ev_id(item, assigned_id)
                continue

            # Find next available sequential EV ID not colliding with any pre-existing or auto-generated ID
            while f"EV-{next_counter:03d}" in ev_id_to_ident:
                next_counter += 1

            assigned_id = f"EV-{next_counter:03d}"
            next_counter += 1

            ev_id_to_ident[assigned_id] = ident
            ident_to_ev_id[ident] = assigned_id
            ev_id_to_item[assigned_id] = item
            _set_ev_id(item, assigned_id)

        # Step 4: Populate evidence_map with clean, numerically sorted mapping
        def _ev_sort_key(k: str) -> tuple[int, str]:
            parts = k.split("-")
            if len(parts) == 2 and parts[1].isdigit():
                return (int(parts[1]), k)
            return (999999, k)

        sorted_map = {k: ev_id_to_item[k] for k in sorted(ev_id_to_item.keys(), key=_ev_sort_key)}
        data["evidence_map"] = sorted_map

        return data

    @field_validator("evidence_map")
    @classmethod
    def validate_evidence_map(cls, v: dict[str, Evidence]) -> dict[str, Evidence]:
        seen_idents: dict[str, str] = {}
        for ref_id, item in v.items():
            if not re.match(r"^EV-\d{3,}$", ref_id):
                raise ValueError(
                    f"Invalid evidence reference key '{ref_id}' in evidence_map. Expected pattern 'EV-xxx' (e.g. 'EV-001')."
                )
            if not isinstance(item, Evidence):
                raise ValueError(
                    f"Evidence map entry for '{ref_id}' must be an Evidence instance, got {type(item).__name__}."
                )
            if item.ev_id and item.ev_id != ref_id:
                raise ValueError(
                    f"Mismatched evidence reference: key is '{ref_id}' but Evidence item has ev_id='{item.ev_id}'."
                )
            ident = item.identifier.strip().lower()
            if ident in seen_idents:
                raise ValueError(
                    f"Duplicate evidence identifier in evidence_map: '{ident}' is mapped to both '{seen_idents[ident]}' and '{ref_id}'. "
                    f"An Evidence item cannot have multiple EV IDs."
                )
            seen_idents[ident] = ref_id
        return v

    @model_validator(mode="after")
    def validate_group_and_map_consistency(self) -> "EvidenceContext":
        for group in self.evidence_groups:
            for item in group.items:
                if not item.ev_id:
                    raise ValueError(
                        f"Evidence item '{item.identifier}' in group '{group.task_question}' has no ev_id assigned."
                    )
                if item.ev_id not in self.evidence_map:
                    raise ValueError(f"Evidence item ev_id '{item.ev_id}' missing from evidence_map.")
                map_item = self.evidence_map[item.ev_id]
                if map_item.identifier.strip().lower() != item.identifier.strip().lower():
                    raise ValueError(
                        f"Mismatched evidence: item '{item.identifier}' in group '{group.task_question}' has ev_id '{item.ev_id}', "
                        f"which resolves to '{map_item.identifier}' in evidence_map."
                    )
        return self

    def get_evidence(self, ev_id: str) -> Evidence:
        """
        Retrieve an Evidence item by its reasoning-facing reference ID (e.g. 'EV-001').
        Raises EvidenceReferenceError if the reference is not found.
        """
        ref_clean = ev_id.strip().upper()
        if ref_clean not in self.evidence_map:
            raise EvidenceReferenceError(
                f"Evidence reference '{ev_id}' not found in EvidenceContext. "
                f"Available references: {list(self.evidence_map.keys())}"
            )
        return self.evidence_map[ref_clean]

    def resolve_reference(self, ev_id: str) -> Evidence:
        """Alias for get_evidence."""
        return self.get_evidence(ev_id)

    def resolve_references(self, ev_ids: Sequence[str]) -> list[Evidence]:
        """
        Resolve a sequence of reasoning-facing references (e.g. ['EV-001', 'EV-003'])
        into their underlying Evidence objects. Raises EvidenceReferenceError if any ID is missing.
        """
        return [self.get_evidence(ref_id) for ref_id in ev_ids]

    def get_evidence_by_identifier(self, identifier: str) -> Evidence | None:
        """
        Lookup an evidence item by its underlying technical identifier (e.g. 'github:owner/repo').
        """
        ident_clean = identifier.strip().lower()
        for ev in self.evidence_map.values():
            if ev.identifier.strip().lower() == ident_clean:
                return ev
        return None

    def get_group_for_question(self, question: str) -> EvidenceGroup | None:
        """Retrieve the evidence group matching the given research question."""
        q_clean = question.strip().lower()
        for group in self.evidence_groups:
            if group.task_question.strip().lower() == q_clean:
                return group
        return None

    def get_evidence_ids_for_question(self, question: str) -> list[str]:
        """
        Return the reasoning-facing EV reference IDs for all evidence items
        associated with a research question.
        """
        group = self.get_group_for_question(question)
        if not group:
            return []
        return [e.ev_id for e in group.items if e.ev_id]

    @property
    def total_evidence_count(self) -> int:
        """Total number of unique indexed evidence items."""
        return len(self.evidence_map)

    def to_reasoning_summary(self) -> dict[str, Any]:
        """
        Produce a clean, structured summary mapping research questions to their
        reasoning-facing evidence IDs.
        """
        return {
            "user_request": self.user_request,
            "goal": self.requirements.goal,
            "total_tasks": len(self.tasks),
            "total_evidence_items": self.total_evidence_count,
            "questions": [
                {
                    "question": g.task_question,
                    "evidence_ids": [e.ev_id for e in g.items if e.ev_id],
                    "evidence_count": g.total_count,
                    "breakdown": {
                        "web": g.web_count,
                        "github": g.github_count,
                        "rag": g.rag_count,
                    },
                }
                for g in self.evidence_groups
            ],
        }

    def format_for_reasoning(self) -> str:
        """
        Format the evidence context into a clean, markdown representation
        ready for the future Reasoning Engine.
        """
        lines: list[str] = [
            f"# Technical Research Context",
            f"**Goal**: {self.requirements.goal}",
            f"**Technologies**: {', '.join(self.requirements.technologies) if self.requirements.technologies else 'None specified'}",
            f"",
            f"## Research Questions & Indexed Evidence",
        ]

        for q_idx, group in enumerate(self.evidence_groups, start=1):
            lines.append(f"### Question {q_idx}: {group.task_question}")
            if not group.items:
                lines.append("  *(No evidence retrieved for this question)*")
            else:
                for item in group.items:
                    ref_tag = f"[{item.ev_id}]" if item.ev_id else "[EV-???]"
                    src_badge = f"({item.source_type.upper()})"
                    score_info = f" [Score: {item.rank_score:.3f}]" if item.rank_score else ""
                    lines.append(f"- **{ref_tag}** {src_badge} *{item.title}*{score_info}")
                    if item.url:
                        lines.append(f"  Source URL: {item.url}")
                    lines.append(f"  Excerpt: {item.content}")
            lines.append("")

        return "\n".join(lines).strip()

    def to_dict(self) -> dict[str, Any]:
        """Convert the context model into a standard Python dictionary."""
        return self.model_dump()







