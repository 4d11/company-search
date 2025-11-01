"""
LLM client using OpenAI SDK.
Works for OpenAI, Anthropic, and other OpenAI-compatible APIs.
"""
import json
from typing import Any, Dict

from backend.settings import settings


class LLMClient:
    """LLM client using OpenAI SDK."""

    def __init__(self, api_key: str, model: str, base_url: str = None):
        from openai import OpenAI
        if base_url:
            self.client = OpenAI(api_key=api_key, base_url=base_url)
        else:
            self.client = OpenAI(api_key=api_key)
        self.model = model

    def generate(self, prompt: str, response_format: Dict[str, Any] = None) -> Dict[str, Any]:
        """Generate structured JSON output using OpenAI SDK."""
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.1,
            response_format={"type": "json_object"}
        )

        content = response.choices[0].message.content
        return json.loads(content)


_llm_client = None


def get_llm_client() -> LLMClient:
    """
    Get the LLM client singleton.

    Uses OpenAI SDK which works for:
    - OpenAI (no base_url needed)
    - Anthropic (set base_url to "https://api.anthropic.com/v1")
    - Other OpenAI-compatible APIs

    Returns:
        LLMClient instance
    """
    global _llm_client

    if _llm_client is None:
        if not settings.llm_api_key:
            raise ValueError("LLM API key is required (set llm_api_key)")

        _llm_client = LLMClient(
            api_key=settings.llm_api_key,
            model=settings.llm_model,
            base_url=settings.llm_base_url
        )

    return _llm_client
