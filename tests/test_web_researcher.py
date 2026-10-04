"""
Unit tests for WebResearcher and WebResearchResult schema.
Uses mock search providers to guarantee fast, deterministic, offline execution.
"""

import unittest
from unittest.mock import MagicMock
from models import ResearchTask, WebResearchResult
from web_researcher import (
    WebResearcher,
    WebResearchError,
    WebSearchConnectionError,
    WebSearchValidationError,
    research_web_task,
)


class MockSearchProvider:
    """Mock provider for unit testing WebResearcher."""
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


class TestWebResearchResultSchema(unittest.TestCase):
    def test_valid_web_research_result(self):
        result = WebResearchResult(
            title="Go WebSocket Benchmark Comparison",
            url="https://github.com/lesismal/go-websocket-benchmark",
            source="github.com",
            snippet="Benchmark testing 100k concurrent connections with Gorilla and Fasthttp.",
            task_question="Which Go WebSocket libraries are actively maintained?",
            query="Go WebSocket libraries benchmark",
        )
        self.assertEqual(result.title, "Go WebSocket Benchmark Comparison")
        self.assertEqual(result.source, "github.com")
        self.assertIn("100k concurrent", result.snippet)
        self.assertEqual(result.query, "Go WebSocket libraries benchmark")
        self.assertIsInstance(result.to_dict(), dict)

    def test_missing_required_fields_rejected(self):
        # Missing URL
        with self.assertRaises(Exception):
            WebResearchResult(
                title="Some title",
                source="example.com",
                task_question="A question?",
                query="A query",
            )

    def test_empty_string_fields_rejected(self):
        # Empty title
        with self.assertRaises(Exception):
            WebResearchResult(
                title="   ",
                url="https://example.com",
                source="example.com",
                task_question="A question?",
                query="A query",
            )


class TestWebResearcher(unittest.TestCase):
    def setUp(self):
        self.valid_web_task = ResearchTask(
            question="What are the storage cost differences between TimescaleDB and ClickHouse?",
            source_type="web",
            priority="high",
            target="TimescaleDB vs ClickHouse",
            purpose="Determine storage expenses under 30-day retention.",
        )
        self.github_task = ResearchTask(
            question="Which Go WebSocket libraries are actively maintained?",
            source_type="github",
            priority="high",
            target="Go WebSocket libraries",
            purpose="Find actively maintained open-source repos.",
        )

    def test_successful_search_and_conversion(self):
        mock_data = [
            {
                "title": "ClickHouse vs TimescaleDB Cost Analysis",
                "url": "https://clickhouse.com/blog/clickhouse-vs-timescaledb-cost",
                "source": "clickhouse.com",
                "snippet": "ClickHouse offers up to 5x higher compression ratios than TimescaleDB for time-series.",
            }
        ]
        provider = MockSearchProvider(return_results=mock_data)
        researcher = WebResearcher(provider=provider)

        results = researcher.search(self.valid_web_task)
        self.assertEqual(len(results), 1)
        res = results[0]
        self.assertIsInstance(res, WebResearchResult)
        self.assertEqual(res.title, "ClickHouse vs TimescaleDB Cost Analysis")
        self.assertEqual(res.url, "https://clickhouse.com/blog/clickhouse-vs-timescaledb-cost")
        self.assertEqual(res.source, "clickhouse.com")
        self.assertEqual(res.task_question, self.valid_web_task.question)
        self.assertTrue(len(res.query) > 0)

    def test_multiple_results(self):
        mock_data = [
            {"title": f"Result {i}", "url": f"https://example.com/{i}", "source": "example.com", "snippet": f"Snippet {i}"}
            for i in range(5)
        ]
        provider = MockSearchProvider(return_results=mock_data)
        researcher = WebResearcher(provider=provider, max_results_per_task=5)

        results = researcher.search(self.valid_web_task)
        self.assertEqual(len(results), 5)

    def test_empty_result_set(self):
        provider = MockSearchProvider(return_results=[])
        researcher = WebResearcher(provider=provider)

        results = researcher.search(self.valid_web_task)
        self.assertEqual(results, [])

    def test_invalid_task_source_type_rejected(self):
        researcher = WebResearcher(provider=MockSearchProvider())
        # Passing github task to WebResearcher should raise WebSearchValidationError
        with self.assertRaises(WebSearchValidationError) as ctx:
            researcher.search(self.github_task)
        self.assertIn("Only source_type='web' is supported", str(ctx.exception))

    def test_invalid_task_type_rejected(self):
        researcher = WebResearcher(provider=MockSearchProvider())
        with self.assertRaises(WebSearchValidationError):
            researcher.search("not a research task")

    def test_malformed_provider_result_raises_validation_error(self):
        # Provider returns items missing URL or Title
        malformed_data = [{"snippet": "Missing title and URL"}]
        provider = MockSearchProvider(return_results=malformed_data)
        researcher = WebResearcher(provider=provider)

        with self.assertRaises(WebSearchValidationError):
            researcher.search(self.valid_web_task)

    def test_provider_connection_failure_propagates_connection_error(self):
        error = WebSearchConnectionError("Failed to reach search server")
        provider = MockSearchProvider(error_to_raise=error)
        researcher = WebResearcher(provider=provider)

        with self.assertRaises(WebSearchConnectionError):
            researcher.search(self.valid_web_task)

    def test_correct_query_construction(self):
        researcher = WebResearcher(provider=MockSearchProvider())

        # Task with explicit target
        q1 = researcher.build_query(self.valid_web_task)
        self.assertTrue(len(q1) > 0)
        self.assertIn("TimescaleDB", q1)
        self.assertIn("ClickHouse", q1)

        # Task with leading question words
        task_with_opening = ResearchTask(
            question="How to scale WebSocket connections on Go?",
            source_type="web",
            priority="high",
            target="Go WebSocket connections",
            purpose="Determine concurrency limits.",
        )
        q2 = researcher.build_query(task_with_opening)
        self.assertFalse(q2.lower().startswith("how to"))
        self.assertIn("WebSocket", q2)
        self.assertIn("Go", q2)

    def test_convenience_function(self):
        mock_data = [
            {
                "title": "Convenience Function Test",
                "url": "https://example.com/test",
                "source": "example.com",
                "snippet": "Testing research_web_task helper.",
            }
        ]
        provider = MockSearchProvider(return_results=mock_data)
        results = research_web_task(self.valid_web_task, provider=provider)
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].title, "Convenience Function Test")


if __name__ == "__main__":
    unittest.main()
