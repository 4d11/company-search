from typing import List, Optional

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from backend.db.database import Location, Industry, TargetMarket, FundingStage, get_db
from backend.logic.search import search_companies_with_extraction
from backend.models.filters import QueryFilters

router = APIRouter()


class QueryRequest(BaseModel):
    query: str
    filters: Optional[QueryFilters] = None
    excluded_segments: Optional[List[str]] = None


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


class FilterOptionsResponse(BaseModel):
    locations: List[str]
    industries: List[str]
    target_markets: List[str]
    stages: List[str]


@router.get("/filter-options", response_model=FilterOptionsResponse)
async def get_filter_options(db: Session = Depends(get_db)):
    """
    Get all available filter options for locations, industries, target markets, and stages.
    """
    locations = [loc.city for loc in db.query(Location).order_by(Location.city).all()]
    industries = [ind.name for ind in db.query(Industry).order_by(Industry.name).all()]
    target_markets = [tm.name for tm in db.query(TargetMarket).order_by(TargetMarket.name).all()]
    stages = [stage.name for stage in db.query(FundingStage).order_by(FundingStage.order_index).all()]

    return FilterOptionsResponse(
        locations=locations,
        industries=industries,
        target_markets=target_markets,
        stages=stages
    )


@router.post("/submit-query", response_model=QueryResponse)
async def submit_query(request: QueryRequest, db: Session = Depends(get_db)):
    """
    Submit a natural language query with optional filters.
    LLM extraction is always enabled to extract filters from the query.
    """
    # Search with LLM extraction and explainability
    companies_with_explanations, applied_filters = search_companies_with_extraction(
        query_text=request.query,
        db=db,
        user_filters=request.filters,
        excluded_segments=request.excluded_segments or [],
        size=10
    )

    # Convert to response format
    company_responses = [
        CompanyResponse.from_company(company, explanation)
        for company, explanation in companies_with_explanations
    ]

    return QueryResponse(
        companies=company_responses,
        applied_filters=applied_filters
    )
