"""
Convert QueryFilters to Elasticsearch query DSL.
"""
from typing import List

from backend.models.filters import FilterType, LogicType, OperatorType, QueryFilters, SegmentFilter


def convert_segment_filter(segment_filter: SegmentFilter) -> dict:
    """
    Convert a single SegmentFilter to Elasticsearch query clauses.

    Args:
        segment_filter: The segment filter to convert

    Returns:
        Elasticsearch query clause(s)
    """
    segment = segment_filter.segment
    logic = segment_filter.logic
    rules = segment_filter.rules
    filter_type = segment_filter.type

    # Build individual rule clauses
    clauses = []

    for rule in rules:
        op = rule.op
        value = rule.value

        if filter_type == FilterType.TEXT:
            # Text segment filters (exact term queries - values are pre-validated)
            if op == OperatorType.EQ:
                clauses.append({"term": {segment: value}})
            elif op == OperatorType.NEQ:
                clauses.append({"bool": {"must_not": {"term": {segment: value}}}})

        elif filter_type == FilterType.NUMERIC:
            if op == OperatorType.EQ:
                clauses.append({"term": {segment: value}})
            elif op == OperatorType.NEQ:
                clauses.append({"bool": {"must_not": {"term": {segment: value}}}})
            elif op == OperatorType.GT:
                clauses.append({"range": {segment: {"gt": value}}})
            elif op == OperatorType.GTE:
                clauses.append({"range": {segment: {"gte": value}}})
            elif op == OperatorType.LT:
                clauses.append({"range": {segment: {"lt": value}}})
            elif op == OperatorType.LTE:
                clauses.append({"range": {segment: {"lte": value}}})

    # Combine clauses based on logic
    if not clauses:
        return {}

    if len(clauses) == 1:
        return clauses[0]

    # Multiple clauses: combine with logic operator
    if logic == LogicType.AND:
        return {"bool": {"must": clauses}}
    else:
        return {"bool": {"should": clauses, "minimum_should_match": 1}}


def filters_to_es_query(filters: QueryFilters, query_vector: List[float] = None) -> dict:
    """
    Convert QueryFilters to complete Elasticsearch query with optional vector search.

    Args:
        filters: The filters to convert
        query_vector: Optional query embedding vector for semantic search. If None, returns pure filter query.

    Returns:
        Complete Elasticsearch query body
    """
    # Convert each segment filter
    filter_clauses = []
    for segment_filter in filters.filters:
        clause = convert_segment_filter(segment_filter)
        if clause:
            filter_clauses.append(clause)

    # Build query based on whether we have filters and vector
    if not filter_clauses:
        # No filters
        if query_vector is not None:
            # Use pure kNN search
            return {
                "knn": {
                    "field": "description_vector",
                    "query_vector": query_vector,
                    "k": 10,
                    "num_candidates": 100,
                }
            }
        else:
            return {"query": {"match_all": {}}}

    # With filters: combine filter clauses based on top-level logic
    if len(filter_clauses) == 1:
        filter_query = filter_clauses[0]
    elif filters.logic == LogicType.AND:
        filter_query = {"bool": {"must": filter_clauses}}
    else:  # OR
        filter_query = {"bool": {"should": filter_clauses, "minimum_should_match": 1}}

    # If vector provided, use script_score; otherwise return pure filter query
    if query_vector is not None:
        return {
            "query": {
                "script_score": {
                    "query": filter_query,
                    "script": {
                        "source": "cosineSimilarity(params.query_vector, 'description_vector') + 1.0",
                        "params": {"query_vector": query_vector},
                    },
                }
            }
        }
    else:
        return {"query": filter_query}
