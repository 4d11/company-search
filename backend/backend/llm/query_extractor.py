"""
Query filter extraction service using LLM.
"""
import json
from pathlib import Path
from typing import List

from pydantic import ValidationError
from sqlalchemy.orm import Session

from backend.db.database import FundingStage, Industry, Location, TargetMarket
from backend.llm.client import get_query_llm_client
from backend.models.filters import QueryFilters

# Load prompt template
PROMPTS_DIR = Path(__file__).parent / "prompts"
with open(PROMPTS_DIR / "query_extraction.txt", "r") as f:
    QUERY_EXTRACTION_PROMPT = f.read()


def get_supported_values(db: Session) -> dict:
    """
    Fetch supported values for text segments from the database.

    Args:
        db: Database session

    Returns:
        Dictionary mapping segment names to their possible values
    """
    locations = [loc.city for loc in db.query(Location).all()]
    industries = [ind.name for ind in db.query(Industry).all()]
    target_markets = [tm.name for tm in db.query(TargetMarket).all()]
    funding_stages = [
        stage.name
        for stage in db.query(FundingStage).order_by(FundingStage.order_index).all()
    ]

    return {
        "locations": locations,
        "industries": industries,
        "target_markets": target_markets,
        "funding_stages": funding_stages,
    }


def extract_query_filters(
    query: str, db: Session, excluded_segments: List[str] = None
) -> QueryFilters:
    """
    Extract structured filters from a natural language query using LLM.

    Args:
        query: Natural language query from user
        db: Database session
        excluded_segments: List of segment names to exclude from extraction

    Returns:
        QueryFilters object containing extracted filters
    """
    if excluded_segments is None:
        excluded_segments = []

    # Get supported values from database
    supported = get_supported_values(db)

    # Build the prompt from template
    prompt = QUERY_EXTRACTION_PROMPT.format(
        query=query,
        locations=", ".join(supported["locations"]),
        industries=", ".join(supported["industries"]),
        target_markets=", ".join(supported["target_markets"]),
        funding_stages=", ".join(supported["funding_stages"]),
        excluded_segments=", ".join(excluded_segments) if excluded_segments else "none",
    )

    # Get LLM response using query-time client (online API)
    try:
        query_client = get_query_llm_client()
        response = query_client.generate(prompt=prompt)

        # Debug: print the raw response
        print(f"LLM Response: {json.dumps(response, indent=2)}")

        # Parse and validate the response
        filters = QueryFilters(**response)

        # Additional validation: ensure text values are in supported lists
        for segment_filter in filters.filters:
            if segment_filter.type.value == "text":
                segment_name = segment_filter.segment
                supported_key = None

                # Map segment name to supported values key
                if segment_name == "location":
                    supported_key = "locations"
                elif segment_name == "industries":
                    supported_key = "industries"
                elif segment_name == "target_markets":
                    supported_key = "target_markets"
                elif segment_name == "funding_stage":
                    supported_key = "funding_stages"

                if supported_key:
                    valid_values = set(supported[supported_key])
                    # Filter out invalid values
                    valid_rules = [
                        rule
                        for rule in segment_filter.rules
                        if rule.value in valid_values
                    ]
                    segment_filter.rules = valid_rules

            # Remove segment filters that are in excluded_segments
            if segment_filter.segment in excluded_segments:
                filters = filters.remove_segment(segment_filter.segment)

        # Remove empty filters (where all rules were filtered out)
        filters.filters = [f for f in filters.filters if f.rules]

        return filters

    except ValidationError as e:
        print(f"Validation error in LLM response: {e}")
        # Return empty filters on validation error
        return QueryFilters(logic="AND", filters=[])

    except json.JSONDecodeError as e:
        print(f"JSON decode error in LLM response: {e}")
        return QueryFilters(logic="AND", filters=[])

    except Exception as e:
        print(f"Error extracting query filters: {e}")
        # Return empty filters on any error
        return QueryFilters(logic="AND", filters=[])
