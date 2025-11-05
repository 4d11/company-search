from typing import List

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from backend.db.database import get_db
from backend.logic.researcher import research_companies

router = APIRouter()


class ResearchRequest(BaseModel):
    company_ids: List[int]
    query: str

class CompanyDetailsResponse(BaseModel):
    company_details: dict[int, str]


@router.post("/research", response_model=CompanyDetailsResponse)
async def submit_research(request: ResearchRequest, db: Session = Depends(get_db)):
    """
    Submit a research request for a list of companies
    """
    researched_companies = await research_companies(db, request.company_ids, request.query)
    return researched_companies
