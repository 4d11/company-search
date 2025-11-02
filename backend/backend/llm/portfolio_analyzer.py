"""
Portfolio analysis for generating complementary investment recommendations.
"""
from pathlib import Path
from typing import Optional

from pydantic import BaseModel, Field

from backend.llm.client import get_llm_client


# Load prompt template

PROMPTS_DIR = Path(__file__).parent / "prompts"
with open(PROMPTS_DIR / "portfolio_analysis.txt", "r") as f:
    PORTFOLIO_ANALYSIS_PROMPT = f.read()


class PortfolioAnalysis(BaseModel):
    """Result of portfolio analysis."""
    portfolio_summary: str = Field(description="Brief summary of the portfolio")
    themes: list[str] = Field(description="Key themes and patterns in portfolio")
    gaps: list[str] = Field(description="Strategic gaps to fill")
    complementary_areas: list[str] = Field(description="Specific complementary investment areas")
    expanded_query: str = Field(description="Expanded search query for complementary companies")
    strategic_reasoning: str = Field(description="Explanation of strategic fit")


def analyze_portfolio_for_complementary_thesis(query: str) -> Optional[PortfolioAnalysis]:
    """
    Analyze a portfolio-based query to generate complementary investment recommendations.

    This function extracts portfolio context from the query, identifies themes and gaps,
    and generates a strategic search query for complementary companies.

    Args:
        query: User query containing portfolio context (e.g., "My investments include X, Y. Suggest additions.")

    Returns:
        PortfolioAnalysis object with strategic recommendations, or None if analysis fails

    Example:
        query = "My investments include consumer credit and AI tax prep. Suggest additions."
        result = analyze_portfolio_for_complementary_thesis(query)
        # result.expanded_query = "B2B financial infrastructure APIs, AI healthcare billing..."
        # result.strategic_reasoning = "Diversifies into B2B while leveraging AI expertise..."
    """
    try:
        system_message = PORTFOLIO_ANALYSIS_PROMPT
        user_message = f"USER QUERY: {query}"

        llm_client = get_llm_client()
        analysis = llm_client.generate(
            response_model=PortfolioAnalysis,
            system_message=system_message,
            user_message=user_message
        )

        print(f"Portfolio Analysis:")
        print(f"  Summary: {analysis.portfolio_summary}")
        print(f"  Themes: {', '.join(analysis.themes)}")
        print(f"  Gaps: {', '.join(analysis.gaps)}")
        print(f"  Complementary Areas: {', '.join(analysis.complementary_areas)}")
        print(f"  Expanded Query: {analysis.expanded_query}")
        print(f"  Strategic Reasoning: {analysis.strategic_reasoning}")

        return analysis

    except Exception as e:
        print(f"Error analyzing portfolio: {e}")
        return None
