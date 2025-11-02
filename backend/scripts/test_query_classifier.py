"""
Quick test script for the query classifier.
Run this from the backend directory: poetry run python scripts/test_query_classifier.py
"""
from backend.llm.query_classifier import get_query_classifier


def test_classifier():
    """Test the query classifier with sample queries."""
    classifier = get_query_classifier()

    test_cases = [
        # Explicit search - simple
        ("fintech startups in New York", "explicit_search", False),
        ("AI companies with Series A funding", "explicit_search", False),
        ("show me healthcare companies in SF", "explicit_search", False),
        ("B2B SaaS companies in Austin", "explicit_search", False),

        # Explicit search - conceptual
        ("API-first vertical SaaS for regulated industries", "explicit_search", True),
        ("companies using AI to revolutionize hospital billing", "explicit_search", True),
        ("emerging trends in climate tech", "explicit_search", True),
        ("next-generation infrastructure to optimize supply chains", "explicit_search", True),
        ("AI-driven platforms disrupting healthcare", "explicit_search", True),

        # Portfolio analysis
        ("My prior investments include consumer credit and AI tax prep. Suggest additions.", "portfolio_analysis", False),
        ("I've invested in logistics companies, what's adjacent?", "portfolio_analysis", False),
        ("My portfolio has fintech companies, recommend some complementary investments", "portfolio_analysis", False),
    ]

    print("=" * 80)
    print("QUERY CLASSIFIER TEST (LLM-Based)")
    print("=" * 80)
    print()

    all_passed = True
    passed = 0
    failed = 0

    for query, expected_class, expected_conceptual in test_cases:
        try:
            result = classifier.classify(query)

            class_match = result.classification == expected_class
            conceptual_match = result.is_conceptual == expected_conceptual

            test_passed = class_match and conceptual_match
            status = "✓" if test_passed else "✗"

            if test_passed:
                passed += 1
            else:
                failed += 1
                all_passed = False

            print(f"{status} Query: {query[:60]}...")
            print(f"  Classification: {result.classification} (expected: {expected_class})")
            print(f"  Conceptual: {result.is_conceptual} (expected: {expected_conceptual})")
            print(f"  Confidence: {result.confidence:.2f}")
            print(f"  Reasoning: {result.reasoning}")
            print()

        except Exception as e:
            print(f"✗ Query: {query[:60]}...")
            print(f"  ERROR: {e}")
            print()
            failed += 1
            all_passed = False

    print("=" * 80)
    print(f"Results: {passed}/{passed+failed} tests passed")
    if all_passed:
        print("✓ ALL TESTS PASSED")
    else:
        print(f"✗ {failed} TESTS FAILED")
    print("=" * 80)


if __name__ == "__main__":
    test_classifier()
