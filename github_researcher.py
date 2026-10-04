"""
GitHub Research connector for DEVSCOUT.
Executes targeted repository and implementation research for tasks requiring GitHub intelligence.
"""

import os
import re
from typing import Any, Protocol, runtime_checkable

import httpx

from models import ResearchTask, GitHubResearchResult


class GitHubResearchError(Exception):
    """Base exception for all GitHub Research connector errors."""
    pass


class GitHubConnectionError(GitHubResearchError):
    """Raised when communication with the GitHub API fails or provider encounters connection issues."""
    pass


class GitHubValidationError(GitHubResearchError):
    """Raised when a task or result violates schema or source-type constraints."""
    pass


@runtime_checkable
class GitHubSearchProvider(Protocol):
    """Protocol defining the interface for GitHub repository search backends."""
    def search(self, query: str, max_results: int = 5) -> list[dict[str, Any]]:
        """Execute a repository search query and return raw repository dictionaries."""
        ...


class GitHubAPIProvider:
    """
    Search provider querying the official GitHub REST API (v3) using httpx.
    """

    def __init__(
        self,
        token: str | None = None,
        timeout: float = 10.0,
        api_base_url: str = "https://api.github.com",
        client: httpx.Client | None = None,
    ):
        self.timeout = timeout
        self.api_base_url = api_base_url.rstrip("/")
        self.token = token or os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
        self._client = client

    def _get_headers(self) -> dict[str, str]:
        headers = {
            "Accept": "application/vnd.github+json",
            "User-Agent": "DEVSCOUT-Research-Assistant",
            "X-GitHub-Api-Version": "2022-11-28",
        }
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        return headers

    def search(self, query: str, max_results: int = 5) -> list[dict[str, Any]]:
        endpoint = f"{self.api_base_url}/search/repositories"
        per_page = min(max(max_results, 1), 30)
        params = {
            "q": query,
            "sort": "stars",
            "order": "desc",
            "per_page": per_page,
        }
        headers = self._get_headers()

        try:
            if self._client:
                response = self._client.get(
                    endpoint, params=params, headers=headers, timeout=self.timeout
                )
            else:
                with httpx.Client(timeout=self.timeout) as client:
                    response = client.get(endpoint, params=params, headers=headers)

            if response.status_code in (403, 429):
                raise GitHubConnectionError(
                    f"GitHub API rate limit exceeded or access forbidden (HTTP {response.status_code}): {response.text}"
                )
            if response.status_code == 422:
                # Unprocessable query (e.g. invalid syntax)
                return []

            response.raise_for_status()
            data = response.json()
        except GitHubConnectionError:
            raise
        except httpx.HTTPStatusError as e:
            raise GitHubConnectionError(f"GitHub API HTTP error ({e.response.status_code}): {e}") from e
        except httpx.RequestError as e:
            raise GitHubConnectionError(f"GitHub API connection failed: {e}") from e
        except Exception as e:
            raise GitHubConnectionError(f"GitHub search failed for query '{query}': {e}") from e

        items = data.get("items", []) if isinstance(data, dict) else []
        results: list[dict[str, Any]] = []

        for item in items[:max_results]:
            if not isinstance(item, dict):
                continue

            owner_val = item.get("owner")
            owner_login = ""
            if isinstance(owner_val, dict):
                owner_login = owner_val.get("login", "")
            elif isinstance(owner_val, str):
                owner_login = owner_val

            full_name = item.get("full_name") or item.get("name") or ""
            if not owner_login and "/" in full_name:
                owner_login = full_name.split("/")[0]

            html_url = item.get("html_url") or item.get("url") or ""

            if full_name and html_url:
                results.append({
                    "repo_name": full_name.strip(),
                    "url": html_url.strip(),
                    "description": (item.get("description") or "").strip(),
                    "owner": owner_login.strip() or "unknown",
                    "stars": item.get("stargazers_count", item.get("stars", 0)),
                    "forks": item.get("forks_count", item.get("forks", 0)),
                    "language": (item.get("language") or "").strip(),
                    "open_issues": item.get("open_issues_count", item.get("open_issues", 0)),
                    "last_updated": str(item.get("updated_at") or item.get("last_updated") or "").strip(),
                })

        return results


def get_default_github_provider() -> GitHubSearchProvider:
    """Instantiate the default GitHub API search provider."""
    return GitHubAPIProvider()


