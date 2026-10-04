"""
Evidence Layer for DEVSCOUT.
Normalizes, deduplicates, ranks, and groups research results from Web, GitHub,
and RAG connectors into canonical Evidence representations with preserved provenance.
"""

import math
import re
from typing import Any, Sequence
from urllib.parse import urlparse

from models import (
    Evidence,
    EvidenceGroup,
    GitHubResearchResult,
    PriorityLevel,
    RAGResearchResult,
    SourceType,
    WebResearchResult,
    generate_stable_identifier,
)


class EvidenceError(Exception):
    """Base exception for all Evidence Layer errors."""
    pass


class EvidenceValidationError(EvidenceError):
    """Raised when an evidence input violates schema or constraints."""
    pass


class EvidenceProcessingError(EvidenceError):
    """Raised when evidence processing, deduplication, or ranking fails."""
    pass


def from_web_result(
    result: WebResearchResult,
    task_priority: PriorityLevel = "medium",
) -> Evidence:
    """
    Convert a WebResearchResult into a canonical Evidence item with preserved provenance.
    """
    if not isinstance(result, WebResearchResult):
        raise EvidenceValidationError(
            f"Expected WebResearchResult, got {type(result).__name__}"
        )

    content = result.snippet.strip() or result.title.strip()
    identifier = generate_stable_identifier(
        source_type="web",
        url=result.url,
        title=result.title,
        content=content,
    )

    return Evidence(
        source_type="web",
        title=result.title.strip(),
        content=content,
        url=result.url.strip(),
        source=result.source.strip() or (urlparse(result.url).netloc or "web"),
        identifier=identifier,
        task_question=result.task_question.strip(),
        task_priority=task_priority,
        query=result.query.strip(),
        relevance_score=None,
        metadata={
            "source": result.source.strip(),
            "domain": urlparse(result.url).netloc,
        },
    )


def from_github_result(
    result: GitHubResearchResult,
    task_priority: PriorityLevel = "medium",
) -> Evidence:
    """
    Convert a GitHubResearchResult into a canonical Evidence item with preserved provenance.
    """
    if not isinstance(result, GitHubResearchResult):
        raise EvidenceValidationError(
            f"Expected GitHubResearchResult, got {type(result).__name__}"
        )

    content = (
        result.description.strip()
        or f"GitHub repository {result.repo_name} ({result.language or 'Codebase'}) with {result.stars:,} stars."
    )
    identifier = generate_stable_identifier(
        source_type="github",
        url=result.url,
        repo_name=result.repo_name,
        title=result.repo_name,
        content=content,
    )

    return Evidence(
        source_type="github",
        title=result.repo_name.strip(),
        content=content,
        url=result.url.strip(),
        source=result.owner.strip() or f"github/{result.repo_name.split('/')[0]}",
        identifier=identifier,
        task_question=result.task_question.strip(),
        task_priority=task_priority,
        query=result.query.strip(),
        relevance_score=None,
        metadata={
            "owner": result.owner.strip(),
            "repo_name": result.repo_name.strip(),
            "stars": result.stars,
            "forks": result.forks,
            "language": result.language.strip(),
            "open_issues": result.open_issues,
            "last_updated": result.last_updated.strip(),
        },
    )


def from_rag_result(
    result: RAGResearchResult,
    task_priority: PriorityLevel = "medium",
) -> Evidence:
    """
    Convert a RAGResearchResult into a canonical Evidence item with preserved provenance.
    """
    if not isinstance(result, RAGResearchResult):
        raise EvidenceValidationError(
            f"Expected RAGResearchResult, got {type(result).__name__}"
        )

    content = result.content.strip()
    identifier = generate_stable_identifier(
        source_type="rag",
        doc_id=result.doc_id,
        url=result.source if result.source.startswith(("http://", "https://")) else None,
        title=result.title,
        content=content,
    )

    url = result.source if result.source.startswith(("http://", "https://")) else None

    return Evidence(
        source_type="rag",
        title=result.title.strip(),
        content=content,
        url=url,
        source=result.source.strip() or "internal-knowledge-base",
        identifier=identifier,
        task_question=result.task_question.strip(),
        task_priority=task_priority,
        query=result.query.strip(),
        relevance_score=result.score,
        metadata={
            "source": result.source.strip(),
            "doc_id": result.doc_id,
        },
    )


def normalize_evidence(
    item: Any,
    task_priority: PriorityLevel = "medium",
) -> Evidence:
    """
    Deterministically normalize any supported research result or dictionary into an Evidence model.
    """
    if isinstance(item, Evidence):
        return item
    if isinstance(item, WebResearchResult):
        return from_web_result(item, task_priority=task_priority)
    if isinstance(item, GitHubResearchResult):
        return from_github_result(item, task_priority=task_priority)
    if isinstance(item, RAGResearchResult):
        return from_rag_result(item, task_priority=task_priority)

    if isinstance(item, dict):
        source_type = str(item.get("source_type", "")).strip().lower()
        try:
            if source_type == "web":
                web_res = WebResearchResult.model_validate(item)
                return from_web_result(web_res, task_priority=task_priority)
            if source_type == "github":
                gh_res = GitHubResearchResult.model_validate(item)
                return from_github_result(gh_res, task_priority=task_priority)
            if source_type == "rag":
                rag_res = RAGResearchResult.model_validate(item)
                return from_rag_result(rag_res, task_priority=task_priority)
            # Direct evidence dictionary
            return Evidence.model_validate(item)
        except Exception as e:
            raise EvidenceValidationError(f"Failed to validate evidence dictionary: {e}") from e

    raise EvidenceValidationError(
        f"Unsupported result type for evidence normalization: {type(item).__name__}"
    )


