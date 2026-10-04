"""
Tests for DEVSCOUT FastAPI HTTP Layer (api.py).
Verifies all REST API endpoints, session state management, filtering, and pipeline invocation.
"""

import unittest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient

from api import app, session_store, SessionStore, CreateResearchRequest, run_research_pipeline
from models import (
    Alternative,
    DecisionReport,
    Evidence,
    EvidenceContext,
    Finding,
    Recommendation,
    RequirementAnalysis,
    ResearchPlan,
    ResearchQuestion,
    ResearchTask,
    Risk,
    Tradeoff,
    WebResearchResult,
    GitHubResearchResult,
    RAGResearchResult,
)


class TestSessionStore(unittest.TestCase):
    """Unit tests for the thread-safe SessionStore."""

    def setUp(self):
        self.store = SessionStore()

    def test_create_session_defaults(self):
        req = CreateResearchRequest(objective="Compare Redis vs Memcached")
        session = self.store.create(req)

        self.assertTrue(session["id"].startswith("res-"))
        self.assertEqual(session["objective"], "Compare Redis vs Memcached")
        self.assertEqual(session["status"], "running")
        self.assertEqual(len(session["stages"]), 8)
        self.assertEqual(session["stages"][0]["status"], "running")
        self.assertEqual(session["stages"][1]["status"], "queued")
        self.assertEqual(len(session["events"]), 1)
        self.assertEqual(session["tasks"], [])
        self.assertEqual(session["evidence"], [])
        self.assertEqual(session["repositories"], [])
        self.assertIsNone(session["report"])

    def test_create_session_fallback_objective(self):
        req = CreateResearchRequest(prompt="Evaluate Kafka vs RabbitMQ")
        session = self.store.create(req)
        self.assertEqual(session["objective"], "Evaluate Kafka vs RabbitMQ")

        req_empty = CreateResearchRequest()
        session_empty = self.store.create(req_empty)
        self.assertEqual(session_empty["objective"], "Technical Architecture Research")

    def test_get_and_list_summaries(self):
        req1 = CreateResearchRequest(objective="Topic 1")
        req2 = CreateResearchRequest(objective="Topic 2")
        s1 = self.store.create(req1)
        s2 = self.store.create(req2)

        self.assertIsNotNone(self.store.get(s1["id"]))
        self.assertIsNotNone(self.store.get(s2["id"]))
        self.assertIsNone(self.store.get("non-existent-id"))

        summaries = self.store.list_summaries()
        self.assertEqual(len(summaries), 2)
        summary_ids = [s["id"] for s in summaries]
        self.assertIn(s1["id"], summary_ids)
        self.assertIn(s2["id"], summary_ids)

    def test_update_stage_and_events(self):
        req = CreateResearchRequest(objective="Test Stages")
        session = self.store.create(req)
        s_id = session["id"]

        self.store.update_stage(s_id, "requirement_analysis", "completed", progress=15)
        updated = self.store.get(s_id)
        self.assertEqual(updated["stages"][0]["status"], "completed")
        self.assertEqual(updated["progress"], 15)

        self.store.append_event(s_id, "Analyzed requirements", level="info")
        updated = self.store.get(s_id)
        self.assertEqual(len(updated["events"]), 2)
        self.assertEqual(updated["events"][-1]["message"], "Analyzed requirements")

    def test_append_tasks_evidence_repositories(self):
        req = CreateResearchRequest(objective="Test Collections")
        session = self.store.create(req)
        s_id = session["id"]

        self.store.append_tasks(s_id, [{"id": "task-1", "question": "Q1"}])
        self.store.append_evidence(s_id, [{"id": "ev-1", "title": "Doc 1"}])
        self.store.append_repositories(s_id, [{"id": "repo-1", "name": "owner/repo"}])

        updated = self.store.get(s_id)
        self.assertEqual(len(updated["tasks"]), 1)
        self.assertEqual(len(updated["evidence"]), 1)
        self.assertEqual(len(updated["repositories"]), 1)

    def test_complete_and_fail(self):
        req = CreateResearchRequest(objective="Test Completion")
        session = self.store.create(req)
        s_id = session["id"]

        mock_report = {"executiveSummary": "Done", "recommendedApproach": "Option A"}
        self.store.complete(s_id, mock_report)
        completed = self.store.get(s_id)
        self.assertEqual(completed["status"], "completed")
        self.assertEqual(completed["progress"], 100)
        self.assertIsNotNone(completed["report"])

        session2 = self.store.create(req)
        s2_id = session2["id"]
        self.store.fail(s2_id, "Network timeout")
        failed = self.store.get(s2_id)
        self.assertEqual(failed["status"], "failed")
        self.assertIn("Network timeout", failed["error"])


