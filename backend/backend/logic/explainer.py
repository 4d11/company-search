"""
Explainability logic for search results.
"""
from backend.db.database import Company
from backend.models.filters import FilterType, LogicType, OperatorType, QueryFilters, SegmentFilter


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
    company: Company, query: str, applied_filters: QueryFilters, es_score: float
) -> str:
    """
    Generate a human-readable explanation for why a company was returned.

    Args:
        company: The company result
        query: The original query text
        applied_filters: The filters that were applied
        es_score: The Elasticsearch relevance score

    Returns:
        Human-readable explanation string
    """
    explanations = []

    # Explain filter matches
    filter_explanations = []
    for segment_filter in applied_filters.filters:
        explanation = explain_segment_filter(segment_filter, company)
        if explanation:
            filter_explanations.append(explanation)

    if filter_explanations:
        filters_str = ", ".join(filter_explanations)
        explanations.append(f"Matched filters: {filters_str}")

    # Explain semantic relevance
    # Normalize ES score (script_score returns cosine + 1, so range is 0-2)
    normalized_score = (es_score - 1.0) if es_score > 1.0 else es_score
    normalized_score = max(0.0, min(1.0, normalized_score))  # Clamp to 0-1

    if normalized_score >= 0.8:
        relevance = "very high relevance"
    elif normalized_score >= 0.6:
        relevance = "high relevance"
    elif normalized_score >= 0.4:
        relevance = "moderate relevance"
    else:
        relevance = "some relevance"

    explanations.append(f"Semantic similarity: {normalized_score:.2f} ({relevance} to query)")

    return ". ".join(explanations) + "."
