"""
Tests for filter schema models.
"""
import pytest
from pydantic import ValidationError

from backend.models.filters import (
    FilterRule,
    FilterType,
    LogicType,
    OperatorType,
    QueryFilters,
    SegmentFilter,
)


class TestFilterRule:
    """Test suite for FilterRule."""

    def test_valid_rule(self):
        """Test creating a valid filter rule."""
        rule = FilterRule(op=OperatorType.EQ, value="San Francisco")
        assert rule.op == OperatorType.EQ
        assert rule.value == "San Francisco"

    def test_numeric_value(self):
        """Test filter rule with numeric value."""
        rule = FilterRule(op=OperatorType.GTE, value=50)
        assert rule.op == OperatorType.GTE
        assert rule.value == 50


class TestSegmentFilter:
    """Test suite for SegmentFilter."""

    def test_valid_text_segment(self):
        """Test creating a valid text segment filter."""
        segment = SegmentFilter(
            segment="location",
            type=FilterType.TEXT,
            logic=LogicType.AND,
            rules=[FilterRule(op=OperatorType.EQ, value="San Francisco")],
        )
        assert segment.segment == "location"
        assert segment.type == FilterType.TEXT

    def test_valid_numeric_segment(self):
        """Test creating a valid numeric segment filter."""
        segment = SegmentFilter(
            segment="employee_count",
            type=FilterType.NUMERIC,
            logic=LogicType.AND,
            rules=[
                FilterRule(op=OperatorType.GTE, value=50),
                FilterRule(op=OperatorType.LTE, value=100),
            ],
        )
        assert segment.segment == "employee_count"
        assert len(segment.rules) == 2

    def test_invalid_segment_name(self):
        """Test that invalid segment names are rejected."""
        with pytest.raises(ValidationError, match="Invalid segment"):
            SegmentFilter(
                segment="invalid_segment",
                type=FilterType.TEXT,
                logic=LogicType.AND,
                rules=[FilterRule(op=OperatorType.EQ, value="test")],
            )

    def test_text_segment_with_numeric_operator(self):
        """Test that text segments reject numeric operators."""
        with pytest.raises(ValidationError, match="not allowed for text segments"):
            SegmentFilter(
                segment="location",
                type=FilterType.TEXT,
                logic=LogicType.AND,
                rules=[FilterRule(op=OperatorType.GTE, value="San Francisco")],
            )

    def test_numeric_segment_with_text_value(self):
        """Test that numeric segments reject text values."""
        with pytest.raises(ValidationError, match="must be a number"):
            SegmentFilter(
                segment="employee_count",
                type=FilterType.NUMERIC,
                logic=LogicType.AND,
                rules=[FilterRule(op=OperatorType.GTE, value="fifty")],
            )

    def test_wrong_type_for_segment(self):
        """Test that segment type must match segment name."""
        with pytest.raises(ValidationError, match="is numeric but type is 'text'"):
            SegmentFilter(
                segment="employee_count",
                type=FilterType.TEXT,
                logic=LogicType.AND,
                rules=[FilterRule(op=OperatorType.EQ, value="50")],
            )

    def test_empty_rules(self):
        """Test that at least one rule is required."""
        with pytest.raises(ValidationError, match="At least one rule must be provided"):
            SegmentFilter(
                segment="location",
                type=FilterType.TEXT,
                logic=LogicType.AND,
                rules=[],
            )


class TestQueryFilters:
    """Test suite for QueryFilters."""

    def test_valid_query_filters(self):
        """Test creating valid query filters."""
        filters = QueryFilters(
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
        assert filters.logic == LogicType.AND
        assert len(filters.filters) == 1

    def test_empty_filters(self):
        """Test that empty filters list is allowed."""
        filters = QueryFilters(logic=LogicType.AND, filters=[])
        assert filters.logic == LogicType.AND
        assert len(filters.filters) == 0

    def test_get_segment_filter(self):
        """Test getting a specific segment filter."""
        segment = SegmentFilter(
            segment="location",
            type=FilterType.TEXT,
            logic=LogicType.AND,
            rules=[FilterRule(op=OperatorType.EQ, value="San Francisco")],
        )
        filters = QueryFilters(logic=LogicType.AND, filters=[segment])

        result = filters.get_segment_filter("location")
        assert result is not None
        assert result.segment == "location"

        no_result = filters.get_segment_filter("industries")
        assert no_result is None

    def test_has_segment(self):
        """Test checking if a segment exists."""
        segment = SegmentFilter(
            segment="location",
            type=FilterType.TEXT,
            logic=LogicType.AND,
            rules=[FilterRule(op=OperatorType.EQ, value="San Francisco")],
        )
        filters = QueryFilters(logic=LogicType.AND, filters=[segment])

        assert filters.has_segment("location")
        assert not filters.has_segment("industries")

    def test_remove_segment(self):
        """Test removing a segment filter."""
        segment1 = SegmentFilter(
            segment="location",
            type=FilterType.TEXT,
            logic=LogicType.AND,
            rules=[FilterRule(op=OperatorType.EQ, value="San Francisco")],
        )
        segment2 = SegmentFilter(
            segment="employee_count",
            type=FilterType.NUMERIC,
            logic=LogicType.AND,
            rules=[FilterRule(op=OperatorType.GTE, value=50)],
        )
        filters = QueryFilters(logic=LogicType.AND, filters=[segment1, segment2])

        new_filters = filters.remove_segment("location")
        assert len(new_filters.filters) == 1
        assert new_filters.filters[0].segment == "employee_count"

    def test_merge_segment(self):
        """Test adding/replacing a segment filter."""
        segment1 = SegmentFilter(
            segment="location",
            type=FilterType.TEXT,
            logic=LogicType.AND,
            rules=[FilterRule(op=OperatorType.EQ, value="San Francisco")],
        )
        filters = QueryFilters(logic=LogicType.AND, filters=[segment1])

        # Replace existing segment
        segment2 = SegmentFilter(
            segment="location",
            type=FilterType.TEXT,
            logic=LogicType.OR,
            rules=[
                FilterRule(op=OperatorType.EQ, value="New York"),
                FilterRule(op=OperatorType.EQ, value="Boston"),
            ],
        )
        new_filters = filters.merge_segment(segment2)

        assert len(new_filters.filters) == 1
        assert new_filters.filters[0].logic == LogicType.OR
        assert len(new_filters.filters[0].rules) == 2

    def test_complex_filter_structure(self):
        """Test a complex filter with multiple segments and logic."""
        filters = QueryFilters(
            logic=LogicType.AND,
            filters=[
                SegmentFilter(
                    segment="location",
                    type=FilterType.TEXT,
                    logic=LogicType.OR,
                    rules=[
                        FilterRule(op=OperatorType.EQ, value="San Francisco"),
                        FilterRule(op=OperatorType.EQ, value="New York"),
                    ],
                ),
                SegmentFilter(
                    segment="employee_count",
                    type=FilterType.NUMERIC,
                    logic=LogicType.AND,
                    rules=[
                        FilterRule(op=OperatorType.GTE, value=50),
                        FilterRule(op=OperatorType.LTE, value=100),
                    ],
                ),
                SegmentFilter(
                    segment="industries",
                    type=FilterType.TEXT,
                    logic=LogicType.OR,
                    rules=[
                        FilterRule(op=OperatorType.EQ, value="AI/ML"),
                        FilterRule(op=OperatorType.EQ, value="FinTech"),
                    ],
                ),
            ],
        )

        assert len(filters.filters) == 3
        assert filters.has_segment("location")
        assert filters.has_segment("employee_count")
        assert filters.has_segment("industries")
