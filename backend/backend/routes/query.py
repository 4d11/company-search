import time
from typing import Optional

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from backend.db.database import Company, get_db

router = APIRouter()


class QueryRequest(BaseModel):
    query: str


class CompanyResponse(BaseModel):
    id: int
    company_name: str
    company_id: Optional[int]
    city: Optional[str]
    description: Optional[str]
    website_url: Optional[str]

    class Config:
        from_attributes = True


class QueryResponse(BaseModel):
    companies: list[CompanyResponse]


@router.post("/submit-query", response_model=QueryResponse)
async def submit_query(request: QueryRequest, db: Session = Depends(get_db)):
    # Simulate some processing time
    time.sleep(1)

    # Placeholder: Query first 5 companies from database
    companies = db.query(Company).limit(5).all()

    return QueryResponse(companies=companies)
