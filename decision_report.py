"""
DecisionReport Contract Layer for DEVSCOUT.
Defines reasoning-facing models and deterministic validation for decision reports
produced by the future Reasoning Engine.
"""

from models import (
    Alternative,
    Comparison,
    ComparisonAssessment,
    Confidence,
    DecisionReport,
    DecisionReportError,
    DecisionReportValidationError,
    EvidenceConflict,
    Finding,
    Recommendation,
    Risk,
    Tradeoff,
    Uncertainty,
    validate_decision_report_evidence,
)
from reasoning_engine import (
    APIConnectionError,
    ReasoningEngine,
    ReasoningEngineError,
    ReasoningValidationError,
    synthesize_decision_report,
)

__all__ = [
    "Confidence",
    "Finding",
    "ComparisonAssessment",
    "Comparison",
    "Recommendation",
    "Alternative",
    "Tradeoff",
    "Risk",
    "EvidenceConflict",
    "Uncertainty",
    "DecisionReport",
    "DecisionReportError",
    "DecisionReportValidationError",
    "validate_decision_report_evidence",
    "ReasoningEngine",
    "ReasoningEngineError",
    "ReasoningValidationError",
    "APIConnectionError",
    "synthesize_decision_report",
]
