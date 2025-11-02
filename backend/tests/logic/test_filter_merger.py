"""
Tests for filter merging logic.
"""
import pytest

from backend.logic.filter_merger import merge_filters
from backend.models.filters import (
    FilterRule,
    FilterType,
    LogicType,
    OperatorType,
    QueryFilters,
    SegmentFilter,
)


class TestFilterMerger:
    """Test suite for filter merging."""

    def test_merge_both_none(self):
        """Test merging when both filters are None."""
        result = merge_filters(None, None, [])
        assert result.logic == LogicType.AND
        assert len(result.filters) == 0

    def test_merge_only_user_filters(self):
        """Test merging when only user filters exist."""
        user_filters = QueryFilters(
            logic=LogicType.AND,
            filters=[
                SegmentFilter(
                    segment="location",
                    type=FilterType.TEXT,
                    logic=LogicType.AND,
                    rules=[FilterRule(op=OperatorType.EQ, value="San Francisco")],
                )
            ],
        )

        result = merge_filters(user_filters, None, [])
        assert len(result.filters) == 1
        assert result.filters[0].segment == "location"

    def test_merge_only_llm_filters(self):
        """Test merging when only LLM filters exist."""
        llm_filters = QueryFilters(
            logic=LogicType.AND,
            filters=[
                SegmentFilter(
                    segment="industries",
                    type=FilterType.TEXT,
                    logic=LogicType.OR,
                    rules=[FilterRule(op=OperatorType.EQ, value="AI/ML")],
                )
            ],
        )

        result = merge_filters(None, llm_filters, [])
        assert len(result.filters) == 1
        assert result.filters[0].segment == "industries"

    def test_user_override_llm(self):
        """Test that user filters override LLM filters for same segment."""
        user_filters = QueryFilters(
            logic=LogicType.AND,
            filters=[
                SegmentFilter(
                    segment="location",
                    type=FilterType.TEXT,
                    logic=LogicType.AND,
                    rules=[FilterRule(op=OperatorType.EQ, value="San Francisco")],
                )
            ],
        )

        llm_filters = QueryFilters(
            logic=LogicType.AND,
            filters=[
                SegmentFilter(
                    segment="location",
                    type=FilterType.TEXT,
                    logic=LogicType.AND,
                    rules=[FilterRule(op=OperatorType.EQ, value="New York")],
                )
            ],
        )

        result = merge_filters(user_filters, llm_filters, [])
        assert len(result.filters) == 1
        assert result.filters[0].segment == "location"
        assert result.filters[0].rules[0].value == "San Francisco"  # User value wins

    def test_merge_non_overlapping_segments(self):
        """Test merging filters with different segments."""
        user_filters = QueryFilters(
            logic=LogicType.AND,
            filters=[
                SegmentFilter(
                    segment="employee_count",
                    type=FilterType.NUMERIC,
                    logic=LogicType.AND,
                    rules=[FilterRule(op=OperatorType.GTE, value=50)],
                )
            ],
        )

        llm_filters = QueryFilters(
            logic=LogicType.AND,
            filters=[
                SegmentFilter(
                    segment="industries",
                    type=FilterType.TEXT,
                    logic=LogicType.OR,
                    rules=[FilterRule(op=OperatorType.EQ, value="AI/ML")],
                )
            ],
        )

        result = merge_filters(user_filters, llm_filters, [])
        assert len(result.filters) == 2
        assert result.has_segment("employee_count")
        assert result.has_segment("industries")

    def test_excluded_segments_user_filters(self):
        """Test that excluded segments are removed from user filters."""
        user_filters = QueryFilters(
            logic=LogicType.AND,
            filters=[
                SegmentFilter(
                    segment="location",
                    type=FilterType.TEXT,
                    logic=LogicType.AND,
                    rules=[FilterRule(op=OperatorType.EQ, value="San Francisco")],
                ),
                SegmentFilter(
                    segment="industries",
                    type=FilterType.TEXT,
                    logic=LogicType.OR,
                    rules=[FilterRule(op=OperatorType.EQ, value="AI/ML")],
                ),
            ],
        )

        result = merge_filters(user_filters, None, excluded_segments=["industries"])
        assert len(result.filters) == 1
        assert result.filters[0].segment == "location"

    def test_excluded_segments_llm_filters(self):
        """Test that excluded segments are removed from LLM filters."""
        llm_filters = QueryFilters(
            logic=LogicType.AND,
            filters=[
                SegmentFilter(
                    segment="target_markets",
                    type=FilterType.TEXT,
                    logic=LogicType.OR,
                    rules=[FilterRule(op=OperatorType.EQ, value="Enterprise")],
                )
            ],
        )

        result = merge_filters(None, llm_filters, excluded_segments=["target_markets"])
        assert len(result.filters) == 0

    def test_excluded_segments_both_filters(self):
        """Test that excluded segments are removed from both filter sources."""
        user_filters = QueryFilters(
            logic=LogicType.AND,
            filters=[
                SegmentFilter(
                    segment="location",
                    type=FilterType.TEXT,
                    logic=LogicType.AND,
                    rules=[FilterRule(op=OperatorType.EQ, value="San Francisco")],
                ),
                SegmentFilter(
                    segment="industries",
                    type=FilterType.TEXT,
                    logic=LogicType.OR,
                    rules=[FilterRule(op=OperatorType.EQ, value="AI/ML")],
                ),
            ],
        )

        llm_filters = QueryFilters(
            logic=LogicType.AND,
            filters=[
                SegmentFilter(
                    segment="target_markets",
                    type=FilterType.TEXT,
                    logic=LogicType.OR,
                    rules=[FilterRule(op=OperatorType.EQ, value="Enterprise")],
                ),
                SegmentFilter(
                    segment="employee_count",
                    type=FilterType.NUMERIC,
                    logic=LogicType.AND,
                    rules=[FilterRule(op=OperatorType.GTE, value=50)],
                ),
            ],
        )

        result = merge_filters(
            user_filters,
            llm_filters,
            excluded_segments=["industries", "target_markets"],
        )

        assert len(result.filters) == 2
        assert result.has_segment("location")  # From user
        assert result.has_segment("employee_count")  # From LLM
        assert not result.has_segment("industries")  # Excluded
        assert not result.has_segment("target_markets")  # Excluded

    def test_preserve_user_logic_operator(self):
        """Test that user's logic operator is preserved."""
        user_filters = QueryFilters(
            logic=LogicType.OR,
            filters=[
                SegmentFilter(
                    segment="location",
                    type=FilterType.TEXT,
                    logic=LogicType.AND,
                    rules=[FilterRule(op=OperatorType.EQ, value="San Francisco")],
                )
            ],
        )

        llm_filters = QueryFilters(
            logic=LogicType.AND,
            filters=[
                SegmentFilter(
                    segment="industries",
                    type=FilterType.TEXT,
                    logic=LogicType.OR,
                    rules=[FilterRule(op=OperatorType.EQ, value="AI/ML")],
                )
            ],
        )

        result = merge_filters(user_filters, llm_filters, [])
        assert result.logic == LogicType.OR  # User's logic wins