def normalize_results(
    items: Sequence[Any],
    task_priority: PriorityLevel = "medium",
) -> list[Evidence]:
    """
    Normalize an iterable of research results into canonical Evidence objects.
    """
    evidence_list: list[Evidence] = []
    for idx, item in enumerate(items):
        try:
            evidence = normalize_evidence(item, task_priority=task_priority)
            evidence_list.append(evidence)
        except EvidenceValidationError:
            raise
        except Exception as e:
            raise EvidenceProcessingError(
                f"Error normalizing research result at index {idx}: {e}"
            ) from e
    return evidence_list


def deduplicate_evidence(evidence_list: Sequence[Evidence]) -> list[Evidence]:
    """
    Deduplicate a sequence of Evidence items deterministically.
    Prefers stable identifiers (URL, repo name, document ID), and merges / preserves
    the highest-quality candidate when duplicates exist.
    """
    seen_identifiers: dict[str, Evidence] = {}
    seen_urls: dict[str, str] = {}  # normalized url -> primary identifier
    seen_content_hashes: dict[str, str] = {}  # content hash -> primary identifier
    order: list[str] = []

    priority_weight = {"high": 3, "medium": 2, "low": 1}

    for item in evidence_list:
        if not isinstance(item, Evidence):
            raise EvidenceValidationError(
                f"Expected Evidence instance in deduplicate_evidence, got {type(item).__name__}"
            )

        ident = item.identifier.strip().lower()
        norm_url = item.url.strip().lower().rstrip("/") if item.url else ""

        # Normalize content for content-level duplicate detection
        clean_text = re.sub(r"\s+", " ", f"{item.title.lower()} {item.content[:200].lower()}").strip()

        # Check existing match
        match_id: str | None = None
        if ident in seen_identifiers:
            match_id = ident
        elif norm_url and norm_url in seen_urls:
            match_id = seen_urls[norm_url]
        elif clean_text in seen_content_hashes:
            match_id = seen_content_hashes[clean_text]

        if match_id is None:
            # New unique evidence
            seen_identifiers[ident] = item
            order.append(ident)
            if norm_url:
                seen_urls[norm_url] = ident
            seen_content_hashes[clean_text] = ident
        else:
            # Duplicate found: compare existing vs new to retain the higher-signal candidate
            existing = seen_identifiers[match_id]
            replace = False

            # Signal 1: explicit relevance score
            ex_score = existing.relevance_score if existing.relevance_score is not None else -1.0
            new_score = item.relevance_score if item.relevance_score is not None else -1.0
            if new_score > ex_score:
                replace = True
            elif new_score == ex_score:
                # Signal 2: task priority
                ex_prio = priority_weight.get(existing.task_priority, 1)
                new_prio = priority_weight.get(item.task_priority, 1)
                if new_prio > ex_prio:
                    replace = True
                elif new_prio == ex_prio:
                    # Signal 3: content completeness / length
                    if len(item.content) > len(existing.content):
                        replace = True

            if replace:
                seen_identifiers[match_id] = item

    return [seen_identifiers[k] for k in order]


def calculate_evidence_rank_score(evidence: Evidence) -> float:
    """
    Deterministically calculate a composite rank score in [0.0, 1.0] for an Evidence item.
    Factors in:
    1. Task priority (up to 0.30)
    2. Source type weight (up to 0.20)
    3. Explicit or heuristic relevance signal (up to 0.35)
    4. Evidence completeness & provenance (up to 0.15)
    """
    # 1. Task Priority Signal (0.0 to 0.30)
    priority_scores = {
        "high": 0.30,
        "medium": 0.18,
        "low": 0.08,
    }
    prio_score = priority_scores.get(evidence.task_priority, 0.15)

    # 2. Source Type Base Signal (0.0 to 0.20)
    source_type_scores = {
        "rag": 0.20,      # Internal domain/architecture knowledge
        "github": 0.16,   # Code implementation & repository proofs
        "web": 0.12,      # External documentation & articles
    }
    st_score = source_type_scores.get(evidence.source_type, 0.10)

    # 3. Explicit or Source-Specific Relevance Signal (0.0 to 0.35)
    rel_score = 0.0
    if evidence.relevance_score is not None:
        # Scale provider relevance score (typically 0.0 - 1.0)
        norm_score = max(0.0, min(1.0, float(evidence.relevance_score)))
        rel_score = norm_score * 0.35
    elif evidence.source_type == "github":
        # Heuristic star signal on logarithmic scale
        stars = evidence.metadata.get("stars", 0)
        if isinstance(stars, (int, float)) and stars > 0:
            star_ratio = min(1.0, math.log10(stars + 1) / 4.5)  # 30,000+ stars ~= 1.0
            rel_score = star_ratio * 0.30
        else:
            rel_score = 0.10
    elif evidence.source_type == "web":
        # Web baseline score
        rel_score = 0.18
    else:
        rel_score = 0.15

    # 4. Evidence Completeness & Provenance (0.0 to 0.15)
    comp_score = 0.0
    if len(evidence.title.strip()) >= 8:
        comp_score += 0.03
    if len(evidence.content.strip()) >= 80:
        comp_score += 0.04
    if len(evidence.content.strip()) >= 200:
        comp_score += 0.03
    if evidence.url or evidence.metadata.get("doc_id"):
        comp_score += 0.03
    if len(evidence.query.strip()) >= 5:
        comp_score += 0.02

    total_score = prio_score + st_score + rel_score + comp_score
    return round(min(1.0, max(0.0, total_score)), 4)


