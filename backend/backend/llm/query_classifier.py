"""Query classifier for determining user intent."""
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, Field

from backend.llm.client import get_llm_client
from backend.logging_config import get_logger

logger = get_logger(__name__)

PROMPTS_DIR = Path(__file__).parent / "prompts"
CLASSIFICATION_PROMPT = (PROMPTS_DIR / "query_classification.txt").read_text()


class QueryClassificationResponse(BaseModel):
    classification: Literal["explicit_search", "portfolio_analysis"] = Field(
        description="The type of query"
    )
    is_conceptual: bool = Field(
        description="Whether the query is conceptual/thesis-based (only relevant for explicit_search)"
    )
    confidence: float = Field(
        ge=0.0, le=1.0,
        description="Confidence score between 0.0 and 1.0"
    )
    reasoning: str = Field(
        description="Brief explanation for the classification"
    )


@dataclass
class QueryClassification:
    classification: Literal["explicit_search", "portfolio_analysis"]
    is_conceptual: bool
    confidence: float
    reasoning: str


class QueryClassifier:
    def __init__(self):
        self.llm_client = get_llm_client()

    def classify(self, query: str) -> QueryClassification:
        try:
            formatted_prompt = CLASSIFICATION_PROMPT.format(query=query)

            raw_response = self.llm_client.generate_raw(
                system_message="You are a query classifier. Respond with valid JSON only.",
                user_message=formatted_prompt
            )

            classification = raw_response.get("classification", "explicit_search")
            if classification not in ["explicit_search", "portfolio_analysis"]:
                logger.warning(f"Invalid classification '{classification}', defaulting to explicit_search")
                classification = "explicit_search"

            is_conceptual = bool(raw_response.get("is_conceptual", False))
            confidence = max(0.0, min(1.0, float(raw_response.get("confidence", 0.5))))
            reasoning = raw_response.get("reasoning", "No reasoning provided")

            logger.info(
                f"Query classified as '{classification}' "
                f"(conceptual: {is_conceptual}, confidence: {confidence:.2f}): {query}"
            )

            return QueryClassification(
                classification=classification,
                is_conceptual=is_conceptual,
                confidence=confidence,
                reasoning=reasoning
            )

        except Exception as e:
            logger.error(f"Error classifying query: {e}")
            return QueryClassification(
                classification="explicit_search",
                is_conceptual=False,
                confidence=0.5,
                reasoning=f"Fallback due to error: {str(e)}"
            )


_query_classifier = None


def get_query_classifier() -> QueryClassifier:
    global _query_classifier
    if _query_classifier is None:
        _query_classifier = QueryClassifier()
    return _query_classifier
