"""
Quick test script for portfolio recommendation queries.

This script tests the enhanced query extraction and rewriting
for portfolio recommendation use cases.
"""
import os
import sys

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from backend.llm.client import get_llm_client
from backend.llm.query_rewriter import rewrite_query_for_search
from backend.models.filters import QueryFilters


def test_query_extraction(query: str):
    """Test filter extraction for a portfolio query."""
    print(f"\n{'='*80}")
    print(f"Query: {query}")
    print(f"{'='*80}")

    # Simulate extraction (would normally use extract_query_filters)
    llm_client = get_llm_client()

    # Read the prompt template
    with open("backend/llm/prompts/query_extraction.txt", "r") as f:
        prompt_template = f.read()

    # Simple test prompt (not using full template system)
    test_prompt = f"""Extract structured filters from this query about companies.

Query: "{query}"

Focus on recognizing portfolio recommendation patterns:
- If query mentions existing investments and asks for recommendations
- Extract COMPLEMENTARY industries (NOT the ones they already own)

Available industries: AI/ML, FinTech, Healthcare IT, E-commerce, Supply Chain Tech, HR Tech, PropTech, EdTech, Real Estate Tech, Enterprise SaaS, Consumer Finance, Tax & Accounting

Return JSON:
{{
    "logic": "AND",
    "filters": [
        {{
            "segment": "industries",
            "type": "text",
            "logic": "OR",
            "rules": [{{"op": "EQ", "value": "Industry Name"}}]
        }}
    ]
}}
"""

    print("\n🔍 Extracting filters...")
    response = llm_client.generate(prompt=test_prompt)
    print(f"Extracted filters: {response}")

    # Test query rewriting
    try:
        filters = QueryFilters(**response)
        print("\n✏️  Rewriting query...")
        clean_query = rewrite_query_for_search(query, filters)
        print(f"Original query: {query}")
        print(f"Rewritten query: {clean_query}")
    except Exception as e:
        print(f"\n❌ Error during rewriting: {e}")


def main():
    """Run tests with sample portfolio recommendation queries."""
    print("\n" + "="*80)
    print("PORTFOLIO RECOMMENDATION QUERY TESTS")
    print("="*80)

    test_queries = [
        "My investments include a consumer credit building app and AI tax prep software. Suggest some strategic additions to my portfolio.",
        "I own FinTech and AI companies. What should I add?",
        "Portfolio has consumer apps and tax software. Recommend additions.",
        "Investments include FinTech startups in San Francisco. Suggest strategic additions.",
    ]

    for query in test_queries:
        try:
            test_query_extraction(query)
        except Exception as e:
            print(f"\n❌ Test failed: {e}")
            import traceback
            traceback.print_exc()

    print("\n" + "="*80)
    print("TESTS COMPLETE")
    print("="*80)


if __name__ == "__main__":
    main()