def rank_evidence(
    evidence_list: Sequence[Evidence],
    reverse: bool = True,
) -> list[Evidence]:
    """
    Sort a list of Evidence items deterministically using composite rank scores.
    Updates the rank_score field on each Evidence object and guarantees reproducible ordering.
    """
    scored_items: list[Evidence] = []
    for item in evidence_list:
        if not isinstance(item, Evidence):
            raise EvidenceValidationError(
                f"Expected Evidence instance in rank_evidence, got {type(item).__name__}"
            )
        score = calculate_evidence_rank_score(item)
        # Update rank_score
        item.rank_score = score
        scored_items.append(item)

    # Sort key: (-rank_score, source_type, title, identifier)
    def sort_key(e: Evidence) -> tuple[float, str, str, str]:
        score_component = -e.rank_score if reverse else e.rank_score
        return (score_component, e.source_type, e.title.lower(), e.identifier.lower())

    return sorted(scored_items, key=sort_key)


def group_evidence_by_question(
    evidence_list: Sequence[Evidence],
) -> dict[str, list[Evidence]]:
    """
    Group evidence items by their task_question while preserving question order.
    """
    grouped: dict[str, list[Evidence]] = {}
    for item in evidence_list:
        if not isinstance(item, Evidence):
            raise EvidenceValidationError(
                f"Expected Evidence instance in group_evidence_by_question, got {type(item).__name__}"
            )
        q = item.task_question.strip()
        if q not in grouped:
            grouped[q] = []
        grouped[q].append(item)
    return grouped


def group_evidence(
    evidence_list: Sequence[Evidence],
    sort_items: bool = True,
) -> list[EvidenceGroup]:
    """
    Group evidence items into structured EvidenceGroup objects.
    Each group contains evidence items sorted deterministically by rank score.
    """
    grouped_dict = group_evidence_by_question(evidence_list)
    groups: list[EvidenceGroup] = []

    for question, items in grouped_dict.items():
        if sort_items:
            ranked_items = rank_evidence(items)
        else:
            ranked_items = items
        groups.append(EvidenceGroup(task_question=question, items=ranked_items))

    return groups


class EvidenceLayer:
    """
    Coordinator for the Evidence Layer.
    Ingests raw or normalized research results from Web, GitHub, and RAG,
    performing deterministic normalization, deduplication, ranking, and grouping.
    """

    def __init__(self, deduplicate: bool = True, rank: bool = True):
        self.deduplicate = deduplicate
        self.rank = rank

    def normalize(
        self,
        results: Sequence[Any],
        task_priority: PriorityLevel = "medium",
    ) -> list[Evidence]:
        """Normalize research results into Evidence models."""
        return normalize_results(results, task_priority=task_priority)

    def process(
        self,
        results: Sequence[Any],
        task_priority: PriorityLevel = "medium",
    ) -> list[Evidence]:
        """
        Normalize, optionally deduplicate, and optionally rank research results.
        """
        evidence_items = self.normalize(results, task_priority=task_priority)
        if self.deduplicate:
            evidence_items = deduplicate_evidence(evidence_items)
        if self.rank:
            evidence_items = rank_evidence(evidence_items)
        return evidence_items

    def deduplicate_items(self, evidence_list: Sequence[Evidence]) -> list[Evidence]:
        """Deduplicate evidence items deterministically."""
        return deduplicate_evidence(evidence_list)

    def rank_items(self, evidence_list: Sequence[Evidence]) -> list[Evidence]:
        """Rank evidence items deterministically."""
        return rank_evidence(evidence_list)

    def group_items(self, evidence_list: Sequence[Evidence]) -> list[EvidenceGroup]:
        """Group evidence items by question with deterministic ranking."""
        return group_evidence(evidence_list, sort_items=self.rank)

    def process_and_group(
        self,
        results: Sequence[Any],
        task_priority: PriorityLevel = "medium",
    ) -> list[EvidenceGroup]:
        """
        Process research results and group them into ranked EvidenceGroup objects.
        """
        processed_evidence = self.process(results, task_priority=task_priority)
        return group_evidence(processed_evidence, sort_items=self.rank)
