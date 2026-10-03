"""
DEVSCOUT - AI-powered technical research and decision assistant.
Requirement Analyzer demonstration.
"""

import json
from analyzer import RequirementAnalyzer, AnalyzerError


def run_demo():
    print("=" * 60)
    print("DEVSCOUT: Requirement Analyzer Demo")
    print("=" * 60)

    # Sample Request 1: Frontend + Real-time collaboration
    request_1 = """
    I want to build a real-time collaborative whiteboard
    using React and Go. Around 1,000 users, low budget,
    and I prefer open-source technologies.
    """

    # Sample Request 2: Backend + Data Engineering / Distributed Systems
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
    except AnalyzerError as e:
        print(f"[Error initializing analyzer]: {e}")
        return

    for title, request_text in test_requests:
        print(f"\n--- {title} ---")
        print("Raw Request:")
        print(request_text.strip())
        print("\nAnalyzing requirements...")

        try:
            analysis = analyzer.analyze(request_text)
            print("\nValidated Result:")
            print(json.dumps(analysis.to_dict(), indent=2))
        except AnalyzerError as e:
            print(f"[Analysis Failed]: {e}")
            if hasattr(e, "raw_response") and e.raw_response:
                print(f"Raw Response: {e.raw_response}")

    print("\n" + "=" * 60)
    print("Demo completed.")
    print("=" * 60)


if __name__ == "__main__":
    run_demo()