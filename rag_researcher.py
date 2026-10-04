"""
RAG Research connector for DEVSCOUT.
Retrieves targeted internal/domain knowledge from the vector knowledge base (Pinecone)
for tasks requiring grounded architectural or project intelligence.
"""

import os
import re
from typing import Any, Protocol, runtime_checkable

import httpx

from models import ResearchTask, RAGResearchResult


class RAGResearchError(Exception):
    """Base exception for all RAG Research connector errors."""
    pass


class RAGConnectionError(RAGResearchError):
    """Raised when communication with the vector database / Pinecone fails."""
    pass


class RAGValidationError(RAGResearchError):
    """Raised when a task or result violates schema or source-type constraints."""
    pass


@runtime_checkable
class RAGSearchProvider(Protocol):
    """Protocol defining the interface for RAG / vector search backends."""
    def search(self, query: str, max_results: int = 5) -> list[dict[str, Any]]:
        """Execute a knowledge base search query and return raw result dictionaries."""
        ...


class PineconeProvider:
    """
    Search provider querying a Pinecone vector index via REST API using httpx.
    Resolves index host dynamically from Pinecone control plane or uses direct PINECONE_INDEX_HOST.
    """

    def __init__(
        self,
        api_key: str | None = None,
        index_name: str | None = None,
        index_host: str | None = None,
        embedding_model: str | None = None,
        namespace: str | None = None,
        timeout: float = 10.0,
        client: httpx.Client | None = None,
        embed_fn: Any = None,
    ):
        if api_key is not None:
            self.api_key = api_key.strip()
        else:
            self.api_key = (os.environ.get("PINECONE_API_KEY") or "").strip()

        if index_name is not None:
            self.index_name = index_name.strip()
        else:
            self.index_name = (os.environ.get("PINECONE_INDEX") or "").strip()

        if index_host is not None:
            self.index_host = index_host.strip()
        else:
            self.index_host = (
                os.environ.get("PINECONE_INDEX_HOST")
                or os.environ.get("PINECONE_HOST")
                or ""
            ).strip()

        self.embedding_model = (
            embedding_model
            or os.environ.get("PINECONE_EMBEDDING_MODEL")
            or "multilingual-e5-large"
        ).strip()
        self.namespace = (
            namespace
            or os.environ.get("PINECONE_NAMESPACE")
            or ""
        ).strip()
        self.timeout = timeout
        self._client = client
        self._embed_fn = embed_fn

    def _get_headers(self) -> dict[str, str]:
        if not self.api_key:
            raise RAGConnectionError(
                "PINECONE_API_KEY is not configured. Please set PINECONE_API_KEY in your environment."
            )
        return {
            "Api-Key": self.api_key,
            "Content-Type": "application/json",
            "X-Pinecone-API-Version": "2024-07",
        }

    def _resolve_host(self) -> str:
        """Resolve the host URL for the Pinecone index data plane."""
        if self.index_host:
            host = self.index_host.strip()
            if not host.startswith("http://") and not host.startswith("https://"):
                host = f"https://{host}"
            return host.rstrip("/")

        headers = self._get_headers()
        try:
            url = "https://api.pinecone.io/indexes"
            if self._client:
                r = self._client.get(url, headers=headers, timeout=self.timeout)
            else:
                with httpx.Client(timeout=self.timeout) as client:
                    r = client.get(url, headers=headers)

            if r.status_code in (401, 403):
                raise RAGConnectionError(
                    f"Pinecone authentication failed (HTTP {r.status_code}): {r.text}"
                )
            r.raise_for_status()
            data = r.json()
            indexes = data.get("indexes", [])
            if not indexes:
                raise RAGConnectionError(
                    "No Pinecone indexes found in account. "
                    "Please create an index or specify PINECONE_INDEX / PINECONE_INDEX_HOST."
                )

            target_index = None
            if self.index_name:
                for idx in indexes:
                    if idx.get("name") == self.index_name:
                        target_index = idx
                        break
                if not target_index:
                    raise RAGConnectionError(
                        f"Pinecone index '{self.index_name}' not found among available indexes."
                    )
            else:
                target_index = indexes[0]

            host = target_index.get("host", "")
            if not host:
                raise RAGConnectionError("Target Pinecone index does not have an active host.")
            if not host.startswith("http://") and not host.startswith("https://"):
                host = f"https://{host}"
            return host.rstrip("/")
        except RAGConnectionError:
            raise
        except Exception as e:
            raise RAGConnectionError(f"Failed to resolve Pinecone index host: {e}") from e

    def embed_query(self, text: str) -> list[float]:
        """
        Generate a query embedding vector for the input text using Pinecone Inference API.
        """
        if self._embed_fn:
            return self._embed_fn(text)

        if not self.api_key:
            raise RAGConnectionError(
                "PINECONE_API_KEY is not configured. Please set PINECONE_API_KEY in your environment."
            )

        url = "https://api.pinecone.io/embed"
        headers = self._get_headers()
        payload = {
            "model": self.embedding_model,
            "parameters": {
                "input_type": "query",
                "truncate": "END",
            },
            "inputs": [{"text": text}],
        }

        try:
            if self._client:
                response = self._client.post(url, json=payload, headers=headers, timeout=self.timeout)
            else:
                with httpx.Client(timeout=self.timeout) as client:
                    response = client.post(url, json=payload, headers=headers)

            if response.status_code in (401, 403):
                raise RAGConnectionError(
                    f"Pinecone embedding authentication failed (HTTP {response.status_code}): {response.text}"
                )
            response.raise_for_status()
            data = response.json()
        except RAGConnectionError:
            raise
        except httpx.HTTPStatusError as e:
            raise RAGConnectionError(
                f"Pinecone embedding API HTTP error ({e.response.status_code}): {e}"
            ) from e
        except httpx.RequestError as e:
            raise RAGConnectionError(f"Pinecone embedding API connection failed: {e}") from e
        except Exception as e:
            raise RAGConnectionError(f"Failed to generate query embedding for '{text}': {e}") from e

        embed_data = data.get("data", [])
        if not embed_data or not isinstance(embed_data, list) or "values" not in embed_data[0]:
            raise RAGConnectionError(f"Pinecone embedding API returned malformed response: {data}")

        vector = embed_data[0]["values"]
        if not isinstance(vector, list) or not vector:
            raise RAGConnectionError("Pinecone embedding API returned empty vector representation.")

        return [float(x) for x in vector]

    def search(self, query: str, max_results: int = 5) -> list[dict[str, Any]]:
        """
        Perform semantic search against the Pinecone index:
        1. Embed the query string into a dense vector representation.
        2. Query the Pinecone index data plane using the vector embedding.
        3. Extract and normalize matched document records.
        """
        if not self.api_key:
            raise RAGConnectionError(
                "PINECONE_API_KEY is not configured. Please set PINECONE_API_KEY in your environment."
            )

        query_clean = query.strip()
        if not query_clean:
            return []

        # 1. Generate query embedding representation via Pinecone Inference
        query_vector = self.embed_query(query_clean)

        # 2. Resolve index host data plane
        host = self._resolve_host()
        endpoint = f"{host}/query"
        headers = self._get_headers()

        payload: dict[str, Any] = {
            "vector": query_vector,
            "topK": max(1, max_results),
            "includeMetadata": True,
            "includeValues": False,
        }
        if self.namespace:
            payload["namespace"] = self.namespace

        # 3. Query index endpoint
        try:
            if self._client:
                response = self._client.post(
                    endpoint, json=payload, headers=headers, timeout=self.timeout
                )
            else:
                with httpx.Client(timeout=self.timeout) as client:
                    response = client.post(endpoint, json=payload, headers=headers)

            if response.status_code in (401, 403):
                raise RAGConnectionError(
                    f"Pinecone query authentication failed (HTTP {response.status_code}): {response.text}"
                )
            response.raise_for_status()
            data = response.json()
        except RAGConnectionError:
            raise
        except httpx.HTTPStatusError as e:
            raise RAGConnectionError(
                f"Pinecone API HTTP error ({e.response.status_code}): {e}"
            ) from e
        except httpx.RequestError as e:
            raise RAGConnectionError(f"Pinecone API connection failed: {e}") from e
        except Exception as e:
            raise RAGConnectionError(f"Pinecone search failed for query '{query}': {e}") from e

        matches = data.get("matches", []) if isinstance(data, dict) else []
        results: list[dict[str, Any]] = []

        for match in matches[:max_results]:
            if not isinstance(match, dict):
                continue
            metadata = match.get("metadata") or {}
            title = (
                metadata.get("title")
                or metadata.get("name")
                or match.get("id")
                or "Knowledge Document"
            )
            content = metadata.get("text") or metadata.get("content") or metadata.get("snippet") or ""
            source = metadata.get("source") or metadata.get("collection") or "pinecone"
            doc_id = match.get("id")
            score = match.get("score")

            if title and content:
                results.append({
                    "title": str(title).strip(),
                    "content": str(content).strip(),
                    "source": str(source).strip(),
                    "doc_id": str(doc_id).strip() if doc_id else None,
                    "score": float(score) if score is not None else None,
                })

        return results


