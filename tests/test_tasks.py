"""
Unit tests for ResearchTask schema and TaskGenerator.
"""

import unittest
from models import ResearchPlan, ResearchQuestion, ResearchTask
from task_generator import TaskGenerator, generate_research_tasks, _derive_target


class TestResearchTaskSchema(unittest.TestCase):
    def test_valid_research_task(self):
        task = ResearchTask(
            question="Which Go WebSocket libraries are actively maintained?",
            source_type="github",
            priority="high",
            target="Go WebSocket libraries",
            purpose="Find maintained open-source options suitable for the project's requirements.",
        )
        self.assertEqual(task.question, "Which Go WebSocket libraries are actively maintained?")
        self.assertEqual(task.source_type, "github")
        self.assertEqual(task.priority, "high")
        self.assertEqual(task.target, "Go WebSocket libraries")
        self.assertEqual(task.purpose, "Find maintained open-source options suitable for the project's requirements.")
        self.assertIsInstance(task.to_dict(), dict)

    def test_source_type_normalization(self):
        task = ResearchTask(
            question="Compare Redis and Memcached performance.",
            source_type="WEB",  # Uppercase
            priority="MEDIUM",  # Uppercase
            target="Redis vs Memcached",
            purpose="Determine memory caching layer.",
        )
        self.assertEqual(task.source_type, "web")
        self.assertEqual(task.priority, "medium")

    def test_invalid_source_type_rejected(self):
        with self.assertRaises(Exception):
            ResearchTask(
                question="Some question?",
                source_type="twitter",  # Invalid
                priority="high",
                target="Tech",
                purpose="Purpose",
            )

    def test_invalid_priority_rejected(self):
        with self.assertRaises(Exception):
            ResearchTask(
                question="Some question?",
                source_type="web",
                priority="critical",  # Invalid
                target="Tech",
                purpose="Purpose",
            )

    def test_missing_required_fields_rejected(self):
        # Missing purpose
        with self.assertRaises(Exception):
            ResearchTask(
                question="Some question?",
                source_type="web",
                priority="high",
                target="Tech",
            )

    def test_empty_question_rejected(self):
        with self.assertRaises(Exception):
            ResearchTask(
                question="",
                source_type="web",
                priority="high",
                target="Tech",
                purpose="Purpose",
            )
        with self.assertRaises(Exception):
            ResearchTask(
                question="   ",
                source_type="web",
                priority="high",
                target="Tech",
                purpose="Purpose",
            )

    def test_empty_target_rejected(self):
        with self.assertRaises(Exception):
            ResearchTask(
                question="Valid question?",
                source_type="web",
                priority="high",
                target="",
                purpose="Purpose",
            )
        with self.assertRaises(Exception):
            ResearchTask(
                question="Valid question?",
                source_type="web",
                priority="high",
                target="   ",
                purpose="Purpose",
            )

    def test_empty_purpose_rejected(self):
        with self.assertRaises(Exception):
            ResearchTask(
                question="Valid question?",
                source_type="web",
                priority="high",
                target="Tech",
                purpose="",
            )
        with self.assertRaises(Exception):
            ResearchTask(
                question="Valid question?",
                source_type="web",
                priority="high",
                target="Tech",
                purpose="   ",
            )


