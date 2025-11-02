"""
Admin API endpoints for analytics and LLM extraction management.
"""
import json
from collections import defaultdict
from datetime import datetime, timedelta
from typing import List, Dict

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import desc, func
from sqlalchemy.orm import Session

from backend.db.database import (
    Industry,
    LLMExtraction,
    SearchLog,
    get_db,
)

router = APIRouter(prefix="/api/admin", tags=["admin"])


# Response models
class SearchAnalyticsResponse(BaseModel):
    total_searches: int
    searches_last_7_days: int
    searches_last_30_days: int
    top_queries_by_segment: Dict[str, List[dict]]  # {segment: [{query: str, values: [str], count: int}]}


class UnknownIndustryResponse(BaseModel):
    id: int
    raw_value: str
    segment: str
    count: int
    first_seen: datetime
    last_seen: datetime
    status: str


class ApproveIndustryRequest(BaseModel):
    extraction_id: int
    approved_name: str  # The cleaned-up industry name to add to DB


class MapIndustryRequest(BaseModel):
    extraction_id: int
    industry_id: int  # Existing industry to map to


# Endpoints
@router.get("/search-analytics", response_model=SearchAnalyticsResponse)
def get_search_analytics(db: Session = Depends(get_db)):
    """
    Get search analytics including:
    - Total search count
    - Searches in last 7/30 days
    - Top queries broken down by segment (industry, location, etc.)
    """
    now = datetime.utcnow()
    seven_days_ago = now - timedelta(days=7)
    thirty_days_ago = now - timedelta(days=30)

    # Total searches
    total_searches = db.query(SearchLog).count()

    # Recent searches
    searches_last_7_days = db.query(SearchLog).filter(
        SearchLog.timestamp >= seven_days_ago
    ).count()

    searches_last_30_days = db.query(SearchLog).filter(
        SearchLog.timestamp >= thirty_days_ago
    ).count()

    # Parse all search logs and group queries by filter segments
    all_logs = db.query(SearchLog).filter(
        SearchLog.query.isnot(None),
        SearchLog.query != ""
    ).all()

    # Structure: {segment: {query: {values: set, count: int}}}
    segment_query_map = defaultdict(lambda: defaultdict(lambda: {"values": set(), "count": 0}))

    for log in all_logs:
        query = log.query
        if not log.filters_applied:
            continue

        try:
            filters_data = json.loads(log.filters_applied) if isinstance(log.filters_applied, str) else log.filters_applied

            # Parse filters to extract segment values
            if "filters" in filters_data:
                for segment_filter in filters_data["filters"]:
                    segment = segment_filter.get("segment")
                    rules = segment_filter.get("rules", [])

                    # Extract values from rules
                    values = [str(rule.get("value")) for rule in rules if rule.get("op") == "EQ"]

                    if segment and values:
                        segment_query_map[segment][query]["values"].update(values)
                        segment_query_map[segment][query]["count"] += 1
        except (json.JSONDecodeError, TypeError, KeyError):
            continue

    # Convert to response format and sort by count
    top_queries_by_segment = {}
    for segment, queries in segment_query_map.items():
        sorted_queries = sorted(
            [
                {
                    "query": query,
                    "values": sorted(list(data["values"])),
                    "count": data["count"]
                }
                for query, data in queries.items()
            ],
            key=lambda x: x["count"],
            reverse=True
        )[:10]  # Top 10 per segment

        top_queries_by_segment[segment] = sorted_queries

    return SearchAnalyticsResponse(
        total_searches=total_searches,
        searches_last_7_days=searches_last_7_days,
        searches_last_30_days=searches_last_30_days,
        top_queries_by_segment=top_queries_by_segment,
    )


@router.get("/unknown-industries", response_model=List[UnknownIndustryResponse])
def get_unknown_industries(
    status: str = "pending",
    segment: str = "industries",
    db: Session = Depends(get_db)
):
    """
    Get LLM-discovered values that don't match existing database entries.

    Args:
        status: Filter by status (pending/approved/mapped/ignored)
        segment: Filter by segment type (industries/target_markets/etc.)
    """
    query = db.query(LLMExtraction).filter(
        LLMExtraction.status == status,
        LLMExtraction.segment == segment
    ).order_by(desc(LLMExtraction.count))

    extractions = query.all()

    return [
        UnknownIndustryResponse(
            id=e.id,
            raw_value=e.raw_value,
            segment=e.segment,
            count=e.count,
            first_seen=e.first_seen,
            last_seen=e.last_seen,
            status=e.status
        )
        for e in extractions
    ]


@router.post("/approve-industry")
def approve_industry(request: ApproveIndustryRequest, db: Session = Depends(get_db)):
    """
    Approve an LLM extraction and add it as a new industry to the database.
    """
    # Get the extraction
    extraction = db.query(LLMExtraction).filter(
        LLMExtraction.id == request.extraction_id
    ).first()

    if not extraction:
        raise HTTPException(status_code=404, detail="Extraction not found")

    # Check if industry already exists
    existing = db.query(Industry).filter(
        Industry.name == request.approved_name
    ).first()

    if existing:
        raise HTTPException(
            status_code=400,
            detail=f"Industry '{request.approved_name}' already exists"
        )

    # Create new industry
    new_industry = Industry(name=request.approved_name)
    db.add(new_industry)

    # Update extraction status
    extraction.status = "approved"
    extraction.matched_to = request.approved_name

    db.commit()

    return {
        "success": True,
        "industry_id": new_industry.id,
        "industry_name": new_industry.name
    }


@router.post("/map-industry")
def map_industry(request: MapIndustryRequest, db: Session = Depends(get_db)):
    """
    Map an LLM extraction to an existing industry in the database.
    """
    # Get the extraction
    extraction = db.query(LLMExtraction).filter(
        LLMExtraction.id == request.extraction_id
    ).first()

    if not extraction:
        raise HTTPException(status_code=404, detail="Extraction not found")

    # Get the industry
    industry = db.query(Industry).filter(Industry.id == request.industry_id).first()

    if not industry:
        raise HTTPException(status_code=404, detail="Industry not found")

    # Update extraction
    extraction.status = "mapped"
    extraction.matched_to = industry.name

    db.commit()

    return {
        "success": True,
        "extraction_id": extraction.id,
        "mapped_to": industry.name
    }


@router.get("/industries", response_model=List[dict])
def get_all_industries(db: Session = Depends(get_db)):
    """
    Get all existing industries for mapping dropdown.
    """
    industries = db.query(Industry).order_by(Industry.name).all()
    return [{"id": i.id, "name": i.name} for i in industries]