class TestFastAPIEndpoints(unittest.TestCase):
    """Integration tests for all HTTP API endpoints."""

    def setUp(self):
        self.client = TestClient(app)

    def test_health_check(self):
        response = self.client.get("/health")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["status"], "ok")
        self.assertEqual(data["service"], "devscout-api")

    def test_history_endpoint(self):
        response = self.client.get("/api/v1/research/history")
        self.assertEqual(response.status_code, 200)
        self.assertIsInstance(response.json(), list)

    @patch("api.run_research_pipeline")
    def test_start_research_session_api_v1(self, mock_pipeline):
        payload = {
            "objective": "Evaluate WebSockets vs SSE for real-time dashboards",
            "technologies": ["FastAPI", "React"],
            "constraints": ["Low latency", "Scalable"],
            "scale": "10,000 active sockets",
            "budget": "Moderate",
        }
        response = self.client.post("/api/v1/research/start", json=payload)
        self.assertIn(response.status_code, (200, 201))

        data = response.json()
        self.assertTrue(data["id"].startswith("res-"))
        self.assertEqual(data["objective"], payload["objective"])
        self.assertEqual(data["status"], "running")
        self.assertEqual(len(data["stages"]), 8)
        self.assertEqual(data["progress"], 5)
        self.assertEqual(data["technologies"], ["FastAPI", "React"])

        # Check session can be fetched
        s_id = data["id"]
        get_res = self.client.get(f"/api/v1/research/{s_id}")
        self.assertEqual(get_res.status_code, 200)
        self.assertEqual(get_res.json()["id"], s_id)

    @patch("api.run_research_pipeline")
    def test_start_research_session_root_prefix(self, mock_pipeline):
        payload = {"objective": "Root prefix route test"}
        response = self.client.post("/research/start", json=payload)
        self.assertIn(response.status_code, (200, 201))
        data = response.json()
        self.assertTrue(data["id"].startswith("res-"))

        get_res = self.client.get(f"/research/{data['id']}")
        self.assertEqual(get_res.status_code, 200)

    def test_get_session_not_found(self):
        response = self.client.get("/api/v1/research/non-existent-session-id")
        self.assertEqual(response.status_code, 404)
        self.assertIn("not found", response.json()["detail"].lower())

    def test_get_status_endpoint(self):
        req = CreateResearchRequest(objective="Check status endpoint")
        session = session_store.create(req)
        s_id = session["id"]

        response = self.client.get(f"/api/v1/research/{s_id}/status")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["sessionId"], s_id)
        self.assertEqual(data["status"], "running")
        self.assertEqual(data["progress"], 5)
        self.assertIsInstance(data["stages"], list)
        self.assertIsInstance(data["events"], list)

    def test_get_tasks_endpoint(self):
        req = CreateResearchRequest(objective="Check tasks endpoint")
        session = session_store.create(req)
        s_id = session["id"]
        mock_tasks = [
            {"id": "t1", "sourceType": "web", "question": "How fast is FastAPI?", "status": "completed"},
            {"id": "t2", "sourceType": "github", "question": "Check star history", "status": "running"},
        ]
        session_store.append_tasks(s_id, mock_tasks)

        response = self.client.get(f"/api/v1/research/{s_id}/tasks")
        self.assertEqual(response.status_code, 200)
        tasks = response.json()
        self.assertEqual(len(tasks), 2)
        self.assertEqual(tasks[0]["id"], "t1")

    def test_get_repositories_endpoint(self):
        req = CreateResearchRequest(objective="Check repos endpoint")
        session = session_store.create(req)
        s_id = session["id"]
        mock_repos = [
            {"id": "r1", "name": "fastapi/fastapi", "stars": 75000, "relevanceScore": 0.95},
        ]
        session_store.append_repositories(s_id, mock_repos)

        response = self.client.get(f"/api/v1/research/{s_id}/repositories")
        self.assertEqual(response.status_code, 200)
        repos = response.json()
        self.assertEqual(len(repos), 1)
        self.assertEqual(repos[0]["name"], "fastapi/fastapi")

    def test_get_evidence_endpoint_filtering_and_sorting(self):
        req = CreateResearchRequest(objective="Check evidence endpoint")
        session = session_store.create(req)
        s_id = session["id"]

        evidence_items = [
            {
                "id": "e1",
                "title": "FastAPI Benchmarks",
                "sourceType": "web",
                "domain": "fastapi.tiangolo.com",
                "snippet": "High performance async Python framework",
                "relevance": "primary",
                "timestamp": "2026-01-01T00:00:00Z",
            },
            {
                "id": "e2",
                "title": "GitHub repository encode/starlette",
                "sourceType": "github",
                "domain": "github.com",
                "snippet": "The ASGI framework under FastAPI",
                "relevance": "high",
                "timestamp": "2026-02-01T00:00:00Z",
            },
            {
                "id": "e3",
                "title": "Internal Architecture RAG Document",
                "sourceType": "rag",
                "domain": "internal-wiki",
                "snippet": "Guidelines on concurrency and thread safety",
                "relevance": "medium",
                "timestamp": "2026-03-01T00:00:00Z",
            },
        ]
        session_store.append_evidence(s_id, evidence_items)

        # 1. Fetch all
        res_all = self.client.get(f"/api/v1/research/{s_id}/evidence")
        self.assertEqual(res_all.status_code, 200)
        self.assertEqual(len(res_all.json()), 3)

        # 2. Filter by sourceType
        res_web = self.client.get(f"/api/v1/research/{s_id}/evidence?sourceType=web")
        self.assertEqual(res_web.status_code, 200)
        self.assertEqual(len(res_web.json()), 1)
        self.assertEqual(res_web.json()[0]["sourceType"], "web")

        # 3. Filter by query string
        res_query = self.client.get(f"/api/v1/research/{s_id}/evidence?query=starlette")
        self.assertEqual(res_query.status_code, 200)
        self.assertEqual(len(res_query.json()), 1)
        self.assertEqual(res_query.json()[0]["id"], "e2")

        # 4. Sort by relevance
        res_sort = self.client.get(f"/api/v1/research/{s_id}/evidence?sortBy=relevance")
        self.assertEqual(res_sort.status_code, 200)
        items = res_sort.json()
        self.assertEqual(items[0]["id"], "e1")

        # 5. Sort by newest
        res_newest = self.client.get(f"/api/v1/research/{s_id}/evidence?sortBy=newest")
        self.assertEqual(res_newest.status_code, 200)
        self.assertEqual(res_newest.json()[0]["id"], "e3")

    def test_get_report_endpoint(self):
        req = CreateResearchRequest(objective="Check report endpoint")
        session = session_store.create(req)
        s_id = session["id"]

        # Report not yet generated -> 404
        res_pending = self.client.get(f"/api/v1/research/{s_id}/report")
        self.assertEqual(res_pending.status_code, 404)
        self.assertIn("synthesis", res_pending.json()["detail"].lower())

        # Complete session with formatted report
        mock_report = {
            "executiveSummary": "FastAPI is the recommended framework for this high-throughput API.",
            "recommendedApproach": "Deploy FastAPI with Uvicorn workers behind NGINX.",
            "whyItFits": [{"point": "Native async/await, low memory footprint", "evidenceIds": ["EV-1"]}],
            "alternatives": [
                {
                    "title": "Go Gin",
                    "fitLevel": "viable",
                    "summary": "Statically compiled Go microservice",
                    "pros": ["Highest raw throughput"],
                    "cons": ["Team lacks Go expertise"],
                    "verdict": "Viable alternative",
                    "evidenceIds": ["EV-2"],
                }
            ],
            "tradeoffs": [
                {
                    "dimension": "Performance vs Developer Velocity",
                    "analysis": "Python async meets all targets while keeping Python ecosystem speed.",
                    "winner": "FastAPI",
                    "evidenceIds": ["EV-1", "EV-2"],
                }
            ],
            "technicalConsiderations": [
                {
                    "category": "Deployment",
                    "guidance": "Use multi-stage Docker container.",
                    "actionableRule": "Pin dependencies and run as non-root user.",
                }
            ],
            "confidence": "high",
        }
        session_store.complete(s_id, mock_report)

        # Now report is available -> 200
        res_report = self.client.get(f"/api/v1/research/{s_id}/report")
        self.assertEqual(res_report.status_code, 200)
        data = res_report.json()
        self.assertEqual(data["executiveSummary"], mock_report["executiveSummary"])
        self.assertEqual(data["recommendedApproach"], mock_report["recommendedApproach"])
        self.assertEqual(len(data["alternatives"]), 1)
        self.assertEqual(data["confidence"], "high")


