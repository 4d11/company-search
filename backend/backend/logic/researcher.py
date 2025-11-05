import asyncio
from pathlib import Path
from typing import List

from pydantic import BaseModel

from backend.db.database import Company
from backend.llm.client import get_llm_client
from backend.logging_config import get_logger

logger = get_logger(__name__)

PROMPTS_DIR = Path(__file__).parent.parent / "llm" / "prompts"
with open(PROMPTS_DIR / "research_prompt.txt", "r") as f:
    RESEARCH_PROMPT = f.read()

class CompanyDetailsResponse(BaseModel):
    company_details: dict[int, str]

async def _research_single_company(company: Company, query: str, client) -> tuple[int, str]:
    """Research a single company asynchronously."""
    try:
        # Build query with company context
        updated_query = f"Company Name: {company.company_name}. Query: {query}"

        logger.info(f"Researching company: {company.company_name} (ID: {company.id})")

        # Run the blocking web search in a thread pool to avoid blocking the event loop
        details = await asyncio.to_thread(
            client.do_web_search,
            RESEARCH_PROMPT,
            updated_query
        )

        logger.info(f"Successfully researched company {company.id}")
        return (company.id, details)

    except Exception as e:
        logger.error(f"Failed to research company {company.id} ({company.company_name}): {e}")
        return (company.id, f"Error: Unable to research this company. {str(e)}")


async def research_companies(db, company_ids: List[int], query: str) -> CompanyDetailsResponse:
    # Validate input
    if not company_ids:
        logger.warning("No company IDs provided for research")
        return CompanyDetailsResponse(company_details={})

    if not query or not query.strip():
        logger.warning("Empty query provided for research")
        return CompanyDetailsResponse(company_details={})

    # Fetch companies from database
    companies = db.query(Company).filter(Company.id.in_(company_ids)).all()

    # Check for missing companies
    found_ids = {company.id for company in companies}
    missing_ids = set(company_ids) - found_ids
    if missing_ids:
        logger.warning(f"Companies not found in database: {missing_ids}")

    logger.info(f"Researching {len(companies)} companies with query: '{query}'")

    client = get_llm_client()

    # Research all companies in parallel
    tasks = [_research_single_company(company, query, client) for company in companies]
    results = await asyncio.gather(*tasks)

    # Convert results to dictionary
    company_details = dict(results)

    logger.info(f"Completed research for {len(company_details)} companies")

    return CompanyDetailsResponse(company_details=company_details)