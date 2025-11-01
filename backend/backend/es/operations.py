from typing import List, Optional
from elasticsearch import Elasticsearch
from elasticsearch.helpers import bulk

from backend.db.database import Company
from backend.es.embeddings import generate_embeddings_batch, generate_embedding
from backend.es.index import COMPANY_INDEX_NAME
from backend.es.filter_converter import filters_to_es_query
from backend.models.filters import QueryFilters


def index_company(es: Elasticsearch, company: Company, index_name: str = COMPANY_INDEX_NAME):
    """
    Index a single company into Elasticsearch with vector embedding.

    Args:
        es: Elasticsearch client
        company: SQLAlchemy Company model instance
        index_name: Name of the index
    """
    from backend.es.embeddings import generate_embedding

    # Generate embedding for company description
    description_text = company.description or ""
    description_vector = generate_embedding(description_text)

    # Prepare document
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
        "employee_count": company.employee_count,
        "stage": company.funding_stage.name if company.funding_stage else None,
        "stage_order": company.funding_stage.order_index if company.funding_stage else None,
        "funding_amount": company.funding_amount,
        "description_vector": description_vector
    }

    # Index document using company.id as the document ID
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
    # Extract descriptions for batch embedding generation
    descriptions = [company.description or "" for company in companies]

    # Generate embeddings for all descriptions at once
    print(f"Generating embeddings for {len(companies)} companies...")
    description_vectors = generate_embeddings_batch(descriptions)

    # Prepare bulk indexing actions
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
                "employee_count": company.employee_count,
                "stage": company.funding_stage.name if company.funding_stage else None,
                "stage_order": company.funding_stage.order_index if company.funding_stage else None,
                "funding_amount": company.funding_amount,
                "description_vector": description_vector
            }
        }
        actions.append(doc)

    # Perform bulk indexing
    print(f"Bulk indexing {len(actions)} companies...")
    success, failed = bulk(es, actions, raise_on_error=False)
    print(f"Successfully indexed {success} companies")
    if failed:
        print(f"Failed to index {len(failed)} companies")

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
    min_stage_order: int = None,
    max_stage_order: int = None,
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

    # Generate embedding for the query
    query_vector = generate_embedding(query_text)

    # Build filter clauses
    filters = []
    if location:
        filters.append({"term": {"location": location}})
    if industries:
        filters.append({"terms": {"industries": industries}})
    if target_markets:
        filters.append({"terms": {"target_markets": target_markets}})
    if stages:
        filters.append({"terms": {"stage": stages}})

    # Add range filters for employee count
    if min_employees is not None or max_employees is not None:
        range_filter = {"range": {"employee_count": {}}}
        if min_employees is not None:
            range_filter["range"]["employee_count"]["gte"] = min_employees
        if max_employees is not None:
            range_filter["range"]["employee_count"]["lte"] = max_employees
        filters.append(range_filter)

    # Add range filters for stage order (enables comparisons like "Series A or later")
    if min_stage_order is not None or max_stage_order is not None:
        range_filter = {"range": {"stage_order": {}}}
        if min_stage_order is not None:
            range_filter["range"]["stage_order"]["gte"] = min_stage_order
        if max_stage_order is not None:
            range_filter["range"]["stage_order"]["lte"] = max_stage_order
        filters.append(range_filter)

    # Add range filters for funding amount
    if min_funding is not None or max_funding is not None:
        range_filter = {"range": {"funding_amount": {}}}
        if min_funding is not None:
            range_filter["range"]["funding_amount"]["gte"] = min_funding
        if max_funding is not None:
            range_filter["range"]["funding_amount"]["lte"] = max_funding
        filters.append(range_filter)

    # Use different query structure based on whether filters are present
    if filters:
        # Use script_score query with MUST filters when filters are provided
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
        # Use pure kNN search when no filters
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
    query_text: str,
    filters: Optional[QueryFilters] = None,
    size: int = 10,
    index_name: str = COMPANY_INDEX_NAME,
) -> List[dict]:
    """
    Search companies using the new QueryFilters structure.

    Args:
        es: Elasticsearch client
        query_text: The search query text
        filters: QueryFilters object containing structured filters
        size: Number of results to return
        index_name: Name of the index to search

    Returns:
        List of search result hits with scores
    """
    # Generate embedding for query text
    query_vector = generate_embedding(query_text)

    # Convert filters to ES query
    if filters and filters.filters:
        search_body = filters_to_es_query(filters, query_vector)
        search_body["size"] = size
    else:
        # No filters: use pure kNN
        search_body = {
            "knn": {
                "field": "description_vector",
                "query_vector": query_vector,
                "k": size,
                "num_candidates": size * 10,
            }
        }

    response = es.search(index=index_name, body=search_body)
    return response["hits"]["hits"]
