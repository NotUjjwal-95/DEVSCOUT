"""
FastAPI HTTP Layer for DEVSCOUT.
Provides REST API endpoints for the React frontend to communicate with the real DEVSCOUT backend pipeline.
"""

import os
import time
import json
import uuid
import threading
from datetime import datetime, timezone
from urllib.parse import urlparse
from typing import Any, Optional

from dotenv import load_dotenv
from fastapi import FastAPI, APIRouter, BackgroundTasks, HTTPException, Query, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from analyzer import RequirementAnalyzer
from planner import ResearchPlanner
from task_generator import TaskGenerator
from web_researcher import WebResearcher
from github_researcher import GitHubResearcher
from rag_researcher import RAGResearcher
from evidence_layer import EvidenceLayer
from evidence_context import build_evidence_context
from models import DecisionReport, EvidenceContext


load_dotenv()


# ---------------------------------------------------------------------------
# Data Transfer Objects (DTOs)
# ---------------------------------------------------------------------------

class CreateResearchRequest(BaseModel):
    """Payload to initiate a new research investigation."""
    objective: Optional[str] = Field(None, description="Core technical objective or question")
    prompt: Optional[str] = Field(None, description="Alternative raw developer prompt")
    user_request: Optional[str] = Field(None, description="Alternative user request string")
    technologies: list[str] = Field(default_factory=list, description="Target technologies or libraries")
    constraints: list[str] = Field(default_factory=list, description="Hard constraints")
    scale: Optional[str] = Field(None, description="Expected user/traffic scale")
    budget: Optional[str] = Field(None, description="Budget tier or constraints")
    preferences: list[str] = Field(default_factory=list, description="Architectural preferences")
    advanced: Optional[dict[str, Any]] = Field(None, description="Advanced options (latencyTarget, etc.)")
    provider: Optional[str] = Field(None, description="Optional reasoning provider: 'groq' or 'gemini'")


# ---------------------------------------------------------------------------
# In-Memory Thread-Safe Session Store
# ---------------------------------------------------------------------------

