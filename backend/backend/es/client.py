from elasticsearch import Elasticsearch

from backend.settings import settings


def get_elasticsearch_client() -> Elasticsearch:
    """
    Create and return an Elasticsearch client instance.
    """
    if settings.elasticsearch_api_key:
        es = Elasticsearch(
            settings.elasticsearch_url,
            api_key=settings.elasticsearch_api_key
        )
    else:
        es = Elasticsearch(settings.elasticsearch_url)

    return es


# Global client instance
es_client = get_elasticsearch_client()
