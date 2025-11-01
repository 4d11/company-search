"""
Query filter extraction service using LLM.
"""
import json
from pathlib import Path
from typing import List

from elasticsearch import Elasticsearch
from pydantic import ValidationError
from sqlalchemy.orm import Session

from backend.db.database import FundingStage
from backend.es.fuzzy_matcher import validate_segment_value_es
from backend.llm.client import get_llm_client
from backend.models.filters import QueryFilters

# Load prompt template
PROMPTS_DIR = Path(__file__).parent / "prompts"
with open(PROMPTS_DIR / "query_extraction.txt", "r") as f:
    QUERY_EXTRACTION_PROMPT = f.read()


def get_supported_values(db: Session) -> dict:
    """
    Fetch funding stages for prompt (small stable list).

    Args:
        db: Database session

    Returns:
        Dictionary with funding_stages list
    """
    funding_stages = [
        stage.name
        for stage in db.query(FundingStage).order_by(FundingStage.order_index).all()
    ]

    return {
        "funding_stages": funding_stages,
    }


def validate_funding_stage(value: str, db: Session) -> str:
    """
    Validate funding stage value against database (exact match, case-insensitive).

    Args:
        value: Funding stage value to validate
        db: Database session

    Returns:
        Matched funding stage name or None
    """
    stages = db.query(FundingStage).all()
    for stage in stages:
        if stage.name.lower() == value.lower():
            return stage.name
    return None


def extract_query_filters(
    query: str, db: Session, es_client: Elasticsearch, excluded_segments: List[str] = None
) -> QueryFilters:
    """
    Extract structured filters from a natural language query using LLM.

    Values are validated using ES fuzzy matching to find exact database values.

    Args:
        query: Natural language query from user
        db: Database session
        es_client: Elasticsearch client for fuzzy matching
        excluded_segments: List of segment names to exclude from extraction

    Returns:
        QueryFilters object containing extracted and validated filters
    """
    if excluded_segments is None:
        excluded_segments = []

    # Get supported values from database
    supported = get_supported_values(db)

    # Build the prompt from template
    # Use examples for dynamic segments (fuzzy matched), full list for stable segments
    prompt = QUERY_EXTRACTION_PROMPT.format(
        query=query,
        location_examples="San Francisco, New York, Boston",
        industry_examples="AI/ML, FinTech, Healthcare IT",
        target_market_examples="Enterprise, SMB, Mid-Market",
        funding_stages=", ".join(supported["funding_stages"]),
        excluded_segments=", ".join(excluded_segments) if excluded_segments else "none",
    )

    # Get LLM response using unified client
    try:
        llm_client = get_llm_client()
        response = llm_client.generate(prompt=prompt)

        # Debug: print the raw response
        print(f"LLM Response: {json.dumps(response, indent=2)}")

        # Fix common LLM mistake: using "EQ" as a logic value instead of "AND"/"OR"
        # Do this BEFORE parsing to avoid Pydantic validation errors
        if "filters" in response:
            for segment_filter in response["filters"]:
                if segment_filter.get("logic") not in ["AND", "OR"]:
                    print(f"  ⚠️  Warning: Invalid logic '{segment_filter.get('logic')}' for {segment_filter.get('segment')}, fixing to 'AND'")
                    segment_filter["logic"] = "AND"

        # Parse and validate the response
        filters = QueryFilters(**response)

        # Validate extracted values using ES fuzzy matching
        print("Validating extracted filters with ES fuzzy matching...")
        for segment_filter in filters.filters:
            if segment_filter.type.value == "text":
                validated_rules = []
                for rule in segment_filter.rules:
                    # For funding_stage, use exact validation against database
                    if segment_filter.segment == "funding_stage":
                        matched_value = validate_funding_stage(str(rule.value), db)
                        if matched_value:
                            rule.value = matched_value
                            validated_rules.append(rule)
                    else:
                        # For other text segments, use ES fuzzy matching (returns list)
                        matched_values = validate_segment_value_es(
                            es_client=es_client,
                            segment=segment_filter.segment,
                            value=str(rule.value),
                            threshold=0.80,  # 80% balanced threshold
                        )

                        if matched_values:
                            # Create a rule for each matched value
                            # This expands "Real Estate" into ["Real Estate Tech", "Real Estate Services", etc.]
                            for matched_value in matched_values:
                                # Create new rule with matched value
                                from backend.models.filters import FilterRule
                                new_rule = FilterRule(op=rule.op, value=matched_value)
                                validated_rules.append(new_rule)
                        else:
                            # Skip rule - no good match found (silent)
                            print(f"  Skipping '{rule.value}' for {segment_filter.segment} - no match found")

                # Update segment filter with validated rules
                segment_filter.rules = validated_rules

        # Remove segment filters that are in excluded_segments
        filters.filters = [f for f in filters.filters if f.segment not in excluded_segments]

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
