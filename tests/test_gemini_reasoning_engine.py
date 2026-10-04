"""
Unit tests for the Gemini Reasoning Engine component in DEVSCOUT.
Tests Gemini initialization, configuration, prompt construction, adherence to evidence rules,
JSON parsing, deterministic reference validation against EvidenceContext, error handling,
and mocking of Google GenAI SDK calls.
"""

import json
import os
import unittest
from unittest.mock import MagicMock

from google.genai import errors

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
    ReasoningEngineError,
    APIConnectionError,
    ReasoningValidationError,
)
from gemini_reasoning_engine import (
    GeminiAPIConnectionError,
    GeminiReasoningEngine,
    GeminiReasoningEngineError,
    GeminiReasoningValidationError,
    synthesize_gemini_decision_report,
)


class TestGeminiReasoningEngine(unittest.TestCase):
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

        # Mock Google GenAI client
        self.mock_client = MagicMock()
        self.engine = GeminiReasoningEngine(api_key="mock-gemini-key", client=self.mock_client)

    # -----------------------------------------------------------------------
    # 1. Initialization and API Key Validation
    # -----------------------------------------------------------------------
    def test_init_without_api_key_raises_gemini_api_connection_error(self):
        old_gemini_key = os.environ.pop("GEMINI_API_KEY", None)
        old_google_key = os.environ.pop("GOOGLE_API_KEY", None)
        try:
            with self.assertRaises(GeminiAPIConnectionError):
                GeminiReasoningEngine(api_key=None, client=None)
        finally:
            if old_gemini_key is not None:
                os.environ["GEMINI_API_KEY"] = old_gemini_key
            if old_google_key is not None:
                os.environ["GOOGLE_API_KEY"] = old_google_key

    def test_default_model_is_gemini_2_5_flash(self):
        self.assertEqual(self.engine.model, "gemini-2.5-flash")

    def test_custom_model_configuration(self):
        custom_engine = GeminiReasoningEngine(
            api_key="mock-key",
            model="gemini-2.5-pro",
            client=self.mock_client,
        )
        self.assertEqual(custom_engine.model, "gemini-2.5-pro")

    # -----------------------------------------------------------------------
    # 2. Prompt Construction and Core Rules
    # -----------------------------------------------------------------------
    def test_build_prompts_enforces_core_rules_and_context(self):
        system_msg, user_msg = self.engine._build_prompts(self.context)

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
        with self.assertRaises(GeminiReasoningValidationError) as cm:
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
        with self.assertRaises(GeminiReasoningValidationError) as cm:
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
        with self.assertRaises(GeminiReasoningValidationError) as cm:
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
        with self.assertRaises(GeminiReasoningValidationError):
            self.engine._parse_and_validate(bad_json, self.context)

        bad_json2 = json.dumps({
            "summary": "Valid summary text.",
            "overall_confidence": "certain",  # Not high/medium/low
        })
        with self.assertRaises(GeminiReasoningValidationError):
            self.engine._parse_and_validate(bad_json2, self.context)

    # -----------------------------------------------------------------------
    # 9. Rejection of Malformed / Empty Responses
    # -----------------------------------------------------------------------
    def test_parse_and_validate_rejects_empty_response(self):
        with self.assertRaises(GeminiReasoningValidationError):
            self.engine._parse_and_validate("", self.context)

        with self.assertRaises(GeminiReasoningValidationError):
            self.engine._parse_and_validate("   ", self.context)

        with self.assertRaises(GeminiReasoningValidationError):
            self.engine._parse_and_validate(None, self.context)

    def test_parse_and_validate_rejects_malformed_json(self):
        with self.assertRaises(GeminiReasoningValidationError):
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
    # 11. End-to-End Mock Execution of reason() with Gemini Structured Schema
    # -----------------------------------------------------------------------
    def test_reason_successful_execution_with_mock_client(self):
        expected_json = json.dumps({
            "summary": "Comprehensive architectural recommendation for IoT telemetry pipeline via Gemini.",
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

        mock_response = MagicMock()
        mock_response.text = expected_json
        self.mock_client.models.generate_content.return_value = mock_response

        report = self.engine.reason(self.context)
        self.assertIsInstance(report, DecisionReport)
        self.assertEqual(report.summary, "Comprehensive architectural recommendation for IoT telemetry pipeline via Gemini.")
        self.assertEqual(report.recommendation.option, "AWS Kinesis + ClickHouse")
        self.assertEqual(report.overall_confidence, "high")

        # Verify Google GenAI client call parameters
        self.mock_client.models.generate_content.assert_called_once()
        call_kwargs = self.mock_client.models.generate_content.call_args[1]
        self.assertEqual(call_kwargs["model"], self.engine.model)
        config = call_kwargs["config"]
        self.assertEqual(config.response_mime_type, "application/json")
        self.assertEqual(config.response_schema, DecisionReport)

    # -----------------------------------------------------------------------
    # 12. Error Translation for Google GenAI Exceptions
    # -----------------------------------------------------------------------
    def test_reason_translates_gemini_api_error(self):
        self.mock_client.models.generate_content.side_effect = errors.APIError(
            code=429, response_json={"error": {"message": "Resource has been exhausted"}}
        )
        with self.assertRaises(GeminiAPIConnectionError) as cm:
            self.engine.reason(self.context)
        self.assertIn("Gemini API error occurred", str(cm.exception))

    def test_reason_translates_unexpected_error(self):
        self.mock_client.models.generate_content.side_effect = RuntimeError("Network socket dropped")
        with self.assertRaises(GeminiAPIConnectionError) as cm:
            self.engine.reason(self.context)
        self.assertIn("Unexpected connection error", str(cm.exception))

    # -----------------------------------------------------------------------
    # 13. Convenience Function: synthesize_gemini_decision_report
    # -----------------------------------------------------------------------
    def test_synthesize_gemini_decision_report_convenience_function(self):
        expected_json = json.dumps({
            "summary": "Synthesized via Gemini convenience function.",
            "overall_confidence": "low",
        })
        mock_response = MagicMock()
        mock_response.text = expected_json
        self.mock_client.models.generate_content.return_value = mock_response

        report = synthesize_gemini_decision_report(self.context, api_key="test-key", client=self.mock_client)
        self.assertIsInstance(report, DecisionReport)
        self.assertEqual(report.summary, "Synthesized via Gemini convenience function.")

    # -----------------------------------------------------------------------
    # 14. Exception Hierarchy Compatibility
    # -----------------------------------------------------------------------
    def test_exception_inheritance_compatibility(self):
        self.assertTrue(issubclass(GeminiReasoningEngineError, ReasoningEngineError))
        self.assertTrue(issubclass(GeminiAPIConnectionError, APIConnectionError))
        self.assertTrue(issubclass(GeminiReasoningValidationError, ReasoningValidationError))
        self.assertTrue(issubclass(GeminiReasoningValidationError, ValueError))

    # -----------------------------------------------------------------------
    # 15. Normalization of missing overall_confidence
    # -----------------------------------------------------------------------
    def test_parse_and_validate_missing_overall_confidence_copies_recommendation_confidence(self):
        json_without_overall_conf = json.dumps({
            "summary": "FastAPI is recommended for low-latency asynchronous API services.",
            "findings": [
                {
                    "question": self.q1.question,
                    "finding": "Throughput satisfies architectural targets.",
                    "reasoning": "EV-001 shows high concurrency support.",
                    "evidence_references": ["EV-001"],
                    "confidence": "high",
                }
            ],
            "recommendation": {
                "option": "FastAPI",
                "reason": "Meets performance, validation, and documentation criteria.",
                "evidence_references": ["EV-001"],
                "confidence": "high",
            },
        })
        report = self.engine._parse_and_validate(json_without_overall_conf, self.context)
        self.assertIsInstance(report, DecisionReport)
        self.assertEqual(report.overall_confidence, "high")
        self.assertEqual(report.recommendation.confidence, "high")

    def test_parse_and_validate_missing_overall_confidence_derives_from_findings(self):
        json_without_overall_conf_no_rec = json.dumps({
            "summary": "Evidence is inconclusive for a definitive framework recommendation.",
            "findings": [
                {
                    "question": self.q1.question,
                    "finding": "Measured latency is within acceptable tolerance.",
                    "reasoning": "EV-001 benchmark demonstrates stable latency.",
                    "evidence_references": ["EV-001"],
                    "confidence": "medium",
                }
            ],
            "recommendation": None,
            "uncertainties": [
                {
                    "topic": "Long term support",
                    "reason": "No evidence gathered on LTS commitments.",
                    "impact": "May affect upgrade lifecycle.",
                }
            ],
        })
        report = self.engine._parse_and_validate(json_without_overall_conf_no_rec, self.context)
        self.assertIsInstance(report, DecisionReport)
        self.assertEqual(report.overall_confidence, "medium")

    def test_parse_and_validate_missing_overall_confidence_no_usable_confidence_fails(self):
        json_no_usable_conf = json.dumps({
            "summary": "Summary without any usable confidence in recommendation or findings.",
            "findings": [],
            "recommendation": None,
        })
        with self.assertRaises(GeminiReasoningValidationError) as cm:
            self.engine._parse_and_validate(json_no_usable_conf, self.context)
        self.assertIn("overall_confidence", str(cm.exception))
        self.assertIn("Field required", str(cm.exception))

    def test_parse_and_validate_missing_overall_confidence_invalid_evidence_ref_still_fails(self):
        json_missing_overall_bad_ev = json.dumps({
            "summary": "Valid summary.",
            "findings": [
                {
                    "question": self.q1.question,
                    "finding": "Valid finding citing non-existent evidence.",
                    "reasoning": "Reasoning citing EV-999.",
                    "evidence_references": ["EV-999"],
                    "confidence": "high",
                }
            ],
            "recommendation": {
                "option": "Option A",
                "reason": "Good choice.",
                "evidence_references": ["EV-001"],
                "confidence": "high",
            },
        })
        with self.assertRaises(GeminiReasoningValidationError) as cm:
            self.engine._parse_and_validate(json_missing_overall_bad_ev, self.context)
        self.assertIn("EV-999", str(cm.exception))
        self.assertIn("reference not found", str(cm.exception))


if __name__ == "__main__":
    unittest.main()

