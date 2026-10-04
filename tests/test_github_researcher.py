"""
Unit tests for GitHubResearcher and GitHubResearchResult schema.
Uses mock search providers to guarantee fast, deterministic, offline execution.
"""

import unittest
from unittest.mock import MagicMock
import httpx
from pydantic import ValidationError

from models import ResearchTask, GitHubResearchResult
from github_researcher import (
    GitHubResearcher,
    GitHubResearchError,
    GitHubConnectionError,
    GitHubValidationError,
    GitHubAPIProvider,
    research_github_task,
)


class MockGitHubProvider:
    """Mock provider for unit testing GitHubResearcher."""
    def __init__(self, return_results=None, error_to_raise=None):
        self.return_results = return_results if return_results is not None else []
        self.error_to_raise = error_to_raise
        self.last_query = None
        self.last_max_results = None

    def search(self, query: str, max_results: int = 5):
        self.last_query = query
        self.last_max_results = max_results
        if self.error_to_raise:
            raise self.error_to_raise
        return self.return_results


class TestGitHubResearchResultSchema(unittest.TestCase):
    def test_valid_github_research_result(self):
        result = GitHubResearchResult(
            repo_name="gorilla/websocket",
            url="https://github.com/gorilla/websocket",
            description="Package gorilla/websocket is a Fast, well-tested WebSocket implementation for Go.",
            owner="gorilla",
            stars=22000,
            forks=3500,
            language="Go",
            open_issues=45,
            last_updated="2026-03-01T10:00:00Z",
            task_question="Which Go WebSocket libraries are actively maintained?",
            query="Go WebSocket libraries",
        )
        self.assertEqual(result.repo_name, "gorilla/websocket")
        self.assertEqual(result.name, "gorilla/websocket")
        self.assertEqual(result.owner, "gorilla")
        self.assertEqual(result.stars, 22000)
        self.assertEqual(result.forks, 3500)
        self.assertEqual(result.language, "Go")
        self.assertEqual(result.open_issues, 45)
        self.assertEqual(result.last_updated, "2026-03-01T10:00:00Z")
        self.assertIsInstance(result.to_dict(), dict)

    def test_missing_required_fields_rejected(self):
        # Missing URL
        with self.assertRaises(ValidationError):
            GitHubResearchResult(
                repo_name="gorilla/websocket",
                owner="gorilla",
                task_question="Which Go WebSocket libraries are actively maintained?",
                query="Go WebSocket",
            )
        # Missing repo_name
        with self.assertRaises(ValidationError):
            GitHubResearchResult(
                url="https://github.com/gorilla/websocket",
                owner="gorilla",
                task_question="Which Go WebSocket libraries are actively maintained?",
                query="Go WebSocket",
            )
        # Missing owner
        with self.assertRaises(ValidationError):
            GitHubResearchResult(
                repo_name="gorilla/websocket",
                url="https://github.com/gorilla/websocket",
                task_question="Which Go WebSocket libraries are actively maintained?",
                query="Go WebSocket",
            )

    def test_empty_string_fields_rejected(self):
        # Empty repo_name
        with self.assertRaises(ValidationError):
            GitHubResearchResult(
                repo_name="   ",
                url="https://github.com/gorilla/websocket",
                owner="gorilla",
                task_question="Which Go WebSocket libraries?",
                query="Go WebSocket",
            )
        # Empty owner
        with self.assertRaises(ValidationError):
            GitHubResearchResult(
                repo_name="gorilla/websocket",
                url="https://github.com/gorilla/websocket",
                owner="   ",
                task_question="Which Go WebSocket libraries?",
                query="Go WebSocket",
            )

    def test_invalid_url_scheme_rejected(self):
        # Non-http/https schemes must be rejected
        for bad_url in [
            "ftp://github.com/gorilla/websocket",
            "file:///path/to/repo",
            "javascript:alert(1)",
            "git@github.com:gorilla/websocket.git",
        ]:
            with self.subTest(bad_url=bad_url):
                with self.assertRaises(ValidationError):
                    GitHubResearchResult(
                        repo_name="gorilla/websocket",
                        url=bad_url,
                        owner="gorilla",
                        task_question="Which Go WebSocket libraries?",
                        query="Go WebSocket",
                    )

    def test_missing_scheme_or_host_rejected(self):
        for bad_url in [
            "github.com/gorilla/websocket",
            "https://",
            "http://",
            "not a url",
        ]:
            with self.subTest(bad_url=bad_url):
                with self.assertRaises(ValidationError):
                    GitHubResearchResult(
                        repo_name="gorilla/websocket",
                        url=bad_url,
                        owner="gorilla",
                        task_question="Which Go WebSocket libraries?",
                        query="Go WebSocket",
                    )

    def test_valid_http_and_https_urls_accepted(self):
        valid_urls = [
            "http://github.com/gorilla/websocket",
            "https://github.com/gorilla/websocket",
            "https://gitlab.com/group/project",
            "http://localhost:3000/repo",
        ]
        for valid_url in valid_urls:
            with self.subTest(valid_url=valid_url):
                result = GitHubResearchResult(
                    repo_name="gorilla/websocket",
                    url=valid_url,
                    owner="gorilla",
                    task_question="Which Go WebSocket libraries?",
                    query="Go WebSocket",
                )
                self.assertEqual(result.url, valid_url)

    def test_optional_fields_defaults_and_normalization(self):
        # When description, language, or numeric metrics are None or omitted
        result = GitHubResearchResult(
            repo_name="gorilla/websocket",
            url="https://github.com/gorilla/websocket",
            owner="gorilla",
            description=None,
            language=None,
            stars=None,
            forks=None,
            open_issues=None,
            last_updated=None,
            task_question="Which Go WebSocket libraries?",
            query="Go WebSocket",
        )
        self.assertEqual(result.description, "")
        self.assertEqual(result.language, "")
        self.assertEqual(result.stars, 0)
        self.assertEqual(result.forks, 0)
        self.assertEqual(result.open_issues, 0)
        self.assertEqual(result.last_updated, "")

    def test_alias_normalization(self):
        # Passing name or full_name instead of repo_name, and updated_at instead of last_updated
        data = {
            "full_name": "nhooyr/websocket",
            "url": "https://github.com/nhooyr/websocket",
            "owner": "nhooyr",
            "updated_at": "2026-01-15T12:00:00Z",
            "task_question": "Which Go WebSocket libraries?",
            "query": "Go WebSocket",
        }
        result = GitHubResearchResult.model_validate(data)
        self.assertEqual(result.repo_name, "nhooyr/websocket")
        self.assertEqual(result.last_updated, "2026-01-15T12:00:00Z")


