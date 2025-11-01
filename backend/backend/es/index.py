import json
from pathlib import Path
from elasticsearch import Elasticsearch

from backend.settings import settings

COMPANY_INDEX_NAME = "companies"


def get_company_index_mapping():
    """
    Load the company index mapping from JSON file and update with settings.
    """
    mapping_path = Path(__file__).parent / "company_index_mapping.json"
    with open(mapping_path, 'r') as f:
        mapping = json.load(f)

    # Update vector dimensions from settings
    mapping["mappings"]["properties"]["description_vector"]["dims"] = settings.embedding_dimensions

    return mapping


def create_company_index(es: Elasticsearch, index_name: str = COMPANY_INDEX_NAME):
    """
    Create the companies index with vector field mapping.
    If the index already exists, it will be deleted and recreated.
    """
    # Delete index if it exists
    if es.indices.exists(index=index_name):
        es.indices.delete(index=index_name)
        print(f"Deleted existing index: {index_name}")

    # Create new index with mapping
    mapping = get_company_index_mapping()
    es.indices.create(index=index_name, body=mapping)
    print(f"Created index: {index_name}")


def index_exists(es: Elasticsearch, index_name: str = COMPANY_INDEX_NAME) -> bool:
    """
    Check if the index exists.
    """
    return es.indices.exists(index=index_name)
