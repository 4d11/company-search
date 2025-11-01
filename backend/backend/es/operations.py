from typing import List
from elasticsearch import Elasticsearch
from elasticsearch.helpers import bulk

from backend.db.database import Company
from backend.es.embeddings import generate_embeddings_batch
from backend.es.index import COMPANY_INDEX_NAME


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
    index_name: str = COMPANY_INDEX_NAME
):
    """
    Search for companies using vector similarity search.

    Args:
        es: Elasticsearch client
        query_text: The search query text
        size: Number of results to return
        index_name: Name of the index

    Returns:
        List of search results
    """
    from backend.es.embeddings import generate_embedding

    # Generate embedding for the query
    query_vector = generate_embedding(query_text)

    # Perform vector search using kNN
    search_body = {
        "knn": {
            "field": "description_vector",
            "query_vector": query_vector,
            "k": size,
            "num_candidates": size * 10  # Number of candidates to consider
        },
        "_source": {
            "excludes": ["description_vector"]  # Don't return the vector in results
        }
    }

    response = es.search(index=index_name, body=search_body)
    return response["hits"]["hits"]
