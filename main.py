"""
DEVSCOUT - AI-powered technical research and decision assistant.
Integrated Demo: Requirement Analyzer -> Research Planner
"""

import sys
import json

# Ensure UTF-8 output encoding on Windows consoles
if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from analyzer import RequirementAnalyzer, AnalyzerError
from planner import ResearchPlanner, PlannerError


def run_pipeline_demo():
    print("=" * 70)
    print("DEVSCOUT: Requirement Analysis & Research Planning Pipeline")
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
    except (AnalyzerError, PlannerError) as e:
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

            # Formatted Summary for quick inspection
            print("\nSummary of Planned Investigations:")
            print(f"Total Research Questions: {len(plan.research_questions)}")
            print(f"Technologies to Investigate: {', '.join(plan.technologies_to_investigate)}")

            for i, q in enumerate(plan.research_questions, start=1):
                sources = ", ".join(q.source_types)
                print(f"  {i}. [{q.priority.upper()}] ({sources}) {q.question}")
                print(f"     Rationale: {q.rationale}")

        except PlannerError as e:
            print(f"[Research Planning Failed]: {e}")
            if hasattr(e, "raw_response") and e.raw_response:
                print(f"Raw Response: {e.raw_response}")

    print("\n" + "=" * 70)
    print("Pipeline Demo completed successfully.")
    print("=" * 70)


if __name__ == "__main__":
    run_pipeline_demo()