def get_default_rag_provider() -> RAGSearchProvider:
    """Instantiate the default RAG / Pinecone search provider."""
    return PineconeProvider()


class RAGResearcher:
    """
    Executes RAG knowledge base research for a ResearchTask and returns normalized RAGResearchResult objects.
    """

    def __init__(
        self,
        provider: RAGSearchProvider | None = None,
        max_results_per_task: int = 5,
    ):
        self.provider = provider or get_default_rag_provider()
        self.max_results_per_task = max_results_per_task

    def build_query(self, task: ResearchTask) -> str:
        """
        Deterministically derive a clean, keyword-dense search query from
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
            r"^(?:optimal|best|suitable|typical|acceptable|recommended|detailed)\s+",
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
            "detailed", "suitable", "acceptable", "typical"
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

        # Keep top 6-8 meaningful keyword terms for optimal vector/semantic recall
        query = " ".join(clean_words[:8])
        if not query and target and not is_generic_target:
            return target
        return query.strip()

    def search(self, task: ResearchTask) -> list[RAGResearchResult]:
        """
        Execute RAG research for a valid ResearchTask.
        Validates source_type, queries the provider, and returns validated RAGResearchResults.
        """
        if not isinstance(task, ResearchTask):
            raise RAGValidationError(
                f"Expected ResearchTask instance, got {type(task).__name__}"
            )

        if task.source_type != "rag":
            raise RAGValidationError(
                f"Cannot execute RAG research on task with source_type='{task.source_type}'. "
                "Only source_type='rag' is supported by RAGResearcher."
            )

        query = self.build_query(task)
        if not query:
            raise RAGValidationError("Failed to derive a valid RAG search query from task.")

        try:
            raw_items = self.provider.search(query, max_results=self.max_results_per_task)

            # If primary query returned no results and target is specific, retry with target alone
            if not raw_items and task.target and task.target.lower() not in {
                "architecture & implementation",
                "architecture",
                "implementation",
            } and task.target != query:
                raw_items = self.provider.search(task.target, max_results=self.max_results_per_task)
        except RAGConnectionError:
            raise
        except Exception as e:
            raise RAGConnectionError(f"RAG search provider error: {e}") from e

        results: list[RAGResearchResult] = []
        for item in raw_items:
            try:
                result = RAGResearchResult(
                    title=item.get("title", ""),
                    content=item.get("content") or item.get("snippet", ""),
                    source=item.get("source", ""),
                    doc_id=item.get("doc_id") or item.get("id"),
                    score=item.get("score"),
                    task_question=task.question,
                    query=query,
                )
                results.append(result)
            except Exception as e:
                raise RAGValidationError(
                    f"Provider returned malformed RAG result item {item}: {e}"
                ) from e

        return results


def research_rag_task(task: ResearchTask, **kwargs: Any) -> list[RAGResearchResult]:
    """Convenience function to run RAG research on a single ResearchTask."""
    researcher = RAGResearcher(**kwargs)
    return researcher.search(task)
