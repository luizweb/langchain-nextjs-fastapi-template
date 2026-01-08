"""Ollama provider implementation."""

from typing import List

from langchain_core.runnables import Runnable
from langchain_ollama import ChatOllama

from app.services.llm.base import LLMProvider
from app.settings import Settings


class OllamaProvider(LLMProvider):
    """Provider for Ollama models."""

    def __init__(self):
        """Initialize Ollama provider with settings."""
        settings = Settings()
        self.base_url = settings.OLLAMA_BASE_URL

    def get_model(self, model_name: str, **kwargs) -> Runnable:
        """Return an Ollama model instance.

        Args:
            model_name: The name of the Ollama model
            **kwargs: Additional parameters for the ChatOllama constructor

        Returns:
            A ChatOllama instance
        """
        params = {
            'base_url': self.base_url,
            'temperature': 0,
        }
        params.update(kwargs)

        return ChatOllama(model=model_name, **params)

    @staticmethod
    def get_available_models() -> List[str]:
        """Return a list of available Ollama models.

        Returns:
            List of supported Ollama model names
        """
        return [
            'gpt-oss:120b-cloud',
            'mistral',
        ]
