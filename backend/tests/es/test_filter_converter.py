"""
Tests for Elasticsearch filter converter.
"""
from backend.es.filter_converter import convert_segment_filter, filters_to_es_query
from backend.models.filters import (
    FilterRule,
    FilterType,
    LogicType,
    OperatorType,
    QueryFilters,
    SegmentFilter,
)


class TestConvertSegmentFilter:
    """Test conversion of SegmentFilter to ES query clauses."""

    def test_text_eq_uses_term_query(self):
        """Test that text EQ operator uses exact term query (values are pre-validated)."""
        segment_filter = SegmentFilter(
            segment="location",
            type=FilterType.TEXT,
            logic=LogicType.AND,
            rules=[FilterRule(op=OperatorType.EQ, value="San Francisco")],
        )

        result = convert_segment_filter(segment_filter)

        assert result == {"term": {"location": "San Francisco"}}

    def test_text_neq_uses_term_query(self):
        """Test that text NEQ operator uses term query (no fuzziness for negation)."""
        segment_filter = SegmentFilter(
            segment="location",
            type=FilterType.TEXT,
            logic=LogicType.AND,
            rules=[FilterRule(op=OperatorType.NEQ, value="Tokyo")],
        )

        result = convert_segment_filter(segment_filter)

        assert result == {"bool": {"must_not": {"term": {"location": "Tokyo"}}}}

    def test_text_multiple_values_or_logic(self):
        """Test multiple text values with OR logic (exact term queries)."""
        segment_filter = SegmentFilter(
            segment="industries",
            type=FilterType.TEXT,
            logic=LogicType.OR,
            rules=[
                FilterRule(op=OperatorType.EQ, value="AI/ML"),
                FilterRule(op=OperatorType.EQ, value="FinTech"),
            ],
        )

        result = convert_segment_filter(segment_filter)

        assert result == {
            "bool": {
                "should": [
                    {"term": {"industries": "AI/ML"}},
                    {"term": {"industries": "FinTech"}},
                ],
                "minimum_should_match": 1,
            }
        }

    def test_numeric_range_and_logic(self):
        """Test numeric range with AND logic."""
        segment_filter = SegmentFilter(
            segment="employee_count",
            type=FilterType.NUMERIC,
            logic=LogicType.AND,
            rules=[
                FilterRule(op=OperatorType.GTE, value=50),
                FilterRule(op=OperatorType.LTE, value=100),
            ],
        )

        result = convert_segment_filter(segment_filter)

        assert result == {
            "bool": {
                "must": [
                    {"range": {"employee_count": {"gte": 50}}},
                    {"range": {"employee_count": {"lte": 100}}},
                ]
            }
        }

    def test_numeric_eq_operator(self):
        """Test numeric EQ operator."""
        segment_filter = SegmentFilter(
            segment="employee_count",
            type=FilterType.NUMERIC,
            logic=LogicType.AND,
            rules=[FilterRule(op=OperatorType.EQ, value=100)],
        )

        result = convert_segment_filter(segment_filter)

        assert result == {"term": {"employee_count": 100}}


