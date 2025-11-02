"""
Elasticsearch index mapping configurations.

Defines mappings for all segment indices (industries, locations, target_markets, etc.).
Uses template-based approach with dynamic synonym injection.
"""
from pathlib import Path
import json
from typing import List, Optional
from copy import deepcopy


# Load mapping template from config
def _load_mapping_template():
    """Load base mapping template from config/segment_mapping_template.json"""
    template_path = Path(__file__).parent.parent / "config" / "segment_mapping_template.json"
    with open(template_path, 'r') as f:
        return json.load(f)


# Load synonyms from seed_data.json
def _load_synonyms():
    """Load synonyms from seed_data.json"""
    seed_data_path = Path(__file__).parent.parent / "db" / "seed_data.json"
    with open(seed_data_path, 'r') as f:
        data = json.load(f)
    return data.get("synonyms", {})


def _build_synonym_list(synonyms_dict):
    """
    Convert synonym dictionary to Elasticsearch synonym format.

    Args:
        synonyms_dict: Dict mapping canonical_name -> [synonyms]

    Returns:
        List of "canonical, synonym1, synonym2" strings
    """
    synonym_list = []
    for canonical, synonyms in synonyms_dict.items():
        # Format: "canonical, synonym1, synonym2, ..."
        synonym_string = f"{canonical}, " + ", ".join(synonyms)
        synonym_list.append(synonym_string)
    return synonym_list


# Load synonyms
_SYNONYMS = _load_synonyms()
INDUSTRY_SYNONYMS = _build_synonym_list(_SYNONYMS.get("industries", {}))
BUSINESS_MODEL_SYNONYMS = _build_synonym_list(_SYNONYMS.get("business_models", {}))
REVENUE_MODEL_SYNONYMS = _build_synonym_list(_SYNONYMS.get("revenue_models", {}))


def create_segment_mapping(synonyms: Optional[List[str]] = None) -> dict:
    """
    Create Elasticsearch mapping for a segment index.

    Loads base template from JSON config and optionally injects synonym analyzer.

    Args:
        synonyms: Optional list of synonym strings in ES format
                 Example: ["AI, Artificial Intelligence, ML"]

    Returns:
        Complete ES index mapping configuration dict
    """
    # Load base mapping template from JSON config
    mapping = deepcopy(_load_mapping_template())

    # If synonyms provided, inject synonym analyzer (same names for all indices)
    if synonyms:
        # Add synonym analyzer to settings
        mapping["settings"]["analysis"]["analyzer"]["synonym_analyzer"] = {
            "type": "custom",
            "tokenizer": "standard",
            "filter": ["lowercase", "synonym_filter"]
        }

        # Add synonym filter to settings
        mapping["settings"]["analysis"]["filter"]["synonym_filter"] = {
            "type": "synonym",
            "synonyms": synonyms
        }

        # Update field to use synonym analyzer at search time
        mapping["mappings"]["properties"]["name"]["search_analyzer"] = "synonym_analyzer"

    return mapping


# Generate mappings using the template
SEGMENT_INDEX_MAPPING = create_segment_mapping()  # No synonyms for locations/target_markets
INDUSTRIES_INDEX_MAPPING = create_segment_mapping(INDUSTRY_SYNONYMS)
BUSINESS_MODELS_INDEX_MAPPING = create_segment_mapping(BUSINESS_MODEL_SYNONYMS)
REVENUE_MODELS_INDEX_MAPPING = create_segment_mapping(REVENUE_MODEL_SYNONYMS)
