"""
Tests for LLM client.
"""
import json
from unittest.mock import MagicMock, patch

import pytest

from backend.llm.client import OpenAIClient, get_llm_client


class TestOpenAIClient:
    """Test suite for OpenAIClient."""

    @patch('openai.OpenAI')
    def test_initialization(self, mock_openai_class):
        """Test OpenAIClient initialization."""
        client = OpenAIClient(
            api_key="test-key",
            model="claude-3-5-haiku-20241022"
        )

        mock_openai_class.assert_called_once_with(api_key="test-key")
        assert client.model == "claude-3-5-haiku-20241022"

    @patch('openai.OpenAI')
    def test_initialization_with_base_url(self, mock_openai_class):
        """Test OpenAIClient initialization with custom base URL."""
        client = OpenAIClient(
            api_key="test-key",
            model="claude-3-5-haiku-20241022",
            base_url="https://api.anthropic.com/v1"
        )

        mock_openai_class.assert_called_once_with(
            api_key="test-key",
            base_url="https://api.anthropic.com/v1"
        )

    @patch('openai.OpenAI')
    def test_generate_json_response(self, mock_openai_class):
        """Test generating JSON response."""
        # Mock the OpenAI client
        mock_client = MagicMock()
        mock_openai_class.return_value = mock_client

        response_data = {
            "location": "San Francisco",
            "industries": ["SaaS"],
            "target_markets": ["SMB"]
        }

        # Mock the completion response
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = json.dumps(response_data)
        mock_client.chat.completions.create.return_value = mock_response

        client = OpenAIClient(api_key="test-key", model="claude-3-5-haiku-20241022")
        result = client.generate(prompt="Test prompt")

        # Verify the result
        assert result["location"] == "San Francisco"
        assert result["industries"] == ["SaaS"]
        assert result["target_markets"] == ["SMB"]

        # Verify the API call
        mock_client.chat.completions.create.assert_called_once()
        call_args = mock_client.chat.completions.create.call_args[1]
        assert call_args["model"] == "claude-3-5-haiku-20241022"
        assert call_args["messages"][0]["content"] == "Test prompt"
        assert call_args["temperature"] == 0.1
        assert call_args["response_format"] == {"type": "json_object"}


class TestGetLLMClient:
    """Test suite for get_llm_client factory function."""

    @patch('openai.OpenAI')
    @patch('backend.llm.client.settings')
    @patch('backend.llm.client._llm_client', None)
    def test_get_anthropic_client(self, mock_settings, mock_openai_class):
        """Test getting Anthropic client."""
        mock_settings.llm_provider = "anthropic"
        mock_settings.llm_api_key = "test-key"
        mock_settings.llm_model = "claude-3-5-haiku-20241022"
        mock_settings.llm_base_url = None

        client = get_llm_client()

        assert isinstance(client, OpenAIClient)
        mock_openai_class.assert_called_once_with(api_key="test-key")

    @patch('openai.OpenAI')
    @patch('backend.llm.client.settings')
    @patch('backend.llm.client._llm_client', None)
    def test_get_openai_client(self, mock_settings, mock_openai_class):
        """Test getting OpenAI client."""
        mock_settings.llm_provider = "openai"
        mock_settings.llm_api_key = "test-key"
        mock_settings.llm_model = "gpt-4"
        mock_settings.llm_base_url = None

        client = get_llm_client()

        assert isinstance(client, OpenAIClient)

    @patch('backend.llm.client.settings')
    def test_unsupported_provider(self, mock_settings):
        """Test that unsupported provider raises error."""
        mock_settings.llm_provider = "ollama"
        mock_settings.llm_api_key = "test-key"

        with pytest.raises(ValueError, match="Unsupported LLM provider"):
            get_llm_client()

    @patch('backend.llm.client.settings')
    def test_missing_api_key(self, mock_settings):
        """Test that missing API key raises error."""
        mock_settings.llm_provider = "anthropic"
        mock_settings.llm_api_key = None

        with pytest.raises(ValueError, match="API key is required"):
            get_llm_client()
