"""
Unit tests for the Evidence Layer in DEVSCOUT.
Tests normalization, provenance, deduplication, ranking, grouping,
and error handling across Web, GitHub, and RAG research results.
"""

import unittest
from pydantic import ValidationError

from models import (
    Evidence,
    EvidenceGroup,
    GitHubResearchResult,
    RAGResearchResult,
    WebResearchResult,
    generate_stable_identifier,
)
from evidence_layer import (
    EvidenceError,
    EvidenceLayer,
    EvidenceValidationError,
    calculate_evidence_rank_score,
    deduplicate_evidence,
    from_github_result,
    from_rag_result,
    from_web_result,
    group_evidence,
    group_evidence_by_question,
    normalize_evidence,
    normalize_results,
    rank_evidence,
)


class TestEvidenceNormalization(unittest.TestCase):
    def setUp(self):
        self.web_res = WebResearchResult(
            title="Managed Streaming Data Service - Amazon Kinesis Data Streams",
            url="https://aws.amazon.com/kinesis/data-streams/",
            source="aws.amazon.com",
            snippet="Amazon Kinesis Data Streams is a serverless, real-time data streaming service that scales elastically.",
            task_question="How does AWS Kinesis compare to MSK for 50k events/sec?",
            query="AWS Kinesis Data Streams Managed Streaming",
        )
        self.gh_res = GitHubResearchResult(
            repo_name="aws-samples/dynamic-rules-engine",
            url="https://github.com/aws-samples/dynamic-rules-engine",
            description="Serverless application that enables real-time evaluation of rules against sensor data using Kinesis.",
            owner="aws-samples",
            stars=1420,
            forks=210,
            language="Java",
            open_issues=12,
            last_updated="2026-08-15T12:00:00Z",
            task_question="How does AWS Kinesis compare to MSK for 50k events/sec?",
            query="AWS Kinesis Data Streams Managed Streaming",
        )
        self.rag_res = RAGResearchResult(
            title="Corporate Streaming Pipeline Guidelines 2026",
            content="Internal benchmark: Amazon MSK achieves 30% lower cost than Kinesis at 50k events/sec with m5.large 3-broker cluster.",
            source="internal-wiki/streaming-eval.md",
            doc_id="pol-2026-streaming",
            score=0.945,
            task_question="How does AWS Kinesis compare to MSK for 50k events/sec?",
            query="AWS Kinesis vs MSK internal benchmark",
        )

    def test_web_result_normalization(self):
        evidence = from_web_result(self.web_res, task_priority="high")
        self.assertIsInstance(evidence, Evidence)
        self.assertEqual(evidence.source_type, "web")
        self.assertEqual(evidence.title, "Managed Streaming Data Service - Amazon Kinesis Data Streams")
        self.assertEqual(evidence.content, self.web_res.snippet)
        self.assertEqual(evidence.url, "https://aws.amazon.com/kinesis/data-streams/")
        self.assertEqual(evidence.source, "aws.amazon.com")
        self.assertEqual(evidence.task_question, self.web_res.task_question)
        self.assertEqual(evidence.task_priority, "high")
        self.assertEqual(evidence.query, self.web_res.query)
        self.assertIsNone(evidence.relevance_score)
        self.assertEqual(evidence.identifier, "web:https://aws.amazon.com/kinesis/data-streams")
        self.assertEqual(evidence.metadata.get("domain"), "aws.amazon.com")

    def test_web_result_empty_snippet_falls_back_to_title(self):
        web_res = WebResearchResult(
            title="AWS Kinesis Overview Article",
            url="https://example.com/kinesis",
            source="example.com",
            snippet="",
            task_question="What is Kinesis?",
            query="AWS Kinesis",
        )
        evidence = from_web_result(web_res)
        self.assertEqual(evidence.content, "AWS Kinesis Overview Article")

    def test_github_result_normalization(self):
        evidence = from_github_result(self.gh_res, task_priority="medium")
        self.assertIsInstance(evidence, Evidence)
        self.assertEqual(evidence.source_type, "github")
        self.assertEqual(evidence.title, "aws-samples/dynamic-rules-engine")
        self.assertEqual(evidence.content, self.gh_res.description)
        self.assertEqual(evidence.url, "https://github.com/aws-samples/dynamic-rules-engine")
        self.assertEqual(evidence.source, "aws-samples")
        self.assertEqual(evidence.task_question, self.gh_res.task_question)
        self.assertEqual(evidence.task_priority, "medium")
        self.assertEqual(evidence.query, self.gh_res.query)
        self.assertEqual(evidence.metadata.get("stars"), 1420)
        self.assertEqual(evidence.metadata.get("language"), "Java")
        self.assertEqual(evidence.identifier, "github:aws-samples/dynamic-rules-engine")

    def test_github_result_empty_description_falls_back(self):
        gh_res = GitHubResearchResult(
            repo_name="myorg/telemetry-worker",
            url="https://github.com/myorg/telemetry-worker",
            description="",
            owner="myorg",
            stars=45,
            forks=5,
            language="Go",
            task_question="Go worker examples?",
            query="Go telemetry worker",
        )
        evidence = from_github_result(gh_res)
        self.assertIn("myorg/telemetry-worker", evidence.content)
        self.assertIn("Go", evidence.content)
        self.assertIn("45 stars", evidence.content)

    def test_rag_result_normalization(self):
        evidence = from_rag_result(self.rag_res, task_priority="high")
        self.assertIsInstance(evidence, Evidence)
        self.assertEqual(evidence.source_type, "rag")
        self.assertEqual(evidence.title, "Corporate Streaming Pipeline Guidelines 2026")
        self.assertEqual(evidence.content, self.rag_res.content)
        self.assertIsNone(evidence.url)
        self.assertEqual(evidence.source, "internal-wiki/streaming-eval.md")
        self.assertEqual(evidence.relevance_score, 0.945)
        self.assertEqual(evidence.task_question, self.rag_res.task_question)
        self.assertEqual(evidence.task_priority, "high")
        self.assertEqual(evidence.query, self.rag_res.query)
        self.assertEqual(evidence.metadata.get("doc_id"), "pol-2026-streaming")
        self.assertEqual(evidence.identifier, "rag:pol-2026-streaming")

    def test_rag_result_with_http_source_sets_url(self):
        rag_res = RAGResearchResult(
            title="Online Architecture Document",
            content="Detailed streaming architecture in cloud docs.",
            source="https://docs.mycompany.io/arch/telemetry.md",
            doc_id="arch-001",
            score=0.88,
            task_question="What is the architecture?",
            query="telemetry architecture",
        )
        evidence = from_rag_result(rag_res)
        self.assertEqual(evidence.url, "https://docs.mycompany.io/arch/telemetry.md")

    def test_normalize_evidence_dispatcher(self):
        e1 = normalize_evidence(self.web_res)
        e2 = normalize_evidence(self.gh_res)
        e3 = normalize_evidence(self.rag_res)
        self.assertEqual(e1.source_type, "web")
        self.assertEqual(e2.source_type, "github")
        self.assertEqual(e3.source_type, "rag")

    def test_dict_input_normalization(self):
        web_dict = self.web_res.to_dict()
        web_dict["source_type"] = "web"
        evidence = normalize_evidence(web_dict)
        self.assertEqual(evidence.source_type, "web")
        self.assertEqual(evidence.title, self.web_res.title)

    def test_already_normalized_evidence_passthrough(self):
        ev = from_web_result(self.web_res)
        ev_out = normalize_evidence(ev)
        self.assertIs(ev, ev_out)