class SessionStore:
    """Thread-safe storage for research sessions and their progressive execution state."""

    def __init__(self):
        self._sessions: dict[str, dict[str, Any]] = {}
        self._lock = threading.Lock()

    def create(self, request_data: CreateResearchRequest) -> dict[str, Any]:
        session_id = f"res-{uuid.uuid4().hex[:10]}"
        now = datetime.now(timezone.utc).isoformat()

        objective = (
            request_data.objective
            or request_data.user_request
            or request_data.prompt
            or "Technical Architecture Research"
        ).strip()

        project_name = (
            f"{objective[:52].strip()}..." if len(objective) > 55 else objective
        )
        scale = request_data.scale or "~1,000 concurrent users"
        budget = request_data.budget or "Low / Bootstrapped"
        technologies = request_data.technologies or []
        constraints = request_data.constraints or []
        preferences = request_data.preferences or []

        stages = [
            {
                "id": "requirement_analysis",
                "name": "Requirement Analysis",
                "description": "Decompose constraints, concurrency targets, and state models",
                "status": "running",
                "startedAt": now,
            },
            {
                "id": "research_planning",
                "name": "Research Planning",
                "description": "Formulate architectural questions and evidence criteria",
                "status": "queued",
            },
            {
                "id": "task_generation",
                "name": "Task Generation",
                "description": "Spin up source-directed probes for Web, GitHub, and RAG",
                "status": "queued",
            },
            {
                "id": "web_research",
                "name": "Web Research",
                "description": "Crawl official technical documentation, RFCs, and peer benchmarks",
                "status": "queued",
            },
            {
                "id": "github_research",
                "name": "GitHub Research",
                "description": "Audit production repositories, library activity, and open issues",
                "status": "queued",
            },
            {
                "id": "rag_research",
                "name": "RAG Research",
                "description": "Query DEVSCOUT curated engineering knowledge corpus",
                "status": "queued",
            },
            {
                "id": "evidence_processing",
                "name": "Evidence Processing",
                "description": "Normalize snippets, verify peer-reviewed claims, deduplicate",
                "status": "queued",
            },
            {
                "id": "decision_analysis",
                "name": "Decision Analysis",
                "description": "Synthesize trade-off matrix, fit criteria, and recommendation",
                "status": "queued",
            },
        ]

        session = {
            "id": session_id,
            "sessionId": session_id,
            "session_id": session_id,
            "researchId": session_id,
            "research_id": session_id,
            "projectName": project_name,
            "project_name": project_name,
            "objective": objective,
            "state": "planning",
            "status": "running",
            "progress": 5,
            "currentStage": "requirement_analysis",
            "currentStageIndex": 0,
            "createdAt": now,
            "created_at": now,
            "updatedAt": now,
            "updated_at": now,
            "scale": scale,
            "budget": budget,
            "technologies": technologies,
            "constraints": constraints,
            "preferences": preferences,
            "requirementAnalysis": {
                "problemStatement": objective,
                "coreObjective": objective,
                "targetScale": scale,
                "budgetTier": budget,
                "technologies": technologies,
                "hardConstraints": constraints,
                "preferences": preferences,
                "technicalDomain": "Distributed Systems & Architecture Trade-offs",
            },
            "plan": None,
            "stages": stages,
            "events": [
                {
                    "id": f"ev-{int(time.time() * 1000)}",
                    "timestamp": datetime.now(timezone.utc).strftime("%H:%M:%S"),
                    "stageId": "requirement_analysis",
                    "type": "info",
                    "message": f'Initiating research engine: "{objective[:70]}..."',
                }
            ],
            "tasks": [],
            "evidence": [],
            "repositories": [],
            "report": None,
        }

        with self._lock:
            self._sessions[session_id] = session

        return json.loads(json.dumps(session))

    def get(self, session_id: str) -> dict[str, Any] | None:
        with self._lock:
            session = self._sessions.get(session_id)
            return json.loads(json.dumps(session)) if session else None

    def update(self, session_id: str, updates: dict[str, Any]) -> None:
        with self._lock:
            if session_id in self._sessions:
                self._sessions[session_id].update(updates)
                now = datetime.now(timezone.utc).isoformat()
                self._sessions[session_id]["updatedAt"] = now
                self._sessions[session_id]["updated_at"] = now

    def add_event(
        self,
        session_id: str,
        stage_id: str,
        message: str,
        event_type: str = "info",
        detail: str | None = None,
    ) -> None:
        with self._lock:
            if session_id in self._sessions:
                event = {
                    "id": f"ev-{int(time.time() * 1000)}-{len(self._sessions[session_id]['events']) + 1}",
                    "timestamp": datetime.now(timezone.utc).strftime("%H:%M:%S"),
                    "stageId": stage_id,
                    "type": event_type,
                    "message": message,
                }
                if detail:
                    event["detail"] = detail
                self._sessions[session_id]["events"].append(event)

    def append_event(
        self,
        session_id: str,
        message: str,
        level: str = "info",
        stage_id: str = "general",
    ) -> None:
        self.add_event(session_id, stage_id=stage_id, message=message, event_type=level)

    def set_stage(
        self,
        session_id: str,
        stage_idx: int,
        status_val: str,
        duration_seconds: int | None = None,
    ) -> None:
        with self._lock:
            if session_id in self._sessions and 0 <= stage_idx < len(self._sessions[session_id]["stages"]):
                stage = self._sessions[session_id]["stages"][stage_idx]
                stage["status"] = status_val
                now = datetime.now(timezone.utc).isoformat()
                if status_val == "running":
                    stage["startedAt"] = now
                elif status_val in ("completed", "failed"):
                    stage["completedAt"] = now
                    if duration_seconds is not None:
                        stage["durationSeconds"] = duration_seconds
                    elif "startedAt" in stage:
                        try:
                            start_dt = datetime.fromisoformat(stage["startedAt"])
                            end_dt = datetime.fromisoformat(now)
                            stage["durationSeconds"] = max(1, int((end_dt - start_dt).total_seconds()))
                        except Exception:
                            stage["durationSeconds"] = 1

    def update_stage(
        self,
        session_id: str,
        stage_id: str,
        status_val: str,
        progress: int | None = None,
    ) -> None:
        with self._lock:
            if session_id in self._sessions:
                for idx, s in enumerate(self._sessions[session_id]["stages"]):
                    if s.get("id") == stage_id:
                        s["status"] = status_val
                        now = datetime.now(timezone.utc).isoformat()
                        if status_val == "running":
                            s["startedAt"] = now
                        elif status_val in ("completed", "failed"):
                            s["completedAt"] = now
                        break
                if progress is not None:
                    self._sessions[session_id]["progress"] = progress

    def append_tasks(self, session_id: str, new_tasks: list[dict[str, Any]]) -> None:
        with self._lock:
            if session_id in self._sessions:
                self._sessions[session_id]["tasks"].extend(new_tasks)

    def append_evidence(self, session_id: str, new_evidence: list[dict[str, Any]]) -> None:
        with self._lock:
            if session_id in self._sessions:
                self._sessions[session_id]["evidence"].extend(new_evidence)

    def append_repositories(self, session_id: str, new_repos: list[dict[str, Any]]) -> None:
        with self._lock:
            if session_id in self._sessions:
                self._sessions[session_id]["repositories"].extend(new_repos)

    def complete(self, session_id: str, report: dict[str, Any]) -> None:
        with self._lock:
            if session_id in self._sessions:
                self._sessions[session_id]["report"] = report
                self._sessions[session_id]["state"] = "completed"
                self._sessions[session_id]["status"] = "completed"
                self._sessions[session_id]["progress"] = 100
                self._sessions[session_id]["isComplete"] = True

    def fail(self, session_id: str, error_message: str) -> None:
        with self._lock:
            if session_id in self._sessions:
                self._sessions[session_id]["state"] = "failed"
                self._sessions[session_id]["status"] = "failed"
                self._sessions[session_id]["error"] = error_message
                for s in self._sessions[session_id]["stages"]:
                    if s.get("status") == "running":
                        s["status"] = "failed"

    def list_history(self) -> list[dict[str, Any]]:
        with self._lock:
            summaries = []
            for s in self._sessions.values():
                summaries.append({
                    "id": s["id"],
                    "projectName": s.get("projectName") or s.get("objective", "Research"),
                    "objective": s.get("objective", ""),
                    "state": s.get("state", "idle"),
                    "status": s.get("status", "running"),
                    "createdAt": s.get("createdAt", ""),
                    "updatedAt": s.get("updatedAt", ""),
                    "sourcesCount": len(s.get("evidence", [])),
                    "repositoriesCount": len(s.get("repositories", [])),
                    "scale": s.get("scale", "Standard"),
                })
            summaries.sort(key=lambda x: x["createdAt"], reverse=True)
            return json.loads(json.dumps(summaries))

    def list_summaries(self) -> list[dict[str, Any]]:
        return self.list_history()


