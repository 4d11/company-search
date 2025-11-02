"""
Filter schema models for query DSL.
"""
from enum import Enum
from typing import List, Union

from pydantic import BaseModel, field_validator, model_validator


class FilterType(str, Enum):
    """Type of filter value."""
    TEXT = "text"
    NUMERIC = "numeric"


class OperatorType(str, Enum):
    """Comparison operators for filters."""
    EQ = "EQ"
    NEQ = "NEQ"
    GT = "GT"
    GTE = "GTE"
    LT = "LT"
    LTE = "LTE"


class LogicType(str, Enum):
    """Logical operators for combining filters."""
    AND = "AND"
    OR = "OR"


# Valid segments
TEXT_SEGMENTS = {"location", "industries", "target_markets", "funding_stage", "business_models", "revenue_models"}
NUMERIC_SEGMENTS = {"employee_count", "funding_amount", "stage_order"}
ALL_SEGMENTS = TEXT_SEGMENTS | NUMERIC_SEGMENTS

# Operators allowed per type
TEXT_OPERATORS = {OperatorType.EQ, OperatorType.NEQ}
NUMERIC_OPERATORS = {
    OperatorType.EQ,
    OperatorType.NEQ,
    OperatorType.GT,
    OperatorType.GTE,
    OperatorType.LT,
    OperatorType.LTE,
}


class FilterRule(BaseModel):
    """A single filter rule with operator and value."""
    op: OperatorType
    value: Union[str, int, float]


class SegmentFilter(BaseModel):
    """Filter for a specific segment with multiple rules."""
    segment: str
    type: FilterType
    logic: LogicType
    rules: List[FilterRule]

    @field_validator("segment")
    @classmethod
    def validate_segment(cls, v):
        """Ensure segment is valid."""
        if v not in ALL_SEGMENTS:
            raise ValueError(
                f"Invalid segment '{v}'. Must be one of: {', '.join(sorted(ALL_SEGMENTS))}"
            )
        return v

    @model_validator(mode="after")
    def validate_type_and_operators(self):
        """Validate that operators match the segment type."""
        segment = self.segment
        filter_type = self.type

        # Check segment type consistency
        if filter_type == FilterType.TEXT and segment not in TEXT_SEGMENTS:
            raise ValueError(
                f"Segment '{segment}' is numeric but type is 'text'. Use 'numeric' instead."
            )
        if filter_type == FilterType.NUMERIC and segment not in NUMERIC_SEGMENTS:
            raise ValueError(
                f"Segment '{segment}' is text but type is 'numeric'. Use 'text' instead."
            )

        # Check operators are valid for type
        for rule in self.rules:
            if filter_type == FilterType.TEXT and rule.op not in TEXT_OPERATORS:
                raise ValueError(
                    f"Operator '{rule.op}' not allowed for text segments. "
                    f"Allowed: {', '.join(op.value for op in TEXT_OPERATORS)}"
                )
            if filter_type == FilterType.NUMERIC and rule.op not in NUMERIC_OPERATORS:
                raise ValueError(
                    f"Operator '{rule.op}' not allowed for numeric segments. "
                    f"Allowed: {', '.join(op.value for op in NUMERIC_OPERATORS)}"
                )

            # Check value type matches filter type
            if filter_type == FilterType.TEXT and not isinstance(rule.value, str):
                raise ValueError(
                    f"Value for text segment '{segment}' must be a string, got {type(rule.value).__name__}"
                )
            if filter_type == FilterType.NUMERIC and not isinstance(rule.value, (int, float)):
                raise ValueError(
                    f"Value for numeric segment '{segment}' must be a number, got {type(rule.value).__name__}"
                )

        return self

    @field_validator("rules")
    @classmethod
    def validate_rules_not_empty(cls, v):
        """Ensure at least one rule is provided."""
        if not v:
            raise ValueError("At least one rule must be provided")
        return v


class QueryFilters(BaseModel):
    """Complete filter specification for a query."""
    logic: LogicType
    filters: List[SegmentFilter]

    def get_segment_filter(self, segment: str) -> Union[SegmentFilter, None]:
        """Get filter for a specific segment if it exists."""
        for f in self.filters:
            if f.segment == segment:
                return f
        return None

    def has_segment(self, segment: str) -> bool:
        """Check if a segment is filtered."""
        return any(f.segment == segment for f in self.filters)

    def remove_segment(self, segment: str) -> "QueryFilters":
        """Return a new QueryFilters with the specified segment removed."""
        return QueryFilters(
            logic=self.logic,
            filters=[f for f in self.filters if f.segment != segment]
        )

    def merge_segment(self, segment_filter: SegmentFilter) -> "QueryFilters":
        """Return a new QueryFilters with the segment filter added/replaced."""
        filters = [f for f in self.filters if f.segment != segment_filter.segment]
        filters.append(segment_filter)
        return QueryFilters(logic=self.logic, filters=filters)