class TestEvidenceProvenance(unittest.TestCase):
    def test_provenance_fields_preserved_across_all_sources(self):
        web = WebResearchResult(
            title="Kafka Documentation",
            url="https://kafka.apache.org/documentation/",
            source="kafka.apache.org",
            snippet="Official Apache Kafka documentation.",
            task_question="What are Kafka replication mechanics?",
            query="Apache Kafka replication mechanics",
        )
        gh = GitHubResearchResult(
            repo_name="segmentio/kafka-go",
            url="https://github.com/segmentio/kafka-go",
            description="Kafka library in Go",
            owner="segmentio",
            stars=6500,
            task_question="What are Kafka replication mechanics?",
            query="Kafka Go library",
        )
        rag = RAGResearchResult(
            title="Internal Kafka Runbook",
            content="Cluster runbook for production Kafka brokers.",
            source="runbooks/kafka.md",
            doc_id="rb-kafka-prod",
            task_question="What are Kafka replication mechanics?",
            query="production Kafka broker runbook",
        )

        ev_web = from_web_result(web, task_priority="high")
        ev_gh = from_github_result(gh, task_priority="medium")
        ev_rag = from_rag_result(rag, task_priority="high")

        for ev in (ev_web, ev_gh, ev_rag):
            self.assertEqual(ev.task_question, "What are Kafka replication mechanics?")
            self.assertTrue(len(ev.query) > 0)
            self.assertTrue(len(ev.source) > 0)
            self.assertTrue(len(ev.identifier) > 0)

        self.assertEqual(ev_web.metadata["domain"], "kafka.apache.org")
        self.assertEqual(ev_gh.metadata["owner"], "segmentio")
        self.assertEqual(ev_rag.metadata["doc_id"], "rb-kafka-prod")


