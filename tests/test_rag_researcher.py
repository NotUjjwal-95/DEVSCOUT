"""
Unit tests for RAGResearcher and RAGResearchResult schema.
Uses mock search providers to guarantee fast, deterministic, offline execution without requiring live Pinecone.
"""

import unittest
from unittest.mock import MagicMock
import httpx
from pydantic import ValidationError

from models import ResearchTask, RAGResearchResult
from rag_researcher import (
    RAGResearcher,
    RAGResearchError,
    RAGConnectionError,
    RAGValidationError,
    PineconeProvider,
    research_rag_task,
)


class MockRAGProvider:
    """Mock provider for unit testing RAGResearcher."""
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


class TestRAGResearchResultSchema(unittest.TestCase):
    def test_valid_rag_research_result(self):
        result = RAGResearchResult(
            title="Kafka vs Kinesis Cost and SLA Evaluation",
            content="Internal benchmark: Amazon MSK achieves 30% lower cost than Kinesis at 50k events/sec with 3-broker m5.large cluster.",
            source="internal-wiki/streaming-eval.md",
            doc_id="doc-kafka-001",
            score=0.925,
            task_question="What are the cost differences between Kafka and Kinesis?",
            query="Kafka Kinesis cost differences",
        )
        self.assertEqual(result.title, "Kafka vs Kinesis Cost and SLA Evaluation")
        self.assertIn("Amazon MSK achieves", result.content)
        self.assertEqual(result.snippet, result.content)
        self.assertEqual(result.source, "internal-wiki/streaming-eval.md")
        self.assertEqual(result.doc_id, "doc-kafka-001")
        self.assertEqual(result.score, 0.925)
        self.assertEqual(result.task_question, "What are the cost differences between Kafka and Kinesis?")
        self.assertEqual(result.query, "Kafka Kinesis cost differences")
        self.assertIsInstance(result.to_dict(), dict)

    def test_missing_required_fields_rejected(self):
        # Missing content
        with self.assertRaises(ValidationError):
            RAGResearchResult(
                title="A Document",
                source="internal-docs",
                task_question="A question?",
                query="A query",
            )
        # Missing title
        with self.assertRaises(ValidationError):
            RAGResearchResult(
                content="Some content",
                source="internal-docs",
                task_question="A question?",
                query="A query",
            )
        # Missing source
        with self.assertRaises(ValidationError):
            RAGResearchResult(
                title="A Document",
                content="Some content",
                task_question="A question?",
                query="A query",
            )

    def test_empty_string_fields_rejected(self):
        # Empty title
        with self.assertRaises(ValidationError):
            RAGResearchResult(
                title="   ",
                content="Valid content",
                source="wiki",
                task_question="A question?",
                query="A query",
            )
        # Empty content
        with self.assertRaises(ValidationError):
            RAGResearchResult(
                title="Valid Title",
                content="   ",
                source="wiki",
                task_question="A question?",
                query="A query",
            )
        # Empty source
        with self.assertRaises(ValidationError):
            RAGResearchResult(
                title="Valid Title",
                content="Valid content",
                source="   ",
                task_question="A question?",
                query="A query",
            )

    def test_relevance_score_validation(self):
        # Valid float score
        res1 = RAGResearchResult(
            title="Title",
            content="Content",
            source="wiki",
            score=0.88,
            task_question="Q?",
            query="Q",
        )
        self.assertEqual(res1.score, 0.88)

        # None score allowed
        res2 = RAGResearchResult(
            title="Title",
            content="Content",
            source="wiki",
            score=None,
            task_question="Q?",
            query="Q",
        )
        self.assertIsNone(res2.score)

        # Non-numeric score rejected
        with self.assertRaises(ValidationError):
            RAGResearchResult(
                title="Title",
                content="Content",
                source="wiki",
                score="not-a-number",
                task_question="Q?",
                query="Q",
            )

    def test_alias_normalization(self):
        # Using snippet instead of content, and id instead of doc_id
        data = {
            "title": "Normalized Doc",
            "snippet": "Snippet content here",
            "source": "kb/doc1",
            "id": "item-1234",
            "task_question": "What is the architecture?",
            "query": "architecture overview",
        }
        res = RAGResearchResult.model_validate(data)
        self.assertEqual(res.content, "Snippet content here")
        self.assertEqual(res.doc_id, "item-1234")


