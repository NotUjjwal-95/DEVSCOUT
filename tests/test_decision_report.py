"""
Unit tests for DecisionReport contract and deterministic evidence validation in DEVSCOUT.
Tests reasoning-facing models, Pydantic validations, confidence levels,
reference resolution against EvidenceContext, and error cases across all sections.
"""

import json
import unittest
from pydantic import ValidationError

from models import (
    Alternative,
    Comparison,
    ComparisonAssessment,
    DecisionReport,
    DecisionReportError,
    DecisionReportValidationError,
    Evidence,
    EvidenceConflict,
    EvidenceContext,
    EvidenceGroup,
    EvidenceReferenceError,
    Finding,
    Recommendation,
    RequirementAnalysis,
    ResearchPlan,
    ResearchQuestion,
    ResearchTask,
    Risk,
    Tradeoff,
    Uncertainty,
    validate_decision_report_evidence,
)
from evidence_context import build_evidence_context


class TestDecisionReportContract(unittest.TestCase):
    def setUp(self):
        # Base Requirement Analysis & Tasks
        self.user_request = (
            "Build an IoT telemetry ingestion pipeline processing 50k events/sec on AWS."
        )
        self.requirements = RequirementAnalysis(
            goal="Build an IoT telemetry ingestion pipeline on AWS processing 50k events/sec.",
            technologies=["AWS", "Kinesis", "Kafka", "ClickHouse", "TimescaleDB"],
            requirements=["Ingest 50k events/sec", "At-least-once delivery"],
            constraints=["AWS only", "Strict budget"],
            unknowns=["Cost trade-offs between Kafka and Kinesis"],
        )
        self.q1 = ResearchQuestion(
            question="Which stream processing service (Kafka vs Kinesis) offers better cost/latency tradeoff on AWS?",
            priority="high",
            source_types=["web", "github"],
            rationale="Select optimal streaming backbone for 50k events/sec.",
        )
        self.q2 = ResearchQuestion(
            question="Which database (TimescaleDB vs ClickHouse) meets sub-second query latency under strict budget?",
            priority="high",
            source_types=["web", "rag"],
            rationale="Select optimal persistence engine under budget.",
        )
        self.plan = ResearchPlan(
            research_questions=[self.q1, self.q2],
            technologies_to_investigate=["Kafka", "Kinesis", "ClickHouse", "TimescaleDB"],
        )
        self.tasks = [
            ResearchTask(
                question=self.q1.question,
                source_type="web",
                priority="high",
                target="Kafka vs Kinesis",
                purpose="Evaluate throughput vs AWS hosting cost",
            ),
            ResearchTask(
                question=self.q2.question,
                source_type="rag",
                priority="high",
                target="TimescaleDB vs ClickHouse",
                purpose="Evaluate query performance benchmarks",
            ),
        ]

        # Valid Evidence items with reasoning-facing references EV-001, EV-002, EV-003
        self.ev1 = Evidence(
            source_type="web",
            title="AWS Kinesis vs Kafka Architecture & Cost Analysis",
            content="Managed Kinesis provides lower operational overhead for under 50k events/sec with built-in AWS IAM.",
            url="https://aws.amazon.com/blogs/kinesis-vs-kafka",
            source="aws.amazon.com",
            task_question=self.q1.question,
            query="AWS Kinesis vs Kafka",
            ev_id="EV-001",
        )
        self.ev2 = Evidence(
            source_type="github",
            title="apache/kafka",
            content="Apache Kafka open-source distributed event streaming platform.",
            url="https://github.com/apache/kafka",
            source="apache/kafka",
            task_question=self.q1.question,
            query="apache kafka",
            ev_id="EV-002",
        )
        self.ev3 = Evidence(
            source_type="rag",
            title="Internal Database Benchmark 2026",
            content="ClickHouse maintains sub-100ms p99 query latency on 30-day retention workloads.",
            source="internal-wiki/benchmark.md",
            task_question=self.q2.question,
            query="ClickHouse latency benchmark",
            ev_id="EV-003",
        )

        self.context = build_evidence_context(
            user_request=self.user_request,
            requirements=self.requirements,
            plan=self.plan,
            tasks=self.tasks,
            evidence_groups=[
                EvidenceGroup(task_question=self.q1.question, items=[self.ev1, self.ev2]),
                EvidenceGroup(task_question=self.q2.question, items=[self.ev3]),
            ],
        )

    # -----------------------------------------------------------------------
    # 1. Valid Minimal DecisionReport
    # -----------------------------------------------------------------------
    def test_valid_minimal_decision_report(self):
        report = DecisionReport(
            summary="Minimal executive summary of technical evaluation.",
            overall_confidence="medium",
        )

        self.assertEqual(report.summary, "Minimal executive summary of technical evaluation.")
        self.assertEqual(report.overall_confidence, "medium")
        self.assertEqual(report.findings, [])
        self.assertEqual(report.comparisons, [])
        self.assertIsNone(report.recommendation)
        self.assertEqual(report.alternatives, [])
        self.assertEqual(report.tradeoffs, [])
        self.assertEqual(report.risks, [])
        self.assertEqual(report.conflicts, [])
        self.assertEqual(report.uncertainties, [])
        self.assertEqual(report.all_evidence_references, [])

        # Validates successfully against context
        report.validate_evidence_references(self.context)
        validate_decision_report_evidence(report, self.context)

        # to_dict produces valid dictionary
        d = report.to_dict()
        self.assertEqual(d["summary"], report.summary)
        self.assertIsNone(d["recommendation"])

    # -----------------------------------------------------------------------
    # 2. Valid Complete DecisionReport
    # -----------------------------------------------------------------------
    def test_valid_complete_decision_report(self):
        report = DecisionReport(
            summary="Comprehensive decision analysis for IoT telemetry ingestion on AWS.",
            findings=[
                Finding(
                    question=self.q1.question,
                    finding="AWS Kinesis reduces operational management overhead for 50k events/sec workloads.",
                    reasoning="Managed serverless scaling and native IAM integration eliminate self-hosted broker overhead.",
                    evidence_references=["EV-001"],
                    confidence="high",
                ),
                Finding(
                    question=self.q2.question,
                    finding="ClickHouse delivers required sub-second query latency for 30-day telemetry retention.",
                    reasoning="Columnar storage compression and vectorized execution meet query requirements.",
                    evidence_references=["EV-003"],
                    confidence="high",
                ),
            ],
            comparisons=[
                Comparison(
                    criterion="Operational Complexity",
                    assessments=[
                        ComparisonAssessment(
                            option="AWS Kinesis",
                            assessment="Fully managed AWS service with zero broker administration.",
                            evidence_references=["EV-001"],
                        ),
                        ComparisonAssessment(
                            option="Apache Kafka",
                            assessment="Requires cluster provisioning, ZooKeeper/KRaft quorum management, and patch cycles.",
                            evidence_references=["EV-002"],
                        ),
                    ],
                )
            ],
            recommendation=Recommendation(
                option="AWS Kinesis + ClickHouse Cloud",
                reason="Provides the best balance of at-least-once ingestion guarantees and sub-second query speeds under budget.",
                evidence_references=["EV-001", "EV-003"],
                confidence="high",
            ),
            alternatives=[
                Alternative(
                    option="Self-hosted Kafka on EC2",
                    reason="Viable if cross-cloud portability becomes a mandatory hard requirement.",
                    evidence_references=["EV-002"],
                )
            ],
            tradeoffs=[
                Tradeoff(
                    decision="Choose managed AWS Kinesis over self-hosted Kafka",
                    gain="Zero cluster operational overhead and native AWS integration",
                    cost="AWS vendor lock-in and per-shard throughput constraints",
                    evidence_references=["EV-001"],
                )
            ],
            risks=[
                Risk(
                    risk="Kinesis partition key hot-spotting",
                    impact="Uneven distribution may cause throttled ingestion during burst traffic.",
                    evidence_references=["EV-001"],
                )
            ],
            conflicts=[
                EvidenceConflict(
                    topic="Kafka vs Kinesis Cost at 50,000 events/second",
                    evidence_references=["EV-001", "EV-002"],
                    assessment="Vendor documentation claims Kinesis is cheaper under 100k events/sec, while OSS advocates argue Kafka is cheaper at steady-state.",
                )
            ],
            uncertainties=[
                Uncertainty(
                    topic="Exact ClickHouse cloud hosting pricing at 30-day retention",
                    reason="Workload-specific compression ratios cannot be determined prior to pilot benchmark.",
                    impact="May require fine-tuning retention policies if storage costs exceed estimates.",
                )
            ],
            overall_confidence="high",
        )

        self.assertEqual(len(report.findings), 2)
        self.assertEqual(len(report.comparisons), 1)
        self.assertEqual(len(report.comparisons[0].assessments), 2)
        self.assertIsNotNone(report.recommendation)
        self.assertEqual(len(report.alternatives), 1)
        self.assertEqual(len(report.tradeoffs), 1)
        self.assertEqual(len(report.risks), 1)
        self.assertEqual(len(report.conflicts), 1)
        self.assertEqual(len(report.uncertainties), 1)
        self.assertEqual(report.overall_confidence, "high")

        # Resolves all references without error
        report.validate_evidence_references(self.context)
        self.assertEqual(set(report.all_evidence_references), {"EV-001", "EV-002", "EV-003"})

    # -----------------------------------------------------------------------
    # 3. Invalid Empty Strings
    # -----------------------------------------------------------------------
    def test_invalid_empty_strings_rejected(self):
        # DecisionReport summary
        with self.assertRaises(ValidationError):
            DecisionReport(summary="", overall_confidence="high")
        with self.assertRaises(ValidationError):
            DecisionReport(summary="   ", overall_confidence="high")

        # Finding fields
        with self.assertRaises(ValidationError):
            Finding(question="", finding="F", reasoning="R", confidence="high")
        with self.assertRaises(ValidationError):
            Finding(question="Q", finding="   ", reasoning="R", confidence="high")
        with self.assertRaises(ValidationError):
            Finding(question="Q", finding="F", reasoning=" ", confidence="high")

        # ComparisonAssessment fields
        with self.assertRaises(ValidationError):
            ComparisonAssessment(option="", assessment="A")
        with self.assertRaises(ValidationError):
            ComparisonAssessment(option="O", assessment="   ")

        # Comparison fields
        with self.assertRaises(ValidationError):
            Comparison(
                criterion="",
                assessments=[ComparisonAssessment(option="O", assessment="A")],
            )

        # Recommendation fields
        with self.assertRaises(ValidationError):
            Recommendation(option="", reason="R", confidence="high")
        with self.assertRaises(ValidationError):
            Recommendation(option="O", reason="   ", confidence="high")

        # Alternative fields
        with self.assertRaises(ValidationError):
            Alternative(option="", reason="R")
        with self.assertRaises(ValidationError):
            Alternative(option="O", reason="  ")

        # Tradeoff fields
        with self.assertRaises(ValidationError):
            Tradeoff(decision="", gain="G", cost="C")
        with self.assertRaises(ValidationError):
            Tradeoff(decision="D", gain=" ", cost="C")
        with self.assertRaises(ValidationError):
            Tradeoff(decision="D", gain="G", cost="")

        # Risk fields
        with self.assertRaises(ValidationError):
            Risk(risk="", impact="I")
        with self.assertRaises(ValidationError):
            Risk(risk="R", impact="   ")

        # EvidenceConflict fields
        with self.assertRaises(ValidationError):
            EvidenceConflict(topic="", assessment="A")
        with self.assertRaises(ValidationError):
            EvidenceConflict(topic="T", assessment="   ")

        # Uncertainty fields
        with self.assertRaises(ValidationError):
            Uncertainty(topic="", reason="R", impact="I")
        with self.assertRaises(ValidationError):
            Uncertainty(topic="T", reason="   ", impact="I")
        with self.assertRaises(ValidationError):
            Uncertainty(topic="T", reason="R", impact="")

    # -----------------------------------------------------------------------
    # 4. Invalid Confidence Value
    # -----------------------------------------------------------------------
    def test_invalid_confidence_value(self):
        # DecisionReport
        with self.assertRaises(ValidationError):
            DecisionReport(summary="Summary", overall_confidence="very_high")
        with self.assertRaises(ValidationError):
            DecisionReport(summary="Summary", overall_confidence="unknown")

        # Finding
        with self.assertRaises(ValidationError):
            Finding(question="Q", finding="F", reasoning="R", confidence="super")

        # Recommendation
        with self.assertRaises(ValidationError):
            Recommendation(option="O", reason="R", confidence="medium_low")

    # -----------------------------------------------------------------------
    # 5. Invalid Empty Comparison
    # -----------------------------------------------------------------------
    def test_invalid_empty_comparison(self):
        with self.assertRaises(ValidationError):
            Comparison(criterion="Cost", assessments=[])

    # -----------------------------------------------------------------------
    # 6. Valid Evidence References
    # -----------------------------------------------------------------------
    def test_valid_evidence_references(self):
        finding = Finding(
            question=self.q1.question,
            finding="Kinesis is suitable.",
            reasoning="Handles the load.",
            evidence_references=["EV-001", "EV-002"],
            confidence="high",
        )
        report = DecisionReport(
            summary="Decision summary",
            findings=[finding],
            overall_confidence="high",
        )
        # Does not raise error
        report.validate_evidence_references(self.context)
        self.assertEqual(finding.evidence_references, ["EV-001", "EV-002"])

    # -----------------------------------------------------------------------
    # 7. Unknown Evidence Reference
    # -----------------------------------------------------------------------
    def test_unknown_evidence_reference(self):
        finding = Finding(
            question=self.q1.question,
            finding="Unverifiable claim.",
            reasoning="Citing an unknown document.",
            evidence_references=["EV-999"],
            confidence="low",
        )
        report = DecisionReport(
            summary="Decision summary",
            findings=[finding],
            overall_confidence="low",
        )

        with self.assertRaises(DecisionReportValidationError) as err_ctx:
            report.validate_evidence_references(self.context)

        self.assertIn("EV-999", str(err_ctx.exception))
        # Ensure it also satisfies standard exception hierarchy
        self.assertIsInstance(err_ctx.exception, EvidenceReferenceError)
        self.assertIsInstance(err_ctx.exception, DecisionReportError)
        self.assertIsInstance(err_ctx.exception, ValueError)

    # -----------------------------------------------------------------------
    # 8. Malformed Evidence Reference
    # -----------------------------------------------------------------------
    def test_malformed_evidence_reference(self):
        # Missing digits
        with self.assertRaises(ValidationError):
            Finding(
                question="Q",
                finding="F",
                reasoning="R",
                evidence_references=["EV-1"],  # Needs at least 3 digits
                confidence="high",
            )

        # Invalid prefix
        with self.assertRaises(ValidationError):
            Finding(
                question="Q",
                finding="F",
                reasoning="R",
                evidence_references=["DOC-001"],
                confidence="high",
            )

        # Empty reference in list
        with self.assertRaises(ValidationError):
            Finding(
                question="Q",
                finding="F",
                reasoning="R",
                evidence_references=["   "],
                confidence="high",
            )

    # -----------------------------------------------------------------------
    # 9. Duplicate References in One Claim
    # -----------------------------------------------------------------------
    def test_duplicate_references_in_one_claim(self):
        # Exact duplicate
        with self.assertRaises(ValidationError):
            Finding(
                question="Q",
                finding="F",
                reasoning="R",
                evidence_references=["EV-001", "EV-001"],
                confidence="high",
            )

        # Case-insensitive duplicate
        with self.assertRaises(ValidationError):
            Recommendation(
                option="Opt",
                reason="Reason",
                evidence_references=["EV-001", "ev-001"],
                confidence="medium",
            )

    # -----------------------------------------------------------------------
    # 10. Recommendation Can Be None
    # -----------------------------------------------------------------------
    def test_recommendation_can_be_none(self):
        report = DecisionReport(
            summary="Insufficient evidence to make a firm recommendation.",
            recommendation=None,
            overall_confidence="low",
        )
        self.assertIsNone(report.recommendation)
        report.validate_evidence_references(self.context)

    # -----------------------------------------------------------------------
    # 11. Uncertainty Can Exist Without Evidence References
    # -----------------------------------------------------------------------
    def test_uncertainty_can_exist_without_evidence_references(self):
        u = Uncertainty(
            topic="Network egress cost across availability zones",
            reason="AWS pricing depends on actual multi-AZ replication volume.",
            impact="Unknown monthly operational expense variance.",
        )
        self.assertEqual(u.topic, "Network egress cost across availability zones")
        self.assertFalse(hasattr(u, "evidence_references"))

        report = DecisionReport(
            summary="Summary with uncertainty.",
            uncertainties=[u],
            overall_confidence="medium",
        )
        report.validate_evidence_references(self.context)
        self.assertEqual(len(report.uncertainties), 1)

    # -----------------------------------------------------------------------
    # 12. Multiple Findings Referencing Different EvidenceContext Items
    # -----------------------------------------------------------------------
    def test_multiple_findings_referencing_different_evidence_items(self):
        f1 = Finding(
            question=self.q1.question,
            finding="Finding 1",
            reasoning="Reasoning 1",
            evidence_references=["EV-001"],
            confidence="high",
        )
        f2 = Finding(
            question=self.q1.question,
            finding="Finding 2",
            reasoning="Reasoning 2",
            evidence_references=["EV-002"],
            confidence="medium",
        )
        f3 = Finding(
            question=self.q2.question,
            finding="Finding 3",
            reasoning="Reasoning 3",
            evidence_references=["EV-001", "EV-003"],
            confidence="high",
        )

        report = DecisionReport(
            summary="Multi-finding summary.",
            findings=[f1, f2, f3],
            overall_confidence="high",
        )
        report.validate_evidence_references(self.context)
        self.assertEqual(set(report.all_evidence_references), {"EV-001", "EV-002", "EV-003"})

    # -----------------------------------------------------------------------
    # 13. Deterministic Serialization
    # -----------------------------------------------------------------------
    def test_deterministic_serialization(self):
        report = DecisionReport(
            summary="Serialization check.",
            findings=[
                Finding(
                    question=self.q1.question,
                    finding="Kinesis scales well.",
                    reasoning="Tested throughput.",
                    evidence_references=["EV-001"],
                    confidence="high",
                )
            ],
            recommendation=Recommendation(
                option="Kinesis",
                reason="Native AWS support.",
                evidence_references=["EV-001"],
                confidence="high",
            ),
            overall_confidence="high",
        )

        dict1 = report.to_dict()
        dict2 = report.to_dict()
        self.assertEqual(dict1, dict2)

        # JSON round-trip
        json_str = json.dumps(dict1)
        parsed = json.loads(json_str)
        self.assertEqual(parsed["summary"], report.summary)
        self.assertEqual(parsed["overall_confidence"], "high")
        self.assertEqual(parsed["findings"][0]["evidence_references"], ["EV-001"])

    # -----------------------------------------------------------------------
    # 14. Full DecisionReport Validation Across Every Section
    # -----------------------------------------------------------------------
    def test_full_decision_report_validation_across_every_section(self):
        # Base valid complete report
        def make_report(**kwargs):
            base = {
                "summary": "Valid base report",
                "findings": [
                    Finding(
                        question="Q1",
                        finding="F1",
                        reasoning="R1",
                        evidence_references=["EV-001"],
                        confidence="high",
                    )
                ],
                "comparisons": [
                    Comparison(
                        criterion="Latency",
                        assessments=[
                            ComparisonAssessment(
                                option="Kinesis",
                                assessment="Low latency",
                                evidence_references=["EV-001"],
                            )
                        ],
                    )
                ],
                "recommendation": Recommendation(
                    option="Kinesis",
                    reason="Best fit",
                    evidence_references=["EV-001"],
                    confidence="high",
                ),
                "alternatives": [
                    Alternative(
                        option="Kafka",
                        reason="If open source",
                        evidence_references=["EV-002"],
                    )
                ],
                "tradeoffs": [
                    Tradeoff(
                        decision="Kinesis",
                        gain="Managed",
                        cost="Locked in",
                        evidence_references=["EV-001"],
                    )
                ],
                "risks": [
                    Risk(
                        risk="Throttling",
                        impact="Delay",
                        evidence_references=["EV-001"],
                    )
                ],
                "conflicts": [
                    EvidenceConflict(
                        topic="Cost",
                        evidence_references=["EV-001", "EV-002"],
                        assessment="Disputed cost curves",
                    )
                ],
                "uncertainties": [
                    Uncertainty(
                        topic="Network fees",
                        reason="Not measured yet",
                        impact="Budget impact",
                    )
                ],
                "overall_confidence": "high",
            }
            base.update(kwargs)
            return DecisionReport(**base)

        # Baseline validates cleanly
        valid_rep = make_report()
        valid_rep.validate_evidence_references(self.context)

        # 1. Invalid Finding reference
        rep_bad_finding = make_report(
            findings=[
                Finding(
                    question="Q",
                    finding="F",
                    reasoning="R",
                    evidence_references=["EV-999"],
                    confidence="high",
                )
            ]
        )
        with self.assertRaises(DecisionReportValidationError):
            rep_bad_finding.validate_evidence_references(self.context)

        # 2. Invalid ComparisonAssessment reference
        rep_bad_comp = make_report(
            comparisons=[
                Comparison(
                    criterion="Latency",
                    assessments=[
                        ComparisonAssessment(
                            option="Opt",
                            assessment="Ass",
                            evidence_references=["EV-999"],
                        )
                    ],
                )
            ]
        )
        with self.assertRaises(DecisionReportValidationError):
            rep_bad_comp.validate_evidence_references(self.context)

        # 3. Invalid Recommendation reference
        rep_bad_rec = make_report(
            recommendation=Recommendation(
                option="Opt",
                reason="Reason",
                evidence_references=["EV-999"],
                confidence="high",
            )
        )
        with self.assertRaises(DecisionReportValidationError):
            rep_bad_rec.validate_evidence_references(self.context)

        # 4. Invalid Alternative reference
        rep_bad_alt = make_report(
            alternatives=[
                Alternative(
                    option="Alt",
                    reason="Reason",
                    evidence_references=["EV-999"],
                )
            ]
        )
        with self.assertRaises(DecisionReportValidationError):
            rep_bad_alt.validate_evidence_references(self.context)

        # 5. Invalid Tradeoff reference
        rep_bad_tradeoff = make_report(
            tradeoffs=[
                Tradeoff(
                    decision="Dec",
                    gain="G",
                    cost="C",
                    evidence_references=["EV-999"],
                )
            ]
        )
        with self.assertRaises(DecisionReportValidationError):
            rep_bad_tradeoff.validate_evidence_references(self.context)

        # 6. Invalid Risk reference
        rep_bad_risk = make_report(
            risks=[
                Risk(
                    risk="Risk",
                    impact="Imp",
                    evidence_references=["EV-999"],
                )
            ]
        )
        with self.assertRaises(DecisionReportValidationError):
            rep_bad_risk.validate_evidence_references(self.context)

        # 7. Invalid EvidenceConflict reference
        rep_bad_conflict = make_report(
            conflicts=[
                EvidenceConflict(
                    topic="Conflict topic",
                    evidence_references=["EV-001", "EV-999"],
                    assessment="Analysis",
                )
            ]
        )
        with self.assertRaises(DecisionReportValidationError):
            rep_bad_conflict.validate_evidence_references(self.context)

    # -----------------------------------------------------------------------
    # 15. Invalid Context Type Handling
    # -----------------------------------------------------------------------
    def test_invalid_context_type_handling(self):
        report = DecisionReport(summary="Summary", overall_confidence="high")
        with self.assertRaises(TypeError):
            report.validate_evidence_references(None)  # type: ignore
        with self.assertRaises(TypeError):
            validate_decision_report_evidence(None, self.context)  # type: ignore


if __name__ == "__main__":
    unittest.main()
