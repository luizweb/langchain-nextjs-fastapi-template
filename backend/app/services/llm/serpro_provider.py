"""Serpro provider implementation."""

from typing import List

import requests
from langchain_core.runnables import Runnable
from langchain_openai import ChatOpenAI

from app.services.llm.base import LLMProvider
from app.settings import Settings


class SerproProvider(LLMProvider):
    """Provider for Serpro LLM models."""

    def __init__(self):
        """Initialize Serpro provider with settings."""
        settings = Settings()
        self.username = settings.SERPRO_USERNAME
        self.password = settings.SERPRO_PASSWORD
        self.token_url = settings.SERPRO_TOKEN_URL
        self.api_base_url = settings.SERPRO_API_BASE_URL

    def get_token(self) -> str:
        """Obtain access token from Serpro API using client credentials.

        Returns:
            Access token as string
        """
        response = requests.post(
            self.token_url,
            data={'grant_type': 'client_credentials'},
            auth=(self.username, self.password),
            timeout=30,
        )
        response.raise_for_status()
        return response.json()['access_token']

    def get_model(self, model_name: str, **kwargs) -> Runnable:
        """Return a Serpro model instance.

        Args:
            model_name: The name of the Serpro model
            **kwargs: Additional parameters for the ChatOpenAI constructor

        Returns:
            A ChatOpenAI instance configured for Serpro
        """
        # Get fresh token for each model instantiation
        token = self.get_token()

        # Set default parameters but allow overrides
        params = {
            'max_tokens': 1000,
            'temperature': 0,
        }
        params.update(kwargs)

        # Create and return the model
        return ChatOpenAI(
            model=model_name,
            openai_api_key=token,
            openai_api_base=self.api_base_url,
            **params,
        )

    @staticmethod
    def get_available_models() -> List[str]:
        """Return a list of available Serpro models.

        Returns:
            List of supported Serpro model names
        """
        return [
            'gpt-oss-120b',
            'deepseek-r1-distill-qwen-14b',
            'devstral-small',
            'llama-3.1-8B-instruct',
            'mistral-small-3.2-24b-instruct',
            'qwen3-32b'

        ]