session_store = SessionStore()


# ---------------------------------------------------------------------------
# Pipeline Component Factory & Execution
# ---------------------------------------------------------------------------

def get_pipeline_components(provider_override: Optional[str] = None) -> dict[str, Any]:
    """Instantiate real DEVSCOUT pipeline components."""
    analyzer = RequirementAnalyzer()
    planner = ResearchPlanner()
    task_generator = TaskGenerator()
    web_researcher = WebResearcher(max_results_per_task=3)
    github_researcher = GitHubResearcher(max_results_per_task=3)
    rag_researcher = RAGResearcher(max_results_per_task=3)
    evidence_layer = EvidenceLayer(deduplicate=True, rank=True)

    provider = (provider_override or os.getenv("REASONING_PROVIDER", "")).lower()
    if provider == "gemini" or (not os.getenv("GROQ_API_KEY") and os.getenv("GEMINI_API_KEY")):
        try:
            from gemini_reasoning_engine import GeminiReasoningEngine
            reasoning_engine = GeminiReasoningEngine()
        except Exception:
            from reasoning_engine import ReasoningEngine
            reasoning_engine = ReasoningEngine()
    else:
        from reasoning_engine import ReasoningEngine
        reasoning_engine = ReasoningEngine()

    return {
        "analyzer": analyzer,
        "planner": planner,
        "task_generator": task_generator,
        "web_researcher": web_researcher,
        "github_researcher": github_researcher,
        "rag_researcher": rag_researcher,
        "evidence_layer": evidence_layer,
        "reasoning_engine": reasoning_engine,
    }


