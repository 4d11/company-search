"""
Pydantic schemas for LLM responses.
"""
from typing import List, Optional

from pydantic import BaseModel, Field


class AttributeExtractionResponse(BaseModel):
    """Schema for attribute extraction LLM response."""

    location: Optional[str] = Field(
        None,
        description="City where company is headquartered"
    )
    industries: List[str] = Field(
        default_factory=list,
        description="1-3 industries that describe what the company does",
        max_length=3
    )
    target_markets: List[str] = Field(
        default_factory=list,
        description="1-2 target markets that describe who the company serves",
        max_length=2
    )
    business_models: List[str] = Field(
        default_factory=list,
        description="1-3 business models that describe how the company operates",
        max_length=3
    )
    revenue_models: List[str] = Field(
        default_factory=list,
        description="1-2 revenue models that describe how the company monetizes",
        max_length=2
    )


class QueryRewriteResponse(BaseModel):
    """Schema for query rewriting LLM response."""

    rewritten_query: str = Field(
        ...,
        description="Query rewritten for semantic search"
    )
