import json
from typing import List, Optional
from elasticsearch import Elasticsearch
from elasticsearch.helpers import bulk

from backend.db.database import Company
from backend.es.embeddings import generate_embeddings_batch, generate_embedding, generate_composite_embedding, generate_composite_embeddings_batch
from backend.es.index import COMPANY_INDEX_NAME
from backend.es.filter_converter import filters_to_es_query
from backend.logging_config import get_logger
from backend.models.filters import QueryFilters

logger = get_logger(__name__)


def index_company(es: Elasticsearch, company: Company, index_name: str = COMPANY_INDEX_NAME):
    """
    Index a single company into Elasticsearch with vector embedding.

    Args:
        es: Elasticsearch client
        company: SQLAlchemy Company model instance
        index_name: Name of the index
    """
    description_text = company.description or ""
    website_text = company.website_text or ""
    # Generate composite embedding from description + website_text (70/30)
    description_vector = generate_composite_embedding(description_text, website_text)

    doc = {
        "company_id": company.company_id,
        "company_name": company.company_name,
        "city": company.city,
        "description": company.description,
        "website_url": company.website_url,
        "website_text": company.website_text,
        "created_at": company.created_at.isoformat() if company.created_at else None,
        "location": company.location.city if company.location else None,
        "industries": [industry.name for industry in company.industries],
        "target_markets": [market.name for market in company.target_markets],
        "business_models": [bm.name for bm in company.business_models],
        "revenue_models": [rm.name for rm in company.revenue_models],
        "employee_count": company.employee_count,
        "funding_stage": company.funding_stage.name if company.funding_stage else None,
        "funding_amount": company.funding_amount,
        "description_vector": description_vector
    }

    es.index(index=index_name, id=company.id, document=doc)


def bulk_index_companies(es: Elasticsearch, companies: List[Company], index_name: str = COMPANY_INDEX_NAME):
    """
    Bulk index multiple companies into Elasticsearch with vector embeddings.
    More efficient than indexing one at a time.

    Args:
        es: Elasticsearch client
        companies: List of SQLAlchemy Company model instances
        index_name: Name of the index
    """
    company_data = [
        (company.description or "", company.website_text or "")
        for company in companies
    ]

    logger.info(f"Generating composite embeddings for {len(companies)} companies (70% description, 30% website)...")
    description_vectors = generate_composite_embeddings_batch(company_data)

    actions = []
    for company, description_vector in zip(companies, description_vectors):
        doc = {
            "_index": index_name,
            "_id": company.id,
            "_source": {
                "company_id": company.company_id,
                "company_name": company.company_name,
                "city": company.city,
                "description": company.description,
                "website_url": company.website_url,
                "website_text": company.website_text,
                "created_at": company.created_at.isoformat() if company.created_at else None,
                "location": company.location.city if company.location else None,
                "industries": [industry.name for industry in company.industries],
                "target_markets": [market.name for market in company.target_markets],
                "business_models": [bm.name for bm in company.business_models],
                "revenue_models": [rm.name for rm in company.revenue_models],
                "employee_count": company.employee_count,
                "funding_stage": company.funding_stage.name if company.funding_stage else None,
                "funding_amount": company.funding_amount,
                "description_vector": description_vector
            }
        }
        actions.append(doc)

    logger.info(f"Bulk indexing {len(actions)} companies...")
    success, failed = bulk(es, actions, raise_on_error=False)
    logger.info(f"Successfully indexed {success} companies")
    if failed:
        logger.warning(f"Failed to index {len(failed)} companies")

    return success, failed