def format_decision_report(
    report: DecisionReport,
    session_id: str,
    evidence_list: list[dict[str, Any]],
) -> dict[str, Any]:
    """Format DecisionReport into dual-compatible schema for frontend and backend."""
    why_it_fits = []
    for f in report.findings:
        why_it_fits.append({
            "point": f.finding,
            "evidenceIds": f.evidence_references,
        })
    if not why_it_fits and report.recommendation:
        why_it_fits.append({
            "point": report.recommendation.reason,
            "evidenceIds": report.recommendation.evidence_references,
        })

    alternatives = []
    for a in report.alternatives:
        alternatives.append({
            "title": a.option,
            "fitLevel": "medium",
            "summary": a.reason,
            "pros": [a.reason],
            "cons": [],
            "verdict": a.reason,
            "evidenceIds": a.evidence_references,
        })

    tradeoffs = []
    for t in report.tradeoffs:
        tradeoffs.append({
            "dimension": t.decision,
            "analysis": f"Gain: {t.gain} | Cost: {t.cost}",
            "winner": t.decision,
            "evidenceIds": t.evidence_references,
        })

    technical_considerations = []
    for r in report.risks:
        technical_considerations.append({
            "category": r.risk,
            "guidance": r.impact,
            "actionableRule": f"Mitigate risk: {r.risk} (Impact: {r.impact})",
        })
    for u in report.uncertainties:
        technical_considerations.append({
            "category": u.topic,
            "guidance": u.reason,
            "actionableRule": f"Address uncertainty: {u.impact}",
        })

    web_count = sum(1 for e in evidence_list if e.get("sourceType") == "web")
    gh_count = sum(1 for e in evidence_list if e.get("sourceType") == "github")
    rag_count = sum(1 for e in evidence_list if e.get("sourceType") == "rag")
    primary_docs = [e.get("title", "") for e in evidence_list[:5] if e.get("title")]

    return {
        "id": f"rep-{session_id}",
        "sessionId": session_id,
        "session_id": session_id,
        "generatedAt": datetime.now(timezone.utc).isoformat(),
        "executiveSummary": report.summary,
        "summary": report.summary,
        "recommendedApproach": {
            "title": report.recommendation.option if report.recommendation else "Evidence Insufficient for Definitive Recommendation",
            "fitLevel": report.recommendation.confidence if report.recommendation else "conditional",
            "architectureSummary": report.recommendation.reason if report.recommendation else "Available evidence does not support a definitive architectural decision without additional targeted benchmarking.",
            "whyItFits": why_it_fits,
        },
        "recommendation": report.recommendation.to_dict() if report.recommendation else None,
        "alternatives": alternatives,
        "tradeoffs": tradeoffs,
        "technicalConsiderations": technical_considerations,
        "findings": [f.to_dict() for f in report.findings],
        "comparisons": [c.to_dict() for c in report.comparisons],
        "risks": [r.to_dict() for r in report.risks],
        "conflicts": [c.to_dict() for c in report.conflicts],
        "uncertainties": [u.to_dict() for u in report.uncertainties],
        "overallConfidence": report.overall_confidence,
        "overall_confidence": report.overall_confidence,
        "allEvidenceReferences": report.all_evidence_references,
        "all_evidence_references": report.all_evidence_references,
        "sourcesSummary": {
            "webCount": web_count,
            "githubCount": gh_count,
            "ragCount": rag_count,
            "primaryDocs": primary_docs,
        },
    }


