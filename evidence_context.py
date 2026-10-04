"""
Evidence Context Layer for DEVSCOUT.
Packages validated research state into a deterministic contract (EvidenceContext)
with human-readable, reasoning-facing reference IDs ('EV-001', 'EV-002', ...)
for consumption by the future Reasoning Engine.
"""

import re
from typing import Any, Sequence

from models import (
    Evidence,
    EvidenceContext,
    EvidenceGroup,
    EvidenceReferenceError,
    RequirementAnalysis,
    ResearchPlan,
    ResearchTask,
)
from evidence_layer import group_evidence


class EvidenceContextError(Exception):
    """Base exception for all EvidenceContext errors."""
    pass


class EvidenceContextValidationError(EvidenceContextError):
    """Raised when context validation fails."""
    pass


def build_evidence_context(
    user_request: str,
    requirements: RequirementAnalysis,
    plan: ResearchPlan,
    tasks: Sequence[ResearchTask],
    evidence_groups: Sequence[EvidenceGroup] | None = None,
    evidence: Sequence[Evidence] | None = None,
) -> EvidenceContext:
    """
    Build and validate a canonical EvidenceContext packaging the original user request,
    requirements, research plan, atomic tasks, and evidence grouped by research question.

    Assigns deterministic, human-readable reasoning reference IDs ('EV-001', 'EV-002', ...)
    to each unique evidence item while preserving underlying provenance and identifiers.
    """
    if not isinstance(user_request, str) or not user_request.strip():
        raise EvidenceContextValidationError("user_request must be a non-empty string.")

    if not isinstance(requirements, RequirementAnalysis):
        raise EvidenceContextValidationError(
            f"Expected RequirementAnalysis instance, got {type(requirements).__name__}."
        )

    if not isinstance(plan, ResearchPlan):
        raise EvidenceContextValidationError(
            f"Expected ResearchPlan instance, got {type(plan).__name__}."
        )

    if not tasks:
        raise EvidenceContextValidationError("tasks sequence cannot be empty.")

    task_list: list[ResearchTask] = []
    for idx, t in enumerate(tasks):
        if not isinstance(t, ResearchTask):
            raise EvidenceContextValidationError(
                f"Task at index {idx} is not a ResearchTask instance (got {type(t).__name__})."
            )
        task_list.append(t)

    # Resolve groups
    groups: list[EvidenceGroup] = []
    if evidence_groups is not None:
        for idx, g in enumerate(evidence_groups):
            if not isinstance(g, EvidenceGroup):
                raise EvidenceContextValidationError(
                    f"Evidence group at index {idx} is not an EvidenceGroup instance."
                )
            groups.append(g)
    elif evidence is not None:
        groups = group_evidence(evidence)
    else:
        groups = []

    # Deterministically assign sequential reasoning references: EV-001, EV-002, ...
    seen_identifiers: dict[str, str] = {}  # identifier -> ev_id
    evidence_map: dict[str, Evidence] = {}

    for group in groups:
        for item in group.items:
            if not isinstance(item, Evidence):
                raise EvidenceContextValidationError(
                    f"Evidence group '{group.task_question}' contains non-Evidence item: {type(item).__name__}."
                )

            ident = item.identifier.strip().lower()
            if ident in seen_identifiers:
                # Reuse reference ID for identical evidence across questions
                item.ev_id = seen_identifiers[ident]
            else:
                next_num = len(seen_identifiers) + 1
                ev_id = f"EV-{next_num:03d}"
                item.ev_id = ev_id
                seen_identifiers[ident] = ev_id
                evidence_map[ev_id] = item

    return EvidenceContext(
        user_request=user_request.strip(),
        requirements=requirements,
        plan=plan,
        tasks=task_list,
        evidence_groups=groups,
        evidence_map=evidence_map,
    )


def resolve_evidence_references(
    context: EvidenceContext,
    ev_ids: Sequence[str],
) -> list[Evidence]:
    """
    Resolve reasoning-facing references (e.g. ['EV-001', 'EV-003']) back to
    their underlying Evidence items.
    """
    if not isinstance(context, EvidenceContext):
        raise EvidenceContextValidationError(
            f"Expected EvidenceContext instance, got {type(context).__name__}."
        )
    return context.resolve_references(ev_ids)


def format_evidence_context_for_prompt(context: EvidenceContext) -> str:
    """
    Format an EvidenceContext into structured markdown context ready for the future
    Reasoning Engine prompt.
    """
    if not isinstance(context, EvidenceContext):
        raise EvidenceContextValidationError(
            f"Expected EvidenceContext instance, got {type(context).__name__}."
        )
    return context.format_for_reasoning()


__all__ = [
    "EvidenceContext",
    "EvidenceReferenceError",
    "EvidenceContextError",
    "EvidenceContextValidationError",
    "build_evidence_context",
    "resolve_evidence_references",
    "format_evidence_context_for_prompt",
]
