"""
Business logic for search operations.
"""
from typing import List, Optional, Tuple
from sqlalchemy.orm import Session

from backend.db.database import Company
from backend.es.client import es_client
from backend.es.operations import search_companies_with_filters
from backend.llm.query_extractor import extract_query_filters
from backend.logic.filter_merger import merge_filters
from backend.logic.explainer import explain_result
from backend.models.filters import QueryFilters


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
    excluded_segments: List[str] = None,
    size: int = 10,
) -> Tuple[List[Tuple[Company, str]], QueryFilters]:
    """
    Search for companies with optional LLM extraction and explainability.

    Steps:
    1. Extract filters from query using LLM (if query provided)
    2. Merge user filters with LLM filters (user overrides)
    3. Perform search with merged filters
    4. Generate explanations for each result
    5. Return companies with explanations and applied filters

    Args:
        query_text: Optional natural language query (if None, only uses user_filters)
        db: Database session
        user_filters: Optional filters provided by user
        excluded_segments: Segments to exclude from extraction
        size: Number of results to return

    Returns:
        Tuple of:
        - List of (Company, explanation) tuples
        - Applied filters (merged result)
    """
    if excluded_segments is None:
        excluded_segments = []

    # Step 1: Extract filters from query using LLM (skip if no query provided)
    if query_text and query_text.strip():
        llm_filters = extract_query_filters(query_text, db, es_client, excluded_segments)
    else:
        # No query provided - use empty filters (only user filters will be applied)
        llm_filters = QueryFilters(logic="AND", filters=[])

    # Step 2: Merge user filters with LLM filters (user overrides)
    applied_filters = merge_filters(user_filters, llm_filters, excluded_segments)

    # Step 3: Perform vector search with merged filters
    search_results = search_companies_with_filters(
        es_client, query_text=query_text, filters=applied_filters, size=size
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

        # Step 5: Generate explanations
        for company in sorted_companies:
            score = company_scores.get(company.id, 0.0)
            explanation = explain_result(company, query_text, applied_filters, score)
            companies_with_explanations.append((company, explanation))

    return companies_with_explanations, applied_filters
