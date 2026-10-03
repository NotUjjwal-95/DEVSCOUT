"""
Tests for Requirement Analyzer and schema validation.
"""

import unittest
from models import RequirementAnalysis
from analyzer import RequirementAnalyzer, AnalysisValidationError


class TestRequirementAnalysisSchema(unittest.TestCase):
    def test_valid_schema(self):
        data = {
            "goal": "Build real-time collaborative whiteboard",
            "technologies": ["React", "Go", "WebSockets"],
            "requirements": ["Support 1,000 concurrent users", "Canvas synchronization"],
            "constraints": ["Low budget", "Open-source only"],
            "unknowns": ["CRDT vs OT implementation details", "Hosting infra cost"],
        }
        model = RequirementAnalysis.model_validate(data)
        self.assertEqual(model.goal, "Build real-time collaborative whiteboard")
        self.assertEqual(len(model.technologies), 3)
        self.assertIn("React", model.technologies)
        self.assertIn("Go", model.technologies)
        self.assertIsInstance(model.to_dict(), dict)

    def test_missing_goal_raises_validation_error(self):
        data = {
            "technologies": ["React"],
            "requirements": ["Fast UI"],
        }
        with self.assertRaises(Exception):
            RequirementAnalysis.model_validate(data)

    def test_empty_goal_raises_validation_error(self):
        data = {
            "goal": "",
            "technologies": [],
            "requirements": [],
            "constraints": [],
            "unknowns": [],
        }
        with self.assertRaises(Exception):
            RequirementAnalysis.model_validate(data)


class TestAnalyzerParsingAndErrorHandling(unittest.TestCase):
    def setUp(self):
        # Initialize analyzer with a dummy key for offline testing of parsing logic
        self.analyzer = RequirementAnalyzer(api_key="test_dummy_key")

    def test_clean_markdown_code_fences(self):
        raw = """```json
{
    "goal": "Build a CLI in Rust",
    "technologies": ["Rust", "Clap"],
    "requirements": ["Fast startup"],
    "constraints": ["Cross-platform"],
    "unknowns": ["Config format"]
}
```"""
        result = self.analyzer._parse_and_validate(raw)
        self.assertEqual(result.goal, "Build a CLI in Rust")
        self.assertEqual(result.technologies, ["Rust", "Clap"])

    def test_commentary_around_json(self):
        raw = """Here is your analysis:
{
    "goal": "Build a caching layer",
    "technologies": ["Redis"],
    "requirements": ["Sub-millisecond latency"],
    "constraints": ["Memory limit 4GB"],
    "unknowns": ["Eviction policy"]
}
Hope this helps!"""
        result = self.analyzer._parse_and_validate(raw)
        self.assertEqual(result.goal, "Build a caching layer")
        self.assertIn("Redis", result.technologies)

    def test_malformed_json_raises_analysis_validation_error(self):
        raw = "This is not json at all, just plain text from model."
        with self.assertRaises(AnalysisValidationError):
            self.analyzer._parse_and_validate(raw)

    def test_empty_content_raises_analysis_validation_error(self):
        with self.assertRaises(AnalysisValidationError):
            self.analyzer._parse_and_validate("")

        with self.assertRaises(AnalysisValidationError):
            self.analyzer._parse_and_validate(None)

    def test_invalid_schema_inside_valid_json(self):
        # Valid JSON but missing required "goal" key
        raw = '{"technologies": ["Python"], "requirements": []}'
        with self.assertRaises(AnalysisValidationError):
            self.analyzer._parse_and_validate(raw)

    def test_empty_user_request_raises_value_error(self):
        with self.assertRaises(ValueError):
            self.analyzer.analyze("")

        with self.assertRaises(ValueError):
            self.analyzer.analyze("   ")


if __name__ == "__main__":
    unittest.main()
