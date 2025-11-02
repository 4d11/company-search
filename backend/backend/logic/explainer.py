"""
Explainability logic for search results.
"""
from typing import Optional, Tuple, List
from backend.db.database import Company
from backend.models.filters import FilterType, LogicType, OperatorType, QueryFilters, SegmentFilter

# Common stop words to filter out from keyword matching
STOP_WORDS = {
    "a", "an", "and", "are", "as", "at", "be", "by", "for", "from", "has", "he",
    "in", "is", "it", "its", "of", "on", "that", "the", "to", "was", "will", "with",
    "companies", "company", "startup", "startups", "find", "looking", "search", "show"
}


def extract_keywords(text: str, min_length: int = 3) -> List[str]:
    """
    Extract meaningful keywords from text by removing stop words and short words.

    Args:
        text: Text to extract keywords from
        min_length: Minimum word length to consider

    Returns:
        List of lowercase keywords
    """
    if not text:
        return []

    # Tokenize and clean
    words = text.lower().split()
    keywords = []

    for word in words:
        # Remove punctuation
        clean_word = ''.join(c for c in word if c.isalnum())
        # Keep if it's long enough and not a stop word
        if len(clean_word) >= min_length and clean_word not in STOP_WORDS:
            keywords.append(clean_word)

    return keywords


def find_keyword_matches(query: str, company: Company) -> List[str]:
    """
    Find keywords that appear in both the query and company description/attributes.

    Args:
        query: User's search query
        company: Company to match against

    Returns:
        List of matched keywords
    """
    query_keywords = set(extract_keywords(query))

    # Build company text from description, industries, and target markets
    company_text_parts = []
    if company.description:
        company_text_parts.append(company.description)
    if company.industries:
        company_text_parts.extend([ind.name for ind in company.industries])
    if company.target_markets:
        company_text_parts.extend([tm.name for tm in company.target_markets])

    company_text = " ".join(company_text_parts)
    company_keywords = set(extract_keywords(company_text))

    # Find matches
    matches = query_keywords & company_keywords
    return sorted(list(matches))[:5]  # Limit to 5 most relevant


def format_operator(op: OperatorType) -> str:
    """Format operator for human-readable output."""
    mapping = {
        OperatorType.EQ: "=",
        OperatorType.NEQ: "≠",
        OperatorType.GT: ">",
        OperatorType.GTE: ">=",
        OperatorType.LT: "<",
        OperatorType.LTE: "<=",
    }
    return mapping.get(op, str(op))


def format_value(value, segment: str) -> str:
    """Format value for display."""
    if segment == "funding_amount":
        # Format as currency
        if value >= 1000000:
            return f"${value / 1000000:.1f}M"
        elif value >= 1000:
            return f"${value / 1000:.1f}K"
        else:
            return f"${value}"
    return str(value)


def explain_segment_filter(segment_filter: SegmentFilter, company: Company) -> str:
    """
    Explain how a company matches a segment filter.

    Args:
        segment_filter: The filter to explain
        company: The company to check against

    Returns:
        Human-readable explanation string, or None if doesn't match
    """
    segment = segment_filter.segment
    rules = segment_filter.rules
    logic = segment_filter.logic

    # Get company's value for this segment
    company_value = None
    if segment == "location":
        company_value = company.location.city if company.location else None
    elif segment == "industries":
        company_value = [ind.name for ind in company.industries]
    elif segment == "target_markets":
        company_value = [tm.name for tm in company.target_markets]
    elif segment == "funding_stage":
        company_value = company.funding_stage.name if company.funding_stage else None
    elif segment == "employee_count":
        company_value = company.employee_count
    elif segment == "funding_amount":
        company_value = company.funding_amount
    elif segment == "stage_order":
        company_value = (
            company.funding_stage.order_index if company.funding_stage else None
        )

    if company_value is None:
        return None

    # Check each rule
    matched_rules = []
    for rule in rules:
        op = rule.op
        filter_value = rule.value
        matches = False

        if segment_filter.type == FilterType.TEXT:
            # Handle text matching
            if isinstance(company_value, list):
                # Multi-value field (industries, target_markets)
                if op == OperatorType.EQ:
                    matches = filter_value in company_value
                elif op == OperatorType.NEQ:
                    matches = filter_value not in company_value
            else:
                # Single value field (location, funding_stage)
                if op == OperatorType.EQ:
                    matches = company_value == filter_value
                elif op == OperatorType.NEQ:
                    matches = company_value != filter_value

        elif segment_filter.type == FilterType.NUMERIC:
            # Handle numeric matching
            if op == OperatorType.EQ:
                matches = company_value == filter_value
            elif op == OperatorType.NEQ:
                matches = company_value != filter_value
            elif op == OperatorType.GT:
                matches = company_value > filter_value
            elif op == OperatorType.GTE:
                matches = company_value >= filter_value
            elif op == OperatorType.LT:
                matches = company_value < filter_value
            elif op == OperatorType.LTE:
                matches = company_value <= filter_value

        if matches:
            formatted_val = format_value(filter_value, segment)
            matched_rules.append(f"{format_operator(op)} {formatted_val}")

    if not matched_rules:
        return None

    # Build explanation based on logic
    rule_str = (
        f" {logic.value.lower()} ".join(matched_rules)
        if len(matched_rules) > 1
        else matched_rules[0]
    )
    return f"{segment} {rule_str}"


