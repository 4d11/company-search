"""
Elasticsearch indices for segment values (industries, locations, target_markets).

These dedicated indices allow for precise fuzzy matching of segment values
without false positives from document-level aggregations.
"""
from typing import List

from elasticsearch import Elasticsearch
from sqlalchemy.orm import Session

from backend.db.database import Industry, Location, TargetMarket, BusinessModel, RevenueModel
from backend.es.index_mappings import (
    INDUSTRIES_INDEX_MAPPING,
    BUSINESS_MODELS_INDEX_MAPPING,
    REVENUE_MODELS_INDEX_MAPPING,
    SEGMENT_INDEX_MAPPING,
    INDUSTRY_SYNONYMS,
    BUSINESS_MODEL_SYNONYMS,
    REVENUE_MODEL_SYNONYMS,
)
from backend.logging_config import get_logger

logger = get_logger(__name__)

# Index names
INDUSTRIES_INDEX = "industries"
LOCATIONS_INDEX = "locations"
TARGET_MARKETS_INDEX = "target_markets"
BUSINESS_MODELS_INDEX = "business_models"
REVENUE_MODELS_INDEX = "revenue_models"

# Re-export synonyms for backward compatibility
# (imported from index_mappings.py, which loads from seed_data.json)
__all__ = [
    "INDUSTRIES_INDEX",
    "LOCATIONS_INDEX",
    "TARGET_MARKETS_INDEX",
    "BUSINESS_MODELS_INDEX",
    "REVENUE_MODELS_INDEX",
    "INDUSTRY_SYNONYMS",
    "BUSINESS_MODEL_SYNONYMS",
    "REVENUE_MODEL_SYNONYMS",
]


def create_segment_index(es: Elasticsearch, index_name: str) -> bool:
    """
    Create a segment index with proper mappings.

    Args:
        es: Elasticsearch client
        index_name: Name of the index to create

    Returns:
        True if created successfully
    """
    try:
        if es.indices.exists(index=index_name):
            logger.info(f"Index {index_name} already exists, deleting...")
            es.indices.delete(index=index_name)

        # Choose mapping based on index type (synonym-based or standard)
        if index_name == INDUSTRIES_INDEX:
            mapping = INDUSTRIES_INDEX_MAPPING
        elif index_name == BUSINESS_MODELS_INDEX:
            mapping = BUSINESS_MODELS_INDEX_MAPPING
        elif index_name == REVENUE_MODELS_INDEX:
            mapping = REVENUE_MODELS_INDEX_MAPPING
        else:
            mapping = SEGMENT_INDEX_MAPPING

        es.indices.create(index=index_name, body=mapping)
        logger.info(f"Created index: {index_name}")
        return True
    except Exception as e:
        logger.error(f"Error creating index {index_name}: {e}")
        return False


def index_industries(es: Elasticsearch, db: Session) -> int:
    """
    Index all unique industries from the database.

    Args:
        es: Elasticsearch client
        db: Database session

    Returns:
        Number of industries indexed
    """
    industries = db.query(Industry).all()
    actions = []

    for industry in industries:
        actions.append({
            "_index": INDUSTRIES_INDEX,
            "_id": industry.id,
            "_source": {
                "name": industry.name
            }
        })

    if actions:
        from elasticsearch.helpers import bulk
        success, failed = bulk(es, actions, raise_on_error=False)
        logger.info(f"Indexed {success} industries")
        return success

    return 0


def index_locations(es: Elasticsearch, db: Session) -> int:
    """
    Index all unique locations from the database.

    Args:
        es: Elasticsearch client
        db: Database session

    Returns:
        Number of locations indexed
    """
    locations = db.query(Location).all()
    actions = []

    for location in locations:
        actions.append({
            "_index": LOCATIONS_INDEX,
            "_id": location.id,
            "_source": {
                "name": location.city
            }
        })

    if actions:
        from elasticsearch.helpers import bulk
        success, failed = bulk(es, actions, raise_on_error=False)
        logger.info(f"Indexed {success} locations")
        return success

    return 0


def index_target_markets(es: Elasticsearch, db: Session) -> int:
    """
    Index all unique target markets from the database.

    Args:
        es: Elasticsearch client
        db: Database session

    Returns:
        Number of target markets indexed
    """
    target_markets = db.query(TargetMarket).all()
    actions = []

    for market in target_markets:
        actions.append({
            "_index": TARGET_MARKETS_INDEX,
            "_id": market.id,
            "_source": {
                "name": market.name
            }
        })

    if actions:
        from elasticsearch.helpers import bulk
        success, failed = bulk(es, actions, raise_on_error=False)
        logger.info(f"Indexed {success} target markets")
        return success

    return 0


def index_business_models(es: Elasticsearch, db: Session) -> int:
    """
    Index all unique business models from the database.

    Args:
        es: Elasticsearch client
        db: Database session

    Returns:
        Number of business models indexed
    """
    business_models = db.query(BusinessModel).all()
    actions = []

    for model in business_models:
        actions.append({
            "_index": BUSINESS_MODELS_INDEX,
            "_id": model.id,
            "_source": {
                "name": model.name
            }
        })

    if actions:
        from elasticsearch.helpers import bulk
        success, failed = bulk(es, actions, raise_on_error=False)
        logger.info(f"Indexed {success} business models")
        return success

    return 0


def index_revenue_models(es: Elasticsearch, db: Session) -> int:
    """
    Index all unique revenue models from the database.

    Args:
        es: Elasticsearch client
        db: Database session

    Returns:
        Number of revenue models indexed
    """
    revenue_models = db.query(RevenueModel).all()
    actions = []

    for model in revenue_models:
        actions.append({
            "_index": REVENUE_MODELS_INDEX,
            "_id": model.id,
            "_source": {
                "name": model.name
            }
        })

    if actions:
        from elasticsearch.helpers import bulk
        success, failed = bulk(es, actions, raise_on_error=False)
        logger.info(f"Indexed {success} revenue models")
        return success

    return 0


def create_and_populate_segment_indices(es: Elasticsearch, db: Session):
    """
    Create and populate all segment indices.

    Args:
        es: Elasticsearch client
        db: Database session
    """
    logger.info("Creating Segment Indices")

    # Create indices
    create_segment_index(es, INDUSTRIES_INDEX)
    create_segment_index(es, LOCATIONS_INDEX)
    create_segment_index(es, TARGET_MARKETS_INDEX)
    create_segment_index(es, BUSINESS_MODELS_INDEX)
    create_segment_index(es, REVENUE_MODELS_INDEX)

    # Populate indices
    logger.info("Populating Segment Indices")
    index_industries(es, db)
    index_locations(es, db)
    index_target_markets(es, db)
    index_business_models(es, db)
    index_revenue_models(es, db)

    logger.info("Segment Indices Ready")


def get_segment_index_name(segment: str) -> str:
    """
    Get the index name for a given segment.

    Args:
        segment: Segment name (e.g., "industries", "location", "target_markets", "business_models", "revenue_models")

    Returns:
        Index name or None if not a segment index
    """
    segment_map = {
        "industries": INDUSTRIES_INDEX,
        "location": LOCATIONS_INDEX,
        "target_markets": TARGET_MARKETS_INDEX,
        "business_models": BUSINESS_MODELS_INDEX,
        "revenue_models": REVENUE_MODELS_INDEX,
    }
    return segment_map.get(segment)
