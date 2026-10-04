"""
DEVSCOUT - AI-powered technical research and decision assistant.
Integrated Demo: Requirement Analysis -> Research Planning -> Task Generation
"""

import sys
import json

# Ensure UTF-8 output encoding on Windows consoles
if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from analyzer import RequirementAnalyzer, AnalyzerError
from planner import ResearchPlanner, PlannerError
from task_generator import TaskGenerator


def run_pipeline_demo():
    print("=" * 70)
    print("DEVSCOUT: Requirements -> Plan -> Research Tasks Pipeline")
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
        except PlannerError as e:
            print(f"[Research Planning Failed]: {e}")
            if hasattr(e, "raw_response") and e.raw_response:
                print(f"Raw Response: {e.raw_response}")
            continue

        # Stage 3: Research Task Generation
        print("\n--- [Stage 3] Generating Executable Research Tasks ---")
        tasks = task_generator.generate_tasks(plan)
        print(f"\nGenerated {len(tasks)} Atomic Research Tasks:")
        print(json.dumps([t.to_dict() for t in tasks], indent=2))

        print("\nBreakdown by Research Connector:")
        for connector in ["web", "github", "rag"]:
            connector_tasks = [t for t in tasks if t.source_type == connector]
            print(f"  [{connector.upper()}] ({len(connector_tasks)} tasks):")
            for t in connector_tasks:
                print(f"    * [{t.priority.upper()}] (Target: {t.target}) {t.question}")
                print(f"      Purpose: {t.purpose}")

    print("\n" + "=" * 70)
    print("Full Pipeline Demo completed successfully.")
    print("=" * 70)


if __name__ == "__main__":
    run_pipeline_demo()