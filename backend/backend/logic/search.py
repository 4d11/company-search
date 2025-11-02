"""
Business logic for search operations.
"""
from typing import List, Optional, Tuple
from sqlalchemy.orm import Session

from backend.db.database import Company
from backend.es.client import es_client
from backend.es.operations import search_companies_with_filters
from backend.llm.query_extractor import extract_query_filters
from backend.llm.thesis_detector import QueryType, detect_query_type
from backend.llm.portfolio_analyzer import analyze_portfolio_for_complementary_thesis
from backend.llm.thesis_expander import expand_conceptual_thesis
from backend.llm.explanation_generator import batch_generate_explanations
from backend.logic.filter_merger import merge_filters
from backend.logic.explainer import explain_result
from backend.models.filters import QueryFilters, ExcludedFilterValue


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
    min_stage_order: Optional[int] = None,
    max_stage_order: Optional[int] = None,
    min_funding: Optional[int] = None,
    max_funding: Optional[int] = None
) -> List[Company]:
    """
    Search for companies based on query text with optional filters.
    Uses Elasticsearch for vector search, then fetches full details from PostgreSQL.

    Args:
        query_text: The search query text
        db: Database session
        size: Number of results to return
        location: Optional city filter
        industries: Optional list of industries to filter by
        target_markets: Optional list of target markets to filter by
        min_employees: Optional minimum employee count
        max_employees: Optional maximum employee count
        stages: Optional list of funding stages to filter by (exact match)
        min_stage_order: Optional minimum stage order (for range queries)
        max_stage_order: Optional maximum stage order (for range queries)
        min_funding: Optional minimum funding amount
        max_funding: Optional maximum funding amount

    Returns:
        List of Company objects sorted by relevance
    """
    # Perform vector search in Elasticsearch with filters
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
        min_stage_order=min_stage_order,
        max_stage_order=max_stage_order,
        min_funding=min_funding,
        max_funding=max_funding
    )

    # Extract company IDs from search results
    company_ids = [int(hit["_id"]) for hit in search_results]

    # Fetch full company details from PostgreSQL
    companies = []
    if company_ids:
        companies = db.query(Company).filter(Company.id.in_(company_ids)).all()

        # Sort companies to match the order from Elasticsearch results
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
    """
    Search for companies with optional LLM extraction and explainability.

    Steps:
    0. Detect query type (simple, portfolio thesis, conceptual thesis)
    1. If thesis query: expand/analyze to get strategic search query
    2. Extract filters from query using LLM (if query provided)
    3. Merge user filters with LLM filters (user overrides)
    4. Perform search with merged filters and thesis-expanded query
    5. Generate explanations for each result
    6. Return companies with explanations, applied filters, and thesis context

    Args:
        query_text: Optional natural language query (if None, only uses user_filters)
        db: Database session
        user_filters: Optional filters provided by user
        excluded_values: Filter values to exclude from extraction (segment, op, value tuples)
        size: Number of results to return

    Returns:
        Tuple of:
        - List of (Company, explanation) tuples
        - Applied filters (merged result)
        - Thesis context (if thesis query, None otherwise)
    """
    if excluded_values is None:
        excluded_values = []

    thesis_context = None
    search_query = query_text

    # Step 0: Detect query type and handle thesis queries
    if query_text and query_text.strip():
        query_type = detect_query_type(query_text)
        print(f"Detected query type: {query_type.value}")

        if query_type == QueryType.PORTFOLIO_THESIS:
            # Analyze portfolio and generate complementary search
            print("Analyzing portfolio for complementary thesis...")
            portfolio_analysis = analyze_portfolio_for_complementary_thesis(query_text)

            if portfolio_analysis:
                # Use expanded query for search
                search_query = portfolio_analysis.expanded_query
                thesis_context = {
                    "type": "portfolio",
                    "summary": portfolio_analysis.portfolio_summary,
                    "themes": portfolio_analysis.themes,
                    "gaps": portfolio_analysis.gaps,
                    "complementary_areas": portfolio_analysis.complementary_areas,
                    "strategic_reasoning": portfolio_analysis.strategic_reasoning,
                }
                print(f"Using thesis-expanded query: {search_query}")

        elif query_type == QueryType.CONCEPTUAL_THESIS:
            # Expand conceptual thesis into concrete terms
            print("Expanding conceptual thesis...")
            thesis_expansion = expand_conceptual_thesis(query_text)

            if thesis_expansion:
                # Use expanded query for search
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
                print(f"Using thesis-expanded query: {search_query}")

    # Step 1: Extract filters from query using LLM (skip if no query provided)
    if search_query and search_query.strip():
        llm_filters = extract_query_filters(search_query, db, es_client, excluded_values)
    else:
        # No query provided - use empty filters (only user filters will be applied)
        llm_filters = QueryFilters(logic="AND", filters=[])

    # Step 2: Merge user filters with LLM filters (user overrides)
    applied_filters = merge_filters(user_filters, llm_filters, excluded_values)

    # Step 2.5: For non-thesis queries, rewrite query for cleaner vector search
    # (Thesis queries are already expanded/cleaned, so skip rewriting)
    clean_query = search_query
    if search_query and search_query.strip() and thesis_context is None:
        from backend.llm.query_rewriter import rewrite_query_for_search
        clean_query = rewrite_query_for_search(search_query, applied_filters)

    # Step 3: Perform vector search with merged filters (using cleaned/expanded query)
    search_results = search_companies_with_filters(
        es_client, query_text=clean_query, filters=applied_filters, size=size
    )

    # Extract company IDs and scores from search results
    company_scores = {int(hit["_id"]): hit["_score"] for hit in search_results}
    company_ids = list(company_scores.keys())

    # Step 4: Fetch full company details from PostgreSQL
    companies_with_explanations = []
    if company_ids:
        companies = db.query(Company).filter(Company.id.in_(company_ids)).all()

        # Sort companies to match Elasticsearch order
        company_dict = {company.id: company for company in companies}
        sorted_companies = [
            company_dict[cid] for cid in company_ids if cid in company_dict
        ]

        # Step 5: Generate explanations using batch LLM call
        try:
            # Convert applied_filters to dict for LLM prompt
            filters_dict = applied_filters.dict() if applied_filters else None

            # Batch generate LLM explanations for all companies at once
            llm_explanations = batch_generate_explanations(
                sorted_companies, query_text, filters_dict
            )

            # Map explanations to companies
            for company in sorted_companies:
                explanation = llm_explanations.get(company.id)

                # Fallback to rule-based explanation if LLM failed
                if not explanation:
                    score = company_scores.get(company.id, 0.0)
                    explanation = explain_result(
                        company, query_text, applied_filters, score, thesis_context
                    )

                companies_with_explanations.append((company, explanation))

        except Exception as e:
            print(f"Error in batch explanation generation, falling back to rule-based: {e}")
            # Fallback to rule-based explanations
            for company in sorted_companies:
                score = company_scores.get(company.id, 0.0)
                explanation = explain_result(
                    company, query_text, applied_filters, score, thesis_context
                )
                companies_with_explanations.append((company, explanation))

    return companies_with_explanations, applied_filters, thesis_context