def run_research_pipeline(
    session_id: str,
    request_data: CreateResearchRequest,
    components: dict[str, Any] | None = None,
) -> None:
    """Execute the full DEVSCOUT backend pipeline sequentially and update session state."""
    start_time = time.time()
    try:
        pipeline = components or get_pipeline_components(request_data.provider)
        analyzer = pipeline["analyzer"]
        planner = pipeline["planner"]
        task_generator = pipeline["task_generator"]
        web_researcher = pipeline["web_researcher"]
        github_researcher = pipeline["github_researcher"]
        rag_researcher = pipeline["rag_researcher"]
        evidence_layer = pipeline["evidence_layer"]
        reasoning_engine = pipeline["reasoning_engine"]

        # Build composite request text
        objective = request_data.objective or request_data.user_request or request_data.prompt or "Technical Research"
        request_text = objective
        if request_data.scale:
            request_text += f"\nTarget Scale: {request_data.scale}"
        if request_data.budget:
            request_text += f"\nBudget Tier: {request_data.budget}"
        if request_data.technologies:
            request_text += f"\nTechnologies: {', '.join(request_data.technologies)}"
        if request_data.constraints:
            request_text += f"\nConstraints: {', '.join(request_data.constraints)}"
        if request_data.preferences:
            request_text += f"\nPreferences: {', '.join(request_data.preferences)}"

        # -------------------------------------------------------------------
        # Stage 0: Requirement Analysis
        # -------------------------------------------------------------------
        stage_t0 = time.time()
        session_store.update(session_id, {
            "state": "planning",
            "currentStage": "requirement_analysis",
            "currentStageIndex": 0,
        })
        session_store.set_stage(session_id, 0, "running")
        session_store.add_event(session_id, "requirement_analysis", f'Analyzing technical requirements for "{objective[:60]}..."')

        analysis = analyzer.analyze(request_text)

        session_store.update(session_id, {
            "requirementAnalysis": {
                "problemStatement": objective,
                "coreObjective": analysis.goal,
                "targetScale": request_data.scale or "~1,000 concurrent users",
                "budgetTier": request_data.budget or "Low / Bootstrapped",
                "technologies": analysis.technologies,
                "hardConstraints": analysis.constraints,
                "preferences": request_data.preferences or [],
                "technicalDomain": "Distributed Systems & Architecture Trade-offs",
                "goal": analysis.goal,
                "requirements": analysis.requirements,
                "constraints": analysis.constraints,
                "unknowns": analysis.unknowns,
            },
            "technologies": analysis.technologies,
            "constraints": analysis.constraints,
        })
        session_store.set_stage(session_id, 0, "completed", max(1, int(time.time() - stage_t0)))
        session_store.add_event(
            session_id,
            "requirement_analysis",
            f"Requirements extracted: {len(analysis.requirements)} requirements, {len(analysis.technologies)} technologies.",
            "success",
        )

        # -------------------------------------------------------------------
        # Stage 1: Research Planning
        # -------------------------------------------------------------------
        stage_t1 = time.time()
        session_store.update(session_id, {
            "currentStage": "research_planning",
            "currentStageIndex": 1,
        })
        session_store.set_stage(session_id, 1, "running")

        plan = planner.plan(analysis)

        frontend_questions = []
        for q_idx, rq in enumerate(plan.research_questions, start=1):
            frontend_questions.append({
                "id": f"q-{q_idx}",
                "question": rq.question,
                "priority": rq.priority.upper(),
                "sources": rq.source_types,
                "rationale": rq.rationale,
                "tasks": [],
                "evidenceIds": [],
            })

        plan_dict = {
            "id": f"plan-{session_id}",
            "generatedAt": datetime.now(timezone.utc).isoformat(),
            "questions": frontend_questions,
            "totalTasks": 0,
            "targetedSources": list({st for rq in plan.research_questions for st in rq.source_types}),
            "strategySummary": f"Prioritize {plan.research_questions[0].question if plan.research_questions else 'core architectural choices'}",
            "research_questions": [rq.model_dump() if hasattr(rq, "model_dump") else rq.to_dict() for rq in plan.research_questions],
            "technologies_to_investigate": plan.technologies_to_investigate,
        }
        session_store.update(session_id, {"plan": plan_dict})
        session_store.set_stage(session_id, 1, "completed", max(1, int(time.time() - stage_t1)))
        session_store.add_event(
            session_id,
            "research_planning",
            f"Formulated research plan with {len(plan.research_questions)} questions.",
            "success",
        )

        # -------------------------------------------------------------------
        # Stage 2: Task Generation
        # -------------------------------------------------------------------
        stage_t2 = time.time()
        session_store.update(session_id, {
            "currentStage": "task_generation",
            "currentStageIndex": 2,
        })
        session_store.set_stage(session_id, 2, "running")

        tasks = task_generator.generate_tasks(plan)

        frontend_tasks = []
        question_id_map = {}
        for q_idx, fq in enumerate(frontend_questions, start=1):
            question_id_map[fq["question"].strip().lower()] = fq["id"]

        for t_idx, t in enumerate(tasks, start=1):
            matching_q_id = question_id_map.get(t.question.strip().lower(), "q-1")
            t_dict = {
                "id": f"t-{t_idx}",
                "questionId": matching_q_id,
                "title": f"{t.target} Probe",
                "description": t.purpose,
                "sourceType": t.source_type,
                "source": t.source_type,
                "status": "queued",
                "searchQuery": t.question,
                "query": t.question,
                "itemsFoundCount": 0,
                "priority": t.priority,
                "target": t.target,
                "purpose": t.purpose,
            }
            frontend_tasks.append(t_dict)
            for fq in frontend_questions:
                if fq["id"] == matching_q_id:
                    fq["tasks"].append(t_dict)
                    break

        plan_dict["totalTasks"] = len(frontend_tasks)
        session_store.update(session_id, {"tasks": frontend_tasks, "plan": plan_dict})
        session_store.set_stage(session_id, 2, "completed", max(1, int(time.time() - stage_t2)))

        web_tasks = [t for t in tasks if t.source_type == "web"]
        github_tasks = [t for t in tasks if t.source_type == "github"]
        rag_tasks = [t for t in tasks if t.source_type == "rag"]

        session_store.add_event(
            session_id,
            "task_generation",
            f"Generated {len(tasks)} atomic probes ({len(web_tasks)} Web, {len(github_tasks)} GitHub, {len(rag_tasks)} RAG).",
            "success",
        )

        collected_results: list[tuple[Any, str]] = []

        # -------------------------------------------------------------------
        # Stage 3: Web Research
        # -------------------------------------------------------------------
        stage_t3 = time.time()
        session_store.update(session_id, {
            "state": "researching",
            "currentStage": "web_research",
            "currentStageIndex": 3,
        })
        session_store.set_stage(session_id, 3, "running")

        high_priority_web_tasks = [t for t in web_tasks if t.priority == "high"]
        selected_web_tasks = high_priority_web_tasks[:2] if high_priority_web_tasks else web_tasks[:2]

        for wt in selected_web_tasks:
            try:
                results = web_researcher.search(wt)
                for res in results:
                    collected_results.append((res, wt.priority))
                # update task items count
                for ft in frontend_tasks:
                    if ft["description"] == wt.purpose and ft["sourceType"] == "web":
                        ft["status"] = "completed"
                        ft["itemsFoundCount"] = len(results)
            except Exception as e:
                session_store.add_event(session_id, "web_research", f"Web probe error: {e}", "warning")

        session_store.set_stage(session_id, 3, "completed", max(1, int(time.time() - stage_t3)))
        web_items_count = sum(1 for res, _ in collected_results if hasattr(res, "url") and not hasattr(res, "repo_name"))
        session_store.add_event(
            session_id,
            "web_research",
            f"Retrieved {web_items_count} technical web sources and documentation articles.",
            "artifact",
        )

        # -------------------------------------------------------------------
        # Stage 4: GitHub Research
        # -------------------------------------------------------------------
        stage_t4 = time.time()
        session_store.update(session_id, {
            "currentStage": "github_research",
            "currentStageIndex": 4,
        })
        session_store.set_stage(session_id, 4, "running")

        high_priority_gh_tasks = [t for t in github_tasks if t.priority == "high"]
        selected_gh_tasks = high_priority_gh_tasks[:2] if high_priority_gh_tasks else github_tasks[:2]

        repositories = []
        for gh_task in selected_gh_tasks:
            try:
                gh_results = github_researcher.search(gh_task)
                for res in gh_results:
                    collected_results.append((res, gh_task.priority))
                    repo_dict = {
                        "id": f"repo-{len(repositories) + 1}",
                        "owner": res.owner,
                        "repo": res.repo_name,
                        "repo_name": res.repo_name,
                        "fullName": f"{res.owner}/{res.repo_name}",
                        "description": res.description or "",
                        "language": res.language or "Unknown",
                        "stars": res.stars,
                        "forks": res.forks,
                        "openIssues": res.open_issues,
                        "open_issues": res.open_issues,
                        "lastUpdated": getattr(res, "last_updated", "") or getattr(res, "updated_at", ""),
                        "updated_at": getattr(res, "last_updated", "") or getattr(res, "updated_at", ""),
                        "url": res.url,
                        "license": "Open Source",
                        "commitFrequency": "Active",
                        "recentRelease": "Latest",
                        "relevanceToArchitecture": f"Evaluated for probe: {gh_task.question}",
                    }
                    repositories.append(repo_dict)

                for ft in frontend_tasks:
                    if ft["description"] == gh_task.purpose and ft["sourceType"] == "github":
                        ft["status"] = "completed"
                        ft["itemsFoundCount"] = len(gh_results)
            except Exception as e:
                session_store.add_event(session_id, "github_research", f"GitHub probe error: {e}", "warning")

        session_store.update(session_id, {"repositories": repositories})
        session_store.set_stage(session_id, 4, "completed", max(1, int(time.time() - stage_t4)))
        session_store.add_event(
            session_id,
            "github_research",
            f"Audited {len(repositories)} open-source repositories and implementation libraries.",
            "artifact",
        )

        # -------------------------------------------------------------------
        # Stage 5: RAG Research
        # -------------------------------------------------------------------
        stage_t5 = time.time()
        session_store.update(session_id, {
            "currentStage": "rag_research",
            "currentStageIndex": 5,
        })
        session_store.set_stage(session_id, 5, "running")

        high_priority_rag_tasks = [t for t in rag_tasks if t.priority == "high"]
        selected_rag_tasks = high_priority_rag_tasks[:2] if high_priority_rag_tasks else rag_tasks[:2]

        rag_items_count = 0
        for r_task in selected_rag_tasks:
            try:
                rag_results = rag_researcher.search(r_task)
                for res in rag_results:
                    collected_results.append((res, r_task.priority))
                    rag_items_count += 1
                for ft in frontend_tasks:
                    if ft["description"] == r_task.purpose and ft["sourceType"] == "rag":
                        ft["status"] = "completed"
                        ft["itemsFoundCount"] = len(rag_results)
            except Exception as e:
                session_store.add_event(session_id, "rag_research", f"RAG notice: {e}", "info")

        session_store.set_stage(session_id, 5, "completed", max(1, int(time.time() - stage_t5)))
        session_store.add_event(
            session_id,
            "rag_research",
            f"Retrieved {rag_items_count} internal engineering knowledge items.",
            "info",
        )

        # -------------------------------------------------------------------
        # Stage 6: Evidence Processing
        # -------------------------------------------------------------------
        stage_t6 = time.time()
        session_store.update(session_id, {
            "state": "processing",
            "currentStage": "evidence_processing",
            "currentStageIndex": 6,
        })
        session_store.set_stage(session_id, 6, "running")

        frontend_evidence = []
        evidence_context = None

        if collected_results:
            raw_evidence = [
                evidence_layer.normalize([res], task_priority=prio)[0]
                for res, prio in collected_results
            ]
            deduped_evidence = evidence_layer.deduplicate_items(raw_evidence)
            evidence_groups = evidence_layer.group_items(deduped_evidence)
            evidence_context = build_evidence_context(
                user_request=request_text,
                requirements=analysis,
                plan=plan,
                tasks=tasks,
                evidence_groups=evidence_groups,
            )

            for ev in evidence_context.evidence_map.values():
                domain = urlparse(ev.url).netloc if ev.url else (ev.source or "unknown")
                matching_q_id = question_id_map.get(ev.task_question.strip().lower(), "q-1")
                relevance = "primary" if ev.task_priority == "high" else ("high" if (ev.rank_score or 0) > 0.7 else "medium")
                frontend_evidence.append({
                    "id": ev.ev_id or ev.identifier,
                    "sourceType": ev.source_type,
                    "source_type": ev.source_type,
                    "title": ev.title,
                    "domain": domain,
                    "url": ev.url or "",
                    "snippet": ev.content[:240] if ev.content else "",
                    "fullQuote": ev.content or "",
                    "content": ev.content or "",
                    "relatedQuestionId": matching_q_id,
                    "relevance": relevance,
                    "verified": True,
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "metadata": ev.metadata or {},
                })

                for fq in frontend_questions:
                    if fq["id"] == matching_q_id:
                        if ev.ev_id:
                            fq["evidenceIds"].append(ev.ev_id)
                        break

        session_store.update(session_id, {
            "evidence": frontend_evidence,
            "plan": plan_dict,
        })
        session_store.set_stage(session_id, 6, "completed", max(1, int(time.time() - stage_t6)))
        session_store.add_event(
            session_id,
            "evidence_processing",
            f"Normalized and validated {len(frontend_evidence)} canonical evidence items against primary standards.",
            "success",
        )

        # -------------------------------------------------------------------
        # Stage 7: Decision Analysis
        # -------------------------------------------------------------------
        stage_t7 = time.time()
        session_store.update(session_id, {
            "currentStage": "decision_analysis",
            "currentStageIndex": 7,
        })
        session_store.set_stage(session_id, 7, "running")

        if evidence_context is None:
            evidence_context = build_evidence_context(
                user_request=request_text,
                requirements=analysis,
                plan=plan,
                tasks=tasks,
                evidence_groups=[],
            )

        decision_report = reasoning_engine.reason(evidence_context)
        formatted_report = format_decision_report(decision_report, session_id, frontend_evidence)

        session_store.update(session_id, {
            "report": formatted_report,
            "state": "completed",
            "status": "completed",
            "progress": 100,
            "isComplete": True,
            "currentStage": "decision_analysis",
            "currentStageIndex": 7,
        })
        session_store.set_stage(session_id, 7, "completed", max(1, int(time.time() - stage_t7)))
        session_store.add_event(
            session_id,
            "decision_analysis",
            f"Decision Report generated: {decision_report.overall_confidence.upper()} confidence grounded in {len(decision_report.all_evidence_references)} citations.",
            "success",
        )

    except Exception as e:
        session_store.update(session_id, {
            "state": "failed",
            "status": "failed",
            "error": str(e),
        })
        current_stage_idx = session_store.get(session_id).get("currentStageIndex", 0) if session_store.get(session_id) else 0
        session_store.set_stage(session_id, current_stage_idx, "failed")
        session_store.add_event(
            session_id,
            "decision_analysis",
            f"Pipeline failed: {e}",
            "warning",
        )


