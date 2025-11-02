"""
Populate synonyms in PostgreSQL database from Elasticsearch synonym lists.

This script reads the hardcoded synonym lists from segment_indices.py
and populates the synonyms column in the industries, business_models,
and revenue_models tables.
"""
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.db.database import SessionLocal, Industry, BusinessModel, RevenueModel
from backend.es.segment_indices import (
    INDUSTRY_SYNONYMS,
    BUSINESS_MODEL_SYNONYMS,
    REVENUE_MODEL_SYNONYMS,
)


def parse_synonym_list(synonym_rules):
    """
    Parse synonym rules from ES format to dictionary.

    ES format: "Main Name, synonym1, synonym2, synonym3"
    Returns: {"Main Name": ["synonym1", "synonym2", "synonym3"]}

    Args:
        synonym_rules: List of synonym rule strings

    Returns:
        Dictionary mapping main name to list of synonyms
    """
    synonym_map = {}

    for rule in synonym_rules:
        # Split by comma
        parts = [p.strip() for p in rule.split(',')]
        if len(parts) < 2:
            continue

        # First part is the main name, rest are synonyms
        main_name = parts[0]
        synonyms = parts[1:]

        synonym_map[main_name] = synonyms

    return synonym_map


def populate_industry_synonyms(db):
    """Populate synonyms for industries."""
    print("\n=== Populating Industry Synonyms ===")

    synonym_map = parse_synonym_list(INDUSTRY_SYNONYMS)
    updated = 0

    for industry in db.query(Industry).all():
        if industry.name in synonym_map:
            industry.synonyms = synonym_map[industry.name]
            updated += 1
            print(f"  Updated {industry.name}: {len(industry.synonyms)} synonyms")

    db.commit()
    print(f"Updated {updated} industries with synonyms")


def populate_business_model_synonyms(db):
    """Populate synonyms for business models."""
    print("\n=== Populating Business Model Synonyms ===")

    synonym_map = parse_synonym_list(BUSINESS_MODEL_SYNONYMS)
    updated = 0

    for model in db.query(BusinessModel).all():
        if model.name in synonym_map:
            model.synonyms = synonym_map[model.name]
            updated += 1
            print(f"  Updated {model.name}: {len(model.synonyms)} synonyms")

    db.commit()
    print(f"Updated {updated} business models with synonyms")


def populate_revenue_model_synonyms(db):
    """Populate synonyms for revenue models."""
    print("\n=== Populating Revenue Model Synonyms ===")

    synonym_map = parse_synonym_list(REVENUE_MODEL_SYNONYMS)
    updated = 0

    for model in db.query(RevenueModel).all():
        if model.name in synonym_map:
            model.synonyms = synonym_map[model.name]
            updated += 1
            print(f"  Updated {model.name}: {len(model.synonyms)} synonyms")

    db.commit()
    print(f"Updated {updated} revenue models with synonyms")


def main():
    """Main entry point."""
    print("Starting synonym population...")

    db = SessionLocal()
    try:
        populate_industry_synonyms(db)
        populate_business_model_synonyms(db)
        populate_revenue_model_synonyms(db)

        print("\n=== Synonym Population Complete ===")

    except Exception as e:
        print(f"Error: {e}")
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()