class TestFiltersToESQuery:
    """Test conversion of QueryFilters to complete ES query."""

    def test_no_filters_uses_knn(self):
        """Test that no filters results in pure kNN search."""
        filters = QueryFilters(logic=LogicType.AND, filters=[])
        query_vector = [0.1] * 384

        result = filters_to_es_query(filters, query_vector)

        assert "knn" in result
        assert result["knn"]["field"] == "description_vector"
        assert result["knn"]["query_vector"] == query_vector
        assert result["knn"]["k"] == 10

    def test_with_filters_uses_script_score(self):
        """Test that filters result in script_score query."""
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
        query_vector = [0.1] * 384

        result = filters_to_es_query(filters, query_vector)

        assert "query" in result
        assert "script_score" in result["query"]
        assert "query" in result["query"]["script_score"]
        assert "script" in result["query"]["script_score"]
        assert (
            result["query"]["script_score"]["script"]["params"]["query_vector"]
            == query_vector
        )

    def test_multiple_filters_with_and_logic(self):
        """Test multiple filters combined with AND logic."""
        filters = QueryFilters(
            logic=LogicType.AND,
            filters=[
                SegmentFilter(
                    segment="location",
                    type=FilterType.TEXT,
                    logic=LogicType.AND,
                    rules=[FilterRule(op=OperatorType.EQ, value="San Francisco")],
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
            ],
        )
        query_vector = [0.1] * 384

        result = filters_to_es_query(filters, query_vector)

        # Verify it's a script_score with filter query
        assert "query" in result
        assert "script_score" in result["query"]

        # Verify filters are combined with AND (must)
        filter_query = result["query"]["script_score"]["query"]
        assert "bool" in filter_query
        assert "must" in filter_query["bool"]
        assert len(filter_query["bool"]["must"]) == 2

    def test_exact_term_queries_in_generated_query(self):
        """Verify exact term queries are used (values are pre-validated by ES)."""
        filters = QueryFilters(
            logic=LogicType.AND,
            filters=[
                SegmentFilter(
                    segment="industries",
                    type=FilterType.TEXT,
                    logic=LogicType.OR,
                    rules=[
                        FilterRule(op=OperatorType.EQ, value="AI/ML"),
                        FilterRule(op=OperatorType.EQ, value="FinTech"),
                    ],
                )
            ],
        )
        query_vector = [0.1] * 384

        result = filters_to_es_query(filters, query_vector)

        # Extract the filter query
        filter_query = result["query"]["script_score"]["query"]

        # Verify term queries are used (not match queries)
        assert "bool" in filter_query
        assert "should" in filter_query["bool"]

        # Check first term query
        first_term = filter_query["bool"]["should"][0]
        assert "term" in first_term
        assert "industries" in first_term["term"]
        assert first_term["term"]["industries"] == "AI/ML"

    def test_single_rule_no_bool_wrapper(self):
        """Test that single rule doesn't get wrapped in unnecessary bool."""
        segment_filter = SegmentFilter(
            segment="location",
            type=FilterType.TEXT,
            logic=LogicType.AND,
            rules=[FilterRule(op=OperatorType.EQ, value="New York")],
        )

        result = convert_segment_filter(segment_filter)

        # Should be direct term query, not wrapped in bool
        assert result == {"term": {"location": "New York"}}
        assert "bool" not in result

    def test_text_multiple_values_and_logic(self):
        """Test multiple text values with AND logic."""
        segment_filter = SegmentFilter(
            segment="industries",
            type=FilterType.TEXT,
            logic=LogicType.AND,
            rules=[
                FilterRule(op=OperatorType.EQ, value="AI/ML"),
                FilterRule(op=OperatorType.EQ, value="FinTech"),
            ],
        )

        result = convert_segment_filter(segment_filter)

        assert result == {
            "bool": {
                "must": [
                    {"term": {"industries": "AI/ML"}},
                    {"term": {"industries": "FinTech"}},
                ],
            }
        }

    def test_numeric_gt_operator(self):
        """Test numeric GT operator."""
        segment_filter = SegmentFilter(
            segment="funding_amount",
            type=FilterType.NUMERIC,
            logic=LogicType.AND,
            rules=[FilterRule(op=OperatorType.GT, value=1000000)],
        )

        result = convert_segment_filter(segment_filter)

        assert result == {"range": {"funding_amount": {"gt": 1000000}}}

    def test_numeric_lt_operator(self):
        """Test numeric LT operator."""
        segment_filter = SegmentFilter(
            segment="funding_amount",
            type=FilterType.NUMERIC,
            logic=LogicType.AND,
            rules=[FilterRule(op=OperatorType.LT, value=5000000)],
        )

        result = convert_segment_filter(segment_filter)

        assert result == {"range": {"funding_amount": {"lt": 5000000}}}

    def test_numeric_neq_operator(self):
        """Test numeric NEQ operator."""
        segment_filter = SegmentFilter(
            segment="employee_count",
            type=FilterType.NUMERIC,
            logic=LogicType.AND,
            rules=[FilterRule(op=OperatorType.NEQ, value=0)],
        )

        result = convert_segment_filter(segment_filter)

        assert result == {"bool": {"must_not": {"term": {"employee_count": 0}}}}

    def test_funding_stage_field_mapping(self):
        """Test that funding_stage segment works correctly (no manual mapping needed)."""
        segment_filter = SegmentFilter(
            segment="funding_stage",
            type=FilterType.TEXT,
            logic=LogicType.OR,
            rules=[
                FilterRule(op=OperatorType.EQ, value="Seed"),
                FilterRule(op=OperatorType.EQ, value="Series A"),
            ],
        )

        result = convert_segment_filter(segment_filter)

        # Should use funding_stage field (no mapping to "stage")
        assert result == {
            "bool": {
                "should": [
                    {"term": {"funding_stage": "Seed"}},
                    {"term": {"funding_stage": "Series A"}},
                ],
                "minimum_should_match": 1,
            }
        }


class TestFiltersToESQueryNoVector:
    """Test filters_to_es_query with no vector (pure filter queries)."""

    def test_no_filters_no_vector_returns_match_all(self):
        """Test that no filters and no vector returns match_all."""
        filters = QueryFilters(logic=LogicType.AND, filters=[])

        result = filters_to_es_query(filters, query_vector=None)

        assert result == {"query": {"match_all": {}}}

    def test_with_filters_no_vector_returns_pure_filter_query(self):
        """Test that filters without vector returns pure filter query (no script_score)."""
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

        result = filters_to_es_query(filters, query_vector=None)

        # Should be pure filter query, not script_score
        assert "query" in result
        assert "script_score" not in result["query"]
        assert result["query"] == {"term": {"location": "San Francisco"}}

    def test_multiple_filters_no_vector_with_and_logic(self):
        """Test multiple filters without vector combined with AND."""
        filters = QueryFilters(
            logic=LogicType.AND,
            filters=[
                SegmentFilter(
                    segment="location",
                    type=FilterType.TEXT,
                    logic=LogicType.AND,
                    rules=[FilterRule(op=OperatorType.EQ, value="New York")],
                ),
                SegmentFilter(
                    segment="employee_count",
                    type=FilterType.NUMERIC,
                    logic=LogicType.AND,
                    rules=[FilterRule(op=OperatorType.GTE, value=100)],
                ),
            ],
        )

        result = filters_to_es_query(filters, query_vector=None)

        assert result == {
            "query": {
                "bool": {
                    "must": [
                        {"term": {"location": "New York"}},
                        {"range": {"employee_count": {"gte": 100}}},
                    ]
                }
            }
        }

    def test_multiple_filters_no_vector_with_or_logic(self):
        """Test multiple filters without vector combined with OR."""
        filters = QueryFilters(
            logic=LogicType.OR,
            filters=[
                SegmentFilter(
                    segment="location",
                    type=FilterType.TEXT,
                    logic=LogicType.AND,
                    rules=[FilterRule(op=OperatorType.EQ, value="Boston")],
                ),
                SegmentFilter(
                    segment="location",
                    type=FilterType.TEXT,
                    logic=LogicType.AND,
                    rules=[FilterRule(op=OperatorType.EQ, value="Austin")],
                ),
            ],
        )

        result = filters_to_es_query(filters, query_vector=None)

        assert result == {
            "query": {
                "bool": {
                    "should": [
                        {"term": {"location": "Boston"}},
                        {"term": {"location": "Austin"}},
                    ],
                    "minimum_should_match": 1,
                }
            }
        }


class TestFiltersToESQueryEdgeCases:
    """Test edge cases for filters_to_es_query."""

    def test_single_filter_no_top_level_bool(self):
        """Test that single filter doesn't get unnecessary top-level bool wrapper."""
        filters = QueryFilters(
            logic=LogicType.AND,
            filters=[
                SegmentFilter(
                    segment="location",
                    type=FilterType.TEXT,
                    logic=LogicType.AND,
                    rules=[FilterRule(op=OperatorType.EQ, value="Seattle")],
                )
            ],
        )
        query_vector = [0.1] * 384

        result = filters_to_es_query(filters, query_vector)

        # Extract the filter query from script_score
        filter_query = result["query"]["script_score"]["query"]

        # Should be direct term query, not wrapped in top-level bool
        assert filter_query == {"term": {"location": "Seattle"}}

    def test_top_level_or_logic(self):
        """Test top-level OR logic between different segment filters."""
        filters = QueryFilters(
            logic=LogicType.OR,
            filters=[
                SegmentFilter(
                    segment="industries",
                    type=FilterType.TEXT,
                    logic=LogicType.AND,
                    rules=[FilterRule(op=OperatorType.EQ, value="AI/ML")],
                ),
                SegmentFilter(
                    segment="industries",
                    type=FilterType.TEXT,
                    logic=LogicType.AND,
                    rules=[FilterRule(op=OperatorType.EQ, value="Blockchain")],
                ),
            ],
        )
        query_vector = [0.1] * 384

        result = filters_to_es_query(filters, query_vector)

        filter_query = result["query"]["script_score"]["query"]
        assert filter_query == {
            "bool": {
                "should": [
                    {"term": {"industries": "AI/ML"}},
                    {"term": {"industries": "Blockchain"}},
                ],
                "minimum_should_match": 1,
            }
        }

    def test_complex_nested_filters(self):
        """Test complex nested filters with mixed AND/OR logic."""
        filters = QueryFilters(
            logic=LogicType.AND,
            filters=[
                # Industry filter with OR (AI/ML OR FinTech)
                SegmentFilter(
                    segment="industries",
                    type=FilterType.TEXT,
                    logic=LogicType.OR,
                    rules=[
                        FilterRule(op=OperatorType.EQ, value="AI/ML"),
                        FilterRule(op=OperatorType.EQ, value="FinTech"),
                    ],
                ),
                # Employee count with AND (>= 50 AND <= 200)
                SegmentFilter(
                    segment="employee_count",
                    type=FilterType.NUMERIC,
                    logic=LogicType.AND,
                    rules=[
                        FilterRule(op=OperatorType.GTE, value=50),
                        FilterRule(op=OperatorType.LTE, value=200),
                    ],
                ),
            ],
        )
        query_vector = [0.1] * 384

        result = filters_to_es_query(filters, query_vector)

        filter_query = result["query"]["script_score"]["query"]

        # Top level should be AND (must)
        assert "bool" in filter_query
        assert "must" in filter_query["bool"]
        assert len(filter_query["bool"]["must"]) == 2

        # First filter should be industries with OR
        industries_filter = filter_query["bool"]["must"][0]
        assert "bool" in industries_filter
        assert "should" in industries_filter["bool"]
        assert industries_filter["bool"]["should"] == [
            {"term": {"industries": "AI/ML"}},
            {"term": {"industries": "FinTech"}},
        ]

        # Second filter should be employee_count with AND
        employee_filter = filter_query["bool"]["must"][1]
        assert "bool" in employee_filter
        assert "must" in employee_filter["bool"]
        assert employee_filter["bool"]["must"] == [
            {"range": {"employee_count": {"gte": 50}}},
            {"range": {"employee_count": {"lte": 200}}},
        ]