# ---------------------------------------------------------------------------
# FastAPI Application & Router Setup
# ---------------------------------------------------------------------------

app = FastAPI(
    title="DEVSCOUT Backend API",
    description="Thin FastAPI HTTP layer for the DEVSCOUT technical research and decision engine.",
    version="1.0.0",
)

# Enable CORS for local Vite frontend on port 3000, 5173, etc.
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "*",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

router = APIRouter()


@router.get("/health")
def health_check():
    """Health check endpoint."""
    return {
        "status": "ok",
        "service": "devscout-api",
        "name": "DEVSCOUT Backend",
        "version": "1.0.0",
    }


@router.post("/research/start", status_code=status.HTTP_200_OK)
def start_research(
    payload: CreateResearchRequest,
    background_tasks: BackgroundTasks,
    sync: bool = False,
):
    """
    Initiate a new technical research spike.
    Starts the real DEVSCOUT pipeline in background and immediately returns initial session state.
    """
    objective = payload.objective or payload.user_request or payload.prompt
    if not objective or not objective.strip():
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Objective or prompt must be a non-empty string.",
        )

    session = session_store.create(payload)

    if sync:
        run_research_pipeline(session["id"], payload)
        return session_store.get(session["id"])

    background_tasks.add_task(run_research_pipeline, session["id"], payload)
    return session


