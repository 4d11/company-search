"""Business logic for search operations."""
from typing import List, Optional, Tuple

from sqlalchemy.orm import Session

from backend.db.database import Company
from backend.es.client import es_client
from backend.es.operations import search_companies_with_filters
from backend.llm.query_extractor import extract_query_filters
from backend.llm.query_classifier import get_query_classifier
from backend.llm.portfolio_analyzer import analyze_portfolio_for_complementary_thesis
from backend.llm.thesis_expander import expand_conceptual_thesis
from backend.llm.query_rewriter import rewrite_query_for_search
from backend.llm.explanation_generator import batch_generate_explanations
from backend.logic.filter_merger import merge_filters
from backend.logic.explainer import explain_result
from backend.models.filters import QueryFilters, ExcludedFilterValue

# Feature flag: Set to False to disable thesis expansion for evaluation
ENABLE_THESIS_EXPANSION = False


def search_companies(
    query_text: str,
    db: Session,
    size: int = 10,
    location: Optional[str] = None,
    industries: Optional[List[str]] = None,
    target_markets: Optional[List[str]] = None,
    min_employees: Optional[int] = None,
    max_employees: Optional[int] = None,
    stages: Optional[List[str]] = None,
    min_funding: Optional[int] = None,
    max_funding: Optional[int] = None
) -> List[Company]:
    search_results = es_search_companies(
        es_client,
        query_text=query_text,
        size=size,
        location=location,
        industries=industries,
        target_markets=target_markets,
        min_employees=min_employees,
        max_employees=max_employees,
        stages=stages,
        min_funding=min_funding,
        max_funding=max_funding
    )

    company_ids = [int(hit["_id"]) for hit in search_results]

    companies = []
    if company_ids:
        companies = db.query(Company).filter(Company.id.in_(company_ids)).all()
        company_dict = {company.id: company for company in companies}
        companies = [company_dict[cid] for cid in company_ids if cid in company_dict]

    return companies


def search_companies_with_extraction(
    query_text: Optional[str],
    db: Session,
    user_filters: Optional[QueryFilters] = None,
    excluded_values: List[ExcludedFilterValue] = None,
    size: int = 10,
) -> Tuple[List[Tuple[Company, str]], QueryFilters, Optional[dict]]:
    if excluded_values is None:
        excluded_values = []

    thesis_context = None
    search_query = query_text

    if query_text and query_text.strip():
        classification = get_query_classifier().classify(query_text)

        if classification.classification == "portfolio_analysis":
            portfolio_analysis = analyze_portfolio_for_complementary_thesis(query_text)
            if portfolio_analysis:
                search_query = portfolio_analysis.expanded_query
                thesis_context = {
                    "type": "portfolio",
                    "summary": portfolio_analysis.portfolio_summary,
                    "themes": portfolio_analysis.themes,
                    "gaps": portfolio_analysis.gaps,
                    "complementary_areas": portfolio_analysis.complementary_areas,
                    "strategic_reasoning": portfolio_analysis.strategic_reasoning,
                }

        elif ENABLE_THESIS_EXPANSION and classification.classification == "explicit_search" and classification.is_conceptual:
            thesis_expansion = expand_conceptual_thesis(query_text)
            if thesis_expansion:
                search_query = thesis_expansion.expanded_query
                thesis_context = {
                    "type": "conceptual",
                    "summary": thesis_expansion.thesis_summary,
                    "core_concepts": {
                        "technology": thesis_expansion.core_concepts.technology,
                        "business_model": thesis_expansion.core_concepts.business_model,
                        "industries": thesis_expansion.core_concepts.industries,
                        "use_case": thesis_expansion.core_concepts.use_case,
                    },
                    "strategic_focus": thesis_expansion.strategic_focus,
                }

    if search_query and search_query.strip():
        llm_filters = extract_query_filters(search_query, db, es_client, excluded_values)
    else:
        llm_filters = QueryFilters(logic="AND", filters=[])

    applied_filters = merge_filters(user_filters, llm_filters, excluded_values)

    clean_query = search_query
    if search_query and search_query.strip() and thesis_context is None:
        clean_query = rewrite_query_for_search(search_query, applied_filters)

    search_results = search_companies_with_filters(
        es_client, query_text=clean_query, filters=applied_filters, size=size
    )

    company_scores = {int(hit["_id"]): hit["_score"] for hit in search_results}
    company_ids = list(company_scores.keys())

    companies_with_explanations = []
    if company_ids:
        companies = db.query(Company).filter(Company.id.in_(company_ids)).all()
        company_dict = {company.id: company for company in companies}
        sorted_companies = [company_dict[cid] for cid in company_ids if cid in company_dict]

        try:
            filters_dict = applied_filters.model_dump() if applied_filters else None
            llm_explanations = batch_generate_explanations(sorted_companies, query_text, filters_dict)

            for company in sorted_companies:
                explanation = llm_explanations.get(company.id)
                if not explanation:
                    score = company_scores.get(company.id, 0.0)
                    explanation = explain_result(company, query_text, applied_filters, score, thesis_context)
                companies_with_explanations.append((company, explanation))

        except Exception as e:
            for company in sorted_companies:
                score = company_scores.get(company.id, 0.0)
                explanation = explain_result(company, query_text, applied_filters, score, thesis_context)
                companies_with_explanations.append((company, explanation))

    return companies_with_explanations, applied_filters, thesis_context
