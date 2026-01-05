"""OpenAI provider implementation."""

from typing import List

from langchain_core.runnables import Runnable
from langchain_openai import ChatOpenAI

from app.services.llm.base import LLMProvider
from app.settings import Settings


class OpenAIProvider(LLMProvider):
    """Provider for OpenAI models."""

    def __init__(self):
        """Initialize OpenAI provider with settings."""
        settings = Settings()
        self.api_key = settings.OPENAI_API_KEY

    def get_model(self, model_name: str, **kwargs) -> Runnable:
        """Return an OpenAI model instance.

        Args:
            model_name: The name of the OpenAI model
            **kwargs: Additional parameters for the ChatOpenAI constructor

        Returns:
            A ChatOpenAI instance
        """
        params = {'api_key': self.api_key}
        params.update(kwargs)
        return ChatOpenAI(model=model_name, **params)

    @staticmethod
    def get_available_models() -> List[str]:
        """Return a list of available OpenAI models.

        Returns:
            List of supported OpenAI model names
        """
        return ['gpt-4o', 'gpt-4o-mini', 'gpt-4-turbo', 'gpt-3.5-turbo']