class TestRAGResearcher(unittest.TestCase):
    def setUp(self):
        self.valid_rag_task = ResearchTask(
            question="What are our organization's internal compliance requirements for IoT telemetry retention?",
            source_type="rag",
            priority="high",
            target="Compliance & Retention Policy",
            purpose="Ensure telemetry architecture meets organizational data retention rules.",
        )
        self.web_task = ResearchTask(
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

    def test_successful_rag_search(self):
        mock_data = [
            {
                "title": "Corporate Data Retention Policy 2026",
                "content": "IoT telemetry must be retained for at least 30 days on hot storage, and archived to S3 Glacier for 1 year.",
                "source": "compliance/data-policy.md",
                "doc_id": "pol-2026-iot",
                "score": 0.94,
            }
        ]
        provider = MockRAGProvider(return_results=mock_data)
        researcher = RAGResearcher(provider=provider)

        results = researcher.search(self.valid_rag_task)
        self.assertEqual(len(results), 1)
        res = results[0]
        self.assertIsInstance(res, RAGResearchResult)
        self.assertEqual(res.title, "Corporate Data Retention Policy 2026")
        self.assertIn("at least 30 days", res.content)
        self.assertEqual(res.source, "compliance/data-policy.md")
        self.assertEqual(res.doc_id, "pol-2026-iot")
        self.assertEqual(res.score, 0.94)
        self.assertEqual(res.task_question, self.valid_rag_task.question)
        self.assertTrue(len(res.query) > 0)

    def test_multiple_results(self):
        mock_data = [
            {
                "title": f"Knowledge Article {i}",
                "content": f"Detailed guidance for topic {i}.",
                "source": "knowledge-base",
                "doc_id": f"kb-{i}",
                "score": 0.8 + (i * 0.02),
            }
            for i in range(5)
        ]
        provider = MockRAGProvider(return_results=mock_data)
        researcher = RAGResearcher(provider=provider, max_results_per_task=5)

        results = researcher.search(self.valid_rag_task)
        self.assertEqual(len(results), 5)

    def test_empty_result_set(self):
        provider = MockRAGProvider(return_results=[])
        researcher = RAGResearcher(provider=provider)

        results = researcher.search(self.valid_rag_task)
        self.assertEqual(results, [])

    def test_wrong_task_source_type_rejected(self):
        researcher = RAGResearcher(provider=MockRAGProvider())
        with self.assertRaises(RAGValidationError) as ctx:
            researcher.search(self.web_task)
        self.assertIn("Only source_type='rag' is supported", str(ctx.exception))

        with self.assertRaises(RAGValidationError) as ctx2:
            researcher.search(self.github_task)
        self.assertIn("Only source_type='rag' is supported", str(ctx2.exception))

    def test_wrong_task_type_rejected(self):
        researcher = RAGResearcher(provider=MockRAGProvider())
        with self.assertRaises(RAGValidationError):
            researcher.search("not a research task")
        with self.assertRaises(RAGValidationError):
            researcher.search({"question": "invalid dict"})

    def test_malformed_provider_result_raises_validation_error(self):
        # Provider returns items missing title or content
        malformed_data = [{"source": "kb/doc"}]
        provider = MockRAGProvider(return_results=malformed_data)
        researcher = RAGResearcher(provider=provider)

        with self.assertRaises(RAGValidationError):
            researcher.search(self.valid_rag_task)

    def test_provider_connection_failure_propagates_connection_error(self):
        error = RAGConnectionError("Failed to connect to vector index")
        provider = MockRAGProvider(error_to_raise=error)
        researcher = RAGResearcher(provider=provider)

        with self.assertRaises(RAGConnectionError):
            researcher.search(self.valid_rag_task)

    def test_unexpected_provider_exception_normalized_to_connection_error(self):
        provider = MockRAGProvider(error_to_raise=RuntimeError("Vector index gRPC channel reset"))
        researcher = RAGResearcher(provider=provider)

        with self.assertRaises(RAGConnectionError) as ctx:
            researcher.search(self.valid_rag_task)
        self.assertIn("Vector index gRPC channel reset", str(ctx.exception))

    def test_deterministic_query_construction(self):
        researcher = RAGResearcher(provider=MockRAGProvider())

        # Standard RAG task
        q1 = researcher.build_query(self.valid_rag_task)
        self.assertTrue(len(q1) > 0)
        self.assertIn("Compliance", q1)
        self.assertIn("Retention", q1)
        self.assertFalse(q1.lower().startswith("what are"))

        # Task with leading question words
        task_with_opening = ResearchTask(
            question="How to ensure at-least-once delivery with Kinesis and Kafka?",
            source_type="rag",
            priority="high",
            target="Delivery Guarantees",
            purpose="Check internal design guidelines.",
        )
        q2 = researcher.build_query(task_with_opening)
        self.assertFalse(q2.lower().startswith("how to"))
        self.assertIn("Kinesis", q2)
        self.assertIn("Kafka", q2)

        # Task with generic target
        task_generic = ResearchTask(
            question="What is our typical smart meter telemetry data schema?",
            source_type="rag",
            priority="medium",
            target="Architecture & Implementation",
            purpose="Find internal schema definitions.",
        )
        q3 = researcher.build_query(task_generic)
        self.assertIn("telemetry", q3.lower())
        self.assertIn("schema", q3.lower())

    def test_convenience_function(self):
        mock_data = [
            {
                "title": "Helper Test Document",
                "content": "Content verifying research_rag_task helper function.",
                "source": "test-suite",
                "score": 0.99,
            }
        ]
        provider = MockRAGProvider(return_results=mock_data)
        results = research_rag_task(self.valid_rag_task, provider=provider)
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].title, "Helper Test Document")