class TestEvidenceDeduplication(unittest.TestCase):
    def test_exact_identifier_duplicates_removed(self):
        ev1 = Evidence(
            source_type="web",
            title="AWS Kinesis Guide",
            content="Detailed Kinesis guide and pricing.",
            url="https://aws.amazon.com/kinesis/",
            source="aws.amazon.com",
            task_question="What is Kinesis?",
            query="AWS Kinesis",
        )
        ev2 = Evidence(
            source_type="web",
            title="AWS Kinesis Guide",
            content="Detailed Kinesis guide and pricing.",
            url="https://aws.amazon.com/kinesis/",
            source="aws.amazon.com",
            task_question="What is Kinesis?",
            query="AWS Kinesis",
        )
        deduped = deduplicate_evidence([ev1, ev2])
        self.assertEqual(len(deduped), 1)

    def test_url_trailing_slash_and_case_deduplication(self):
        ev1 = Evidence(
            source_type="web",
            title="AWS Kinesis Guide 1",
            content="Detailed Kinesis guide.",
            url="https://AWS.Amazon.com/kinesis/",
            source="aws.amazon.com",
            task_question="What is Kinesis?",
            query="AWS Kinesis",
        )
        ev2 = Evidence(
            source_type="web",
            title="AWS Kinesis Guide 2",
            content="Detailed Kinesis guide.",
            url="https://aws.amazon.com/kinesis",
            source="aws.amazon.com",
            task_question="What is Kinesis?",
            query="AWS Kinesis",
        )
        deduped = deduplicate_evidence([ev1, ev2])
        self.assertEqual(len(deduped), 1)

    def test_duplicate_github_repos_removed(self):
        ev1 = Evidence(
            source_type="github",
            title="aws-samples/dynamic-rules-engine",
            content="Sample rules engine.",
            url="https://github.com/aws-samples/dynamic-rules-engine",
            source="aws-samples",
            task_question="Rules engine?",
            query="rules engine",
        )
        ev2 = Evidence(
            source_type="github",
            title="aws-samples/dynamic-rules-engine",
            content="Sample rules engine repository.",
            url="https://github.com/aws-samples/dynamic-rules-engine/",
            source="aws-samples",
            task_question="Rules engine?",
            query="rules engine",
        )
        deduped = deduplicate_evidence([ev1, ev2])
        self.assertEqual(len(deduped), 1)

    def test_higher_relevance_candidate_retained_on_duplicate(self):
        ev_low = Evidence(
            source_type="rag",
            title="Kafka Architecture Note",
            content="Short note.",
            source="internal-wiki",
            identifier="rag:doc-kafka-01",
            task_question="Kafka scaling?",
            query="Kafka scaling",
            relevance_score=0.60,
        )
        ev_high = Evidence(
            source_type="rag",
            title="Kafka Architecture Note",
            content="Comprehensive note with performance benchmarks and cluster tuning.",
            source="internal-wiki",
            identifier="rag:doc-kafka-01",
            task_question="Kafka scaling?",
            query="Kafka scaling",
            relevance_score=0.96,
        )
        deduped = deduplicate_evidence([ev_low, ev_high])
        self.assertEqual(len(deduped), 1)
        self.assertEqual(deduped[0].relevance_score, 0.96)
        self.assertIn("Comprehensive note", deduped[0].content)

    def test_unique_items_preserved(self):
        ev1 = Evidence(
            source_type="web",
            title="Source 1",
            content="Content 1",
            url="https://example.com/page1",
            source="example.com",
            task_question="Q1",
            query="query 1",
        )
        ev2 = Evidence(
            source_type="web",
            title="Source 2",
            content="Content 2",
            url="https://example.com/page2",
            source="example.com",
            task_question="Q1",
            query="query 2",
        )
        ev3 = Evidence(
            source_type="github",
            title="owner/repo1",
            content="Content 3",
            url="https://github.com/owner/repo1",
            source="owner",
            task_question="Q1",
            query="query 3",
        )
        deduped = deduplicate_evidence([ev1, ev2, ev3])
        self.assertEqual(len(deduped), 3)