class TestPipelineExecutionFlow(unittest.TestCase):
    """Tests the real pipeline background executor with mocked components."""

    def test_run_research_pipeline_success(self):
        req = CreateResearchRequest(
            objective="Select database for real-time analytics",
            technologies=["ClickHouse", "TimescaleDB"],
        )
        session = session_store.create(req)
        s_id = session["id"]

        # 1. Mock RequirementAnalyzer
        mock_analyzer = MagicMock()
        mock_analyzer.analyze.return_value = RequirementAnalysis(
            goal="Real-time analytics engine",
            technologies=["ClickHouse", "TimescaleDB"],
            requirements=["5,000 queries/sec", "< 50ms latency"],
            constraints=["Low latency query", "High ingestion rate"],
            unknowns=[],
        )

        # 2. Mock ResearchPlanner
        mock_planner = MagicMock()
        mock_planner.plan.return_value = ResearchPlan(
            research_questions=[
                ResearchQuestion(
                    question="How does ClickHouse perform on 10TB/day ingestion?",
                    priority="high",
                    source_types=["web"],
                    rationale="Ingestion capacity benchmark",
                ),
                ResearchQuestion(
                    question="Audit GitHub activity and stability of ClickHouse/ClickHouse",
                    priority="medium",
                    source_types=["github"],
                    rationale="Maintainability check",
                ),
                ResearchQuestion(
                    question="Retrieve internal vector database knowledge on TimescaleDB vs ClickHouse",
                    priority="medium",
                    source_types=["rag"],
                    rationale="Check prior team decisions",
                ),
            ],
            technologies_to_investigate=["ClickHouse", "TimescaleDB"],
        )

        # 3. Mock TaskGenerator
        mock_tg = MagicMock()
        mock_tg.generate_tasks.return_value = [
            ResearchTask(
                question="How does ClickHouse perform on 10TB/day ingestion?",
                purpose="Ingestion capacity benchmark",
                priority="high",
                target="ClickHouse ingestion benchmark",
                source_type="web",
            ),
            ResearchTask(
                question="Audit GitHub activity and stability of ClickHouse/ClickHouse",
                purpose="Maintainability check",
                priority="medium",
                target="ClickHouse/ClickHouse",
                source_type="github",
            ),
            ResearchTask(
                question="Retrieve internal vector database knowledge on TimescaleDB vs ClickHouse",
                purpose="Prior team decisions",
                priority="medium",
                target="TimescaleDB ClickHouse trade-offs",
                source_type="rag",
            ),
        ]

        # 4. Mock Researchers
        mock_web = MagicMock()
        mock_web.search.return_value = [
            WebResearchResult(
                task_question="How does ClickHouse perform on 10TB/day ingestion?",
                query="ClickHouse ingestion benchmark",
                url="https://benchmark.org/clickhouse",
                title="ClickHouse 10TB Ingestion Benchmark",
                source="benchmark.org",
                snippet="ClickHouse easily ingests 100M rows per second with low CPU overhead.",
            )
        ]

        mock_gh = MagicMock()
        mock_gh.search.return_value = [
            GitHubResearchResult(
                task_question="Audit GitHub activity and stability of ClickHouse/ClickHouse",
                query="ClickHouse/ClickHouse",
                repo_name="ClickHouse/ClickHouse",
                stars=38000,
                forks=6500,
                open_issues=1200,
                owner="ClickHouse",
                description="Fast open-source analytical database",
                language="C++",
                url="https://github.com/ClickHouse/ClickHouse",
                last_updated="2026-03-25T12:00:00Z",
            )
        ]

        mock_rag = MagicMock()
        mock_rag.search.return_value = [
            RAGResearchResult(
                task_question="Retrieve internal vector database knowledge on TimescaleDB vs ClickHouse",
                query="TimescaleDB ClickHouse trade-offs",
                title="doc-internal-db-eval",
                content="Prior tests found ClickHouse 4x faster than TimescaleDB for broad aggregations.",
                score=0.92,
                source="internal-wiki",
                doc_id="doc-internal-db-eval",
            )
        ]

        # 5. EvidenceLayer (use real deterministic EvidenceLayer)
        from evidence_layer import EvidenceLayer
        mock_ev = EvidenceLayer(deduplicate=True, rank=True)

        # 6. Mock ReasoningEngine
        mock_engine = MagicMock()
        mock_engine.reason.return_value = DecisionReport(
            summary="ClickHouse is the optimal selection for 10TB/day real-time analytics.",
            findings=[
                Finding(
                    question="How does ClickHouse perform on 10TB/day ingestion?",
                    finding="ClickHouse processes 100M rows/sec with low overhead.",
                    reasoning="Internal and external benchmarks show sub-50ms query times.",
                    evidence_references=["EV-001"],
                    confidence="high",
                )
            ],
            comparisons=[],
            recommendation=Recommendation(
                option="ClickHouse for real-time analytics",
                reason="Extreme column-scan performance on massive timeseries.",
                evidence_references=["EV-001", "EV-002", "EV-003"],
                confidence="high",
            ),
            alternatives=[
                Alternative(
                    option="TimescaleDB",
                    reason="Better PostgreSQL familiarity but higher storage overhead for broad scans.",
                    evidence_references=["EV-003"],
                )
            ],
            tradeoffs=[
                Tradeoff(
                    decision="ClickHouse over TimescaleDB",
                    gain="Extreme scan throughput and 10TB/day ingestion rate.",
                    cost="Operational overhead of managing ClickHouse distributed nodes.",
                    evidence_references=["EV-001", "EV-003"],
                )
            ],
            risks=[
                Risk(
                    risk="Cluster management overhead",
                    impact="Operational burden without dedicated SRE or managed cluster.",
                    evidence_references=["EV-002"],
                )
            ],
            conflicts=[],
            uncertainties=[],
            overall_confidence="high",
        )

        mock_components = {
            "analyzer": mock_analyzer,
            "planner": mock_planner,
            "task_generator": mock_tg,
            "web_researcher": mock_web,
            "github_researcher": mock_gh,
            "rag_researcher": mock_rag,
            "evidence_layer": mock_ev,
            "reasoning_engine": mock_engine,
        }

        # Execute the pipeline with mocked components
        run_research_pipeline(s_id, req, components=mock_components)

        # Assert final session state
        updated = session_store.get(s_id)
        self.assertEqual(updated["status"], "completed")
        self.assertEqual(updated["progress"], 100)
        self.assertIsNotNone(updated["report"])
        self.assertEqual(
            updated["report"]["executiveSummary"],
            "ClickHouse is the optimal selection for 10TB/day real-time analytics.",
        )
        self.assertEqual(len(updated["tasks"]), 3)
        self.assertEqual(len(updated["evidence"]), 3)
        self.assertEqual(len(updated["repositories"]), 1)

        # Check all 8 stages completed
        for stage in updated["stages"]:
            self.assertEqual(stage["status"], "completed")

    def test_run_research_pipeline_handles_failure(self):
        req = CreateResearchRequest(objective="Fail pipeline test")
        session = session_store.create(req)
        s_id = session["id"]

        with patch("api.get_pipeline_components") as mock_get_comp:
            mock_analyzer = MagicMock()
            mock_analyzer.analyze.side_effect = RuntimeError("Simulated Analyzer Crash")
            mock_get_comp.return_value = {
                "analyzer": mock_analyzer,
                "planner": MagicMock(),
                "task_generator": MagicMock(),
                "web_researcher": MagicMock(),
                "github_researcher": MagicMock(),
                "rag_researcher": MagicMock(),
                "evidence_layer": MagicMock(),
                "reasoning_engine": MagicMock(),
            }
            run_research_pipeline(s_id, req)

        failed = session_store.get(s_id)
        self.assertEqual(failed["status"], "failed")
        self.assertIn("Simulated Analyzer Crash", failed["error"])
        self.assertEqual(failed["stages"][0]["status"], "failed")


if __name__ == "__main__":
    unittest.main()