class TestPineconeProvider(unittest.TestCase):
    def test_missing_api_key_raises_connection_error(self):
        provider = PineconeProvider(api_key="")
        with self.assertRaises(RAGConnectionError) as ctx:
            provider.search("test query")
        self.assertIn("PINECONE_API_KEY is not configured", str(ctx.exception))

    def test_control_plane_no_indexes_raises_connection_error(self):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"indexes": []}
        mock_client = MagicMock()
        mock_client.get.return_value = mock_response

        provider = PineconeProvider(
            api_key="test-key",
            client=mock_client,
            embed_fn=lambda text: [0.1, 0.2, 0.3],
        )
        with self.assertRaises(RAGConnectionError) as ctx:
            provider.search("test query")
        self.assertIn("No Pinecone indexes found", str(ctx.exception))

    def test_embed_query_calls_pinecone_inference_api(self):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "model": "multilingual-e5-large",
            "data": [
                {
                    "values": [0.12, -0.34, 0.56],
                    "vector_type": "dense",
                }
            ],
            "usage": {"total_tokens": 4},
        }
        mock_client = MagicMock()
        mock_client.post.return_value = mock_response

        provider = PineconeProvider(
            api_key="test-key",
            embedding_model="multilingual-e5-large",
            client=mock_client,
        )
        vector = provider.embed_query("Kafka telemetry benchmark")

        self.assertEqual(vector, [0.12, -0.34, 0.56])
        mock_client.post.assert_called_once()
        call_args = mock_client.post.call_args
        called_url = call_args[0][0] if call_args[0] else call_args[1].get("url")
        self.assertEqual(called_url, "https://api.pinecone.io/embed")
        payload = call_args[1].get("json") or call_args[0][1]
        self.assertEqual(payload["model"], "multilingual-e5-large")
        self.assertEqual(payload["inputs"], [{"text": "Kafka telemetry benchmark"}])
        self.assertEqual(payload["parameters"]["input_type"], "query")

    def test_embed_query_authentication_failure(self):
        mock_response = MagicMock()
        mock_response.status_code = 401
        mock_response.text = "Unauthorized: Invalid API Key"
        mock_client = MagicMock()
        mock_client.post.return_value = mock_response

        provider = PineconeProvider(api_key="bad-key", client=mock_client)
        with self.assertRaises(RAGConnectionError) as ctx:
            provider.embed_query("test query")
        self.assertIn("Pinecone embedding authentication failed (HTTP 401)", str(ctx.exception))

    def test_embed_query_malformed_response_raises_connection_error(self):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"data": []}
        mock_client = MagicMock()
        mock_client.post.return_value = mock_response

        provider = PineconeProvider(api_key="test-key", client=mock_client)
        with self.assertRaises(RAGConnectionError) as ctx:
            provider.embed_query("test query")
        self.assertIn("malformed response", str(ctx.exception))

    def test_search_sends_query_vector_in_pinecone_query_payload(self):
        embed_response = MagicMock()
        embed_response.status_code = 200
        embed_response.json.return_value = {
            "model": "multilingual-e5-large",
            "data": [{"values": [0.05, 0.15, -0.25]}],
        }

        query_response = MagicMock()
        query_response.status_code = 200
        query_response.json.return_value = {
            "matches": [
                {
                    "id": "vec-101",
                    "score": 0.91,
                    "metadata": {
                        "title": "Pinecone Document",
                        "text": "Vector search text content.",
                        "source": "pinecone-index",
                    },
                }
            ]
        }

        def mock_post(url, **kwargs):
            if "api.pinecone.io/embed" in url:
                return embed_response
            return query_response

        mock_client = MagicMock()
        mock_client.post.side_effect = mock_post

        provider = PineconeProvider(
            api_key="test-key",
            index_host="https://my-index-xyz.svc.pinecone.io",
            client=mock_client,
        )
        results = provider.search("test query", max_results=3)

        self.assertEqual(len(results), 1)
        item = results[0]
        self.assertEqual(item["title"], "Pinecone Document")
        self.assertEqual(item["content"], "Vector search text content.")
        self.assertEqual(item["source"], "pinecone-index")
        self.assertEqual(item["doc_id"], "vec-101")
        self.assertEqual(item["score"], 0.91)

        # Specifically assert that POST /query was called with the vector representation!
        query_call = [c for c in mock_client.post.call_args_list if "query" in (c[0][0] if c[0] else "")][0]
        query_payload = query_call[1].get("json") or query_call[0][1]
        self.assertIn("vector", query_payload)
        self.assertEqual(query_payload["vector"], [0.05, 0.15, -0.25])
        self.assertEqual(query_payload["topK"], 3)
        self.assertTrue(query_payload["includeMetadata"])
        self.assertFalse(query_payload["includeValues"])

    def test_search_with_namespace(self):
        query_response = MagicMock()
        query_response.status_code = 200
        query_response.json.return_value = {"matches": []}

        mock_client = MagicMock()
        mock_client.post.return_value = query_response

        provider = PineconeProvider(
            api_key="test-key",
            index_host="https://my-index-xyz.svc.pinecone.io",
            namespace="dev-knowledge-base",
            client=mock_client,
            embed_fn=lambda q: [0.1, 0.2, 0.3],
        )
        provider.search("test query", max_results=5)

        call_args = mock_client.post.call_args
        query_payload = call_args[1].get("json")
        self.assertEqual(query_payload["namespace"], "dev-knowledge-base")
        self.assertEqual(query_payload["vector"], [0.1, 0.2, 0.3])

    def test_search_uses_injected_embed_fn(self):
        query_response = MagicMock()
        query_response.status_code = 200
        query_response.json.return_value = {"matches": []}

        mock_client = MagicMock()
        mock_client.post.return_value = query_response

        custom_embed_fn = MagicMock(return_value=[0.77, 0.88, 0.99])

        provider = PineconeProvider(
            api_key="test-key",
            index_host="https://my-index-xyz.svc.pinecone.io",
            client=mock_client,
            embed_fn=custom_embed_fn,
        )
        results = provider.search("custom embed query", max_results=2)

        custom_embed_fn.assert_called_once_with("custom embed query")
        # client.post should only be called once for /query (not for /embed)
        self.assertEqual(mock_client.post.call_count, 1)
        called_url = mock_client.post.call_args[0][0]
        self.assertEqual(called_url, "https://my-index-xyz.svc.pinecone.io/query")
        payload = mock_client.post.call_args[1].get("json")
        self.assertEqual(payload["vector"], [0.77, 0.88, 0.99])

    def test_network_failure_raises_connection_error(self):
        mock_client = MagicMock()
        mock_client.post.side_effect = httpx.ConnectError("Connection refused")

        provider = PineconeProvider(
            api_key="test-key",
            index_host="https://my-index-xyz.svc.pinecone.io",
            client=mock_client,
            embed_fn=lambda q: [0.1, 0.2],
        )
        with self.assertRaises(RAGConnectionError):
            provider.search("test query")


if __name__ == "__main__":
    unittest.main()
