"""
Query rewriting for cleaner vector search.

Removes meta-instructions and portfolio context from queries,
focusing on the actual search intent for semantic matching.
"""
from typing import Optional

from backend.llm.client import get_llm_client
from backend.llm.schemas import QueryRewriteResponse
from backend.models.filters import QueryFilters


def rewrite_query_for_search(query_text: str, extracted_filters: Optional[QueryFilters] = None) -> str:
    """
    Rewrite query to remove meta-text and focus on search intent.

    This improves vector search quality by removing pollution from:
    - Portfolio context ("my investments include...")
    - Meta-instructions ("suggest additions", "recommend")
    - User framing ("to my portfolio")

    Examples:
        "investments include consumer credit. Suggest additions to my portfolio"
        → "healthcare technology, e-commerce platforms, supply chain software"

        "I own FinTech companies in SF. What should I add?"
        → "healthcare IT, enterprise SaaS, e-commerce infrastructure"

        "AI companies in San Francisco with Series A funding"
        → "artificial intelligence, machine learning companies" (no rewriting needed)

    Args:
        query_text: Original user query
        extracted_filters: Optional filters extracted from the query (used for context)

    Returns:
        Cleaned query text focused on search terms
    """
    if not query_text or not query_text.strip():
        return query_text

    # Build filter summary for context
    filter_summary = ""
    if extracted_filters and extracted_filters.filters:
        filter_parts = []
        for segment_filter in extracted_filters.filters:
            if segment_filter.rules:
                values = [rule.value for rule in segment_filter.rules]
                filter_parts.append(f"{segment_filter.segment}: {', '.join(str(v) for v in values)}")
        if filter_parts:
            filter_summary = "\n".join(filter_parts)

    system_message = """You are rewriting a search query to improve semantic matching quality.

Task: Rewrite the query to contain ONLY the relevant search terms for semantic matching.

Remove:
- Portfolio context ("my investments", "I own", "current holdings")
- Meta-instructions ("suggest", "recommend", "what should I add")
- User framing ("to my portfolio", "strategic additions")

Keep/Add:
- Industry terms and sectors to search for
- Technology keywords
- Business model descriptors
- If filters were extracted, focus on those industries/sectors

Examples:
- "investments include consumer credit. Suggest additions" → "healthcare technology, e-commerce platforms, enterprise software"
- "I own FinTech. What should I add?" → "healthcare IT, supply chain technology, e-commerce infrastructure"
- "AI companies in SF" → "artificial intelligence, machine learning" (minimal change)

Return the rewritten query text as a JSON object:
{"rewritten_query": "your rewritten query here"}
"""

    user_message = f"""Original query: "{query_text}"

{f'Extracted filters:{chr(10)}{filter_summary}' if filter_summary else 'No filters extracted.'}"""

    llm_client = get_llm_client()
    response = llm_client.generate(
        response_model=QueryRewriteResponse,
        system_message=system_message,
        user_message=user_message
    )

    # Fallback: if rewriting failed or returned empty, use original
    if not response.rewritten_query or not response.rewritten_query.strip():
        return query_text

    return response.rewritten_query.strip()
