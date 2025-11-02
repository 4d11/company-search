"""
Attribute extraction service that uses LLM to extract structured company attributes.
"""
import functools
from pathlib import Path
from typing import Dict, List, Optional, Set

from sqlalchemy.orm import Session

from backend.db.database import Industry, Location, TargetMarket, BusinessModel, RevenueModel
from backend.llm.client import get_llm_client
from backend.llm.extraction_cache import extraction_cache
from backend.llm.schemas import AttributeExtractionResponse
from backend.logging_config import get_logger
from backend.settings import settings

logger = get_logger(__name__)

@functools.lru_cache
def _load_attribute_extraction_prompt():
    PROMPTS_DIR = Path(__file__).parent / "prompts"
    with open(PROMPTS_DIR / "attribute_extraction.txt", "r") as f:
        attribute_extraction_prompt = f.read()
    return attribute_extraction_prompt

# Empty result structure for errors
EMPTY_ATTRIBUTES = {
    "location": None,
    "industries": [],
    "target_markets": [],
    "business_models": [],
    "revenue_models": [],
}


def get_supported_attributes(db: Session) -> Dict[str, Set[str]]:
    """
    Fetch supported attribute values from the database for validation.

    Args:
        db: Database session

    Returns:
        Dictionary mapping attribute names to sets of valid values (for fast lookup)
    """
    return {
        "locations": {loc.city for loc in db.query(Location).all()},
        "industries": {ind.name for ind in db.query(Industry).all()},
        "target_markets": {tm.name for tm in db.query(TargetMarket).all()},
        "business_models": {bm.name for bm in db.query(BusinessModel).all()},
        "revenue_models": {rm.name for rm in db.query(RevenueModel).all()},
    }


def _validate_attributes(
    raw_llm_response: Dict[str, any],
    supported: Dict[str, Set[str]]
) -> Dict[str, any]:
    """
    Validate raw LLM response against database values.

    Args:
        raw_llm_response: Raw LLM extraction result (before validation)
        supported: Dictionary of supported values from database (as sets)

    Returns:
        Validated extraction result with only database-valid values
    """
    # Validate location (single value)
    location = raw_llm_response.get("location")
    if location and location not in supported["locations"]:
        logger.warning(f"Location '{location}' not in database, setting to null")
        location = None

    validated = {"location": location}
    for attr_name in supported:
        if attr_name == "location":
            continue
        raw_values = raw_llm_response.get(attr_name, [])
        validated[attr_name] = [
            val for val in raw_values
            if val in supported[attr_name]
        ]

    return validated


def extract_company_attributes(
    company_name: str,
    description: str,
    website_text: Optional[str],
    db: Session
) -> Dict[str, any]:
    """
    Extract structured attributes from company information using LLM.

    Extracts: location, industries, target_markets, business_models, revenue_models.
    Note: Employee count, funding stage, and funding amount should be set separately.

    Uses SQLite cache for local development to avoid redundant LLM calls.
    Cache stores raw LLM responses; validation is re-applied on retrieval.

    Args:
        company_name: Name of the company
        description: Company description
        website_text: Optional website text (currently unused but kept for cache key)
        db: Database session

    Returns:
        Dictionary with validated attributes (only values that exist in database)
    """
    supported = get_supported_attributes(db)

    if settings.use_llm_cache:
        cached_raw = extraction_cache.get(company_name, description, website_text)
        if cached_raw:
            logger.debug(f"Using cached extraction for {company_name}")
            return _validate_attributes(cached_raw, supported)

    user_message = f"""Company Name: {company_name}
Description: {description}
"""

    try:
        llm_client = get_llm_client()
        response = llm_client.generate(
            system_message=_load_attribute_extraction_prompt(),
            user_message=user_message,
            response_model=AttributeExtractionResponse
        )

        raw_llm_result = response.model_dump()

        if settings.use_llm_cache:
            extraction_cache.set(company_name, description, website_text, raw_llm_result)

        return _validate_attributes(raw_llm_result, supported)

    except Exception as e:
        logger.exception(f"Error extracting attributes for {company_name}: {e}")

        if settings.use_llm_cache:
            extraction_cache.set(company_name, description, website_text, EMPTY_ATTRIBUTES)

        return EMPTY_ATTRIBUTES.copy()