class TestGitHubResearcher(unittest.TestCase):
    def setUp(self):
        self.valid_github_task = ResearchTask(
            question="Which Go WebSocket libraries are actively maintained?",
            source_type="github",
            priority="high",
            target="Go WebSocket libraries",
            purpose="Find actively maintained open-source repos.",
        )
        self.web_task = ResearchTask(
            question="What are the storage cost differences between TimescaleDB and ClickHouse?",
            source_type="web",
            priority="high",
            target="TimescaleDB vs ClickHouse",
            purpose="Determine storage expenses under 30-day retention.",
        )

    def test_successful_repository_search(self):
        mock_data = [
            {
                "repo_name": "gorilla/websocket",
                "url": "https://github.com/gorilla/websocket",
                "description": "Fast, well-tested WebSocket implementation for Go.",
                "owner": "gorilla",
                "stars": 22000,
                "forks": 3500,
                "language": "Go",
                "open_issues": 45,
                "last_updated": "2026-03-01T10:00:00Z",
            }
        ]
        provider = MockGitHubProvider(return_results=mock_data)
        researcher = GitHubResearcher(provider=provider)

        results = researcher.search(self.valid_github_task)
        self.assertEqual(len(results), 1)
        res = results[0]
        self.assertIsInstance(res, GitHubResearchResult)
        self.assertEqual(res.repo_name, "gorilla/websocket")
        self.assertEqual(res.url, "https://github.com/gorilla/websocket")
        self.assertEqual(res.owner, "gorilla")
        self.assertEqual(res.stars, 22000)
        self.assertEqual(res.task_question, self.valid_github_task.question)
        self.assertTrue(len(res.query) > 0)

    def test_multiple_results(self):
        mock_data = [
            {
                "repo_name": f"org/repo-{i}",
                "url": f"https://github.com/org/repo-{i}",
                "owner": "org",
                "description": f"Description {i}",
                "stars": 100 * i,
                "forks": 10 * i,
                "language": "Go",
                "open_issues": i,
                "last_updated": "2026-01-01T00:00:00Z",
            }
            for i in range(5)
        ]
        provider = MockGitHubProvider(return_results=mock_data)
        researcher = GitHubResearcher(provider=provider, max_results_per_task=5)

        results = researcher.search(self.valid_github_task)
        self.assertEqual(len(results), 5)

    def test_empty_results(self):
        provider = MockGitHubProvider(return_results=[])
        researcher = GitHubResearcher(provider=provider)

        results = researcher.search(self.valid_github_task)
        self.assertEqual(results, [])

    def test_wrong_task_source_type_rejected(self):
        researcher = GitHubResearcher(provider=MockGitHubProvider())
        with self.assertRaises(GitHubValidationError) as ctx:
            researcher.search(self.web_task)
        self.assertIn("Only source_type='github' is supported", str(ctx.exception))

    def test_wrong_task_type_rejected(self):
        researcher = GitHubResearcher(provider=MockGitHubProvider())
        with self.assertRaises(GitHubValidationError):
            researcher.search("not a research task")
        with self.assertRaises(GitHubValidationError):
            researcher.search({"question": "invalid dict"})

    def test_malformed_provider_result_raises_validation_error(self):
        # Provider returns items missing URL or repo_name
        malformed_data = [{"description": "Missing repo_name and url"}]
        provider = MockGitHubProvider(return_results=malformed_data)
        researcher = GitHubResearcher(provider=provider)

        with self.assertRaises(GitHubValidationError):
            researcher.search(self.valid_github_task)

    def test_provider_invalid_url_result_raises_validation_error(self):
        # Provider returns item with non-http/https URL
        bad_url_data = [
            {
                "repo_name": "owner/repo",
                "url": "ftp://bad-url.com/repo",
                "owner": "owner",
            }
        ]
        provider = MockGitHubProvider(return_results=bad_url_data)
        researcher = GitHubResearcher(provider=provider)

        with self.assertRaises(GitHubValidationError):
            researcher.search(self.valid_github_task)

    def test_provider_connection_failure_propagates_connection_error(self):
        error = GitHubConnectionError("GitHub API rate limit exceeded")
        provider = MockGitHubProvider(error_to_raise=error)
        researcher = GitHubResearcher(provider=provider)

        with self.assertRaises(GitHubConnectionError):
            researcher.search(self.valid_github_task)

    def test_unexpected_provider_exception_normalized_to_connection_error(self):
        provider = MockGitHubProvider(error_to_raise=RuntimeError("Socket aborted unexpectedly"))
        researcher = GitHubResearcher(provider=provider)

        with self.assertRaises(GitHubConnectionError) as ctx:
            researcher.search(self.valid_github_task)
        self.assertIn("Socket aborted unexpectedly", str(ctx.exception))

    def test_provider_custom_network_exception_normalized(self):
        provider = MockGitHubProvider(error_to_raise=ConnectionResetError("Connection reset by peer"))
        researcher = GitHubResearcher(provider=provider)

        with self.assertRaises(GitHubConnectionError) as ctx:
            researcher.search(self.valid_github_task)
        self.assertIn("Connection reset by peer", str(ctx.exception))

    def test_deterministic_query_construction(self):
        researcher = GitHubResearcher(provider=MockGitHubProvider())

        # Target with question words
        q1 = researcher.build_query(self.valid_github_task)
        self.assertTrue(len(q1) > 0)
        self.assertIn("Go", q1)
        self.assertIn("WebSocket", q1)
        self.assertFalse(q1.lower().startswith("which"))

        # Task with leading question words
        task_with_opening = ResearchTask(
            question="How to scale WebSocket connections in Go?",
            source_type="github",
            priority="high",
            target="Go WebSocket connections",
            purpose="Determine concurrency limits.",
        )
        q2 = researcher.build_query(task_with_opening)
        self.assertFalse(q2.lower().startswith("how to"))
        self.assertIn("WebSocket", q2)
        self.assertIn("Go", q2)

        # Task with generic target
        task_generic = ResearchTask(
            question="Are there open-source CRDT implementations in TypeScript?",
            source_type="github",
            priority="medium",
            target="Architecture & Implementation",
            purpose="Find CRDT libraries.",
        )
        q3 = researcher.build_query(task_generic)
        self.assertIn("CRDT", q3)
        self.assertIn("TypeScript", q3)

    def test_convenience_function(self):
        mock_data = [
            {
                "repo_name": "example/repo",
                "url": "https://github.com/example/repo",
                "owner": "example",
                "description": "Convenience helper test repo",
                "stars": 500,
            }
        ]
        provider = MockGitHubProvider(return_results=mock_data)
        results = research_github_task(self.valid_github_task, provider=provider)
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].repo_name, "example/repo")


