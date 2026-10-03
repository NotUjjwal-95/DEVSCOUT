"""
Requirement Analyzer component for DEVSCOUT.
Extracts structured technical requirements from raw user requests.
"""

import os
import json
import re
from typing import Any

from dotenv import load_dotenv
from groq import Groq, APIError as GroqAPIError, AuthenticationError as GroqAuthError

from models import RequirementAnalysis


load_dotenv()


class AnalyzerError(Exception):
    """Base exception for Requirement Analyzer errors."""
    pass


class APIConnectionError(AnalyzerError):
    """Raised when communication with Groq API fails or credentials are invalid."""
    pass


class AnalysisValidationError(AnalyzerError):
    """Raised when the model output cannot be parsed or validated against the schema."""
    def __init__(self, message: str, raw_response: str | None = None):
        super().__init__(message)
        self.raw_response = raw_response


class RequirementAnalyzer:
    """
    Analyzes technical requests and extracts structured requirements
    validated against the RequirementAnalysis schema.
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
                "GROQ_API_KEY is not set. Please add it to your .env file or pass it to RequirementAnalyzer."
            )

        self.model = model or os.getenv("GROQ_MODEL", self.DEFAULT_MODEL)
        self.client = client or Groq(api_key=self.api_key)

    def _build_messages(self, user_request: str) -> list[dict[str, str]]:
        system_prompt = (
            "You are the Requirement Analyzer component of DEVSCOUT, an AI-powered technical research "
            "and decision assistant.\n"
            "Your role is to deeply analyze developer requests and extract structured technical specifications.\n"
            "You must return ONLY a valid JSON object matching the requested schema."
        )

        user_prompt = f"""Analyze the following technical request and extract structured requirements.

Schema definition:
- "goal": (string, required) The core technical objective or problem to be solved.
- "technologies": (array of strings) Technologies, libraries, frameworks, or databases specified or implied.
- "requirements": (array of strings) Functional and non-functional requirements (e.g. scale, concurrency, features).
- "constraints": (array of strings) Hard limits (budget, licensing, hardware, deadlines, legacy systems).
- "unknowns": (array of strings) Ambiguities, architectural risks, or unstated questions needing research.

Technical request:
\"\"\"
{user_request}
\"\"\"

Output valid JSON only with keys: "goal", "technologies", "requirements", "constraints", "unknowns".
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

    def _parse_and_validate(self, raw_content: str | None) -> RequirementAnalysis:
        """Parse raw content and validate against the Pydantic schema."""
        if not raw_content or not raw_content.strip():
            raise AnalysisValidationError("Model returned an empty response.", raw_response=raw_content)

        cleaned = self._clean_json_text(raw_content)

        # Attempt 1: Direct Pydantic validation
        try:
            return RequirementAnalysis.model_validate_json(cleaned)
        except Exception:
            pass

        # Attempt 2: Extract outermost JSON object if model included surrounding commentary
        match = re.search(r"\{.*\}", cleaned, re.DOTALL)
        if match:
            try:
                return RequirementAnalysis.model_validate_json(match.group(0))
            except Exception as e:
                raise AnalysisValidationError(
                    f"Model output matched JSON syntax but failed schema validation: {e}",
                    raw_response=raw_content,
                ) from e

        raise AnalysisValidationError(
            "Could not parse valid JSON from the model response.",
            raw_response=raw_content,
        )

    def analyze(self, user_request: str) -> RequirementAnalysis:
        """
        Analyze a raw technical request and return a validated RequirementAnalysis object.
        """
        if not user_request or not user_request.strip():
            raise ValueError("user_request cannot be empty.")

        messages = self._build_messages(user_request.strip())

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


def analyze_requirements(user_request: str, **kwargs: Any) -> dict[str, Any]:
    """
    Convenience function that initializes RequirementAnalyzer and returns a dictionary.
    """
    analyzer = RequirementAnalyzer(**kwargs)
    return analyzer.analyze(user_request).to_dict()