"""
Research Task Generator for DEVSCOUT.
Converts a validated ResearchPlan into atomic, executable ResearchTask objects.
"""

import re
from typing import Any
from models import ResearchPlan, ResearchTask, SourceType, PriorityLevel


def _derive_target(question: str, technologies: list[str]) -> str:
    """
    Deterministically derive the target technology, architecture, or concept
    being investigated from the question and known technologies.
    """
    q_clean = question.strip()

    # 1. Look for explicit comparison patterns in parentheses like "(CRDTs vs. Operational Transformation)"
    parentheses_match = re.search(r"\(([^)]+?\bvs\.?\b[^)]+?)\)", q_clean, re.IGNORECASE)
    if parentheses_match:
        cleaned = parentheses_match.group(1).replace(".", "").strip()
        if len(cleaned) <= 60:
            return cleaned

    # 2. Look for "Between X and Y"
    between_match = re.search(
        r"between\s+([A-Za-z0-9_\-\s]+?)\s+and\s+([A-Za-z0-9_\-\s]+?)(?:\s*[,–—\?]|(?:\s+(?:which|that|for|supports)))",
        q_clean,
        re.IGNORECASE,
    )
    if between_match:
        first = between_match.group(1).strip()
        second = between_match.group(2).strip()
        if len(first) <= 30 and len(second) <= 30:
            return f"{first} vs {second}"

    # 3. Match known technologies from the plan that appear in the question
    matched_techs: list[str] = []
    for tech in technologies:
        # Match as whole word / token
        pattern = r"\b" + re.escape(tech) + r"\b"
        if re.search(pattern, q_clean, re.IGNORECASE):
            # Avoid duplicate sub-matches if already matched
            if not any(tech.lower() in existing.lower() for existing in matched_techs):
                matched_techs.append(tech)

    if len(matched_techs) >= 2:
        if re.search(r"\bvs\.?\b", q_clean, re.IGNORECASE) or " or " in q_clean.lower():
            return " vs ".join(matched_techs[:2])
        return ", ".join(matched_techs[:3])
    elif len(matched_techs) == 1:
        single_tech = matched_techs[0]
        # Look for compound phrases like "Go WebSocket libraries" or "React frontend"
        compound_pattern = (
            r"\b([A-Za-z0-9_\-]*\s*"
            + re.escape(single_tech)
            + r"\s*[A-Za-z0-9_\-]*\s*(?:libraries|frameworks|tools|stack|architecture|database|platform|protocol|engine|frontend|backend)?)\b"
        )
        compound_match = re.search(compound_pattern, q_clean, re.IGNORECASE)
        if compound_match and len(compound_match.group(1).strip()) > len(single_tech):
            candidate = compound_match.group(1).strip()
            candidate = re.sub(
                r"^(?:which|what|how|are|the|for|is|can|between)\s+",
                "",
                candidate,
                flags=re.IGNORECASE,
            ).strip()
            if candidate and len(candidate) <= 50:
                return candidate
        return single_tech

    # 4. Look for common question patterns: "Which [subject]...", "What [subject]...", "How [subject]..."
    subject_match = re.search(
        r"^(?:which|what|how\s+to|how\s+can|best\s+practices\s+for)\s+(?:are\s+the\s+|is\s+the\s+|the\s+)?([A-Za-z0-9_\-\s/]+?)(?:\s+(?:delivers|provides|offers|best|supports|should|is|are|can|will|to|for|in\s+a)\b|[\?,:–—])",
        q_clean,
        re.IGNORECASE,
    )
    if subject_match:
        candidate = subject_match.group(1).strip()
        candidate = re.sub(
            r"^(?:acceptable|best|typical|suitable|average|optimal)\s+",
            "",
            candidate,
            flags=re.IGNORECASE,
        ).strip()
        if len(candidate) >= 3 and len(candidate.split()) <= 6:
            return candidate

    # 5. Fallback: If technologies are available in the plan, use the first one
    if technologies:
        return technologies[0]

    # 6. Generic fallback
    return "Architecture & Implementation"


def _derive_purpose(question_rationale: str, question: str) -> str:
    """
    Derive the purpose of this research task from the question rationale.
    """
    if question_rationale and question_rationale.strip():
        return question_rationale.strip()
    return f"Investigate to address: {question.strip()}"


class TaskGenerator:
    """
    Converts a validated ResearchPlan into a list of atomic ResearchTask objects.
    """

    def generate_tasks(self, plan: ResearchPlan | dict[str, Any]) -> list[ResearchTask]:
        """
        Produce a list of atomic ResearchTasks from a ResearchPlan.
        Each research question fans out into one atomic task per source type.
        """
        if plan is None:
            raise ValueError("ResearchPlan cannot be None.")

        if isinstance(plan, dict):
            try:
                validated_plan = ResearchPlan.model_validate(plan)
            except Exception as e:
                raise ValueError(f"Invalid ResearchPlan dictionary: {e}") from e
        elif isinstance(plan, ResearchPlan):
            validated_plan = plan
        else:
            raise TypeError(
                f"Expected ResearchPlan or dict, got {type(plan).__name__}"
            )

        tasks: list[ResearchTask] = []
        technologies = validated_plan.technologies_to_investigate

        for q in validated_plan.research_questions:
            target = _derive_target(q.question, technologies)
            purpose = _derive_purpose(q.rationale, q.question)

            # Fan out by source type to ensure tasks are atomic for specific connectors
            for source in q.source_types:
                task = ResearchTask(
                    question=q.question,
                    source_type=source,
                    priority=q.priority,
                    target=target,
                    purpose=purpose,
                )
                tasks.append(task)

        return tasks


def generate_research_tasks(plan: ResearchPlan | dict[str, Any]) -> list[ResearchTask]:
    """
    Convenience function that converts a ResearchPlan into a list of ResearchTasks.
    """
    generator = TaskGenerator()
    return generator.generate_tasks(plan)