class TestGitHubAPIProvider(unittest.TestCase):
    def test_api_provider_parses_response_correctly(self):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "items": [
                {
                    "name": "websocket",
                    "full_name": "gorilla/websocket",
                    "html_url": "https://github.com/gorilla/websocket",
                    "description": "Fast WebSocket for Go",
                    "owner": {"login": "gorilla"},
                    "stargazers_count": 22000,
                    "forks_count": 3500,
                    "language": "Go",
                    "open_issues_count": 45,
                    "updated_at": "2026-03-01T10:00:00Z",
                }
            ]
        }
        mock_client = MagicMock()
        mock_client.get.return_value = mock_response

        provider = GitHubAPIProvider(client=mock_client)
        results = provider.search("go websocket", max_results=5)

        self.assertEqual(len(results), 1)
        item = results[0]
        self.assertEqual(item["repo_name"], "gorilla/websocket")
        self.assertEqual(item["url"], "https://github.com/gorilla/websocket")
        self.assertEqual(item["owner"], "gorilla")
        self.assertEqual(item["stars"], 22000)
        self.assertEqual(item["forks"], 3500)
        self.assertEqual(item["language"], "Go")

    def test_api_provider_rate_limit_raises_connection_error(self):
        mock_response = MagicMock()
        mock_response.status_code = 403
        mock_response.text = "API rate limit exceeded"
        mock_client = MagicMock()
        mock_client.get.return_value = mock_response

        provider = GitHubAPIProvider(client=mock_client)
        with self.assertRaises(GitHubConnectionError) as ctx:
            provider.search("query")
        self.assertIn("rate limit exceeded", str(ctx.exception))

    def test_api_provider_unprocessable_query_returns_empty(self):
        mock_response = MagicMock()
        mock_response.status_code = 422
        mock_client = MagicMock()
        mock_client.get.return_value = mock_response

        provider = GitHubAPIProvider(client=mock_client)
        results = provider.search("invalid query")
        self.assertEqual(results, [])

    def test_api_provider_network_error_raises_connection_error(self):
        mock_client = MagicMock()
        mock_client.get.side_effect = httpx.ConnectError("Network unreachable")

        provider = GitHubAPIProvider(client=mock_client)
        with self.assertRaises(GitHubConnectionError):
            provider.search("query")


if __name__ == "__main__":
    unittest.main()
