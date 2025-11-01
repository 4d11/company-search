"""
Business logic for search operations.
"""
from typing import List, Optional
from sqlalchemy.orm import Session

from backend.db.database import Company
from backend.es.client import es_client
from backend.es.operations import search_companies_by_vector as es_search_companies


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