class GitHubResearcher:
    """
    Executes GitHub repository research for a ResearchTask and returns normalized GitHubResearchResult objects.
    """

    def __init__(
        self,
        provider: GitHubSearchProvider | None = None,
        max_results_per_task: int = 5,
    ):
        self.provider = provider or get_default_github_provider()
        self.max_results_per_task = max_results_per_task

    def build_query(self, task: ResearchTask) -> str:
        """
        Deterministically derive a clean, keyword-dense GitHub search query from
        the task's target and question without using an LLM.
        """
        target = task.target.strip()
        question = task.question.strip()

        # Clean non-breaking hyphens and special punctuation
        target = target.replace("\u2011", "-").strip(" ,.-–—")
        cleaned_q = question.replace("\u2011", "-")

        # Strip abbreviations like e.g., i.e., etc.
        cleaned_q = re.sub(r"\b(?:e\.?g\.?|i\.?e\.?|etc\.?)\b", " ", cleaned_q, flags=re.IGNORECASE)

        # Strip parentheses, quotes, and punctuation that distort search queries
        cleaned_q = re.sub(r"[()\"',;/?!–—]", " ", cleaned_q)

        # Remove conversational opening phrases and punctuation
        cleaned_q = re.sub(
            r"^(?:which|what\s+is\s+the|what\s+are\s+the|what|how\s+to|how\s+can|how|why|is\s+it|can|can\s+we|are\s+there|are)\s+",
            "",
            cleaned_q,
            flags=re.IGNORECASE,
        ).strip()

        # Remove filler qualifiers at start
        cleaned_q = re.sub(
            r"^(?:optimal|best|suitable|typical|acceptable|actively\s+maintained|popular|top)\s+",
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
            "which", "what", "how", "why", "who", "where", "when",
            "provides", "offers", "delivers", "needed", "best",
            "perform", "performs", "vs", "versus", "between",
            "actively", "maintained", "suitable", "acceptable", "typical"
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
        if not query and target and not is_generic_target:
            return target
        return query.strip()

    def search(self, task: ResearchTask) -> list[GitHubResearchResult]:
        """
        Execute GitHub research for a valid ResearchTask.
        Validates source_type, queries the provider, and returns validated GitHubResearchResults.
        """
        if not isinstance(task, ResearchTask):
            raise GitHubValidationError(
                f"Expected ResearchTask instance, got {type(task).__name__}"
            )

        if task.source_type != "github":
            raise GitHubValidationError(
                f"Cannot execute GitHub research on task with source_type='{task.source_type}'. "
                "Only source_type='github' is supported by GitHubResearcher."
            )

        query = self.build_query(task)
        if not query:
            raise GitHubValidationError("Failed to derive a valid GitHub search query from task.")

        try:
            raw_items = self.provider.search(query, max_results=self.max_results_per_task)

            # If primary query returned no results and target is specific, retry with target alone
            if not raw_items and task.target and task.target.lower() not in {
                "architecture & implementation",
                "architecture",
                "implementation",
            } and task.target != query:
                raw_items = self.provider.search(task.target, max_results=self.max_results_per_task)
        except GitHubConnectionError:
            raise
        except Exception as e:
            raise GitHubConnectionError(f"GitHub search provider error: {e}") from e

        results: list[GitHubResearchResult] = []
        for item in raw_items:
            try:
                result = GitHubResearchResult(
                    repo_name=item.get("repo_name") or item.get("full_name") or item.get("name", ""),
                    url=item.get("url") or item.get("html_url", ""),
                    description=item.get("description") or "",
                    owner=item.get("owner", ""),
                    stars=item.get("stars", item.get("stargazers_count", 0)),
                    forks=item.get("forks", item.get("forks_count", 0)),
                    language=item.get("language") or "",
                    open_issues=item.get("open_issues", item.get("open_issues_count", 0)),
                    last_updated=item.get("last_updated") or item.get("updated_at") or "",
                    task_question=task.question,
                    query=query,
                )
                results.append(result)
            except Exception as e:
                raise GitHubValidationError(
                    f"Provider returned malformed GitHub result item {item}: {e}"
                ) from e

        return results


def research_github_task(task: ResearchTask, **kwargs: Any) -> list[GitHubResearchResult]:
    """Convenience function to run GitHub research on a single ResearchTask."""
    researcher = GitHubResearcher(**kwargs)
    return researcher.search(task)
