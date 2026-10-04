"""
Gemini Reasoning Engine component for DEVSCOUT.
Synthesizes grounded technical decision reports from validated EvidenceContext using Google Gemini,
enforcing strict evidence citation and deterministic reference validation.
"""

import os
import json
import re
from typing import Any

from dotenv import load_dotenv
from google import genai
from google.genai import types, errors

from models import (
    Confidence,
    DecisionReport,
    DecisionReportError,
    DecisionReportValidationError,
    EvidenceContext,
    EvidenceReferenceError,
)
from reasoning_engine import (
    ReasoningEngineError,
    APIConnectionError,
    ReasoningValidationError,
)


load_dotenv()


class GeminiReasoningEngineError(ReasoningEngineError):
    """Base exception for Gemini Reasoning Engine errors."""
    pass


class GeminiAPIConnectionError(GeminiReasoningEngineError, APIConnectionError):
    """Raised when communication with Gemini API fails or credentials are invalid."""
    pass


class GeminiReasoningValidationError(GeminiReasoningEngineError, ReasoningValidationError):
    """Raised when the Gemini model output fails schema or evidence reference validation."""
    def __init__(self, message: str, raw_response: str | None = None):
        super().__init__(message, raw_response=raw_response)
        self.raw_response = raw_response


class GeminiReasoningEngine:
    """
    Synthesizes grounded, evidence-backed technical decision reports from an EvidenceContext
    using Google Gemini models with structured JSON schema outputs.
    Enforces strict citation rules and deterministic reference validation against the context.
    """

    DEFAULT_MODEL = "gemini-2.5-flash"

    def __init__(
        self,
        api_key: str | None = None,
        model: str | None = None,
        client: genai.Client | None = None,
    ):
        self.api_key = api_key or os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
        if not self.api_key and client is None:
            raise GeminiAPIConnectionError(
                "GEMINI_API_KEY is not set. Please add it to your .env file or pass it to GeminiReasoningEngine."
            )

        self.model = model or os.getenv("GEMINI_MODEL", self.DEFAULT_MODEL)
        self.client = client or genai.Client(api_key=self.api_key)

    def _build_prompts(self, context: EvidenceContext) -> tuple[str, str]:
        """
        Build system instruction and user prompt containing the research context,
        available EV references, and strict evidence grounding rules.
        """
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
        return system_prompt, user_prompt

    def _clean_json_text(self, text: str) -> str:
        """Strip markdown code block fences and surrounding whitespace."""
        cleaned = text.strip()
        if cleaned.startswith("```"):
            cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned, flags=re.IGNORECASE)
            cleaned = re.sub(r"\s*```$", "", cleaned)
            cleaned = cleaned.strip()
        return cleaned

    def _normalize_response_data(self, data: dict[str, Any]) -> dict[str, Any]:
        """
        Normalize raw parsed JSON response from Gemini before Pydantic schema validation.
        If overall_confidence is missing:
          - If recommendation.confidence exists, copy that value into overall_confidence.
          - Otherwise derive it deterministically from available finding/recommendation confidence values.
          - If there is no usable confidence value, default to "low" because the report
            has no evidence-backed confidence signal.
        """
        raw_overall = data.get("overall_confidence")
        is_missing = (
            "overall_confidence" not in data
            or raw_overall is None
            or (isinstance(raw_overall, str) and not raw_overall.strip())
        )

        if is_missing:
            # 1. If recommendation.confidence exists, copy that value into overall_confidence
            rec = data.get("recommendation")
            copied = False
            if isinstance(rec, dict) and "confidence" in rec and rec["confidence"] is not None:
                rec_conf = rec["confidence"]
                if isinstance(rec_conf, str) and rec_conf.strip():
                    data["overall_confidence"] = rec_conf.strip()
                    copied = True
                elif rec_conf:
                    data["overall_confidence"] = rec_conf
                    copied = True

            # 2. Otherwise derive it deterministically from available finding/recommendation confidence values
            if not copied:
                usable_confidences: list[str] = []

                if isinstance(rec, dict):
                    rc = rec.get("confidence")
                    if isinstance(rc, str) and rc.strip().lower() in ("high", "medium", "low"):
                        usable_confidences.append(rc.strip().lower())

                findings = data.get("findings")
                if isinstance(findings, list):
                    for f in findings:
                        if isinstance(f, dict):
                            fc = f.get("confidence")
                            if isinstance(fc, str) and fc.strip().lower() in ("high", "medium", "low"):
                                usable_confidences.append(fc.strip().lower())

                if usable_confidences:
                    weights = {"low": 1, "medium": 2, "high": 3}
                    rev = {1: "low", 2: "medium", 3: "high"}
                    avg_score = round(sum(weights[c] for c in usable_confidences) / len(usable_confidences))
                    data["overall_confidence"] = rev[avg_score]
                else:
                    data["overall_confidence"] = "low"

        return data

    def _parse_and_validate(self, raw_content: str | None, context: EvidenceContext) -> DecisionReport:
        """
        Parse raw content and validate against the DecisionReport schema,
        then deterministically verify all cited evidence references against the EvidenceContext.
        """
        if not raw_content or not raw_content.strip():
            raise GeminiReasoningValidationError("Model returned an empty response.", raw_response=raw_content)

        cleaned = self._clean_json_text(raw_content)

        # 1. Parse the JSON object first
        data: Any = None
        try:
            data = json.loads(cleaned)
        except Exception:
            match = re.search(r"\{.*\}", cleaned, re.DOTALL)
            if match:
                try:
                    data = json.loads(match.group(0))
                except Exception:
                    pass

        if not isinstance(data, dict):
            raise GeminiReasoningValidationError(
                "Could not parse valid JSON from the model response.",
                raw_response=raw_content,
            )

        # 2. Normalize JSON response before Pydantic validation
        data = self._normalize_response_data(data)

        # 3. Pass the normalized object through DecisionReport.model_validate(...)
        try:
            report = DecisionReport.model_validate(data)
        except Exception as e:
            raise GeminiReasoningValidationError(
                f"Model output matched JSON syntax but failed schema validation: {e}",
                raw_response=raw_content,
            ) from e

        # 4. Deterministic evidence reference validation against EvidenceContext
        try:
            report.validate_evidence_references(context)
        except (DecisionReportValidationError, EvidenceReferenceError) as e:
            raise GeminiReasoningValidationError(
                f"Evidence reference validation failed: {e}",
                raw_response=raw_content,
            ) from e

        return report

    def reason(self, context: EvidenceContext) -> DecisionReport:
        """
        Generate a validated DecisionReport from the provided EvidenceContext using Gemini.
        """
        if not isinstance(context, EvidenceContext):
            raise TypeError(
                f"Expected EvidenceContext instance, got {type(context).__name__}."
            )

        system_prompt, user_prompt = self._build_prompts(context)

        config = types.GenerateContentConfig(
            system_instruction=system_prompt,
            response_mime_type="application/json",
            response_schema=DecisionReport,
        )

        try:
            response = self.client.models.generate_content(
                model=self.model,
                contents=user_prompt,
                config=config,
            )
        except errors.APIError as e:
            raise GeminiAPIConnectionError(f"Gemini API error occurred: {e}") from e
        except Exception as e:
            raise GeminiAPIConnectionError(f"Unexpected connection error while calling Gemini: {e}") from e

        content = getattr(response, "text", None)
        return self._parse_and_validate(content, context)


def synthesize_gemini_decision_report(context: EvidenceContext, **kwargs: Any) -> DecisionReport:
    """
    Convenience function that initializes GeminiReasoningEngine and generates a validated DecisionReport.
    """
    engine = GeminiReasoningEngine(**kwargs)
    return engine.reason(context)
