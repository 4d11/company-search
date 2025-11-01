"""
Attribute extraction service that uses LLM to extract structured company attributes.
Dynamically pulls supported attributes from the database schema.
"""
import json
from pathlib import Path
from typing import Dict, List, Optional

from sqlalchemy.orm import Session

from backend.db.database import FundingStage, Industry, Location, TargetMarket
from backend.llm.client import llm_client
from backend.llm.extraction_cache import extraction_cache
from backend.settings import settings

# Load prompt template
PROMPTS_DIR = Path(__file__).parent / "prompts"
with open(PROMPTS_DIR / "attribute_extraction.txt", "r") as f:
    ATTRIBUTE_EXTRACTION_PROMPT = f.read()


def get_supported_attributes(db: Session) -> Dict[str, List[str]]:
    """
    Fetch supported attribute values from the database.

    Args:
        db: Database session

    Returns:
        Dictionary mapping attribute names to their possible values
    """
    locations = [loc.city for loc in db.query(Location).all()]
    industries = [ind.name for ind in db.query(Industry).all()]
    target_markets = [tm.name for tm in db.query(TargetMarket).all()]
    funding_stages = [
        {"name": stage.name, "order": stage.order_index}
        for stage in db.query(FundingStage).order_by(FundingStage.order_index).all()
    ]

    return {
        "locations": locations,
        "industries": industries,
        "target_markets": target_markets,
        "funding_stages": funding_stages,
    }


def extract_company_attributes(
    company_name: str,
    description: str,
    website_text: Optional[str],
    db: Session
) -> Dict[str, any]:
    """
    Extract structured attributes from company information using LLM.
    Only extracts: location, industries, and target_markets.
    Employee count, funding stage, and funding amount should be set separately.

    Uses SQLite cache for LOCAL development to speed up repeated seeding.

    Args:
        company_name: Name of the company
        description: Company description
        website_text: Optional website text content
        db: Database session

    Returns:
        Dictionary containing extracted attributes:
        {
            "location": str or None,
            "industries": List[str],
            "target_markets": List[str]
        }
    """
    # Check cache first (only in local development)
    if settings.use_llm_cache:
        cached = extraction_cache.get(company_name, description, website_text)
        if cached:
            print(f"    ✓ Using cached extraction for {company_name}")
            return cached
    return {}

    # Get supported attributes from database
    supported = get_supported_attributes(db)

    # Build the prompt from template
    prompt = ATTRIBUTE_EXTRACTION_PROMPT.format(
        company_name=company_name,
        description=description,
        locations=', '.join(supported['locations']),
        industries=', '.join(supported['industries']),
        target_markets=', '.join(supported['target_markets'])
    )

    # Get LLM response
    try:
        response = llm_client.generate(prompt=prompt)

        # Validate and clean the response
        validated = {
            "location": response.get("location"),
            "industries": response.get("industries", [])[:3],  # Max 3
            "target_markets": response.get("target_markets", [])[:2],  # Max 2
        }

        # Validate location
        if validated["location"] and validated["location"] not in supported["locations"]:
            validated["location"] = None

        # Validate industries
        validated["industries"] = [
            ind for ind in validated["industries"]
            if ind in supported["industries"]
        ]

        # Validate target markets
        validated["target_markets"] = [
            tm for tm in validated["target_markets"]
            if tm in supported["target_markets"]
        ]

        # Cache the result (only in local development)
        if settings.use_llm_cache:
            extraction_cache.set(company_name, description, website_text, validated)

        return validated

    except Exception as e:
        print(f"Error extracting attributes for {company_name}: {e}")
        # Return empty/null attributes on error
        error_result = {
            "location": None,
            "industries": [],
            "target_markets": [],
        }

        # Cache error results too to avoid retrying failed extractions
        if settings.use_llm_cache:
            extraction_cache.set(company_name, description, website_text, error_result)

        return error_result
