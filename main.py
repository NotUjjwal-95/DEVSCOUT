"""
DEVSCOUT - AI-powered technical research and decision assistant.
Integrated Demo: Requirement Analysis -> Research Planning -> Task Generation -> Web Research
"""

import sys
import json

# Ensure UTF-8 output encoding on Windows consoles
if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from analyzer import RequirementAnalyzer, AnalyzerError
from planner import ResearchPlanner, PlannerError
from task_generator import TaskGenerator
from web_researcher import WebResearcher, WebResearchError


def run_pipeline_demo():
    print("=" * 70)
    print("DEVSCOUT: Requirements -> Plan -> Tasks -> Web Research Pipeline")
    print("=" * 70)

    # Sample Request 1: Collaborative Whiteboard
    request_1 = """
    I want to build a real-time collaborative whiteboard
    using React and Go. Around 1,000 users, low budget,
    and I prefer open-source technologies.
    """

    # Sample Request 2: IoT Telemetry Ingestion Pipeline
    request_2 = """
    We need to build an IoT telemetry ingestion pipeline processing
    50,000 events/second from connected smart meters. We're on AWS,
    need at-least-once delivery, sub-second query latency for the last 24h,
    and 30-day retention under strict cost limits. We are considering Kafka
    or Kinesis with TimescaleDB or ClickHouse.
    """

    test_requests = [
        ("Demo 1: Collaborative Whiteboard", request_1),
        ("Demo 2: IoT Telemetry Pipeline", request_2),
    ]

    try:
        analyzer = RequirementAnalyzer()
        planner = ResearchPlanner()
        task_generator = TaskGenerator()
        web_researcher = WebResearcher(max_results_per_task=3)
    except (AnalyzerError, PlannerError, WebResearchError) as e:
        print(f"[Error initializing components]: {e}")
        return

    for title, request_text in test_requests:
        print(f"\n{'#' * 70}")
        print(f"{title}")
        print(f"{'#' * 70}")
        print("\n[Input] Raw Developer Request:")
        print(request_text.strip())

        # Stage 1: Requirement Analysis
        print("\n--- [Stage 1] Analyzing Requirements ---")
        try:
            analysis = analyzer.analyze(request_text)
            print("\nValidated RequirementAnalysis:")
            print(json.dumps(analysis.to_dict(), indent=2))
        except AnalyzerError as e:
            print(f"[Requirement Analysis Failed]: {e}")
            continue

        # Stage 2: Research Planning
        print("\n--- [Stage 2] Generating Research Plan ---")
        try:
            plan = planner.plan(analysis)
            print("\nValidated ResearchPlan:")
            print(json.dumps(plan.to_dict(), indent=2))
        except PlannerError as e:
            print(f"[Research Planning Failed]: {e}")
            if hasattr(e, "raw_response") and e.raw_response:
                print(f"Raw Response: {e.raw_response}")
            continue

        # Stage 3: Research Task Generation
        print("\n--- [Stage 3] Generating Executable Research Tasks ---")
        tasks = task_generator.generate_tasks(plan)
        print(f"\nGenerated {len(tasks)} Atomic Research Tasks.")

        web_tasks = [t for t in tasks if t.source_type == "web"]
        github_tasks = [t for t in tasks if t.source_type == "github"]
        rag_tasks = [t for t in tasks if t.source_type == "rag"]

        print(f"Task Breakdown: {len(web_tasks)} Web, {len(github_tasks)} GitHub, {len(rag_tasks)} RAG.")

        # Stage 4: Web Research (execute only web tasks)
        print("\n--- [Stage 4] Executing Web Research (web tasks only) ---")
        # For concise demo execution, execute top high-priority web tasks
        high_priority_web_tasks = [t for t in web_tasks if t.priority == "high"]
        selected_web_tasks = high_priority_web_tasks[:2] if high_priority_web_tasks else web_tasks[:2]

        print(f"Executing live search for {len(selected_web_tasks)} high-priority web task(s):\n")

        for task_idx, web_task in enumerate(selected_web_tasks, start=1):
            print(f"  [Web Task {task_idx}/{len(selected_web_tasks)}]")
            print(f"  Question: {web_task.question}")
            print(f"  Target:   {web_task.target}")
            print(f"  Priority: {web_task.priority.upper()}")
            print(f"  Query:    '{web_researcher.build_query(web_task)}'")

            try:
                results = web_researcher.search(web_task)
                print(f"  Retrieved {len(results)} Web Sources:")
                for r_idx, res in enumerate(results, start=1):
                    print(f"    {r_idx}. [{res.source}] {res.title}")
                    print(f"       URL: {res.url}")
                    if res.snippet:
                        snippet_preview = res.snippet.replace("\n", " ")
                        if len(snippet_preview) > 140:
                            snippet_preview = snippet_preview[:140] + "..."
                        print(f"       Snippet: {snippet_preview}")
                print()
            except WebResearchError as e:
                print(f"  [Web Research Error]: {e}\n")

        print("  [Notice] GitHub and RAG research connectors are deferred to upcoming milestones.")

    print("\n" + "=" * 70)
    print("Full Pipeline Demo completed successfully.")
    print("=" * 70)


if __name__ == "__main__":
    run_pipeline_demo()