class TestEvidenceRanking(unittest.TestCase):
    def test_deterministic_ranking_reproducibility(self):
        items = [
            Evidence(
                source_type="web",
                title=f"Article {i}",
                content=f"Substantive article content with lots of engineering details for item {i}.",
                url=f"https://example.com/article{i}",
                source="example.com",
                task_question="Engineering question?",
                task_priority="medium" if i % 2 == 0 else "high",
                query="engineering query",
            )
            for i in range(5)
        ]
        run1 = rank_evidence(items)
        run2 = rank_evidence(items)
        self.assertEqual([e.identifier for e in run1], [e.identifier for e in run2])
        self.assertEqual([e.rank_score for e in run1], [e.rank_score for e in run2])

    def test_high_priority_ranked_higher_than_low_priority(self):
        ev_low = Evidence(
            source_type="web",
            title="Database Comparison Guide",
            content="Database comparison overview between PostgreSQL and MongoDB.",
            url="https://example.com/db-guide",
            source="example.com",
            task_question="Which database?",
            task_priority="low",
            query="database comparison",
        )
        ev_high = Evidence(
            source_type="web",
            title="Database Comparison Guide",
            content="Database comparison overview between PostgreSQL and MongoDB.",
            url="https://example.com/db-guide-2",
            source="example.com",
            task_question="Which database?",
            task_priority="high",
            query="database comparison",
        )
        ranked = rank_evidence([ev_low, ev_high])
        self.assertEqual(ranked[0].task_priority, "high")
        self.assertGreater(ranked[0].rank_score, ranked[1].rank_score)

    def test_explicit_relevance_score_impact(self):
        ev_low_score = Evidence(
            source_type="rag",
            title="RAG Doc A",
            content="Telemetry schema details and internal policy document.",
            source="docs/policy.md",
            task_question="Telemetry schema?",
            task_priority="high",
            query="telemetry schema",
            relevance_score=0.20,
        )
        ev_high_score = Evidence(
            source_type="rag",
            title="RAG Doc B",
            content="Telemetry schema details and internal policy document.",
            source="docs/policy.md",
            task_question="Telemetry schema?",
            task_priority="high",
            query="telemetry schema",
            relevance_score=0.98,
        )
        ranked = rank_evidence([ev_low_score, ev_high_score])
        self.assertEqual(ranked[0].title, "RAG Doc B")
        self.assertGreater(ranked[0].rank_score, ranked[1].rank_score)

    def test_github_stars_impact(self):
        repo_few_stars = Evidence(
            source_type="github",
            title="user/unknown-tool",
            content="New tool repository for stream processing with minimal adoption.",
            url="https://github.com/user/unknown-tool",
            source="user",
            task_question="Streaming tools?",
            task_priority="medium",
            query="streaming tool",
            metadata={"stars": 2},
        )
        repo_many_stars = Evidence(
            source_type="github",
            title="apache/flink",
            content="Apache Flink stateful computations over data streams with massive adoption.",
            url="https://github.com/apache/flink",
            source="apache",
            task_question="Streaming tools?",
            task_priority="medium",
            query="streaming tool",
            metadata={"stars": 24000},
        )
        ranked = rank_evidence([repo_few_stars, repo_many_stars])
        self.assertEqual(ranked[0].title, "apache/flink")
        self.assertGreater(ranked[0].rank_score, ranked[1].rank_score)


class TestEvidenceGrouping(unittest.TestCase):
    def setUp(self):
        self.e1 = Evidence(
            source_type="web",
            title="Web Result 1",
            content="Web content 1",
            url="https://example.com/1",
            source="example.com",
            task_question="Question A",
            query="QA",
        )
        self.e2 = Evidence(
            source_type="github",
            title="owner/repoA",
            content="GitHub content 2",
            url="https://github.com/owner/repoA",
            source="owner",
            task_question="Question A",
            query="QA",
        )
        self.e3 = Evidence(
            source_type="rag",
            title="RAG Item B",
            content="Internal doc content",
            source="wiki/B.md",
            task_question="Question B",
            query="QB",
        )

    def test_group_evidence_by_question(self):
        grouped = group_evidence_by_question([self.e1, self.e2, self.e3])
        self.assertEqual(len(grouped), 2)
        self.assertIn("Question A", grouped)
        self.assertIn("Question B", grouped)
        self.assertEqual(len(grouped["Question A"]), 2)
        self.assertEqual(len(grouped["Question B"]), 1)

    def test_group_evidence_structured(self):
        groups = group_evidence([self.e1, self.e2, self.e3])
        self.assertEqual(len(groups), 2)

        group_a = groups[0]
        self.assertEqual(group_a.task_question, "Question A")
        self.assertEqual(group_a.total_count, 2)
        self.assertEqual(group_a.web_count, 1)
        self.assertEqual(group_a.github_count, 1)
        self.assertEqual(group_a.rag_count, 0)

        by_source = group_a.by_source_type()
        self.assertEqual(len(by_source["web"]), 1)
        self.assertEqual(len(by_source["github"]), 1)
        self.assertEqual(len(by_source["rag"]), 0)


