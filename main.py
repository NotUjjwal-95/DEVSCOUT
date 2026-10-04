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
from rag_researcher import RAGResearcher, RAGResearchError
from evidence_layer import EvidenceLayer, EvidenceError


def run_pipeline_demo():
    print("=" * 70)
    print("DEVSCOUT: Requirements -> Plan -> Tasks -> Web, GitHub & RAG Research Pipeline")
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
        rag_researcher = RAGResearcher(max_results_per_task=3)
        evidence_layer = EvidenceLayer(deduplicate=True, rank=True)
    except (AnalyzerError, PlannerError, WebResearchError, GitHubResearchError, RAGResearchError, EvidenceError) as e:
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

        collected_research_results: list[tuple[Any, str]] = []

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
                    collected_research_results.append((res, web_task.priority))
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
                        collected_research_results.append((res, gh_task.priority))
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

        # Stage 6: RAG Research (execute only rag tasks)
        print("\n--- [Stage 6] Executing RAG Research (rag tasks only) ---")
        high_priority_rag_tasks = [t for t in rag_tasks if t.priority == "high"]
        selected_rag_tasks = high_priority_rag_tasks[:2] if high_priority_rag_tasks else rag_tasks[:2]

        if not selected_rag_tasks:
            print("  No RAG tasks generated for this request.\n")
        else:
            print(f"Executing knowledge base retrieval for {len(selected_rag_tasks)} RAG task(s):\n")
            for task_idx, r_task in enumerate(selected_rag_tasks, start=1):
                print(f"  [RAG Task {task_idx}/{len(selected_rag_tasks)}]")
                print(f"  Question: {r_task.question}")
                print(f"  Target:   {r_task.target}")
                print(f"  Priority: {r_task.priority.upper()}")
                print(f"  Query:    '{rag_researcher.build_query(r_task)}'")

                try:
                    rag_results = rag_researcher.search(r_task)
                    print(f"  Retrieved {len(rag_results)} Knowledge Item(s):")
                    for r_idx, res in enumerate(rag_results, start=1):
                        collected_research_results.append((res, r_task.priority))
                        score_str = f" (Score: {res.score:.4f})" if res.score is not None else ""
                        doc_id_str = f" [{res.doc_id}]" if res.doc_id else ""
                        print(f"    {r_idx}. [{res.source}]{doc_id_str} {res.title}{score_str}")
                        if res.content:
                            content_preview = res.content.replace("\n", " ")
                            if len(content_preview) > 140:
                                content_preview = content_preview[:140] + "..."
                            print(f"       Content: {content_preview}")
                    print()
                except RAGResearchError as e:
                    print(f"  [RAG Research Notice]: {e}\n")

        # Stage 7: Evidence Layer (Normalize, Deduplicate, Rank, and Group)
        print("\n--- [Stage 7] Processing Evidence Layer ---")
        if not collected_research_results:
            print("  No research results retrieved to process into evidence.\n")
        else:
            total_collected = len(collected_research_results)

            # 1. Normalize
            raw_evidence = [
                evidence_layer.normalize([res], task_priority=prio)[0]
                for res, prio in collected_research_results
            ]

            # 2. Deduplicate
            deduped_evidence = evidence_layer.deduplicate_items(raw_evidence)
            duplicates_removed = total_collected - len(deduped_evidence)

            # 3. Group and Rank
            evidence_groups = evidence_layer.group_items(deduped_evidence)
            total_canonical = sum(g.total_count for g in evidence_groups)

            web_count = sum(g.web_count for g in evidence_groups)
            github_count = sum(g.github_count for g in evidence_groups)
            rag_count = sum(g.rag_count for g in evidence_groups)

            print(f"Evidence Ingestion Summary:")
            print(f"  Total Ingested:    {total_collected}")
            print(f"  Duplicates Pruned: {duplicates_removed}")
            print(f"  Canonical Items:   {total_canonical} ({web_count} Web, {github_count} GitHub, {rag_count} RAG)")
            print(f"  Questions Covered: {len(evidence_groups)}\n")

            print("Grouped & Ranked Evidence Repository:")
            for g_idx, group in enumerate(evidence_groups, start=1):
                print(f"  [Evidence Group {g_idx}/{len(evidence_groups)}]")
                print(f"  Question: \"{group.task_question}\"")
                print(f"  Evidence Items ({group.total_count} total: {group.web_count} Web, {group.github_count} GitHub, {group.rag_count} RAG):")
                for item_idx, ev in enumerate(group.items, start=1):
                    badge = f"[{ev.source_type.upper()}]"
                    score_display = f" (Rank Score: {ev.rank_score:.4f})"
                    print(f"    {item_idx}. {badge} {ev.title}{score_display}")
                    if ev.url:
                        print(f"       URL: {ev.url}")
                    print(f"       Source: {ev.source} | Priority: {ev.task_priority.upper()}")
                    if ev.content:
                        content_preview = ev.content.replace("\n", " ")
                        if len(content_preview) > 130:
                            content_preview = content_preview[:130] + "..."
                        print(f"       Excerpt: {content_preview}")
                print()

        print("  [Notice] Evidence Layer completed. Decision & Reasoning Engine are deferred to upcoming milestones.")

    print("\n" + "=" * 70)
    print("Full Pipeline Demo completed successfully.")
    print("=" * 70)


if __name__ == "__main__":
    run_pipeline_demo()