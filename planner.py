"""
Research Planner component for DEVSCOUT.
Generates a structured research plan from validated technical requirements.
"""

import os
import json
import re
from typing import Any

from dotenv import load_dotenv
from groq import Groq, APIError as GroqAPIError, AuthenticationError as GroqAuthError

from models import RequirementAnalysis, ResearchPlan


load_dotenv()


class PlannerError(Exception):
    """Base exception for Research Planner errors."""
    pass


class APIConnectionError(PlannerError):
    """Raised when communication with Groq API fails or credentials are invalid."""
    pass


class PlanValidationError(PlannerError):
    """Raised when the model output cannot be parsed or validated against the ResearchPlan schema."""
    def __init__(self, message: str, raw_response: str | None = None):
        super().__init__(message)
        self.raw_response = raw_response


class ResearchPlanner:
    """
    Formulates a structured, prioritized research plan from a validated RequirementAnalysis.
    """

    DEFAULT_MODEL = "openai/gpt-oss-20b"

    def __init__(
        self,
        api_key: str | None = None,
        model: str | None = None,
        client: Groq | None = None,
    ):
        self.api_key = api_key or os.getenv("GROQ_API_KEY")
        if not self.api_key and client is None:
            raise APIConnectionError(
                "GROQ_API_KEY is not set. Please add it to your .env file or pass it to ResearchPlanner."
            )

        self.model = model or os.getenv("GROQ_MODEL", self.DEFAULT_MODEL)
        self.client = client or Groq(api_key=self.api_key)

    def _build_messages(self, analysis: RequirementAnalysis) -> list[dict[str, str]]:
        system_prompt = (
            "You are the Research Planner component of DEVSCOUT, an AI-powered technical research "
            "and decision assistant.\n"
            "Your role is to formulate a structured, prioritized research plan before making any engineering decision.\n"
            "You identify the specific questions to answer, the technologies/concepts to investigate, "
            "the appropriate source types ('web', 'github', 'rag'), and the technical rationale.\n"
            "You must return ONLY a valid JSON object matching the requested schema."
        )

        user_prompt = f"""Given the following validated technical requirements, generate a structured research plan.

Requirements context:
- Goal: {analysis.goal}
- Technologies: {json.dumps(analysis.technologies)}
- Functional & Non-functional Requirements: {json.dumps(analysis.requirements)}
- Constraints: {json.dumps(analysis.constraints)}
- Unknowns / Risks: {json.dumps(analysis.unknowns)}

Guidelines for the research plan:
1. Research Questions:
   - Identify concrete, targeted technical questions that must be investigated before an architectural recommendation can be made.
   - Ground questions in the stated goal, requirements, constraints, and unknowns.
   - Set priority to "high", "medium", or "low". High priority is for foundational architectural choices or critical constraints.
   - For each question, select one or more appropriate source_types from ["web", "github", "rag"]:
     * "web": documentation, benchmarks, tech articles, architecture blogs, comparisons.
     * "github": open-source libraries, reference implementations, repos, starter kits.
     * "rag": internal team knowledge, proprietary design docs, past project notes.
   - Provide a concise rationale explaining why answering this question is critical to the decision.
2. Technologies to Investigate:
   - Include technologies explicitly mentioned plus necessary alternatives, protocols, or complementary libraries implied by the requirements.
   - Do NOT invent unnecessary or unrelated technologies.

Schema definition:
{{
  "research_questions": [
    {{
      "question": "Specific technical question to investigate",
      "priority": "high" | "medium" | "low",
      "source_types": ["web", "github", "rag"],
      "rationale": "Why this matters for technical decision making"
    }}
  ],
  "technologies_to_investigate": [
    "Technology or concept name"
  ]
}}

Output valid JSON only with keys: "research_questions", "technologies_to_investigate".
"""

        return [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]

    def _clean_json_text(self, text: str) -> str:
        """Strip markdown code block fences and surrounding whitespace."""
        cleaned = text.strip()
        if cleaned.startswith("```"):
            cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned, flags=re.IGNORECASE)
            cleaned = re.sub(r"\s*```$", "", cleaned)
            cleaned = cleaned.strip()
        return cleaned

    def _parse_and_validate(self, raw_content: str | None) -> ResearchPlan:
        """Parse raw content and validate against the ResearchPlan schema."""
        if not raw_content or not raw_content.strip():
            raise PlanValidationError("Model returned an empty response.", raw_response=raw_content)

        cleaned = self._clean_json_text(raw_content)

        # Attempt 1: Direct Pydantic validation
        try:
            return ResearchPlan.model_validate_json(cleaned)
        except Exception:
            pass

        # Attempt 2: Extract outermost JSON object if model included surrounding commentary
        match = re.search(r"\{.*\}", cleaned, re.DOTALL)
        if match:
            try:
                return ResearchPlan.model_validate_json(match.group(0))
            except Exception as e:
                raise PlanValidationError(
                    f"Model output matched JSON syntax but failed schema validation: {e}",
                    raw_response=raw_content,
                ) from e

        raise PlanValidationError(
            "Could not parse valid JSON from the model response.",
            raw_response=raw_content,
        )

    def plan(self, requirements: RequirementAnalysis | dict[str, Any]) -> ResearchPlan:
        """
        Formulate a research plan from a validated RequirementAnalysis object or dictionary.
        """
        if requirements is None:
            raise ValueError("requirements cannot be None.")

        if isinstance(requirements, dict):
            try:
                analysis = RequirementAnalysis.model_validate(requirements)
            except Exception as e:
                raise ValueError(f"Invalid RequirementAnalysis dictionary: {e}") from e
        elif isinstance(requirements, RequirementAnalysis):
            analysis = requirements
        else:
            raise TypeError(
                f"Expected RequirementAnalysis or dict, got {type(requirements).__name__}"
            )

        messages = self._build_messages(analysis)

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                response_format={"type": "json_object"},
            )
        except GroqAuthError as e:
            raise APIConnectionError(f"Groq authentication failed. Please check your GROQ_API_KEY: {e}") from e
        except GroqAPIError as e:
            raise APIConnectionError(f"Groq API error occurred: {e}") from e
        except Exception as e:
            raise APIConnectionError(f"Unexpected connection error while calling Groq: {e}") from e

        choice = response.choices[0]
        content = choice.message.content

        # Handle reasoning models where output might be in reasoning attributes
        if not content and hasattr(choice.message, "reasoning_content"):
            content = getattr(choice.message, "reasoning_content", None)
        if not content and hasattr(choice.message, "reasoning"):
            content = getattr(choice.message, "reasoning", None)

        return self._parse_and_validate(content)


def plan_research(requirements: RequirementAnalysis | dict[str, Any], **kwargs: Any) -> dict[str, Any]:
    """
    Convenience function that initializes ResearchPlanner and returns a dictionary plan.
    """
    planner = ResearchPlanner(**kwargs)
    return planner.plan(requirements).to_dict()