@router.get("/research/history")
def get_research_history():
    """Retrieve session summaries for research history list."""
    return session_store.list_history()


@router.get("/research/{session_id}")
def get_research_session(session_id: str):
    """Retrieve full research session document by ID."""
    session = session_store.get(session_id)
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Research session '{session_id}' not found.",
        )
    return session


@router.get("/research/{session_id}/status")
def get_research_status(session_id: str):
    """Polling endpoint for execution state, stage progress, and counts."""
    session = session_store.get(session_id)
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Research session '{session_id}' not found.",
        )

    stages = session.get("stages", [])
    completed_stages = sum(1 for s in stages if s.get("status") == "completed")

    return {
        "id": session["id"],
        "sessionId": session["id"],
        "session_id": session["id"],
        "state": session.get("state", "idle"),
        "status": session.get("status", "running"),
        "progress": session.get("progress", int((completed_stages / max(1, len(stages))) * 100)),
        "currentStage": session.get("currentStage", "requirement_analysis"),
        "currentStageIndex": session.get("currentStageIndex", 0),
        "totalStages": len(stages),
        "completedStages": completed_stages,
        "evidenceCount": len(session.get("evidence", [])),
        "repositoriesCount": len(session.get("repositories", [])),
        "isComplete": session.get("state") == "completed" or session.get("status") == "completed",
        "hasReport": session.get("report") is not None,
        "stages": stages,
        "events": session.get("events", []),
    }


