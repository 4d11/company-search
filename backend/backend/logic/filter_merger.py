"""
Filter merging logic for combining user-provided and LLM-extracted filters.
"""
from typing import List, Optional

from backend.models.filters import QueryFilters, SegmentFilter, ExcludedFilterValue


def _filter_excluded_values(
    filters: Optional[QueryFilters], excluded_values: List[ExcludedFilterValue]
) -> Optional[QueryFilters]:
    """
    Remove specific (segment, op, value) tuples from filters.

    Args:
        filters: QueryFilters to filter
        excluded_values: List of ExcludedFilterValue objects

    Returns:
        Filtered QueryFilters or None if no filters remain
    """
    if not filters or not excluded_values:
        return filters

    filtered_segments = []
    for segment_filter in filters.filters:
        segment = segment_filter.segment
        # Create set of excluded (op, value) tuples for this segment
        excluded_for_segment = {
            (ev.op, str(ev.value))
            for ev in excluded_values
            if ev.segment == segment
        }
        # Remove rules that match excluded values
        remaining_rules = [
            rule
            for rule in segment_filter.rules
            if (rule.op.value, str(rule.value)) not in excluded_for_segment
        ]
        # Only include segment if it has remaining rules
        if remaining_rules:
            filtered_segment = SegmentFilter(
                segment=segment_filter.segment,
                type=segment_filter.type,
                logic=segment_filter.logic,
                rules=remaining_rules,
            )
            filtered_segments.append(filtered_segment)

    if not filtered_segments:
        return None

    return QueryFilters(logic=filters.logic, filters=filtered_segments)


def merge_filters(
    user_filters: Optional[QueryFilters],
    llm_filters: Optional[QueryFilters],
    excluded_values: List[ExcludedFilterValue] = None,
) -> QueryFilters:
    """
    Merge user-provided filters with LLM-extracted filters.

    Strategy:
    - User filters override LLM filters on a per-segment basis
    - If user provides a filter for a segment, ignore LLM's filter for that segment
    - Combine non-overlapping segments from both sources
    - Preserve top-level logic operator (prefer user's if specified)
    - Filter out specific excluded (segment, op, value) tuples

    Args:
        user_filters: Filters explicitly provided by the user (can be None)
        llm_filters: Filters extracted from query by LLM (can be None)
        excluded_values: List of ExcludedFilterValue objects (segment, op, value tuples) to exclude

    Returns:
        Merged QueryFilters
    """
    if excluded_values is None:
        excluded_values = []

    # Filter out excluded values from both sources
    user_filters = _filter_excluded_values(user_filters, excluded_values)
    llm_filters = _filter_excluded_values(llm_filters, excluded_values)

    # If no filters at all, return empty
    if not user_filters and not llm_filters:
        return QueryFilters(logic="AND", filters=[])

    # If only user filters, return them (already filtered)
    if user_filters and not llm_filters:
        return user_filters

    # If only LLM filters, return them (already filtered)
    if llm_filters and not user_filters:
        return llm_filters

    # Both exist: merge with user override
    # Get segments that user has provided filters for
    user_segments = {f.segment for f in user_filters.filters}

    # Start with all user filters (already filtered)
    merged_filters = list(user_filters.filters)

    # Add LLM filters for segments not covered by user (already filtered)
    for llm_filter in llm_filters.filters:
        if llm_filter.segment not in user_segments:
            merged_filters.append(llm_filter)

    # Prefer user's logic operator if available
    logic = user_filters.logic

    return QueryFilters(logic=logic, filters=merged_filters)
