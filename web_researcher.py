"""
Web Research connector for DEVSCOUT.
Executes targeted web research for tasks requiring external web intelligence.
"""

import os
import re
from typing import Any, Protocol, runtime_checkable
from urllib.parse import urlparse

from models import ResearchTask, WebResearchResult


class WebResearchError(Exception):
    """Base exception for all Web Research connector errors."""
    pass


class WebSearchConnectionError(WebResearchError):
    """Raised when communication with the web search provider fails."""
    pass


class WebSearchValidationError(WebResearchError):
    """Raised when a task or result violates schema or source-type constraints."""
    pass


@runtime_checkable
class WebSearchProvider(Protocol):
    """Protocol defining the interface for web search backends."""
    def search(self, query: str, max_results: int = 5) -> list[dict[str, Any]]:
        """Execute a search query and return raw result dictionaries."""
        ...


class DuckDuckGoProvider:
    """
    Search provider querying DuckDuckGo using the ddgs / duckduckgo_search library,
    with automatic domain extraction and normalized output format.
    """

    def __init__(self, timeout: float = 10.0):
        self.timeout = timeout

    def search(self, query: str, max_results: int = 5) -> list[dict[str, Any]]:
        try:
            try:
                from ddgs import DDGS
            except ImportError:
                from duckduckgo_search import DDGS
        except ImportError as e:
            raise WebSearchConnectionError(
                "ddgs package is not installed. Please install it with 'pip install ddgs'."
            ) from e

        results: list[dict[str, Any]] = []
        try:
            ddgs = DDGS(timeout=self.timeout)
            raw_items = list(ddgs.text(query, max_results=max_results))
        except Exception as e:
            err_msg = str(e).lower()
            if "no results" in err_msg or "not found" in err_msg:
                raw_items = []
            else:
                raise WebSearchConnectionError(f"DuckDuckGo search failed for query '{query}': {e}") from e

        for item in raw_items:
            href = item.get("href") or item.get("link") or ""
            title = item.get("title") or ""
            snippet = item.get("body") or item.get("snippet") or ""

            # Extract source domain
            domain = ""
            if href:
                parsed = urlparse(href)
                domain = parsed.netloc.lower()
                if domain.startswith("www."):
                    domain = domain[4:]

            if href and title:
                results.append({
                    "title": title.strip(),
                    "url": href.strip(),
                    "source": domain or "web",
                    "snippet": snippet.strip(),
                })

        return results


def get_default_search_provider() -> WebSearchProvider:
    """Instantiate the configured web search provider."""
    # Extensible for future providers like Tavily, Serper, SearXNG
    return DuckDuckGoProvider()


class WebResearcher:
    """
    Executes web research for a ResearchTask and returns normalized WebResearchResult objects.
    """

    def __init__(
        self,
        provider: WebSearchProvider | None = None,
        max_results_per_task: int = 5,
    ):
        self.provider = provider or get_default_search_provider()
        self.max_results_per_task = max_results_per_task

    def build_query(self, task: ResearchTask) -> str:
        """
        Deterministically derive a clean, keyword-dense search query from
        the task's target and question.
        """
        target = task.target.strip()
        question = task.question.strip()

        # Clean non-breaking hyphens and special punctuation
        target = target.replace("\u2011", "-").strip(" ,.-–—")
        cleaned_q = question.replace("\u2011", "-")

        # Strip abbreviations like e.g., i.e., etc.
        cleaned_q = re.sub(r"\b(?:e\.?g\.?|i\.?e\.?|etc\.?)\b", " ", cleaned_q, flags=re.IGNORECASE)

        # Strip parentheses, quotes, and punctuation that distort search queries
        cleaned_q = re.sub(r"[()\"',;/?!]", " ", cleaned_q)

        # Remove conversational opening phrases and punctuation
        cleaned_q = re.sub(
            r"^(?:which|what\s+is\s+the|what\s+are\s+the|what|how\s+to|how\s+can|how|why|is\s+it|can|can\s+we)\s+",
            "",
            cleaned_q,
            flags=re.IGNORECASE,
        ).strip()

        # Remove filler qualifiers at start
        cleaned_q = re.sub(
            r"^(?:optimal|best|suitable|typical|acceptable)\s+",
            "",
            cleaned_q,
            flags=re.IGNORECASE,
        ).strip()

        # Check if target is generic (e.g. 'Architecture & Implementation')
        is_generic_target = target.lower() in {
            "architecture & implementation",
            "architecture",
            "implementation",
            "",
        }

        # Combine target and cleaned question tokens, deduplicating while preserving order
        raw_terms: list[str] = []
        if not is_generic_target:
            raw_terms.extend(re.split(r"[\s,]+", target))
        raw_terms.extend(re.split(r"[\s,]+", cleaned_q))

        # Filter out empty terms and common filler stopwords
        stopwords = {
            "or", "and", "the", "a", "an", "for", "to", "in", "of", "on", "at", "by", "with",
            "is", "are", "be", "do", "does", "did", "can", "could", "should", "would",
            "provides", "offers", "delivers", "needed", "best", "how", "what", "which",
            "perform", "performs"
        }

        seen: set[str] = set()
        clean_words: list[str] = []
        for term in raw_terms:
            t_clean = term.strip(" .-_")
            if not t_clean or len(t_clean) < 2:
                continue
            t_lower = t_clean.lower()
            if t_lower in stopwords:
                continue
            if t_lower not in seen:
                seen.add(t_lower)
                clean_words.append(t_clean)

        # Keep top 5-6 meaningful keyword terms for optimal search recall
        query = " ".join(clean_words[:6])
        return query.strip()

    def search(self, task: ResearchTask) -> list[WebResearchResult]:
        """
        Execute web research for a valid ResearchTask.
        Validates source_type, queries the provider, and returns validated WebResearchResults.
        """
        if not isinstance(task, ResearchTask):
            raise WebSearchValidationError(
                f"Expected ResearchTask instance, got {type(task).__name__}"
            )

        if task.source_type != "web":
            raise WebSearchValidationError(
                f"Cannot execute web research on task with source_type='{task.source_type}'. "
                "Only source_type='web' is supported by WebResearcher."
            )

        query = self.build_query(task)
        if not query:
            raise WebSearchValidationError("Failed to derive a valid search query from task.")

        raw_items = self.provider.search(query, max_results=self.max_results_per_task)

        # If primary query returned no results and target is specific, retry with target alone
        if not raw_items and task.target and task.target.lower() not in {
            "architecture & implementation",
            "architecture",
            "implementation",
        } and task.target != query:
            raw_items = self.provider.search(task.target, max_results=self.max_results_per_task)

        results: list[WebResearchResult] = []
        for item in raw_items:
            try:
                result = WebResearchResult(
                    title=item.get("title", ""),
                    url=item.get("url", ""),
                    source=item.get("source", ""),
                    snippet=item.get("snippet", ""),
                    task_question=task.question,
                    query=query,
                )
                results.append(result)
            except Exception as e:
                raise WebSearchValidationError(
                    f"Provider returned malformed result item {item}: {e}"
                ) from e

        return results


def research_web_task(task: ResearchTask, **kwargs: Any) -> list[WebResearchResult]:
    """Convenience function to run web research on a single ResearchTask."""
    researcher = WebResearcher(**kwargs)
    return researcher.search(task)
