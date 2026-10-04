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
from github_researcher import GitHubResearcher, GitHubResearchError


def run_pipeline_demo():
    print("=" * 70)
    print("DEVSCOUT: Requirements -> Plan -> Tasks -> Web & GitHub Research Pipeline")
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
        github_researcher = GitHubResearcher(max_results_per_task=3)
    except (AnalyzerError, PlannerError, WebResearchError, GitHubResearchError) as e:
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

        # Stage 5: GitHub Research (execute only github tasks)
        print("\n--- [Stage 5] Executing GitHub Research (github tasks only) ---")
        high_priority_github_tasks = [t for t in github_tasks if t.priority == "high"]
        selected_github_tasks = high_priority_github_tasks[:2] if high_priority_github_tasks else github_tasks[:2]

        if not selected_github_tasks:
            print("  No GitHub tasks generated for this request.\n")
        else:
            print(f"Executing repository search for {len(selected_github_tasks)} GitHub task(s):\n")
            for task_idx, gh_task in enumerate(selected_github_tasks, start=1):
                print(f"  [GitHub Task {task_idx}/{len(selected_github_tasks)}]")
                print(f"  Question: {gh_task.question}")
                print(f"  Target:   {gh_task.target}")
                print(f"  Priority: {gh_task.priority.upper()}")
                print(f"  Query:    '{github_researcher.build_query(gh_task)}'")

                try:
                    gh_results = github_researcher.search(gh_task)
                    print(f"  Retrieved {len(gh_results)} Repositories:")
                    for r_idx, res in enumerate(gh_results, start=1):
                        lang_str = f" | {res.language}" if res.language else ""
                        print(f"    {r_idx}. [{res.owner}] {res.repo_name} (★ {res.stars:,} | Forks: {res.forks:,}{lang_str})")
                        print(f"       URL: {res.url}")
                        if res.description:
                            desc_preview = res.description.replace("\n", " ")
                            if len(desc_preview) > 140:
                                desc_preview = desc_preview[:140] + "..."
                            print(f"       Desc: {desc_preview}")
                    print()
                except GitHubResearchError as e:
                    print(f"  [GitHub Research Error]: {e}\n")

        print("  [Notice] RAG research connector is deferred to upcoming milestones.")

    print("\n" + "=" * 70)
    print("Full Pipeline Demo completed successfully.")
    print("=" * 70)


if __name__ == "__main__":
    run_pipeline_demo()