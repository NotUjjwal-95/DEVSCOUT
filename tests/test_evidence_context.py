"""
Unit tests for the EvidenceContext and Provenance Contract in DEVSCOUT.
Tests packaging of research state, reasoning-facing reference IDs ('EV-001', ...),
provenance preservation, grouping, validation, and error handling.
"""

import unittest
from pydantic import ValidationError

from models import (
    Evidence,
    EvidenceContext,
    EvidenceGroup,
    EvidenceReferenceError,
    RequirementAnalysis,
    ResearchPlan,
    ResearchQuestion,
    ResearchTask,
)
from evidence_context import (
    EvidenceContextError,
    EvidenceContextValidationError,
    build_evidence_context,
    format_evidence_context_for_prompt,
    resolve_evidence_references,
)


class TestEvidenceContextContract(unittest.TestCase):
    def setUp(self):
        self.user_request = (
            "Build an IoT telemetry ingestion pipeline processing 50k events/sec on AWS."
        )
        self.requirements = RequirementAnalysis(
            goal="Build an IoT telemetry ingestion pipeline on AWS processing 50k events/sec.",
            technologies=["AWS", "Kinesis", "Kafka", "TimescaleDB"],
            requirements=["Ingest 50k events/sec", "At-least-once delivery"],
            constraints=["AWS only", "Strict budget"],
            unknowns=["Cost trade-offs between Kafka and Kinesis"],
        )
        self.q1 = ResearchQuestion(
            question="How does AWS Kinesis compare to MSK in cost and throughput?",
            priority="high",
            source_types=["web", "github"],
            rationale="Select optimal streaming backbone.",
        )
        self.q2 = ResearchQuestion(
            question="Which database provides sub-second query latency for telemetry?",
            priority="high",
            source_types=["web", "rag"],
            rationale="Select optimal persistence engine.",
        )
        self.plan = ResearchPlan(
            research_questions=[self.q1, self.q2],
            technologies_to_investigate=["Kinesis", "MSK", "TimescaleDB", "ClickHouse"],
        )
        self.task1 = ResearchTask(
            question="How does AWS Kinesis compare to MSK in cost and throughput?",
            source_type="web",
            priority="high",
            target="AWS Kinesis vs MSK",
            purpose="Determine streaming throughput and costs.",
        )
        self.task2 = ResearchTask(
            question="Which database provides sub-second query latency for telemetry?",
            source_type="rag",
            priority="high",
            target="TimescaleDB vs ClickHouse",
            purpose="Check internal query benchmarks.",
        )
        self.tasks = [self.task1, self.task2]

        # Evidence for Question 1
        self.ev_web = Evidence(
            source_type="web",
            title="AWS Kinesis vs MSK Pricing & Performance",
            content="Detailed benchmark of Kinesis shard throughput vs MSK m5.large cluster costs.",
            url="https://aws.amazon.com/blogs/big-data/kinesis-vs-msk",
            source="aws.amazon.com",
            task_question=self.q1.question,
            task_priority="high",
            query="AWS Kinesis vs MSK benchmark",
            rank_score=0.85,
        )
        self.ev_gh = Evidence(
            source_type="github",
            title="aws-samples/kinesis-msk-demo",
            content="Sample CDK templates comparing deployment footprints of Kinesis and MSK.",
            url="https://github.com/aws-samples/kinesis-msk-demo",
            source="aws-samples",
            task_question=self.q1.question,
            task_priority="high",
            query="kinesis msk cdk demo",
            rank_score=0.82,
            metadata={"stars": 450, "language": "TypeScript"},
        )

        # Evidence for Question 2
        self.ev_rag = Evidence(
            source_type="rag",
            title="Internal Telemetry Database Evaluation 2026",
            content="Internal benchmark: ClickHouse achieves 120ms p99 query latency over 24h window compared to 650ms on TimescaleDB.",
            source="internal-wiki/telemetry-db.md",
            task_question=self.q2.question,
            task_priority="high",
            query="telemetry database query latency benchmark",
            relevance_score=0.96,
            rank_score=0.91,
            metadata={"doc_id": "pol-2026-db"},
        )

        self.group1 = EvidenceGroup(task_question=self.q1.question, items=[self.ev_web, self.ev_gh])
        self.group2 = EvidenceGroup(task_question=self.q2.question, items=[self.ev_rag])
        self.groups = [self.group1, self.group2]

    def test_valid_evidence_context_creation(self):
        context = build_evidence_context(
            user_request=self.user_request,
            requirements=self.requirements,
            plan=self.plan,
            tasks=self.tasks,
            evidence_groups=self.groups,
        )

        self.assertIsInstance(context, EvidenceContext)
        self.assertEqual(context.user_request, self.user_request)
        self.assertEqual(context.requirements.goal, self.requirements.goal)
        self.assertEqual(len(context.tasks), 2)
        self.assertEqual(len(context.evidence_groups), 2)
        self.assertEqual(context.total_evidence_count, 3)

    def test_direct_instantiation_auto_indexes_evidence(self):
        context = EvidenceContext(
            user_request=self.user_request,
            requirements=self.requirements,
            plan=self.plan,
            tasks=self.tasks,
            evidence_groups=self.groups,
        )
        self.assertIn("EV-001", context.evidence_map)
        self.assertIn("EV-002", context.evidence_map)
        self.assertIn("EV-003", context.evidence_map)
        self.assertEqual(context.total_evidence_count, 3)

    def test_flat_evidence_list_accepted_in_builder(self):
        flat_list = [self.ev_web, self.ev_gh, self.ev_rag]
        context = build_evidence_context(
            user_request=self.user_request,
            requirements=self.requirements,
            plan=self.plan,
            tasks=self.tasks,
            evidence=flat_list,
        )
        self.assertEqual(len(context.evidence_groups), 2)
        self.assertEqual(context.total_evidence_count, 3)

    def test_reasoning_facing_ids_generation_and_uniqueness(self):
        context = build_evidence_context(
            user_request=self.user_request,
            requirements=self.requirements,
            plan=self.plan,
            tasks=self.tasks,
            evidence_groups=self.groups,
        )

        # Check IDs follow EV-xxx pattern
        for ev_id, item in context.evidence_map.items():
            self.assertTrue(ev_id.startswith("EV-"))
            self.assertEqual(item.ev_id, ev_id)

        ev_ids = list(context.evidence_map.keys())
        self.assertEqual(len(ev_ids), len(set(ev_ids)))  # All IDs are unique
        self.assertEqual(ev_ids, ["EV-001", "EV-002", "EV-003"])

    def test_deterministic_id_generation(self):
        context1 = build_evidence_context(
            user_request=self.user_request,
            requirements=self.requirements,
            plan=self.plan,
            tasks=self.tasks,
            evidence_groups=[
                EvidenceGroup(task_question=self.q1.question, items=[self.ev_web, self.ev_gh]),
                EvidenceGroup(task_question=self.q2.question, items=[self.ev_rag]),
            ],
        )
        context2 = build_evidence_context(
            user_request=self.user_request,
            requirements=self.requirements,
            plan=self.plan,
            tasks=self.tasks,
            evidence_groups=[
                EvidenceGroup(task_question=self.q1.question, items=[self.ev_web, self.ev_gh]),
                EvidenceGroup(task_question=self.q2.question, items=[self.ev_rag]),
            ],
        )

        self.assertEqual(list(context1.evidence_map.keys()), list(context2.evidence_map.keys()))
        for ev_id in context1.evidence_map:
            self.assertEqual(
                context1.evidence_map[ev_id].identifier,
                context2.evidence_map[ev_id].identifier,
            )

    def test_evidence_id_reuse_across_multiple_groups(self):
        # Suppose ev_web is relevant to both Question 1 and Question 2
        ev_shared = Evidence(
            source_type="web",
            title="AWS Kinesis vs MSK Pricing & Performance",
            content="Detailed benchmark of Kinesis shard throughput vs MSK m5.large cluster costs.",
            url="https://aws.amazon.com/blogs/big-data/kinesis-vs-msk",
            source="aws.amazon.com",
            task_question=self.q1.question,
            query="AWS Kinesis vs MSK",
        )
        group_a = EvidenceGroup(task_question="Question A", items=[ev_shared, self.ev_gh])
        group_b = EvidenceGroup(task_question="Question B", items=[ev_shared, self.ev_rag])

        context = build_evidence_context(
            user_request=self.user_request,
            requirements=self.requirements,
            plan=self.plan,
            tasks=self.tasks,
            evidence_groups=[group_a, group_b],
        )

        # 3 unique evidence items total (ev_shared is shared between groups)
        self.assertEqual(context.total_evidence_count, 3)
        self.assertEqual(group_a.items[0].ev_id, "EV-001")
        self.assertEqual(group_b.items[0].ev_id, "EV-001")
        self.assertIn("EV-001", context.get_evidence_ids_for_question("Question A"))
        self.assertIn("EV-001", context.get_evidence_ids_for_question("Question B"))

    def test_reference_resolution(self):
        context = build_evidence_context(
            user_request=self.user_request,
            requirements=self.requirements,
            plan=self.plan,
            tasks=self.tasks,
            evidence_groups=self.groups,
        )

        # Single resolve
        item1 = context.resolve_reference("EV-001")
        self.assertEqual(item1.title, self.ev_web.title)

        # Case-insensitive resolve
        item1_lower = context.resolve_reference("ev-001")
        self.assertIs(item1, item1_lower)

        # Multiple resolve
        items = context.resolve_references(["EV-001", "EV-003"])
        self.assertEqual(len(items), 2)
        self.assertEqual(items[0].source_type, "web")
        self.assertEqual(items[1].source_type, "rag")

        # Utility function resolve
        resolved = resolve_evidence_references(context, ["EV-002"])
        self.assertEqual(len(resolved), 1)
        self.assertEqual(resolved[0].title, self.ev_gh.title)

    def test_unknown_reference_resolution_raises_error(self):
        context = build_evidence_context(
            user_request=self.user_request,
            requirements=self.requirements,
            plan=self.plan,
            tasks=self.tasks,
            evidence_groups=self.groups,
        )

        with self.assertRaises(EvidenceReferenceError):
            context.resolve_reference("EV-999")

        with self.assertRaises(EvidenceReferenceError):
            context.resolve_references(["EV-001", "EV-500"])

    def test_provenance_preservation(self):
        context = build_evidence_context(
            user_request=self.user_request,
            requirements=self.requirements,
            plan=self.plan,
            tasks=self.tasks,
            evidence_groups=self.groups,
        )

        # EV-001 (Web)
        ev1 = context.get_evidence("EV-001")
        self.assertEqual(ev1.source_type, "web")
        self.assertEqual(ev1.url, "https://aws.amazon.com/blogs/big-data/kinesis-vs-msk")
        self.assertEqual(ev1.source, "aws.amazon.com")
        self.assertEqual(ev1.task_question, self.q1.question)
        self.assertEqual(ev1.query, "AWS Kinesis vs MSK benchmark")
        self.assertTrue(ev1.identifier.startswith("web:"))

        # EV-002 (GitHub)
        ev2 = context.get_evidence("EV-002")
        self.assertEqual(ev2.source_type, "github")
        self.assertEqual(ev2.metadata.get("stars"), 450)
        self.assertEqual(ev2.metadata.get("language"), "TypeScript")
        self.assertTrue(ev2.identifier.startswith("github:"))

        # EV-003 (RAG)
        ev3 = context.get_evidence("EV-003")
        self.assertEqual(ev3.source_type, "rag")
        self.assertEqual(ev3.metadata.get("doc_id"), "pol-2026-db")
        self.assertEqual(ev3.relevance_score, 0.96)
        self.assertTrue(ev3.identifier.startswith("rag:"))

        # Trace lookup by identifier
        ev_by_id = context.get_evidence_by_identifier(ev2.identifier)
        self.assertIsNotNone(ev_by_id)
        self.assertEqual(ev_by_id.ev_id, "EV-002")

    def test_evidence_grouping_preserved(self):
        context = build_evidence_context(
            user_request=self.user_request,
            requirements=self.requirements,
            plan=self.plan,
            tasks=self.tasks,
            evidence_groups=self.groups,
        )

        # Question 1
        q1_ids = context.get_evidence_ids_for_question(self.q1.question)
        self.assertEqual(q1_ids, ["EV-001", "EV-002"])

        # Question 2
        q2_ids = context.get_evidence_ids_for_question(self.q2.question)
        self.assertEqual(q2_ids, ["EV-003"])

        # Non-existent question returns empty list
        self.assertEqual(context.get_evidence_ids_for_question("Unknown question?"), [])

        # EvidenceGroup object properties
        group1 = context.get_group_for_question(self.q1.question)
        self.assertIsNotNone(group1)
        self.assertEqual(group1.evidence_ids, ["EV-001", "EV-002"])
        self.assertEqual(group1.web_count, 1)
        self.assertEqual(group1.github_count, 1)
        self.assertEqual(group1.rag_count, 0)

    def test_empty_evidence_group_is_valid_and_supported(self):
        empty_group = EvidenceGroup(
            task_question="What are IoT regulatory policies?",
            items=[],
        )
        context = build_evidence_context(
            user_request=self.user_request,
            requirements=self.requirements,
            plan=self.plan,
            tasks=self.tasks,
            evidence_groups=[self.group1, empty_group],
        )

        self.assertEqual(len(context.evidence_groups), 2)
        self.assertEqual(context.total_evidence_count, 2)
        empty_ids = context.get_evidence_ids_for_question("What are IoT regulatory policies?")
        self.assertEqual(empty_ids, [])

    def test_validation_rejects_empty_user_request(self):
        with self.assertRaises(EvidenceContextValidationError):
            build_evidence_context(
                user_request="   ",
                requirements=self.requirements,
                plan=self.plan,
                tasks=self.tasks,
                evidence_groups=self.groups,
            )

        with self.assertRaises(ValidationError):
            EvidenceContext(
                user_request="",
                requirements=self.requirements,
                plan=self.plan,
                tasks=self.tasks,
                evidence_groups=self.groups,
            )

    def test_validation_rejects_empty_tasks(self):
        with self.assertRaises(EvidenceContextValidationError):
            build_evidence_context(
                user_request=self.user_request,
                requirements=self.requirements,
                plan=self.plan,
                tasks=[],
                evidence_groups=self.groups,
            )

    def test_validation_rejects_invalid_ev_id_format_on_evidence(self):
        with self.assertRaises(ValidationError):
            Evidence(
                source_type="web",
                title="Title",
                content="Content",
                url="https://example.com",
                source="example.com",
                task_question="Question?",
                query="query",
                ev_id="INVALID_FORMAT",
            )

        with self.assertRaises(ValidationError):
            Evidence(
                source_type="web",
                title="Title",
                content="Content",
                url="https://example.com",
                source="example.com",
                task_question="Question?",
                query="query",
                ev_id="EV-1",  # Needs 3+ digits
            )

    def test_reasoning_summary_and_markdown_formatting(self):
        context = build_evidence_context(
            user_request=self.user_request,
            requirements=self.requirements,
            plan=self.plan,
            tasks=self.tasks,
            evidence_groups=self.groups,
        )

        summary = context.to_reasoning_summary()
        self.assertIn("user_request", summary)
        self.assertIn("goal", summary)
        self.assertEqual(summary["total_evidence_items"], 3)
        self.assertEqual(len(summary["questions"]), 2)
        self.assertEqual(summary["questions"][0]["evidence_ids"], ["EV-001", "EV-002"])

        md = context.format_for_reasoning()
        self.assertIn("# Technical Research Context", md)
        self.assertIn("[EV-001]", md)
        self.assertIn("[EV-002]", md)
        self.assertIn("[EV-003]", md)
        self.assertIn("(WEB)", md)
        self.assertIn("(GITHUB)", md)
        self.assertIn("(RAG)", md)

        md_prompt = format_evidence_context_for_prompt(context)
        self.assertEqual(md, md_prompt)

    def test_duplicate_ev_id_with_different_evidence_raises_validation_error(self):
        """Test 1: duplicate EV ID + different evidence raises validation error."""
        ev_diff_1 = Evidence(
            source_type="web",
            title="AWS Kinesis Architectural Patterns",
            content="Overview of AWS Kinesis shard limits and streaming patterns.",
            url="https://aws.amazon.com/kinesis/patterns",
            source="aws.amazon.com",
            task_question=self.q1.question,
            query="AWS Kinesis patterns",
            ev_id="EV-001",
        )
        ev_diff_2 = Evidence(
            source_type="github",
            title="apache/kafka",
            content="Mirror of Apache Kafka repository on GitHub.",
            url="https://github.com/apache/kafka",
            source="apache/kafka",
            task_question=self.q1.question,
            query="apache kafka repo",
            ev_id="EV-001",  # Same EV ID but completely different evidence
        )

        # In build_evidence_context
        with self.assertRaises(EvidenceContextValidationError) as ctx_err:
            build_evidence_context(
                user_request=self.user_request,
                requirements=self.requirements,
                plan=self.plan,
                tasks=self.tasks,
                evidence_groups=[
                    EvidenceGroup(task_question=self.q1.question, items=[ev_diff_1, ev_diff_2])
                ],
            )
        self.assertIn("Conflicting EV ID 'EV-001'", str(ctx_err.exception))

        # In direct EvidenceContext instantiation
        with self.assertRaises(ValidationError) as pydantic_err:
            EvidenceContext(
                user_request=self.user_request,
                requirements=self.requirements,
                plan=self.plan,
                tasks=self.tasks,
                evidence_groups=[
                    EvidenceGroup(task_question=self.q1.question, items=[ev_diff_1, ev_diff_2])
                ],
            )
        self.assertIn("Conflicting EV ID 'EV-001'", str(pydantic_err.exception))

    def test_duplicate_ev_id_with_same_evidence_accepted(self):
        """Test 2: duplicate EV ID + same evidence is accepted and preserves single reference."""
        ev_same_1 = Evidence(
            source_type="web",
            title="Kinesis vs Kafka Benchmark",
            content="Throughput and cost comparison between Kinesis and Kafka.",
            url="https://example.com/kinesis-vs-kafka",
            source="example.com",
            task_question=self.q1.question,
            query="kinesis vs kafka",
            ev_id="EV-001",
        )
        ev_same_2 = Evidence(
            source_type="web",
            title="Kinesis vs Kafka Benchmark",
            content="Throughput and cost comparison between Kinesis and Kafka.",
            url="https://example.com/kinesis-vs-kafka",
            source="example.com",
            task_question=self.q2.question,
            query="kinesis vs kafka",
            ev_id="EV-001",  # Same EV ID and same underlying evidence identifier
        )

        group_a = EvidenceGroup(task_question=self.q1.question, items=[ev_same_1])
        group_b = EvidenceGroup(task_question=self.q2.question, items=[ev_same_2])

        # build_evidence_context
        context = build_evidence_context(
            user_request=self.user_request,
            requirements=self.requirements,
            plan=self.plan,
            tasks=self.tasks,
            evidence_groups=[group_a, group_b],
        )

        self.assertEqual(context.total_evidence_count, 1)
        self.assertEqual(list(context.evidence_map.keys()), ["EV-001"])
        self.assertEqual(context.resolve_reference("EV-001").identifier, ev_same_1.identifier)
        self.assertEqual(group_a.items[0].ev_id, "EV-001")
        self.assertEqual(group_b.items[0].ev_id, "EV-001")

        # Direct EvidenceContext instantiation
        direct_context = EvidenceContext(
            user_request=self.user_request,
            requirements=self.requirements,
            plan=self.plan,
            tasks=self.tasks,
            evidence_groups=[group_a, group_b],
        )
        self.assertEqual(direct_context.total_evidence_count, 1)
        self.assertEqual(direct_context.resolve_reference("EV-001").identifier, ev_same_1.identifier)

    def test_valid_pre_existing_ev_ids_preserved(self):
        """Test 3: valid pre-existing EV IDs are preserved in context."""
        ev1 = Evidence(
            source_type="web",
            title="Doc 1",
            content="Content 1",
            url="https://example.com/1",
            source="example.com",
            task_question=self.q1.question,
            query="query 1",
            ev_id="EV-001",
        )
        ev2 = Evidence(
            source_type="github",
            title="org/repo",
            content="Content 2",
            url="https://github.com/org/repo",
            source="github.com",
            task_question=self.q1.question,
            query="query 2",
            ev_id="EV-005",
        )
        ev3 = Evidence(
            source_type="rag",
            title="Doc 3",
            content="Content 3",
            source="wiki",
            task_question=self.q2.question,
            query="query 3",
            ev_id="EV-010",
        )

        group = EvidenceGroup(task_question="Questions", items=[ev1, ev2, ev3])
        context = build_evidence_context(
            user_request=self.user_request,
            requirements=self.requirements,
            plan=self.plan,
            tasks=self.tasks,
            evidence_groups=[group],
        )

        self.assertEqual(context.total_evidence_count, 3)
        self.assertEqual(list(context.evidence_map.keys()), ["EV-001", "EV-005", "EV-010"])
        self.assertEqual(context.resolve_reference("EV-001").identifier, ev1.identifier)
        self.assertEqual(context.resolve_reference("EV-005").identifier, ev2.identifier)
        self.assertEqual(context.resolve_reference("EV-010").identifier, ev3.identifier)

        self.assertEqual(ev1.ev_id, "EV-001")
        self.assertEqual(ev2.ev_id, "EV-005")
        self.assertEqual(ev3.ev_id, "EV-010")

    def test_mixed_pre_existing_and_auto_generated_ids(self):
        """Test 4: mixed pre-existing and auto-generated IDs do not collide."""
        ev_pre_1 = Evidence(
            source_type="web",
            title="Pre-existing Item 1",
            content="Content A",
            url="https://example.com/pre-1",
            source="example.com",
            task_question=self.q1.question,
            query="query",
            ev_id="EV-002",
        )
        ev_auto_1 = Evidence(
            source_type="web",
            title="Auto Item 1",
            content="Content B",
            url="https://example.com/auto-1",
            source="example.com",
            task_question=self.q1.question,
            query="query",
            ev_id=None,
        )
        ev_pre_2 = Evidence(
            source_type="github",
            title="org/repo-pre",
            content="Content C",
            url="https://github.com/org/repo-pre",
            source="github.com",
            task_question=self.q2.question,
            query="query",
            ev_id="EV-004",
        )
        ev_auto_2 = Evidence(
            source_type="rag",
            title="Auto Item 2",
            content="Content D",
            source="wiki",
            task_question=self.q2.question,
            query="query",
            ev_id=None,
        )

        context = build_evidence_context(
            user_request=self.user_request,
            requirements=self.requirements,
            plan=self.plan,
            tasks=self.tasks,
            evidence_groups=[
                EvidenceGroup(task_question=self.q1.question, items=[ev_pre_1, ev_auto_1]),
                EvidenceGroup(task_question=self.q2.question, items=[ev_pre_2, ev_auto_2]),
            ],
        )

        self.assertEqual(context.total_evidence_count, 4)
        # Pre-existing IDs are preserved
        self.assertEqual(ev_pre_1.ev_id, "EV-002")
        self.assertEqual(ev_pre_2.ev_id, "EV-004")

        # Auto-generated IDs fill gaps without colliding: EV-001 and EV-003
        self.assertEqual(ev_auto_1.ev_id, "EV-001")
        self.assertEqual(ev_auto_2.ev_id, "EV-003")

        # All 4 IDs are unique and mapped correctly
        ev_keys = list(context.evidence_map.keys())
        self.assertEqual(len(ev_keys), 4)
        self.assertEqual(len(set(ev_keys)), 4)
        self.assertEqual(ev_keys, ["EV-001", "EV-002", "EV-003", "EV-004"])

        self.assertEqual(context.resolve_reference("EV-001").identifier, ev_auto_1.identifier)
        self.assertEqual(context.resolve_reference("EV-002").identifier, ev_pre_1.identifier)
        self.assertEqual(context.resolve_reference("EV-003").identifier, ev_auto_2.identifier)
        self.assertEqual(context.resolve_reference("EV-004").identifier, ev_pre_2.identifier)

    def test_same_evidence_with_conflicting_ev_ids_raises_error(self):
        """Test conflicting EV IDs on the same evidence raises validation error."""
        ev_conflict_1 = Evidence(
            source_type="web",
            title="Doc Conflict",
            content="Content",
            url="https://example.com/conflict",
            source="example.com",
            task_question=self.q1.question,
            query="query",
            ev_id="EV-001",
        )
        ev_conflict_2 = Evidence(
            source_type="web",
            title="Doc Conflict",
            content="Content",
            url="https://example.com/conflict",
            source="example.com",
            task_question=self.q2.question,
            query="query",
            ev_id="EV-002",  # Same identifier, conflicting EV ID
        )

        with self.assertRaises(EvidenceContextValidationError) as ctx_err:
            build_evidence_context(
                user_request=self.user_request,
                requirements=self.requirements,
                plan=self.plan,
                tasks=self.tasks,
                evidence_groups=[
                    EvidenceGroup(task_question=self.q1.question, items=[ev_conflict_1]),
                    EvidenceGroup(task_question=self.q2.question, items=[ev_conflict_2]),
                ],
            )
        self.assertIn("Conflicting EV ID for evidence", str(ctx_err.exception))


if __name__ == "__main__":
    unittest.main()
