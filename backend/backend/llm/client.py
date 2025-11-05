"""
LLM client using OpenAI SDK.
"""
import json
from typing import Any, Dict, Type, TypeVar, Optional
from openai import OpenAI

from pydantic import BaseModel, ValidationError

from backend.logging_config import get_logger
from backend.settings import settings

logger = get_logger(__name__)

T = TypeVar('T', bound=BaseModel)


class LLMClient:
    """LLM client using OpenAI SDK."""

    def __init__(self, api_key: str, model: str, base_url: str = None):

        if base_url:
            self.client = OpenAI(api_key=api_key, base_url=base_url)
        else:
            self.client = OpenAI(api_key=api_key)
        self.model = model


    def _clean_claude_json_output(self, content):
        """
        Strip Markdown code fences if present (Claude sometimes adds these despite instructions)

        :param content: the output from the model
        :return:
        """

        content = content.strip()
        if content.startswith("```"):
            lines = content.split('\n')
            if lines[0].startswith("```"):
                lines = lines[1:]
            if lines and lines[-1].strip() == "```":
                lines = lines[:-1]
            content = '\n'.join(lines).strip()
        return content



    def generate(
        self,
        response_model: Type[T],
        system_message: str,
        user_message: str,
    ) -> T:
        """
        Generate structured output using OpenAI SDK with Pydantic validation.

        Args:
            response_model: Pydantic model for validation (required)
            system_message: System instructions/role
            user_message: User input/request

        Returns:
            Validated Pydantic model instance
        """
        data = self.generate_raw(system_message=system_message, user_message=user_message)

        try:
            return response_model(**data)
        except ValidationError as e:
            logger.error(f"Pydantic validation error: {e}")
            raise

    def do_web_search(self, prompt: str, query: str) -> Optional[str]:
        """
        Perform a web search using the LLM client.

        Note: Your LLM provider needs to support it!

        Args:
            prompt: System message with instructions for the search
            query: User query to search for

        Returns:
            Text response from the LLM containing search results
        """
        messages = [
            {"role": "system", "content": prompt},
            {"role": "user", "content": query}
        ]
        supported_models = ['gemini']

        if any([m in self.model for m in supported_models]):
            try:
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    extra_body={
                        "tools": [{
                            "type": "google_search_retrieval",
                            "google_search_retrieval": {}
                        }]
                    }
                )
                return response.choices[0].message.content
            except Exception as e:
                logger.error("Error fetching from api")
                return None
        else:
            raise ValueError("Your LLM provider does not support search!")



    def generate_raw(
        self,
        system_message: str,
        user_message: str,
    ) -> Dict[str, Any]:
        """
        Generate raw JSON output without Pydantic validation.

        Use this when you need to manipulate the raw dict before validation
        (e.g., fixing common LLM mistakes).

        Args:
            system_message: System instructions/role
            user_message: User input/request

        Returns:
            Raw dict from LLM response
        """
        messages = [
            {"role": "system", "content": system_message},
            {"role": "user", "content": user_message}
        ]

        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=0.1,
            response_format={"type": "json_object"}
        )

        content = response.choices[0].message.content
        content = self._clean_claude_json_output(content)

        return json.loads(content)


_llm_client = None


def get_llm_client() -> LLMClient:
    """
    Get the LLM client singleton.

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
