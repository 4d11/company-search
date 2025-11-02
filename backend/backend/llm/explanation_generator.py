"""
LLM-based explanation generator for search results.

Generates natural language explanations for why companies match search queries.
Uses batch processing for efficiency (one LLM call for multiple companies).
Includes in-memory caching for better performance on similar queries.
"""
from typing import List, Dict, Optional
import json
from backend.db.database import Company
from backend.llm.client import get_llm_client
from backend.llm.explanation_cache import get_explanation_cache


def batch_generate_explanations(
    companies: List[Company],
    query: str,
    applied_filters: Optional[dict] = None,
    use_cache: bool = True,
) -> Dict[int, str]:
    """
    Generate explanations for multiple companies in one batch LLM call.

    Uses in-memory cache to avoid regenerating explanations for the same
    (company, query) pairs. Particularly useful when users slightly modify
    their searches.

    Args:
        companies: List of Company objects to explain
        query: Original user query
        applied_filters: Extracted filters that were applied (optional)
        use_cache: Whether to use cache (default True)

    Returns:
        Dict mapping company_id -> explanation string
    """
    if not companies:
        return {}

    cache = get_explanation_cache()

    # Step 1: Check cache for all companies
    cached_explanations = {}
    companies_to_generate = []

    if use_cache:
        cached_explanations = cache.get_batch(
            [c.id for c in companies],
            query
        )

        # Filter out companies we already have cached
        companies_to_generate = [
            c for c in companies
            if c.id not in cached_explanations
        ]

        if cached_explanations:
            print(f"Cache hit: {len(cached_explanations)}/{len(companies)} explanations")
    else:
        companies_to_generate = companies

    # Step 2: If all explanations are cached, return early
    if not companies_to_generate:
        return cached_explanations

    # Step 3: Generate explanations for cache misses
    print(f"Generating {len(companies_to_generate)} new explanations via LLM")

    # Build company data for prompt (only for companies we need to generate)
    company_data = []
    for company in companies_to_generate:
        # Extract related data
        industries = [i.name for i in company.industries] if company.industries else []
        target_markets = [tm.name for tm in company.target_markets] if company.target_markets else []
        business_models = [bm.name for bm in company.business_models] if hasattr(company, 'business_models') and company.business_models else []
        revenue_models = [rm.name for rm in company.revenue_models] if hasattr(company, 'revenue_models') and company.revenue_models else []

        company_data.append({
            "id": company.id,
            "name": company.company_name,
            "description": company.description or "No description available",
            "industries": industries,
            "target_markets": target_markets,
            "business_models": business_models,
            "revenue_models": revenue_models,
            "location": company.location.city if company.location else None,
            "stage": company.funding_stage.name if company.funding_stage else None,
            "funding_amount": company.funding_amount,
            "employee_count": company.employee_count,
        })

    # Build filter summary for context
    filter_summary = _build_filter_summary(applied_filters) if applied_filters else "No specific filters applied"

    # Create prompt
    prompt = f"""You are an investment analyst explaining search results to a venture capitalist.

USER QUERY: "{query}"

APPLIED FILTERS: {filter_summary}

COMPANIES TO EXPLAIN (as JSON):
{json.dumps(company_data, indent=2)}

For EACH company, write a concise 2-3 sentence explanation of WHY it matches the query.

Your explanation should:
1. Briefly describe what the company does (1 sentence)
2. Explain how it connects to the user's query (1-2 sentences)
3. Be specific - reference actual query terms, filters, or context
4. Include relevant market context if applicable (market size, complexity, growth potential)
5. For portfolio/thesis queries: highlight technology adjacencies or complementary capabilities

IMPORTANT FORMAT RULES:
- Start directly with the explanation (no preamble like "This company...")
- Be concise but informative (2-3 sentences max)
- Reference specific query terms or filters when relevant
- Use concrete details (technology, market, stage, etc.)

Return ONLY a JSON array in this exact format:
[
  {{"company_id": 1, "explanation": "your explanation here"}},
  {{"company_id": 2, "explanation": "your explanation here"}}
]

Return ONLY valid JSON, no other text."""

    try:
        # Call LLM API (returns parsed JSON)
        client = get_llm_client()
        result = client.generate(prompt=prompt)

        # LLMClient already parses JSON, result should be a list or dict
        explanations_list = None

        if isinstance(result, list):
            # Got the expected array format
            explanations_list = result
        elif isinstance(result, dict):
            # Check if wrapped in a key
            if 'explanations' in result:
                explanations_list = result['explanations']
            elif 'companies' in result:
                explanations_list = result['companies']
            else:
                # Single company case, wrap in list
                explanations_list = [result]

        if not explanations_list:
            print("LLM returned unexpected format")
            # Return cached explanations only
            return cached_explanations

        # Convert to dict mapping company_id -> explanation
        new_explanations = {
            item["company_id"]: item["explanation"]
            for item in explanations_list
            if "company_id" in item and "explanation" in item
        }

        # Step 4: Cache newly generated explanations
        if use_cache and new_explanations:
            cache.set_batch(new_explanations, query)

        # Step 5: Combine cached + newly generated explanations
        all_explanations = {**cached_explanations, **new_explanations}

        return all_explanations

    except Exception as e:
        print(f"Error generating batch explanations: {e}")
        import traceback
        traceback.print_exc()
        # Return cached explanations if available, otherwise empty
        return cached_explanations