class TestEvidenceValidationAndErrors(unittest.TestCase):
    def test_unsupported_type_raises_validation_error(self):
        with self.assertRaises(EvidenceValidationError):
            normalize_evidence(42)
        with self.assertRaises(EvidenceValidationError):
            normalize_evidence("random string")

    def test_missing_required_fields_raises_validation_error(self):
        with self.assertRaises(ValidationError):
            Evidence(
                source_type="web",
                title="Only Title",
                content="",  # empty content
                source="src",
                task_question="Q?",
                query="Q",
            )

    def test_invalid_source_type_rejected(self):
        with self.assertRaises(ValidationError):
            Evidence(
                source_type="twitter",
                title="Title",
                content="Content",
                source="src",
                task_question="Q?",
                query="Q",
            )

    def test_invalid_url_rejected(self):
        with self.assertRaises(ValidationError):
            Evidence(
                source_type="web",
                title="Title",
                content="Content",
                url="ftp://ftp.example.com",
                source="src",
                task_question="Q?",
                query="Q",
            )

    def test_empty_string_fields_rejected(self):
        with self.assertRaises(ValidationError):
            Evidence(
                source_type="web",
                title="   ",
                content="Valid content",
                source="src",
                task_question="Q?",
                query="Q",
            )


class TestEvidenceLayerCoordinator(unittest.TestCase):
    def test_mixed_web_github_rag_pipeline(self):
        web = WebResearchResult(
            title="Kinesis Deep Dive",
            url="https://aws.amazon.com/kinesis/deep-dive",
            source="aws.amazon.com",
            snippet="Comprehensive deep dive into Kinesis architecture and throughput limits.",
            task_question="How to scale Kinesis?",
            query="Kinesis scaling deep dive",
        )
        web_dup = WebResearchResult(
            title="Kinesis Deep Dive (Duplicate URL)",
            url="https://aws.amazon.com/kinesis/deep-dive/",
            source="aws.amazon.com",
            snippet="Duplicate snippet of Kinesis architecture.",
            task_question="How to scale Kinesis?",
            query="Kinesis scaling deep dive",
        )
        gh = GitHubResearchResult(
            repo_name="awslabs/amazon-kinesis-client-python",
            url="https://github.com/awslabs/amazon-kinesis-client-python",
            description="Python client library for Amazon Kinesis.",
            owner="awslabs",
            stars=420,
            task_question="How to scale Kinesis?",
            query="Kinesis Python client",
        )
        rag = RAGResearchResult(
            title="Telemetry Architecture Best Practices",
            content="Internal guide for streaming telemetry at 50,000 events/sec.",
            source="internal-wiki/telemetry-arch.md",
            doc_id="arch-guide-2026",
            score=0.92,
            task_question="How to scale Kinesis?",
            query="streaming telemetry guide",
        )

        layer = EvidenceLayer(deduplicate=True, rank=True)
        raw_items = [web, web_dup, gh, rag]

        processed = layer.process(raw_items, task_priority="high")
        # 4 inputs, 1 duplicate -> 3 unique evidence items
        self.assertEqual(len(processed), 3)

        # Confirm all are Evidence instances with positive rank scores
        for item in processed:
            self.assertIsInstance(item, Evidence)
            self.assertGreater(item.rank_score, 0.0)

        # Confirm grouped output
        groups = layer.process_and_group(raw_items, task_priority="high")
        self.assertEqual(len(groups), 1)
        self.assertEqual(groups[0].total_count, 3)
        self.assertEqual(groups[0].web_count, 1)
        self.assertEqual(groups[0].github_count, 1)
        self.assertEqual(groups[0].rag_count, 1)


if __name__ == "__main__":
    unittest.main()
