from typing import List, Optional

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from backend.db.database import Location, Industry, TargetMarket, FundingStage, get_db
from backend.logic.search import search_companies

router = APIRouter()


class QueryRequest(BaseModel):
    query: str
    location: Optional[str] = None
    industries: Optional[List[str]] = None
    target_markets: Optional[List[str]] = None
    min_employees: Optional[int] = None
    max_employees: Optional[int] = None
    stages: Optional[List[str]] = None
    min_stage_order: Optional[int] = None
    max_stage_order: Optional[int] = None
    min_funding: Optional[int] = None
    max_funding: Optional[int] = None


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

    class Config:
        from_attributes = True

    @staticmethod
    def from_company(company):
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
            target_markets=[tm.name for tm in company.target_markets]
        )


class QueryResponse(BaseModel):
    companies: list[CompanyResponse]


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
    companies = search_companies(
        query_text=request.query,
        db=db,
        size=10,
        location=request.location,
        industries=request.industries,
        target_markets=request.target_markets,
        min_employees=request.min_employees,
        max_employees=request.max_employees,
        stages=request.stages,
        min_stage_order=request.min_stage_order,
        max_stage_order=request.max_stage_order,
        min_funding=request.min_funding,
        max_funding=request.max_funding
    )

    # Convert Company models to CompanyResponse
    company_responses = [CompanyResponse.from_company(company) for company in companies]

    return QueryResponse(companies=company_responses)
