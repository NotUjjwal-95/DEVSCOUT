"""
Unit tests for Research Planner and ResearchPlan schema validation.
"""

import unittest
from models import RequirementAnalysis, ResearchPlan, ResearchQuestion
from planner import ResearchPlanner, PlanValidationError, APIConnectionError


class TestResearchPlanSchema(unittest.TestCase):
    def test_valid_research_plan(self):
        data = {
            "research_questions": [
                {
                    "question": "How should real-time state synchronization be implemented?",
                    "priority": "high",
                    "source_types": ["web", "github", "rag"],
                    "rationale": "Synchronization strategy directly affects scalability and conflict handling.",
                },
                {
                    "question": "What are the hosting costs for 1,000 concurrent WebSocket connections?",
                    "priority": "medium",
                    "source_types": ["web"],
                    "rationale": "Must fit within low budget constraint.",
                },
            ],
            "technologies_to_investigate": ["CRDT", "Yjs", "Automerge", "Gorilla WebSocket"],
        }
        plan = ResearchPlan.model_validate(data)
        self.assertEqual(len(plan.research_questions), 2)
        self.assertEqual(plan.research_questions[0].priority, "high")
        self.assertEqual(len(plan.technologies_to_investigate), 4)

        # Test helper methods
        high_priority = plan.get_questions_by_priority("high")
        self.assertEqual(len(high_priority), 1)
        self.assertEqual(high_priority[0].question, "How should real-time state synchronization be implemented?")

        web_sources = plan.get_questions_by_source("web")
        self.assertEqual(len(web_sources), 2)

        github_sources = plan.get_questions_by_source("github")
        self.assertEqual(len(github_sources), 1)

        dict_form = plan.to_dict()
        self.assertIsInstance(dict_form, dict)
        self.assertIn("research_questions", dict_form)

    def test_priority_normalization(self):
        # Case insensitive priority (e.g. "HIGH" -> "high")
        data = {
            "question": "Which database engine fits time-series queries best?",
            "priority": "HIGH",
            "source_types": ["web", "github"],
            "rationale": "Directly impacts sub-second latency requirement.",
        }
        rq = ResearchQuestion.model_validate(data)
        self.assertEqual(rq.priority, "high")

    def test_source_types_normalization(self):
        # Case insensitive source types
        data = {
            "question": "Which database engine fits time-series queries best?",
            "priority": "high",
            "source_types": ["WEB", "GitHub"],
            "rationale": "Directly impacts sub-second latency requirement.",
        }
        rq = ResearchQuestion.model_validate(data)
        self.assertEqual(rq.source_types, ["web", "github"])

    def test_invalid_priority_rejected(self):
        data = {
            "question": "Valid question about architecture?",
            "priority": "urgent",  # Invalid: only high, medium, low allowed
            "source_types": ["web"],
            "rationale": "Some rationale.",
        }
        with self.assertRaises(Exception):
            ResearchQuestion.model_validate(data)

    def test_invalid_source_type_rejected(self):
        data = {
            "question": "Valid question about architecture?",
            "priority": "high",
            "source_types": ["twitter"],  # Invalid: only web, github, rag allowed
            "rationale": "Some rationale.",
        }
        with self.assertRaises(Exception):
            ResearchQuestion.model_validate(data)

    def test_empty_source_types_rejected(self):
        data = {
            "question": "Valid question about architecture?",
            "priority": "high",
            "source_types": [],  # Min length 1 required
            "rationale": "Some rationale.",
        }
        with self.assertRaises(Exception):
            ResearchQuestion.model_validate(data)

    def test_empty_question_rejected(self):
        data = {
            "question": "",
            "priority": "high",
            "source_types": ["web"],
            "rationale": "Some rationale.",
        }
        with self.assertRaises(Exception):
            ResearchQuestion.model_validate(data)

    def test_missing_required_fields_rejected(self):
        # Missing rationale
        data = {
            "question": "How to scale WebSocket connections?",
            "priority": "high",
            "source_types": ["web"],
        }
        with self.assertRaises(Exception):
            ResearchQuestion.model_validate(data)

    def test_empty_research_questions_in_plan_rejected(self):
        data = {
            "research_questions": [],
            "technologies_to_investigate": ["Go"],
        }
        with self.assertRaises(Exception):
            ResearchPlan.model_validate(data)


class TestResearchPlannerParsingAndErrorHandling(unittest.TestCase):
    def setUp(self):
        self.planner = ResearchPlanner(api_key="test_dummy_key")
        self.sample_analysis = RequirementAnalysis(
            goal="Build real-time whiteboard",
            technologies=["React", "Go"],
            requirements=["1,000 concurrent users"],
            constraints=["Low budget"],
            unknowns=["Sync protocol"],
        )

    def test_clean_markdown_fences(self):
        raw_json = """```json
{
  "research_questions": [
    {
      "question": "What is the memory footprint of Go WebSocket hubs per 1,000 connections?",
      "priority": "high",
      "source_types": ["web", "github"],
      "rationale": "Ensures server fits in low budget RAM limits."
    }
  ],
  "technologies_to_investigate": ["gorilla/websocket", "nhooyr/websocket"]
}
```"""
        plan = self.planner._parse_and_validate(raw_json)
        self.assertEqual(len(plan.research_questions), 1)
        self.assertEqual(plan.research_questions[0].priority, "high")
        self.assertIn("gorilla/websocket", plan.technologies_to_investigate)

    def test_commentary_around_json(self):
        raw_json = """Here is the suggested research plan:
{
  "research_questions": [
    {
      "question": "Should we use Kafka or Kinesis for 50k events/sec?",
      "priority": "high",
      "source_types": ["web", "rag"],
      "rationale": "Affects streaming cost and throughput guarantees."
    }
  ],
  "technologies_to_investigate": ["Kafka", "Kinesis"]
}
Let me know if you need changes."""
        plan = self.planner._parse_and_validate(raw_json)
        self.assertEqual(len(plan.research_questions), 1)
        self.assertEqual(plan.technologies_to_investigate, ["Kafka", "Kinesis"])

    def test_malformed_json_raises_plan_validation_error(self):
        raw = "Not a json response from model."
        with self.assertRaises(PlanValidationError):
            self.planner._parse_and_validate(raw)

    def test_empty_response_raises_plan_validation_error(self):
        with self.assertRaises(PlanValidationError):
            self.planner._parse_and_validate("")

        with self.assertRaises(PlanValidationError):
            self.planner._parse_and_validate(None)

    def test_invalid_schema_in_valid_json_raises_plan_validation_error(self):
        # Valid JSON but missing required research_questions key
        raw = '{"some_other_key": 123}'
        with self.assertRaises(PlanValidationError):
            self.planner._parse_and_validate(raw)

    def test_planner_invalid_input_rejection(self):
        with self.assertRaises(ValueError):
            self.planner.plan(None)

        with self.assertRaises(ValueError):
            self.planner.plan({})  # Empty dict is not valid RequirementAnalysis

        with self.assertRaises(TypeError):
            self.planner.plan("some raw string")  # Must be RequirementAnalysis or dict

    def test_planner_accepts_valid_dict(self):
        valid_dict = self.sample_analysis.to_dict()
        messages = self.planner._build_messages(self.sample_analysis)
        self.assertEqual(len(messages), 2)
        self.assertIn("Build real-time whiteboard", messages[1]["content"])


if __name__ == "__main__":
    unittest.main()
