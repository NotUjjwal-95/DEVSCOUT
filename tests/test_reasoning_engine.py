"""
Unit tests for the Reasoning Engine component in DEVSCOUT.
Tests prompt construction, adherence to evidence rules, JSON parsing,
deterministic reference validation against EvidenceContext, error handling,
and mocking of Groq API calls.
"""

import json
import unittest
from unittest.mock import MagicMock

from groq import APIError as GroqAPIError, AuthenticationError as GroqAuthError

from models import (
    Alternative,
    Comparison,
    ComparisonAssessment,
    DecisionReport,
    Evidence,
    EvidenceConflict,
    EvidenceContext,
    EvidenceGroup,
    Finding,
    Recommendation,
    RequirementAnalysis,
    ResearchPlan,
    ResearchQuestion,
    ResearchTask,
    Risk,
    Tradeoff,
    Uncertainty,
)
from evidence_context import build_evidence_context
from reasoning_engine import (
    APIConnectionError,
    ReasoningEngine,
    ReasoningEngineError,
    ReasoningValidationError,
    synthesize_decision_report,
)


class TestReasoningEngine(unittest.TestCase):
    def setUp(self):
        # 1. Base requirements and plan
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

        # 2. Canonical Evidence items with reasoning reference IDs: EV-001, EV-002, EV-003
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

        # Mock Groq client
        self.mock_client = MagicMock()
        self.engine = ReasoningEngine(api_key="mock-groq-key", client=self.mock_client)

    # -----------------------------------------------------------------------
    # 1. Initialization and API Key Validation
    # -----------------------------------------------------------------------
    def test_init_without_api_key_raises_api_connection_error(self):
        old_key = None
        import os
        if "GROQ_API_KEY" in os.environ:
            old_key = os.environ.pop("GROQ_API_KEY")
        try:
            with self.assertRaises(APIConnectionError):
                ReasoningEngine(api_key=None, client=None)
        finally:
            if old_key is not None:
                os.environ["GROQ_API_KEY"] = old_key

    # -----------------------------------------------------------------------
    # 2. Prompt Construction and Core Rules
    # -----------------------------------------------------------------------
    def test_build_messages_enforces_core_rules_and_context(self):
        messages = self.engine._build_messages(self.context)
        self.assertEqual(len(messages), 2)
        system_msg = messages[0]["content"]
        user_msg = messages[1]["content"]

        # Check the 6 core prompt rules
        self.assertIn("Use only evidence contained in the supplied EvidenceContext", system_msg)
        self.assertIn("Do not invent evidence IDs", system_msg)
        self.assertIn("Every factual finding, comparison assessment, recommendation, alternative, tradeoff, risk, and conflict must cite the relevant EV IDs", system_msg)
        self.assertIn("If evidence is insufficient, express the limitation as an uncertainty rather than inventing a conclusion", system_msg)
        self.assertIn("If sources disagree, represent the disagreement as a conflict rather than arbitrarily choosing one source", system_msg)
        self.assertIn("Do not treat confidence as probability. Use only high, medium, or low", system_msg)

        # Check user message contents
        self.assertIn(self.user_request, user_msg)
        self.assertIn(self.requirements.goal, user_msg)
        self.assertIn("EV-001", user_msg)
        self.assertIn("EV-002", user_msg)
        self.assertIn("EV-003", user_msg)
        self.assertIn("Valid Evidence IDs Available to Cite", user_msg)
        self.assertIn("Technical Research Context", user_msg)

    # -----------------------------------------------------------------------
    # 3. Code Fence Cleaning
    # -----------------------------------------------------------------------
    def test_clean_json_text_removes_fences(self):
        fenced = "```json\n{\"summary\": \"Test\"}\n```"
        cleaned = self.engine._clean_json_text(fenced)
        self.assertEqual(cleaned, '{"summary": "Test"}')

        bare = "  {\"summary\": \"Test bare\"}  "
        self.assertEqual(self.engine._clean_json_text(bare), '{"summary": "Test bare"}')

    # -----------------------------------------------------------------------
    # 4. Parsing Valid Complete DecisionReport
    # -----------------------------------------------------------------------
    def test_parse_and_validate_valid_complete_report(self):
        valid_json = json.dumps({
            "summary": "Executive summary: Kinesis and ClickHouse represent the optimal architecture for 50k events/sec.",
            "findings": [
                {
                    "question": self.q1.question,
                    "finding": "Kinesis provides lowest operational burden for 50k events/sec with native IAM integration.",
                    "reasoning": "Evidence EV-001 demonstrates managed cost-efficiency without running dedicated brokers.",
                    "evidence_references": ["EV-001"],
                    "confidence": "high",
                },
                {
                    "question": self.q2.question,
                    "finding": "ClickHouse easily satisfies sub-second p99 latency requirement on 30-day retention.",
                    "reasoning": "Internal benchmark EV-003 shows sub-100ms p99 query latency.",
                    "evidence_references": ["EV-003"],
                    "confidence": "high",
                },
            ],
            "comparisons": [
                {
                    "criterion": "Operational Burden",
                    "assessments": [
                        {
                            "option": "AWS Kinesis",
                            "assessment": "Fully managed service with native integration and minimal maintenance overhead.",
                            "evidence_references": ["EV-001"],
                        },
                        {
                            "option": "Apache Kafka",
                            "assessment": "Self-hosted requires dedicated broker nodes, Zookeeper/KRaft, and operational maintenance.",
                            "evidence_references": ["EV-002"],
                        },
                    ],
                }
            ],
            "recommendation": {
                "option": "AWS Kinesis + ClickHouse",
                "reason": "Given the AWS environment, strict budget, and 50k events/sec scale, Kinesis eliminates ops overhead while ClickHouse guarantees sub-second query performance.",
                "evidence_references": ["EV-001", "EV-003"],
                "confidence": "high",
            },
            "alternatives": [
                {
                    "option": "Apache Kafka",
                    "reason": "Consider if multi-cloud migration is required or event volume scales beyond 200k/sec.",
                    "evidence_references": ["EV-002"],
                }
            ],
            "tradeoffs": [
                {
                    "decision": "Choose Kinesis over self-hosted Kafka",
                    "gain": "Significantly reduced operational maintenance and integrated AWS security.",
                    "cost": "AWS proprietary lock-in and lower maximum per-partition throughput.",
                    "evidence_references": ["EV-001", "EV-002"],
                }
            ],
            "risks": [
                {
                    "risk": "Self-hosted Kafka cluster management overhead",
                    "impact": "Higher engineering ops burden and potential downtime without dedicated SRE team.",
                    "evidence_references": ["EV-002"],
                }
            ],
            "conflicts": [
                {
                    "topic": "Streaming broker operational costs",
                    "evidence_references": ["EV-001", "EV-002"],
                    "assessment": "Managed cloud services claim lower total cost of ownership whereas open-source proponents highlight raw compute savings at massive scale.",
                }
            ],
            "uncertainties": [
                {
                    "topic": "Long-term data growth beyond 30-day retention",
                    "reason": "Retention policies beyond 30 days were not evaluated in the current benchmark.",
                    "impact": "May require secondary cold storage tier on S3.",
                }
            ],
            "overall_confidence": "high",
        })

        report = self.engine._parse_and_validate(valid_json, self.context)
        self.assertIsInstance(report, DecisionReport)
        self.assertEqual(report.overall_confidence, "high")
        self.assertEqual(len(report.findings), 2)
        self.assertEqual(len(report.comparisons), 1)
        self.assertIsNotNone(report.recommendation)
        self.assertEqual(report.recommendation.option, "AWS Kinesis + ClickHouse")
        self.assertEqual(len(report.alternatives), 1)
        self.assertEqual(len(report.tradeoffs), 1)
        self.assertEqual(len(report.risks), 1)
        self.assertEqual(len(report.conflicts), 1)
        self.assertEqual(len(report.uncertainties), 1)

        # Citations are properly tracked
        all_refs = report.all_evidence_references
        self.assertIn("EV-001", all_refs)
        self.assertIn("EV-002", all_refs)
        self.assertIn("EV-003", all_refs)

    # -----------------------------------------------------------------------
    # 5. Parsing with Surrounding Commentary
    # -----------------------------------------------------------------------
    def test_parse_and_validate_with_commentary(self):
        raw = f"""Here is your synthesized decision report:
```json
{{
  "summary": "Context evaluation indicates Kinesis fits requirements.",
  "overall_confidence": "medium",
  "findings": [
    {{
      "question": "{self.q1.question}",
      "finding": "Kinesis is suitable.",
      "reasoning": "EV-001 confirms throughput suitability.",
      "evidence_references": ["EV-001"],
      "confidence": "medium"
    }}
  ]
}}
```
Let me know if you need any adjustments."""
        report = self.engine._parse_and_validate(raw, self.context)
        self.assertEqual(report.summary, "Context evaluation indicates Kinesis fits requirements.")
        self.assertEqual(report.overall_confidence, "medium")
        self.assertEqual(len(report.findings), 1)

    # -----------------------------------------------------------------------
    # 6. Insufficient Evidence: Recommendation can be None
    # -----------------------------------------------------------------------
    def test_parse_and_validate_insufficient_evidence_recommendation_none(self):
        data = {
            "summary": "Current evidence is insufficient to make a definitive database recommendation.",
            "overall_confidence": "low",
            "findings": [],
            "comparisons": [],
            "recommendation": None,
            "alternatives": [],
            "tradeoffs": [],
            "risks": [],
            "conflicts": [],
            "uncertainties": [
                {
                    "topic": "TimescaleDB query latency at 50k events/sec",
                    "reason": "No benchmark evidence was gathered for TimescaleDB.",
                    "impact": "Cannot compare TimescaleDB against ClickHouse reliably.",
                }
            ],
        }
        report = self.engine._parse_and_validate(json.dumps(data), self.context)
        self.assertIsNone(report.recommendation)
        self.assertEqual(report.overall_confidence, "low")
        self.assertEqual(len(report.uncertainties), 1)

    # -----------------------------------------------------------------------
    # 7. Strict Reference Validation: Rejection of Hallucinated EV IDs
    # -----------------------------------------------------------------------
    def test_parse_and_validate_rejects_hallucinated_ev_id_in_finding(self):
        bad_json = json.dumps({
            "summary": "Valid summary text.",
            "overall_confidence": "medium",
            "findings": [
                {
                    "question": self.q1.question,
                    "finding": "Hallucinated claim.",
                    "reasoning": "Referencing non-existent evidence.",
                    "evidence_references": ["EV-999"],  # Hallucinated ID
                    "confidence": "low",
                }
            ],
        })
        with self.assertRaises(ReasoningValidationError) as cm:
            self.engine._parse_and_validate(bad_json, self.context)
        self.assertIn("EV-999", str(cm.exception))
        self.assertIn("reference not found", str(cm.exception))

    def test_parse_and_validate_rejects_hallucinated_ev_id_in_recommendation(self):
        bad_json = json.dumps({
            "summary": "Valid summary text.",
            "overall_confidence": "high",
            "recommendation": {
                "option": "Kafka",
                "reason": "Some reason.",
                "evidence_references": ["EV-001", "EV-888"],  # EV-888 is invalid
                "confidence": "high",
            },
        })
        with self.assertRaises(ReasoningValidationError) as cm:
            self.engine._parse_and_validate(bad_json, self.context)
        self.assertIn("EV-888", str(cm.exception))

    def test_parse_and_validate_rejects_hallucinated_ev_id_in_tradeoff(self):
        bad_json = json.dumps({
            "summary": "Valid summary text.",
            "overall_confidence": "high",
            "tradeoffs": [
                {
                    "decision": "Choice",
                    "gain": "Gain",
                    "cost": "Cost",
                    "evidence_references": ["EV-777"],  # Invalid
                }
            ],
        })
        with self.assertRaises(ReasoningValidationError) as cm:
            self.engine._parse_and_validate(bad_json, self.context)
        self.assertIn("EV-777", str(cm.exception))

    # -----------------------------------------------------------------------
    # 8. Rejection of Invalid Confidence (Must be 'high', 'medium', or 'low')
    # -----------------------------------------------------------------------
    def test_parse_and_validate_rejects_numeric_or_invalid_confidence(self):
        bad_json = json.dumps({
            "summary": "Valid summary text.",
            "overall_confidence": 0.85,  # Probability instead of Literal
        })
        with self.assertRaises(ReasoningValidationError):
            self.engine._parse_and_validate(bad_json, self.context)

        bad_json2 = json.dumps({
            "summary": "Valid summary text.",
            "overall_confidence": "certain",  # Not high/medium/low
        })
        with self.assertRaises(ReasoningValidationError):
            self.engine._parse_and_validate(bad_json2, self.context)

    # -----------------------------------------------------------------------
    # 9. Rejection of Malformed / Empty Responses
    # -----------------------------------------------------------------------
    def test_parse_and_validate_rejects_empty_response(self):
        with self.assertRaises(ReasoningValidationError):
            self.engine._parse_and_validate("", self.context)

        with self.assertRaises(ReasoningValidationError):
            self.engine._parse_and_validate("   ", self.context)

        with self.assertRaises(ReasoningValidationError):
            self.engine._parse_and_validate(None, self.context)

    def test_parse_and_validate_rejects_malformed_json(self):
        with self.assertRaises(ReasoningValidationError):
            self.engine._parse_and_validate("Not JSON at all.", self.context)

    # -----------------------------------------------------------------------
    # 10. Type Checking on context input
    # -----------------------------------------------------------------------
    def test_reason_rejects_invalid_context_type(self):
        with self.assertRaises(TypeError):
            self.engine.reason(None)  # type: ignore

        with self.assertRaises(TypeError):
            self.engine.reason("not an EvidenceContext")  # type: ignore

        with self.assertRaises(TypeError):
            self.engine.reason({"dict": "instead of EvidenceContext"})  # type: ignore

    # -----------------------------------------------------------------------
    # 11. End-to-End Mock Execution of reason()
    # -----------------------------------------------------------------------
    def test_reason_successful_execution_with_mock_client(self):
        expected_json = json.dumps({
            "summary": "Comprehensive architectural recommendation for IoT telemetry pipeline.",
            "overall_confidence": "high",
            "findings": [
                {
                    "question": self.q1.question,
                    "finding": "Kinesis scales to 50k events/sec with minimal ops cost.",
                    "reasoning": "EV-001 provides managed throughput analysis.",
                    "evidence_references": ["EV-001"],
                    "confidence": "high",
                }
            ],
            "recommendation": {
                "option": "AWS Kinesis + ClickHouse",
                "reason": "Meets 50k events/sec requirement with sub-second latency.",
                "evidence_references": ["EV-001", "EV-003"],
                "confidence": "high",
            },
        })

        mock_choice = MagicMock()
        mock_choice.message.content = expected_json
        self.mock_client.chat.completions.create.return_value.choices = [mock_choice]

        report = self.engine.reason(self.context)
        self.assertIsInstance(report, DecisionReport)
        self.assertEqual(report.summary, "Comprehensive architectural recommendation for IoT telemetry pipeline.")
        self.assertEqual(report.recommendation.option, "AWS Kinesis + ClickHouse")
        self.assertEqual(report.overall_confidence, "high")

        # Verify chat completion call parameters
        self.mock_client.chat.completions.create.assert_called_once()
        call_kwargs = self.mock_client.chat.completions.create.call_args[1]
        self.assertEqual(call_kwargs["response_format"], {"type": "json_object"})
        self.assertEqual(call_kwargs["model"], self.engine.model)

    def test_reason_handles_reasoning_content_attribute(self):
        expected_json = json.dumps({
            "summary": "Reasoning model test output.",
            "overall_confidence": "medium",
        })
        mock_choice = MagicMock()
        mock_choice.message.content = ""
        mock_choice.message.reasoning_content = expected_json
        self.mock_client.chat.completions.create.return_value.choices = [mock_choice]

        report = self.engine.reason(self.context)
        self.assertEqual(report.summary, "Reasoning model test output.")
        self.assertEqual(report.overall_confidence, "medium")

    # -----------------------------------------------------------------------
    # 12. Error Translation for Groq Exceptions
    # -----------------------------------------------------------------------
    def test_reason_translates_groq_auth_error(self):
        mock_req = MagicMock()
        self.mock_client.chat.completions.create.side_effect = GroqAuthError(
            "Invalid API Key", response=MagicMock(status_code=401), body={}
        )
        with self.assertRaises(APIConnectionError) as cm:
            self.engine.reason(self.context)
        self.assertIn("Groq authentication failed", str(cm.exception))

    def test_reason_translates_groq_api_error(self):
        mock_req = MagicMock()
        self.mock_client.chat.completions.create.side_effect = GroqAPIError(
            "Service Unavailable", request=mock_req, body={}
        )
        with self.assertRaises(APIConnectionError) as cm:
            self.engine.reason(self.context)
        self.assertIn("Groq API error occurred", str(cm.exception))

    # -----------------------------------------------------------------------
    # 13. Convenience Function: synthesize_decision_report
    # -----------------------------------------------------------------------
    def test_synthesize_decision_report_convenience_function(self):
        expected_json = json.dumps({
            "summary": "Synthesized via convenience function.",
            "overall_confidence": "low",
        })
        mock_choice = MagicMock()
        mock_choice.message.content = expected_json
        self.mock_client.chat.completions.create.return_value.choices = [mock_choice]

        report = synthesize_decision_report(self.context, api_key="test-key", client=self.mock_client)
        self.assertIsInstance(report, DecisionReport)
        self.assertEqual(report.summary, "Synthesized via convenience function.")


if __name__ == "__main__":
    unittest.main()