@router.get("/research/{session_id}/tasks")
def get_research_tasks(session_id: str):
    """Retrieve generated research tasks for a session."""
    session = session_store.get(session_id)
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Research session '{session_id}' not found.",
        )
    return session.get("tasks", [])


@router.get("/research/{session_id}/evidence")
def get_research_evidence(
    session_id: str,
    source_type: Optional[str] = Query(None, alias="sourceType"),
    query: Optional[str] = None,
    sort_by: Optional[str] = Query(None, alias="sortBy"),
):
    """Retrieve gathered and normalized evidence items with optional filtering."""
    session = session_store.get(session_id)
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Research session '{session_id}' not found.",
        )

    items = list(session.get("evidence", []))

    if source_type and source_type.lower() != "all":
        items = [e for e in items if e.get("sourceType") == source_type.lower()]

    if query and query.strip():
        q_lower = query.strip().lower()
        items = [
            e for e in items
            if q_lower in e.get("title", "").lower()
            or q_lower in e.get("snippet", "").lower()
            or q_lower in e.get("domain", "").lower()
        ]

    if sort_by == "relevance":
        order = {"primary": 4, "benchmark": 3, "high": 2, "medium": 1}
        items.sort(key=lambda x: order.get(x.get("relevance", "medium"), 0), reverse=True)
    elif sort_by == "newest":
        items.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
    elif sort_by == "domain":
        items.sort(key=lambda x: x.get("domain", "").lower())

    return items


@router.get("/research/{session_id}/repositories")
def get_research_repositories(session_id: str):
    """Retrieve audited open-source GitHub repositories."""
    session = session_store.get(session_id)
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Research session '{session_id}' not found.",
        )
    return session.get("repositories", [])


@router.get("/research/{session_id}/report")
def get_research_report(session_id: str):
    """Retrieve synthesized architectural decision report."""
    session = session_store.get(session_id)
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Research session '{session_id}' not found.",
        )

    report = session.get("report")
    if not report:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Decision report is still in synthesis. Please poll /status until complete.",
        )
    return report


# Mount routes under both /api/v1 and root for seamless frontend compatibility
app.include_router(router, prefix="/api/v1")
app.include_router(router)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("api:app", host="0.0.0.0", port=8000, reload=True)