def search_companies_by_vector(
    es: Elasticsearch,
    query_text: str,
    size: int = 10,
    index_name: str = COMPANY_INDEX_NAME,
    location: str = None,
    industries: List[str] = None,
    target_markets: List[str] = None,
    min_employees: int = None,
    max_employees: int = None,
    stages: List[str] = None,
    min_funding: int = None,
    max_funding: int = None
):
    """
    Search for companies using vector similarity search with optional filters.
    When filters are provided, uses a query with term filters instead of kNN filters.

    Args:
        es: Elasticsearch client
        query_text: The search query text
        size: Number of results to return
        index_name: Name of the index
        location: Optional city filter
        industries: Optional list of industries to filter by
        target_markets: Optional list of target markets to filter by
        min_employees: Optional minimum employee count
        max_employees: Optional maximum employee count
        stages: Optional list of funding stages to filter by (exact match)
        min_stage_order: Optional minimum stage order (for range queries like "Series A or later")
        max_stage_order: Optional maximum stage order (for range queries like "up to Series B")
        min_funding: Optional minimum funding amount
        max_funding: Optional maximum funding amount

    Returns:
        List of search results
    """
    from backend.es.embeddings import generate_embedding

    query_vector = generate_embedding(query_text)

    filters = []
    if location:
        filters.append({"term": {"location": location}})
    if industries:
        filters.append({"terms": {"industries": industries}})
    if target_markets:
        filters.append({"terms": {"target_markets": target_markets}})
    if stages:
        filters.append({"terms": {"funding_stage": stages}})

    if min_employees is not None or max_employees is not None:
        range_filter = {"range": {"employee_count": {}}}
        if min_employees is not None:
            range_filter["range"]["employee_count"]["gte"] = min_employees
        if max_employees is not None:
            range_filter["range"]["employee_count"]["lte"] = max_employees
        filters.append(range_filter)


    if min_funding is not None or max_funding is not None:
        range_filter = {"range": {"funding_amount": {}}}
        if min_funding is not None:
            range_filter["range"]["funding_amount"]["gte"] = min_funding
        if max_funding is not None:
            range_filter["range"]["funding_amount"]["lte"] = max_funding
        filters.append(range_filter)

    # Use different query structure based on whether filters are present
    # Use script_score query with MUST filters when filters are provided
    # Use pure kNN search when no filters
    if filters:
        search_body = {
            "query": {
                "script_score": {
                    "query": {
                        "bool": {
                            "must": filters
                        }
                    },
                    "script": {
                        "source": "cosineSimilarity(params.query_vector, 'description_vector') + 1.0",
                        "params": {
                            "query_vector": query_vector
                        }
                    }
                }
            },
            "size": size,
            "_source": {
                "excludes": ["description_vector"]
            }
        }
    else:
        search_body = {
            "knn": {
                "field": "description_vector",
                "query_vector": query_vector,
                "k": size,
                "num_candidates": size * 10
            },
            "_source": {
                "excludes": ["description_vector"]
            }
        }

    response = es.search(index=index_name, body=search_body)
    return response["hits"]["hits"]


def search_companies_with_filters(
    es: Elasticsearch,
    query_text: Optional[str],
    filters: Optional[QueryFilters] = None,
    size: int = 10,
    index_name: str = COMPANY_INDEX_NAME,
) -> List[dict]:
    """
    Search companies using the QueryFilters structure.

    Args:
        es: Elasticsearch client
        query_text: Optional search query text (if None, only uses filters)
        filters: QueryFilters object containing structured filters
        size: Number of results to return
        index_name: Name of the index to search

    Returns:
        List of search result hits with scores
    """
    query_vector = None
    if query_text and query_text.strip():
        query_vector = generate_embedding(query_text)

    if filters and filters.filters:
        search_body = filters_to_es_query(filters, query_vector)
    else:
        # No filters: use empty QueryFilters to get match_all or kNN
        from backend.models.filters import QueryFilters as EmptyFilters
        search_body = filters_to_es_query(EmptyFilters(logic="AND", filters=[]), query_vector)

    search_body["size"] = size

    # Output final ES query as JSON for debugging
    logger.debug(f"Elasticsearch Query: {json.dumps(search_body, indent=2)}")

    response = es.search(index=index_name, body=search_body)
    return response["hits"]["hits"]
