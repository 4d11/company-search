"""
Filter merging logic for combining user-provided and LLM-extracted filters.
"""
from typing import List, Optional

from backend.models.filters import QueryFilters


def merge_filters(
    user_filters: Optional[QueryFilters],
    llm_filters: Optional[QueryFilters],
    excluded_segments: List[str] = None,
) -> QueryFilters:
    """
    Merge user-provided filters with LLM-extracted filters.

    Strategy:
    - User filters override LLM filters on a per-segment basis
    - If user provides a filter for a segment, ignore LLM's filter for that segment
    - Combine non-overlapping segments from both sources
    - Preserve top-level logic operator (prefer user's if specified)

    Args:
        user_filters: Filters explicitly provided by the user (can be None)
        llm_filters: Filters extracted from query by LLM (can be None)
        excluded_segments: List of segment names to exclude

    Returns:
        Merged QueryFilters
    """
    if excluded_segments is None:
        excluded_segments = []

    # If no filters at all, return empty
    if not user_filters and not llm_filters:
        return QueryFilters(logic="AND", filters=[])

    # If only user filters, return them (excluding excluded segments)
    if user_filters and not llm_filters:
        return QueryFilters(
            logic=user_filters.logic,
            filters=[
                f for f in user_filters.filters if f.segment not in excluded_segments
            ],
        )

    # If only LLM filters, return them (excluding excluded segments)
    if llm_filters and not user_filters:
        return QueryFilters(
            logic=llm_filters.logic,
            filters=[
                f for f in llm_filters.filters if f.segment not in excluded_segments
            ],
        )

    # Both exist: merge with user override
    # Get segments that user has provided filters for
    user_segments = {f.segment for f in user_filters.filters}

    # Start with all user filters
    merged_filters = [
        f for f in user_filters.filters if f.segment not in excluded_segments
    ]

    # Add LLM filters for segments not covered by user
    for llm_filter in llm_filters.filters:
        if (
            llm_filter.segment not in user_segments
            and llm_filter.segment not in excluded_segments
        ):
            merged_filters.append(llm_filter)

    # Prefer user's logic operator if available
    logic = user_filters.logic

    return QueryFilters(logic=logic, filters=merged_filters)
