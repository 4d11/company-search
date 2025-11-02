"""LLM-based explanation generator for search results."""
from typing import List, Dict, Optional
import json
import logging
from pathlib import Path

from backend.db.database import Company
from backend.llm.client import get_llm_client
from backend.llm.explanation_cache import get_explanation_cache

logger = logging.getLogger(__name__)

PROMPTS_DIR = Path(__file__).parent / "prompts"
EXPLANATION_PROMPT = (PROMPTS_DIR / "explanation_generation.txt").read_text()


def batch_generate_explanations(
    companies: List[Company],
    query: str,
    applied_filters: Optional[dict] = None,
    use_cache: bool = True,
) -> Dict[int, str]:
    if not companies:
        return {}

    cache = get_explanation_cache()
    cached_explanations = {}
    companies_to_generate = []

    if use_cache:
        cached_explanations = cache.get_batch([c.id for c in companies], query)
        companies_to_generate = [c for c in companies if c.id not in cached_explanations]
    else:
        companies_to_generate = companies

    if not companies_to_generate:
        return cached_explanations

    company_data = []
    for company in companies_to_generate:
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

    filter_summary = _build_filter_summary(applied_filters) if applied_filters else "No specific filters applied"
    prompt = EXPLANATION_PROMPT.format(
        query=query,
        filter_summary=filter_summary,
        company_data=json.dumps(company_data, indent=2)
    )

    try:
        client = get_llm_client()
        result = client.generate_raw(
            system_message="You are an investment analyst. Respond with valid JSON only.",
            user_message=prompt
        )

        explanations_list = None

        if isinstance(result, list):
            explanations_list = result
        elif isinstance(result, dict):
            if 'explanations' in result:
                explanations_list = result['explanations']
            elif 'companies' in result:
                explanations_list = result['companies']
            else:
                explanations_list = [result]

        if not explanations_list:
            return cached_explanations

        new_explanations = {
            item["company_id"]: item["explanation"]
            for item in explanations_list
            if "company_id" in item and "explanation" in item
        }

        if use_cache and new_explanations:
            cache.set_batch(new_explanations, query)

        return {**cached_explanations, **new_explanations}

    except Exception as e:
        logger.error(f"Error generating explanations: {e}")
        return cached_explanations


def _build_filter_summary(applied_filters: dict) -> str:
    if not applied_filters or not applied_filters.get("filters"):
        return "No specific filters applied"

    filter_parts = []
    for segment_filter in applied_filters.get("filters", []):
        segment = segment_filter.get("segment", "")
        rules = segment_filter.get("rules", [])

        if not rules:
            continue

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
            min_emp = next((r["value"] for r in rules if r.get("op") in ["GTE", "GT"]), None)
            max_emp = next((r["value"] for r in rules if r.get("op") in ["LTE", "LT"]), None)
            if min_emp and max_emp:
                filter_parts.append(f"Employees: {min_emp}-{max_emp}")
            elif min_emp:
                filter_parts.append(f"Employees: {min_emp}+")
            elif max_emp:
                filter_parts.append(f"Employees: <{max_emp}")
        elif segment == "funding_amount":
            min_fund = next((r["value"] for r in rules if r.get("op") in ["GTE", "GT"]), None)
            max_fund = next((r["value"] for r in rules if r.get("op") in ["LTE", "LT"]), None)
            if min_fund and max_fund:
                filter_parts.append(f"Funding: ${min_fund/1e6:.1f}M-${max_fund/1e6:.1f}M")
            elif min_fund:
                filter_parts.append(f"Funding: >${min_fund/1e6:.1f}M")
            elif max_fund:
                filter_parts.append(f"Funding: <${max_fund/1e6:.1f}M")

    return "; ".join(filter_parts) if filter_parts else "No specific filters applied"
