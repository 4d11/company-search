"""
Test script for thesis-based search queries.
"""
import requests
import json


def test_query(query_text, description):
    """Test a query and print results."""
    print("\n" + "=" * 80)
    print(f"TEST: {description}")
    print("=" * 80)
    print(f"Query: {query_text}\n")

    response = requests.post(
        "http://localhost:8000/api/submit-query",
        json={"query": query_text}
    )

    if response.status_code != 200:
        print(f"Error: {response.status_code}")
        print(response.text)
        return

    data = response.json()

    # Print thesis context if present
    if data.get("thesis_context"):
        print("THESIS CONTEXT:")
        thesis = data["thesis_context"]
        print(f"  Type: {thesis.get('type')}")

        if thesis.get('type') == 'portfolio':
            print(f"  Summary: {thesis.get('summary')}")
            print(f"  Themes: {', '.join(thesis.get('themes', []))}")
            print(f"  Gaps: {', '.join(thesis.get('gaps', []))}")
            print(f"  Complementary Areas:")
            for area in thesis.get('complementary_areas', []):
                print(f"    - {area}")
            print(f"  Strategic Reasoning: {thesis.get('strategic_reasoning')}")

        elif thesis.get('type') == 'conceptual':
            print(f"  Summary: {thesis.get('summary')}")
            core = thesis.get('core_concepts', {})
            print(f"  Technology: {', '.join(core.get('technology', []))}")
            print(f"  Industries: {', '.join(core.get('industries', []))}")
            print(f"  Strategic Focus: {thesis.get('strategic_focus')}")

        print()

    # Print top 3 results
    companies = data.get("companies", [])
    print(f"RESULTS ({len(companies)} companies):\n")

    for i, company in enumerate(companies[:3], 1):
        print(f"{i}. {company['company_name']}")
        print(f"   Industries: {', '.join(company.get('industries', []))}")
        if company.get('explanation'):
            print(f"   Explanation: {company['explanation']}")
        print()


if __name__ == "__main__":
    # Test 1: Portfolio-based thesis query
    test_query(
        "My prior investments include a consumer credit building app and AI tax prep software. Suggest some strategic additions to my portfolio.",
        "Portfolio Thesis Query"
    )

    # Test 2: Conceptual thesis query
    test_query(
        "API-first vertical SaaS for regulated industries",
        "Conceptual Thesis Query"
    )

    # Test 3: Another conceptual thesis
    test_query(
        "AI to optimize hospital billing",
        "Specific Use Case Thesis"
    )

    # Test 4: Simple search (should NOT trigger thesis mode)
    test_query(
        "fintech companies in New York",
        "Simple Search (Non-Thesis)"
    )