def explain_result(
    company: Company,
    query: str,
    applied_filters: QueryFilters,
    es_score: float,
    thesis_context: Optional[dict] = None,
) -> str:
    """
    Generate a human-readable explanation for why a company was returned.

    Args:
        company: The company result
        query: The original query text
        applied_filters: The filters that were applied
        es_score: The Elasticsearch relevance score
        thesis_context: Optional thesis context for strategic fit explanation

    Returns:
        Human-readable explanation string
    """
    explanations = []

    # Add strategic fit explanation first (if thesis query)
    if thesis_context:
        strategic_explanation = explain_thesis_fit(company, thesis_context)
        if strategic_explanation:
            explanations.append(strategic_explanation)

    # Explain filter matches
    filter_explanations = []
    for segment_filter in applied_filters.filters:
        explanation = explain_segment_filter(segment_filter, company)
        if explanation:
            filter_explanations.append(explanation)

    if filter_explanations:
        filters_str = ", ".join(filter_explanations)
        explanations.append(f"Matched filters: {filters_str}")

    # Find and show keyword matches
    keyword_matches = find_keyword_matches(query, company)
    if keyword_matches:
        explanations.append(f"Matches keywords: {', '.join(keyword_matches)}")


    # Explain semantic relevance with simple message based on score
    # Normalize ES score (script_score returns cosine + 1, so range is 0-2)
    normalized_score = (es_score - 1.0) if es_score > 1.0 else es_score
    normalized_score = max(0.0, min(1.0, normalized_score))  # Clamp to 0-1
    normalized_score_percent = int(normalized_score * 100)

    if normalized_score_percent >= 75:
        relevance_msg = "High relevance with your query"
    elif normalized_score_percent >= 35:
        relevance_msg = "Good relevance with your query"
    else:
        relevance_msg = "Some relevance with your query"

    explanations.append(relevance_msg)

    return ". ".join(explanations) + "."


def explain_thesis_fit(company: Company, thesis_context: dict) -> Optional[str]:
    """
    Generate strategic fit explanation for thesis-based queries.

    Args:
        company: The company to explain
        thesis_context: Thesis context from portfolio analysis or thesis expansion

    Returns:
        Strategic fit explanation string, or None if not applicable
    """
    if not thesis_context:
        return None

    thesis_type = thesis_context.get("type")

    if thesis_type == "portfolio":
        # Portfolio thesis: explain complementary fit
        strategic_reasoning = thesis_context.get("strategic_reasoning", "")
        complementary_areas = thesis_context.get("complementary_areas", [])

        # Check which complementary area this company matches
        company_industries = [ind.name.lower() for ind in company.industries]
        company_desc = company.description.lower() if company.description else ""

        # Simple keyword matching to identify which complementary area matches
        matched_area = None
        for area in complementary_areas:
            area_lower = area.lower()
            # Check if any keywords from area appear in company industries/description
            area_keywords = [w for w in area_lower.split() if len(w) > 3]
            if any(keyword in company_desc for keyword in area_keywords[:3]):
                matched_area = area
                break

        if matched_area:
            return f"Strategic fit: {matched_area}. {strategic_reasoning}"
        else:
            return f"Strategic fit: {strategic_reasoning}"

    elif thesis_type == "conceptual":
        # Conceptual thesis: explain how company fits the thesis
        core_concepts = thesis_context.get("core_concepts", {})
        industries = core_concepts.get("industries", [])
        technology = core_concepts.get("technology", [])
        business_model = core_concepts.get("business_model", [])

        # Check which thesis concepts match this specific company
        company_industries = [ind.name.lower() for ind in company.industries]
        matched_industries = [
            ind for ind in industries if any(ci in ind.lower() or ind.lower() in ci for ci in company_industries)
        ]

        # Build company-specific explanation
        matches = []
        if matched_industries:
            matches.append(f"{', '.join(matched_industries[:2])} focus")

        # Check technology matches in description
        if technology and company.description:
            desc_lower = company.description.lower()
            matched_tech = [tech for tech in technology if tech.lower() in desc_lower]
            if matched_tech:
                matches.append(f"{matched_tech[0]} technology")

        # Check business model matches
        if business_model and company.business_models:
            company_bm = [bm.name.lower() for bm in company.business_models]
            matched_bm = [bm for bm in business_model if bm.lower() in company_bm]
            if matched_bm:
                matches.append(f"{matched_bm[0]} model")

        if matches:
            return f"Thesis fit: {', '.join(matches)}"
        else:
            # Fallback - just show they match the thesis
            return None

    return None
