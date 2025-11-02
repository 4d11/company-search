"""
Elasticsearch-based fuzzy matching for segment values.

Uses dedicated segment indices to find matching values.
"""
from typing import Dict, List, Optional

from elasticsearch import Elasticsearch

from backend.es.segment_indices import get_segment_index_name
from backend.logging_config import get_logger

logger = get_logger(__name__)


# Segments that use ES fuzzy matching
FUZZY_SEGMENTS = {"location", "industries", "target_markets", "business_models", "revenue_models"}

# Minimum similarity score for accepting a match
DEFAULT_THRESHOLD = 0.80


def get_unique_segment_values(
    es_client: Elasticsearch, segment: str, index: str = "companies"
) -> List[str]:
    """
    Get unique values for a segment from the companies index using aggregations.

    Args:
        es_client: Elasticsearch client
        segment: Segment name (e.g., "location", "industries")
        index: Index name to query

    Returns:
        List of unique values for the segment
    """
    query = {
        "size": 0,
        "aggs": {
            "unique_values": {
                "terms": {
                    "field": segment,
                    "size": 500,
                }
            }
        },
    }

    try:
        response = es_client.search(index=index, body=query)
        buckets = response["aggregations"]["unique_values"]["buckets"]
        return [bucket["key"] for bucket in buckets]
    except Exception as e:
        logger.error(f"Error getting unique values for {segment}: {e}")
        return []


def fuzzy_match_value(
    es_client: Elasticsearch,
    segment: str,
    value: str,
    threshold: float = DEFAULT_THRESHOLD,
    index: str = None,
) -> Optional[List[str]]:
    """
    Fuzzy match a single value against segment index.

    Convenience wrapper around batch_fuzzy_match_values for single values.

    Args:
        es_client: Elasticsearch client
        segment: Segment name (e.g., "location", "industries")
        value: Value to match (e.g., "Real Estate", "AI")
        threshold: Minimum similarity score (0.0-1.0) for accepting matches
        index: Index name (ignored, kept for backward compatibility)

    Returns:
        List of all matching values from index (filtered by score) or None if no matches
    """
    results = batch_fuzzy_match_values(es_client, segment, [value], threshold)
    return results.get(value)


def batch_fuzzy_match_values(
    es_client: Elasticsearch,
    segment: str,
    values: List[str],
    threshold: float = DEFAULT_THRESHOLD,
) -> Dict[str, Optional[List[str]]]:
    """
    Batch fuzzy match multiple values for a segment using Elasticsearch msearch API.

    This is much faster than calling fuzzy_match_value individually for each value,
    as it combines all searches into a single HTTP request.

    Args:
        es_client: Elasticsearch client
        segment: Segment name (e.g., "industries", "target_markets")
        values: List of values to match
        threshold: Fuzzy match threshold

    Returns:
        Dictionary mapping each input value to its matched values (or None if no match)
    """
    if not values:
        return {}

    index = get_segment_index_name(segment)
    if index is None:
        logger.warning(f"No segment index for '{segment}'")
        return {value: None for value in values}

    # Build msearch request body
    search_requests = []
    for value in values:
        normalized_value = value.strip()
        value_length = len(normalized_value)

        # Build query with multiple matching strategies (same as single query)
        query = {
            "bool": {
                "should": [
                    # Exact match (highest priority)
                    {
                        "match": {
                            "name.keyword": {
                                "query": normalized_value,
                                "boost": 3.0
                            }
                        }
                    },
                    # Match phrase prefix
                    {
                        "match_phrase_prefix": {
                            "name": {
                                "query": normalized_value,
                                "boost": 2.0
                            }
                        }
                    }
                ]
            }
        }

        # Add synonym-aware and flexible matching for certain segments
        if segment in ["industries", "business_models", "revenue_models"]:
            query["bool"]["should"].extend([
                {"match": {"name": {"query": normalized_value, "operator": "and", "boost": 1.5}}},
                {"match": {"name": {"query": normalized_value, "minimum_should_match": "75%", "boost": 1.2}}},
                {"fuzzy": {"name": {"value": normalized_value, "fuzziness": "AUTO", "boost": 0.8}}}
            ])

            if value_length <= 5:
                query["bool"]["should"].append({
                    "wildcard": {"name.keyword": {"value": f"{normalized_value}*", "boost": 1.5}}
                })
        else:
            query["bool"]["should"].append({
                "fuzzy": {"name": {"value": normalized_value, "fuzziness": "AUTO", "boost": 1.0}}
            })

        # Add index and search
        search_requests.append({"index": index})
        search_requests.append({
            "query": query,
            "size": 50,
            "_source": ["name"],
            "min_score": 1.0
        })

    # Execute msearch
    try:
        response = es_client.msearch(body=search_requests)

        # Process responses
        results = {}
        for idx, value in enumerate(values):
            resp = response["responses"][idx]

            if "error" in resp:
                logger.error(f"Error matching '{value}': {resp['error']}")
                results[value] = None
                continue

            hits = resp.get("hits", {}).get("hits", [])
            if not hits:
                logger.debug(f"No match for '{value}' in {segment}")
                results[value] = None
                continue

            # Apply quality filtering (same as single query)
            normalized_value = value.strip()
            value_length = len(normalized_value)
            max_score = hits[0]["_score"] if hits else 0
            filtered_matches = []

            for hit in hits:
                matched_name = hit["_source"]["name"]
                raw_score = hit["_score"]
                normalized_score = raw_score / max_score if max_score > 0 else 0

                # Token overlap
                query_tokens = set(normalized_value.lower().split())
                match_tokens = set(matched_name.lower().split())
                token_overlap = len(query_tokens & match_tokens) / len(query_tokens) if query_tokens else 0

                # Quality score
                quality_score = (normalized_score * 0.7) + (token_overlap * 0.3)
                min_quality = 0.60 if value_length <= 3 else threshold * 0.8

                if quality_score >= min_quality:
                    filtered_matches.append(matched_name)

            results[value] = filtered_matches if filtered_matches else None
            if filtered_matches:
                logger.debug(f"Fuzzy matched '{value}' → {len(filtered_matches)} matches: {filtered_matches}")

        return results

    except Exception as e:
        logger.error(f"Error in batch fuzzy matching for {segment}: {e}")
        return {value: None for value in values}


def validate_segment_value_es(
    es_client: Elasticsearch,
    segment: str,
    value: str,
    threshold: float = DEFAULT_THRESHOLD,
) -> Optional[List[str]]:
    """
    Validate and fuzzy match a segment value using Elasticsearch.

    This is the main entry point for ES-based fuzzy matching.

    Args:
        es_client: Elasticsearch client
        segment: Segment name
        value: Value to validate
        threshold: Fuzzy match threshold

    Returns:
        List of validated/matched values or None if invalid
        For non-fuzzy segments, returns single-item list
    """
    if segment in FUZZY_SEGMENTS:
        return fuzzy_match_value(es_client, segment, value, threshold)
    else:
        # For non-fuzzy segments (like funding_stage), return as single-item list
        # Validation for those happens in query_extractor
        return [value]
