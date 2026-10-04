"""
Reasoning Engine component for DEVSCOUT.
Synthesizes grounded technical decision reports from validated EvidenceContext,
enforcing strict evidence citation and deterministic reference validation.
"""

import os
import json
import re
from typing import Any

from dotenv import load_dotenv
from groq import Groq, APIError as GroqAPIError, AuthenticationError as GroqAuthError

from models import (
    Confidence,
    DecisionReport,
    DecisionReportError,
    DecisionReportValidationError,
    EvidenceContext,
    EvidenceReferenceError,
)


load_dotenv()


class ReasoningEngineError(Exception):
    """Base exception for Reasoning Engine errors."""
    pass


class APIConnectionError(ReasoningEngineError):
    """Raised when communication with Groq API fails or credentials are invalid."""
    pass


class ReasoningValidationError(ReasoningEngineError, ValueError):
    """Raised when the model output fails schema or evidence reference validation."""
    def __init__(self, message: str, raw_response: str | None = None):
        super().__init__(message)
        self.raw_response = raw_response


class ReasoningEngine:
    """
    Synthesizes grounded, evidence-backed technical decision reports from an EvidenceContext.
    Enforces strict citation rules and deterministic reference validation against the context.
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
                "GROQ_API_KEY is not set. Please add it to your .env file or pass it to ReasoningEngine."
            )

        self.model = model or os.getenv("GROQ_MODEL", self.DEFAULT_MODEL)
        self.client = client or Groq(api_key=self.api_key)

    def _build_messages(self, context: EvidenceContext) -> list[dict[str, str]]:
        available_ev_ids = list(context.evidence_map.keys())
        formatted_context = context.format_for_reasoning()

        system_prompt = (
            "You are the Reasoning Engine component of DEVSCOUT, an AI-powered technical research and decision assistant.\n"
            "Your role is to analyze verified research evidence and synthesize a defensible, grounded technical DecisionReport.\n\n"
            "Strict Reasoning Rules:\n"
            "1. Use only evidence contained in the supplied EvidenceContext.\n"
            "2. Do not invent evidence IDs. Only cite valid EV IDs present in the context.\n"
            "3. Every factual finding, comparison assessment, recommendation, alternative, tradeoff, risk, and conflict must cite the relevant EV IDs.\n"
            "4. If evidence is insufficient, express the limitation as an uncertainty rather than inventing a conclusion.\n"
            "5. If sources disagree, represent the disagreement as a conflict rather than arbitrarily choosing one source.\n"
            "6. Do not treat confidence as probability. Use only high, medium, or low.\n"
            "7. Uncertainties describe missing evidence or unknowns and do not require evidence references.\n"
            "8. The recommendation may be null if the gathered evidence is insufficient to justify a definitive architectural choice.\n"
            "9. You must return ONLY a valid JSON object matching the requested schema without any markdown formatting or commentary."
        )

        user_prompt = f"""Synthesize an evidence-backed DecisionReport based on the following technical context and verified evidence.

Original Developer Request:
\"\"\"
{context.user_request}
\"\"\"

Requirements Analysis:
- Goal: {context.requirements.goal}
- Technologies: {json.dumps(context.requirements.technologies)}
- Functional & Non-functional Requirements: {json.dumps(context.requirements.requirements)}
- Constraints: {json.dumps(context.requirements.constraints)}
- Unknowns: {json.dumps(context.requirements.unknowns)}

Valid Evidence IDs Available to Cite:
{json.dumps(available_ev_ids)}

{formatted_context}

