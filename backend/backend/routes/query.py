from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from backend.db.database import Location, Industry, TargetMarket, FundingStage, BusinessModel, RevenueModel, SearchLog, get_db
from backend.logic.search import search_companies_with_extraction
from backend.models.filters import QueryFilters, ExcludedFilterValue

router = APIRouter()


class QueryRequest(BaseModel):
    query: Optional[str] = None
    filters: Optional[QueryFilters] = None
    excluded_values: Optional[List[ExcludedFilterValue]] = None


class CompanyResponse(BaseModel):
    id: int
    company_name: str
    company_id: Optional[int]
    city: Optional[str]
    description: Optional[str]
    website_url: Optional[str]
    employee_count: Optional[int]
    stage: Optional[str] = None
    funding_amount: Optional[int] = None
    location: Optional[str] = None
    industries: List[str] = []
    target_markets: List[str] = []
    explanation: Optional[str] = None

    class Config:
        from_attributes = True

    @staticmethod
    def from_company(company, explanation: str = None):
        """Convert Company model to CompanyResponse."""
        return CompanyResponse(
            id=company.id,
            company_name=company.company_name,
            company_id=company.company_id,
            city=company.city,
            description=company.description,
            website_url=company.website_url,
            employee_count=company.employee_count,
            stage=company.funding_stage.name if company.funding_stage else None,
            funding_amount=company.funding_amount,
            location=company.location.city if company.location else None,
            industries=[ind.name for ind in company.industries],
            target_markets=[tm.name for tm in company.target_markets],
            explanation=explanation
        )


class QueryResponse(BaseModel):
    companies: list[CompanyResponse]
    applied_filters: QueryFilters
    thesis_context: Optional[dict] = None


class FilterOptionsResponse(BaseModel):
    locations: List[str]
    industries: List[str]
    target_markets: List[str]
    business_models: List[str]
    revenue_models: List[str]
    stages: List[str]


@router.get("/filter-options", response_model=FilterOptionsResponse)
async def get_filter_options(db: Session = Depends(get_db)):
    """
    Get all available filter options for locations, industries, target markets, and stages.
    """
    locations = [loc.city for loc in db.query(Location).order_by(Location.city).all()]
    industries = [ind.name for ind in db.query(Industry).order_by(Industry.name).all()]
    target_markets = [tm.name for tm in db.query(TargetMarket).order_by(TargetMarket.name).all()]
    business_models = [bm.name for bm in db.query(BusinessModel).order_by(BusinessModel.name).all()]
    revenue_models = [rm.name for rm in db.query(RevenueModel).order_by(RevenueModel.name).all()]
    stages = [stage.name for stage in db.query(FundingStage).order_by(FundingStage.order_index).all()]

    return FilterOptionsResponse(
        locations=locations,
        industries=industries,
        target_markets=target_markets,
        business_models=business_models,
        revenue_models=revenue_models,
        stages=stages
    )


@router.post("/submit-query", response_model=QueryResponse)
async def submit_query(request: QueryRequest, db: Session = Depends(get_db)):
    """
    Submit a natural language query with optional filters.
    LLM extraction is performed when a query is provided.
    If no query is provided, only user filters are used for searching.

    For thesis-based queries (portfolio or conceptual), thesis_context will be included
    in the response with strategic analysis and reasoning.
    """
    # Search with LLM extraction and explainability
    companies_with_explanations, applied_filters, thesis_context = search_companies_with_extraction(
        query_text=request.query,
        db=db,
        user_filters=request.filters,
        excluded_values=request.excluded_values or [],
        size=20
    )

    # Convert to response format
    company_responses = [
        CompanyResponse.from_company(company, explanation)
        for company, explanation in companies_with_explanations
    ]

    # Log the search for analytics
    search_log = SearchLog(
        query=request.query,
        filters_applied=applied_filters.model_dump() if applied_filters else None,
        result_count=len(company_responses),
        timestamp=datetime.utcnow()
    )
    db.add(search_log)
    db.commit()

    resp = QueryResponse(
        companies=company_responses,
        applied_filters=applied_filters,
        thesis_context=thesis_context
    )
    return resp