class TestTaskGenerator(unittest.TestCase):
    def setUp(self):
        self.generator = TaskGenerator()
        self.sample_plan = ResearchPlan(
            research_questions=[
                ResearchQuestion(
                    question="Which Go WebSocket libraries are actively maintained?",
                    priority="high",
                    source_types=["github", "web"],
                    rationale="Find maintained open-source options suitable for the project's requirements.",
                ),
                ResearchQuestion(
                    question="What are the storage cost differences between TimescaleDB and ClickHouse?",
                    priority="medium",
                    source_types=["web"],
                    rationale="Determine long-term storage spend under 30-day retention.",
                ),
                ResearchQuestion(
                    question="What internal telemetry schemas exist for smart meters?",
                    priority="low",
                    source_types=["rag"],
                    rationale="Reuse existing internal data definitions.",
                ),
            ],
            technologies_to_investigate=[
                "Go",
                "WebSocket",
                "TimescaleDB",
                "ClickHouse",
                "Kafka",
            ],
        )

    def test_conversion_of_valid_research_plan(self):
        tasks = self.generator.generate_tasks(self.sample_plan)
        # Question 1 has 2 source_types (github, web) -> 2 tasks
        # Question 2 has 1 source_type (web) -> 1 task
        # Question 3 has 1 source_type (rag) -> 1 task
        # Total tasks = 4
        self.assertEqual(len(tasks), 4)
        for t in tasks:
            self.assertIsInstance(t, ResearchTask)
            self.assertTrue(len(t.question) > 0)
            self.assertTrue(len(t.target) > 0)
            self.assertTrue(len(t.purpose) > 0)
            self.assertIn(t.source_type, ["web", "github", "rag"])
            self.assertIn(t.priority, ["high", "medium", "low"])

    def test_preservation_of_priority_and_source_type(self):
        tasks = self.generator.generate_tasks(self.sample_plan)

        # First question produces 2 tasks with priority 'high'
        task_1_github = tasks[0]
        self.assertEqual(task_1_github.question, "Which Go WebSocket libraries are actively maintained?")
        self.assertEqual(task_1_github.source_type, "github")
        self.assertEqual(task_1_github.priority, "high")
        self.assertEqual(task_1_github.purpose, "Find maintained open-source options suitable for the project's requirements.")

        task_1_web = tasks[1]
        self.assertEqual(task_1_web.question, "Which Go WebSocket libraries are actively maintained?")
        self.assertEqual(task_1_web.source_type, "web")
        self.assertEqual(task_1_web.priority, "high")

        # Second question produces 1 task with priority 'medium'
        task_2 = tasks[2]
        self.assertEqual(task_2.source_type, "web")
        self.assertEqual(task_2.priority, "medium")

        # Third question produces 1 task with priority 'low'
        task_3 = tasks[3]
        self.assertEqual(task_3.source_type, "rag")
        self.assertEqual(task_3.priority, "low")

    def test_multiple_research_questions_producing_multiple_tasks(self):
        tasks = generate_research_tasks(self.sample_plan)
        self.assertGreater(len(tasks), 1)

    def test_derive_target_heuristics(self):
        techs = ["Go", "WebSocket", "TimescaleDB", "ClickHouse", "Kafka", "Kinesis"]

        # Case 1: Comparison between X and Y
        t1 = _derive_target("Between TimescaleDB and ClickHouse, which has lower cost?", techs)
        self.assertIn("TimescaleDB", t1)
        self.assertIn("ClickHouse", t1)

        # Case 2: Parentheses comparison
        t2 = _derive_target("What is best (CRDTs vs. Operational Transformation)?", techs)
        self.assertIn("CRDTs vs Operational Transformation", t2)

        # Case 3: Multiple matched technologies
        t3 = _derive_target("Should we pick Kafka or Kinesis for streaming?", techs)
        self.assertIn("Kafka", t3)
        self.assertIn("Kinesis", t3)

        # Case 4: Single technology compound
        t4 = _derive_target("Which Go WebSocket libraries are best?", techs)
        self.assertTrue(len(t4) > 0)

    def test_generator_invalid_input(self):
        with self.assertRaises(ValueError):
            self.generator.generate_tasks(None)

        with self.assertRaises(ValueError):
            self.generator.generate_tasks({})  # Empty dict is not valid ResearchPlan

        with self.assertRaises(TypeError):
            self.generator.generate_tasks("invalid_string_plan")

    def test_generator_accepts_valid_dict(self):
        plan_dict = self.sample_plan.to_dict()
        tasks = self.generator.generate_tasks(plan_dict)
        self.assertEqual(len(tasks), 4)


if __name__ == "__main__":
    unittest.main()
