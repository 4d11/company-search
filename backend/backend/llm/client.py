"""
LLM client abstraction for attribute extraction.
Supports multiple providers (Ollama, OpenAI, Anthropic) via a common interface.
"""
from abc import ABC, abstractmethod
from typing import Any, Dict
import json

from backend.settings import settings


class LLMClient(ABC):
    """Abstract base class for LLM clients."""

    @abstractmethod
    def generate(self, prompt: str, response_format: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Generate a structured response from the LLM.

        Args:
            prompt: The prompt to send to the LLM
            response_format: Optional JSON schema for structured output

        Returns:
            Parsed JSON response
        """
        pass


class OllamaClient(LLMClient):
    """Ollama LLM client."""

    def __init__(self):
        import ollama
        self.client = ollama.Client(host=settings.llm_base_url)
        self.model = settings.llm_model

    def generate(self, prompt: str, response_format: Dict[str, Any] = None) -> Dict[str, Any]:
        """Generate structured output using Ollama."""
        response = self.client.generate(
            model=self.model,
            prompt=prompt,
            format="json" if response_format else None,
            options={
                "temperature": 0.1,  # Lower temperature for more consistent extraction
            }
        )

        return json.loads(response['response'])


class OpenAIClient(LLMClient):
    """OpenAI SDK client - works for both OpenAI and Anthropic."""

    def __init__(self, api_key: str, model: str, base_url: str = None):
        from openai import OpenAI
        if base_url:
            self.client = OpenAI(api_key=api_key, base_url=base_url)
        else:
            self.client = OpenAI(api_key=api_key)
        self.model = model

    def generate(self, prompt: str, response_format: Dict[str, Any] = None) -> Dict[str, Any]:
        """Generate structured output using OpenAI SDK."""
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.1,
            response_format={"type": "json_object"}
        )

        content = response.choices[0].message.content
        return json.loads(content)


def get_llm_client(provider: str = None, model: str = None, api_key: str = None, base_url: str = None) -> LLMClient:
    """
    Factory function to get the appropriate LLM client based on settings.

    Args:
        provider: LLM provider override (uses settings.llm_provider if None)
        model: Model name override (uses settings.llm_model if None)
        api_key: API key override (uses settings if None)
        base_url: Base URL override (for custom endpoints)

    Returns:
        LLMClient instance
    """
    provider = provider or settings.llm_provider

    if provider == "ollama":
        return OllamaClient()
    elif provider in ["anthropic", "openai"]:
        model = model or settings.query_llm_model
        api_key = api_key or settings.query_llm_api_key
        if not api_key:
            raise ValueError(f"{provider.capitalize()} API key is required")
        return OpenAIClient(api_key, model, base_url)
    else:
        raise ValueError(f"Unsupported LLM provider: {provider}")


# Global client instance for attribute extraction (seeding time - Ollama)
llm_client = get_llm_client()

# Query-time client factory (creates client based on query_llm_provider)
def get_query_llm_client() -> LLMClient:
    """Get LLM client for query-time extraction (uses online API)."""
    return get_llm_client(
        provider=settings.query_llm_provider,
        model=settings.query_llm_model,
        api_key=settings.query_llm_api_key,
        base_url=settings.query_llm_base_url,
    )
