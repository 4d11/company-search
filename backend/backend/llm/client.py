"""
LLM client abstraction for attribute extraction.
Supports multiple providers (Ollama, OpenAI, etc.) via a common interface.
"""
from abc import ABC, abstractmethod
from typing import Any, Dict

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

        # Parse the JSON response
        import json
        return json.loads(response['response'])


def get_llm_client() -> LLMClient:
    """
    Factory function to get the appropriate LLM client based on settings.
    """
    if settings.llm_provider == "ollama":
        return OllamaClient()
    else:
        raise ValueError(f"Unsupported LLM provider: {settings.llm_provider}")


# Global client instance
llm_client = get_llm_client()
