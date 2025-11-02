#!/usr/bin/env python3
"""
Quick script to wipe PostgreSQL and Elasticsearch databases.
This will force re-seeding on next application startup.
"""

import sys
from backend.settings import settings
from backend.db.database import engine, Base
from backend.es.client import es_client
from backend.es.index import COMPANY_INDEX_NAME
from sqlalchemy import text

def wipe_postgres():
    """Drop all tables and settings in PostgreSQL."""
    print("Wiping PostgreSQL database...")

    with engine.connect() as conn:
        # Drop all tables
        Base.metadata.drop_all(bind=engine)
        print("✓ Dropped all PostgreSQL tables")

def wipe_elasticsearch():
    """Delete the Elasticsearch index."""
    print("Wiping Elasticsearch...")

    for index in es_client.indices.get_alias():
        try:
            if es_client.indices.exists(index=index):
                es_client.indices.delete(index=index)
                print(f"✓ Deleted Elasticsearch index: {index}")
            else:
                print(f"  Index '{index}' doesn't exist, skipping")
        except Exception as e:
            print(f"✗ Error deleting Elasticsearch index: {e}")

if __name__ == "__main__":
    print("=" * 60)
    print("DATABASE WIPE SCRIPT")
    print("=" * 60)
    print(f"PostgreSQL: {settings.database_url}")
    print(f"Elasticsearch: {settings.elasticsearch_url}")
    print("=" * 60)

    # Check for --yes flag
    skip_confirmation = "--yes" in sys.argv or "-y" in sys.argv

    if skip_confirmation:
        response = "yes"
    else:
        response = input("Are you sure you want to wipe all databases? (yes/no): ")

    if response.lower() == "yes":
        wipe_postgres()
        wipe_elasticsearch()
        print("\n✓ All databases wiped successfully!")
        print("  Restart the application to trigger re-seeding.")
    else:
        print("Aborted.")
