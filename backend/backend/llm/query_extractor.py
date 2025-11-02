"""
Query filter extraction service using LLM.
"""
import json
from datetime import datetime
from pathlib import Path
from typing import List

from elasticsearch import Elasticsearch
from pydantic import ValidationError
from sqlalchemy.orm import Session


from backend.db.database import FundingStage, LLMExtraction
from backend.es.fuzzy_matcher import batch_fuzzy_match_values, validate_segment_value_es
from backend.llm.client import get_llm_client
from backend.logging_config import get_logger
from backend.models.filters import QueryFilters, ExcludedFilterValue, FilterRule, OperatorType

logger = get_logger(__name__)

PROMPTS_DIR = Path(__file__).parent / "prompts"
with open(PROMPTS_DIR / "query_extraction.txt", "r") as f:
    QUERY_EXTRACTION_PROMPT = f.read()




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


def track_unknown_extraction(value: str, segment: str, db: Session):
    """
    Track an LLM-discovered value that didn't match any existing database entry.

    If the value already exists, increment its count and update last_seen.
    Otherwise, create a new extraction record.

    Args:
        value: The raw value extracted by LLM
        segment: The segment type (industries, target_markets, etc.)
        db: Database session
    """
    existing = db.query(LLMExtraction).filter(
        LLMExtraction.raw_value == value,
        LLMExtraction.segment == segment
    ).first()

    if existing:
        existing.count += 1
        existing.last_seen = datetime.utcnow()
    else:
        new_extraction = LLMExtraction(
            raw_value=value,
            segment=segment,
            count=1,
            first_seen=datetime.utcnow(),
            last_seen=datetime.utcnow(),
            status="pending"
        )
        db.add(new_extraction)

    db.commit()


def extract_query_filters(
    query: str, db: Session, es_client: Elasticsearch, excluded_values: List[ExcludedFilterValue] = None
) -> QueryFilters:
    """
    Extract structured filters from a natural language query using LLM.

    Values are validated using ES fuzzy matching to find exact database values.

    Args:
        query: Natural language query from user
        db: Database session
        es_client: Elasticsearch client for fuzzy matching
        excluded_values: List of ExcludedFilterValue objects (segment, op, value tuples) to exclude

    Returns:
        QueryFilters object containing extracted and validated filters
    """
    if excluded_values is None:
        excluded_values = []

    system_message = QUERY_EXTRACTION_PROMPT
    user_message = f"User Query: {query}"

    try:
        llm_client = get_llm_client()
        # Get raw dict to fix common LLM mistakes before Pydantic validation
        raw_response = llm_client.generate_raw(
            system_message=system_message,
            user_message=user_message
        )

        logger.debug(f"LLM Response: {json.dumps(raw_response, indent=2)}")

        # Fix common LLM mistake: using "EQ" as a logic value instead of "AND"/"OR"
        # Do this BEFORE Pydantic parsing to avoid validation errors
        if "filters" in raw_response:
            for segment_filter in raw_response["filters"]:
                if segment_filter.get("logic") not in ["AND", "OR"]:
                    logger.warning(f"Invalid logic '{segment_filter.get('logic')}' for {segment_filter.get('segment')}, fixing to 'AND'")
                    segment_filter["logic"] = "AND"

        filters = QueryFilters(**raw_response)

        logger.info("Validating extracted filters with ES fuzzy matching...")
        for segment_filter in filters.filters:
            if segment_filter.type.value == "text":
                validated_rules = []
                seen_values = set()

                # For funding_stage, use exact validation against database
                if segment_filter.segment == "funding_stage":
                    for rule in segment_filter.rules:
                        matched_value = validate_funding_stage(str(rule.value), db)
                        if matched_value and matched_value not in seen_values:
                            rule.value = matched_value
                            validated_rules.append(rule)
                            seen_values.add(matched_value)
                else:
                    # Batch validate all values for this segment at once
                    values_to_validate = [str(rule.value) for rule in segment_filter.rules]
                    batch_results = batch_fuzzy_match_values(
                        es_client=es_client,
                        segment=segment_filter.segment,
                        values=values_to_validate,
                        threshold=0.80,
                    )

                    # Process batch results
                    for rule in segment_filter.rules:
                        rule_value = str(rule.value)
                        matched_values = batch_results.get(rule_value)

                        if matched_values:
                            # Create a rule for each matched value (deduplicated)
                            # This expands "Real Estate" into ["Real Estate Tech", "Real Estate Services", etc.]
                            for matched_value in matched_values:
                                if matched_value not in seen_values:
                                    from backend.models.filters import FilterRule
                                    new_rule = FilterRule(op=rule.op, value=matched_value)
                                    validated_rules.append(new_rule)
                                    seen_values.add(matched_value)
                        else:
                            # Skip rule - no good match found
                            # Track this unknown extraction for admin review
                            logger.info(f"Skipping '{rule_value}' for {segment_filter.segment} - no match found")
                            track_unknown_extraction(
                                value=rule_value,
                                segment=segment_filter.segment,
                                db=db
                            )

                # Auto-expand Vertical/Horizontal SaaS to include generic SaaS
                if segment_filter.segment == "business_models":
                    has_vertical_or_horizontal = any(
                        rule.value in ["Vertical SaaS", "Horizontal SaaS"]
                        for rule in validated_rules
                    )
                    if has_vertical_or_horizontal and "SaaS" not in seen_values:
                        saas_rule = FilterRule(op=OperatorType.EQ, value="SaaS")
                        validated_rules.append(saas_rule)
                        seen_values.add("SaaS")

                segment_filter.rules = validated_rules

        # Filter out excluded values (specific segment, op, value tuples)
        if excluded_values:
            for segment_filter in filters.filters:
                segment = segment_filter.segment
                excluded_for_segment = {
                    (ev.op, str(ev.value))
                    for ev in excluded_values
                    if ev.segment == segment
                }

                segment_filter.rules = [
                    rule for rule in segment_filter.rules
                    if (rule.op.value, str(rule.value)) not in excluded_for_segment
                ]

        filters.filters = [f for f in filters.filters if f.rules]
        return filters

    except ValidationError as e:
        logger.error(f"Validation error in LLM response: {e}")
        # Return empty filters on validation error
        return QueryFilters(logic="AND", filters=[])

    except json.JSONDecodeError as e:
        logger.error(f"JSON decode error in LLM response: {e}")
        return QueryFilters(logic="AND", filters=[])

    except Exception as e:
        logger.exception(f"Error extracting query filters: {e}")
        # Return empty filters on any error
        return QueryFilters(logic="AND", filters=[])
