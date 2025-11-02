"""
Thesis expansion for conceptual investment queries.

Expands abstract concepts into concrete, searchable terms.
"""
from pathlib import Path
from typing import Optional

from pydantic import BaseModel, Field

from backend.llm.client import get_llm_client


# Load prompt template
PROMPTS_DIR = Path(__file__).parent / "prompts"
with open(PROMPTS_DIR / "thesis_expansion.txt", "r") as f:
    THESIS_EXPANSION_PROMPT = f.read()


class CoreConcepts(BaseModel):
    """Core concepts extracted from thesis."""
    technology: list[str] = Field(description="Technology/approach")
    business_model: list[str] = Field(description="Business model")
    industries: list[str] = Field(description="Target industries")
    use_case: str = Field(description="Problem being solved")


class ThesisExpansion(BaseModel):
    """Result of thesis expansion."""
    thesis_summary: str = Field(description="Brief summary of the thesis")
    core_concepts: CoreConcepts = Field(description="Core concepts extracted")
    expanded_query: str = Field(description="Expanded search query")
    strategic_focus: str = Field(description="What makes this thesis unique")


def expand_conceptual_thesis(query: str) -> Optional[ThesisExpansion]:
    """
    Expand a conceptual investment thesis into concrete search terms.

    This function takes abstract concepts like "API-first vertical SaaS for regulated industries"
    and expands them into specific, searchable terms with industry expansions.

    Args:
        query: Conceptual thesis query (e.g., "AI to optimize hospital billing")

    Returns:
        ThesisExpansion object with expanded query, or None if expansion fails

    Examples:
        query = "API-first vertical SaaS for regulated industries"
        result = expand_conceptual_thesis(query)
        # result.expanded_query = "API platform vertical SaaS healthcare fintech insurance..."
        # result.core_concepts.industries = ["healthcare IT", "fintech", "insurance tech", ...]
    """
    try:
        system_message = THESIS_EXPANSION_PROMPT
        user_message = f"USER THESIS: {query}"

        llm_client = get_llm_client()
        expansion = llm_client.generate(
            response_model=ThesisExpansion,
            system_message=system_message,
            user_message=user_message
        )

        print(f"Thesis Expansion:")
        print(f"  Summary: {expansion.thesis_summary}")
        print(f"  Technology: {', '.join(expansion.core_concepts.technology)}")
        print(f"  Industries: {', '.join(expansion.core_concepts.industries)}")
        print(f"  Expanded Query: {expansion.expanded_query}")
        print(f"  Strategic Focus: {expansion.strategic_focus}")

        return expansion

    except Exception as e:
        print(f"Error expanding thesis: {e}")
        return None