def _build_filter_summary(applied_filters: dict) -> str:
    """
    Build human-readable summary of applied filters.

    Args:
        applied_filters: QueryFilters object as dict

    Returns:
        Human-readable string summarizing filters
    """
    if not applied_filters or not applied_filters.get("filters"):
        return "No specific filters applied"

    filter_parts = []

    for segment_filter in applied_filters.get("filters", []):
        segment = segment_filter.get("segment", "")
        rules = segment_filter.get("rules", [])

        if not rules:
            continue

        # Extract values from rules
        values = [str(rule.get("value", "")) for rule in rules]

        if segment == "location":
            filter_parts.append(f"Location: {', '.join(values)}")
        elif segment == "industries":
            filter_parts.append(f"Industries: {', '.join(values)}")
        elif segment == "target_markets":
            filter_parts.append(f"Target Markets: {', '.join(values)}")
        elif segment == "funding_stage":
            filter_parts.append(f"Stage: {', '.join(values)}")
        elif segment == "business_models":
            filter_parts.append(f"Business Models: {', '.join(values)}")
        elif segment == "revenue_models":
            filter_parts.append(f"Revenue Models: {', '.join(values)}")
        elif segment == "employee_count":
            # Format range
            min_emp = next((r["value"] for r in rules if r.get("op") in ["GTE", "GT"]), None)
            max_emp = next((r["value"] for r in rules if r.get("op") in ["LTE", "LT"]), None)
            if min_emp and max_emp:
                filter_parts.append(f"Employees: {min_emp}-{max_emp}")
            elif min_emp:
                filter_parts.append(f"Employees: {min_emp}+")
            elif max_emp:
                filter_parts.append(f"Employees: <{max_emp}")
        elif segment == "funding_amount":
            # Format range
            min_fund = next((r["value"] for r in rules if r.get("op") in ["GTE", "GT"]), None)
            max_fund = next((r["value"] for r in rules if r.get("op") in ["LTE", "LT"]), None)
            if min_fund and max_fund:
                filter_parts.append(f"Funding: ${min_fund/1e6:.1f}M-${max_fund/1e6:.1f}M")
            elif min_fund:
                filter_parts.append(f"Funding: >${min_fund/1e6:.1f}M")
            elif max_fund:
                filter_parts.append(f"Funding: <${max_fund/1e6:.1f}M")

    return "; ".join(filter_parts) if filter_parts else "No specific filters applied"