Output Schema Definition:
{{
  "summary": "Executive summary of the technical decision analysis",
  "findings": [
    {{
      "question": "Research question being answered",
      "finding": "Substantive conclusion based on evidence",
      "reasoning": "Technical rationale connecting evidence to conclusion",
      "evidence_references": ["EV-001", "EV-002"],
      "confidence": "high" | "medium" | "low"
    }}
  ],
  "comparisons": [
    {{
      "criterion": "Comparison criterion (e.g. Throughput, Cost, Operational Overhead)",
      "assessments": [
        {{
          "option": "Candidate technology (e.g. Kafka, Kinesis)",
          "assessment": "Assessment under this criterion",
          "evidence_references": ["EV-001"]
        }}
      ]
    }}
  ],
  "recommendation": {{
    "option": "Recommended technology or architecture (or null if evidence is insufficient)",
    "reason": "Conditional, context-aware rationale explaining when and why this option is best",
    "evidence_references": ["EV-001"],
    "confidence": "high" | "medium" | "low"
  }} | null,
  "alternatives": [
    {{
      "option": "Viable alternative technology",
      "reason": "Conditions or trade-offs under which this alternative is preferred",
      "evidence_references": ["EV-002"]
    }}
  ],
  "tradeoffs": [
    {{
      "decision": "The engineering choice made",
      "gain": "What is gained (throughput, simplicity, guarantees)",
      "cost": "What is sacrificed (complexity, operational burden, monetary cost)",
      "evidence_references": ["EV-001", "EV-002"]
    }}
  ],
  "risks": [
    {{
      "risk": "Technical or operational risk",
      "impact": "Potential consequence or failure mode",
      "evidence_references": ["EV-002"]
    }}
  ],
  "conflicts": [
    {{
      "topic": "Topic where sources diverge",
      "evidence_references": ["EV-001", "EV-002"],
      "assessment": "Analysis explaining why sources disagree (differing benchmark methodology, setup, etc.)"
    }}
  ],
  "uncertainties": [
    {{
      "topic": "Unresolved technical unknown or missing evidence",
      "reason": "Why this cannot be determined with current evidence",
      "impact": "Impact of this uncertainty on the overall engineering decision"
    }}
  ],
  "overall_confidence": "high" | "medium" | "low"
}}

IMPORTANT:
- Every cited EV ID MUST be in the Valid Evidence IDs list {json.dumps(available_ev_ids)}. Never hallucinate an EV ID.
- If evidence is insufficient, record an uncertainty and set confidence to "low" or "medium".
- Return ONLY the JSON object.
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

    def _parse_and_validate(self, raw_content: str | None, context: EvidenceContext) -> DecisionReport:
        """
        Parse raw content and validate against the DecisionReport schema,
        then deterministically verify all cited evidence references against the EvidenceContext.
        """
        if not raw_content or not raw_content.strip():
            raise ReasoningValidationError("Model returned an empty response.", raw_response=raw_content)

        cleaned = self._clean_json_text(raw_content)

        report: DecisionReport | None = None

        # Attempt 1: Direct Pydantic validation
        try:
            report = DecisionReport.model_validate_json(cleaned)
        except Exception:
            pass

        # Attempt 2: Extract outermost JSON object if model included surrounding commentary
        if report is None:
            match = re.search(r"\{.*\}", cleaned, re.DOTALL)
            if match:
                try:
                    report = DecisionReport.model_validate_json(match.group(0))
                except Exception as e:
                    raise ReasoningValidationError(
                        f"Model output matched JSON syntax but failed schema validation: {e}",
                        raw_response=raw_content,
                    ) from e

        if report is None:
            raise ReasoningValidationError(
                "Could not parse valid JSON from the model response.",
                raw_response=raw_content,
            )

        # Deterministic evidence reference validation against EvidenceContext
        try:
            report.validate_evidence_references(context)
        except (DecisionReportValidationError, EvidenceReferenceError) as e:
            raise ReasoningValidationError(
                f"Evidence reference validation failed: {e}",
                raw_response=raw_content,
            ) from e

        return report

    def reason(self, context: EvidenceContext) -> DecisionReport:
        """
        Generate a validated DecisionReport from the provided EvidenceContext.
        """
        if not isinstance(context, EvidenceContext):
            raise TypeError(
                f"Expected EvidenceContext instance, got {type(context).__name__}."
            )

        messages = self._build_messages(context)

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

        return self._parse_and_validate(content, context)


def synthesize_decision_report(context: EvidenceContext, **kwargs: Any) -> DecisionReport:
    """
    Convenience function that initializes ReasoningEngine and generates a validated DecisionReport.
    """
    engine = ReasoningEngine(**kwargs)
    return engine.reason(context)
