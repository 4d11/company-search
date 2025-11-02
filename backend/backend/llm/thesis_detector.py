"""
Thesis detection for search queries.

Determines whether a query is a simple search or requires thesis-based analysis.
"""
from enum import Enum


class QueryType(Enum):
    """Types of search queries."""
    SIMPLE_SEARCH = "simple_search"
    PORTFOLIO_THESIS = "portfolio_thesis"
    CONCEPTUAL_THESIS = "conceptual_thesis"


# Keywords that indicate portfolio-based thesis queries
PORTFOLIO_KEYWORDS = [
    "portfolio",
    "investments",
    "invested in",
    "holdings",
    "my companies",
    "complement",
    "strategic additions",
    "diversify",
    "prior investments",
]

# Keywords that indicate conceptual thesis queries
CONCEPTUAL_KEYWORDS = [
    "api-first",
    "emerging",
    "optimize",
    "revolutionize",
    "transform",
    "disrupt",
    "next-generation",
    "cutting-edge",
    "innovative approach",
    "strategic thesis",
]

# Patterns that suggest complex conceptual queries
CONCEPTUAL_PATTERNS = [
    " for ",  # "AI for hospital billing"
    " to ",   # "AI to optimize X"
    "-driven",  # "data-driven", "AI-driven"
    "-first",   # "API-first", "mobile-first"
    "-powered", # "AI-powered"
]


def detect_query_type(query: str) -> QueryType:
    """
    Detect whether a query is simple, portfolio-based, or conceptual thesis.

    Args:
        query: The user's search query

    Returns:
        QueryType enum indicating the query type

    Examples:
        "fintech companies in Toronto" → SIMPLE_SEARCH
        "My investments include consumer credit. Suggest additions" → PORTFOLIO_THESIS
        "API-first vertical SaaS for regulated industries" → CONCEPTUAL_THESIS
    """
    if not query or not query.strip():
        return QueryType.SIMPLE_SEARCH

    query_lower = query.lower()

    # Check for portfolio keywords (highest priority)
    for keyword in PORTFOLIO_KEYWORDS:
        if keyword in query_lower:
            return QueryType.PORTFOLIO_THESIS

    # Check for conceptual thesis indicators
    conceptual_score = 0

    # Check conceptual keywords
    for keyword in CONCEPTUAL_KEYWORDS:
        if keyword in query_lower:
            conceptual_score += 1

    # Check conceptual patterns
    for pattern in CONCEPTUAL_PATTERNS:
        if pattern in query_lower:
            conceptual_score += 1

    # Check for multiple complex terms (3+ words with capital letters or hyphens)
    words = query.split()
    complex_terms = [w for w in words if "-" in w or (len(w) > 3 and any(c.isupper() for c in w[1:]))]
    if len(complex_terms) >= 2:
        conceptual_score += 1

    # If conceptual score is high enough, classify as conceptual thesis
    if conceptual_score >= 2:
        return QueryType.CONCEPTUAL_THESIS

    # Otherwise, it's a simple search
    return QueryType.SIMPLE_SEARCH


def is_thesis_query(query: str) -> bool:
    """
    Quick check if a query requires thesis-based processing.

    Args:
        query: The user's search query

    Returns:
        True if query is portfolio or conceptual thesis, False otherwise
    """
    query_type = detect_query_type(query)
    return query_type in [QueryType.PORTFOLIO_THESIS, QueryType.CONCEPTUAL_THESIS]
