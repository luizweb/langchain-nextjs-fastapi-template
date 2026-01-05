"""LLM Factory implementation"""

from typing import Dict, List, Optional

from langchain_core.runnables import Runnable

from app.services.llm.base import LLMProvider
from app.services.llm.ollama_provider import OllamaProvider

# from app.services.llm.openai_provider import OpenAIProvider
from app.services.llm.serpro_provider import SerproProvider


class LLMFactory:
    """Factory class for creating LLM instances."""

    def __init__(self):
        """Initialize the factory with available providers."""
        self.providers: Dict[str, LLMProvider] = {
            'ollama': OllamaProvider(),
            # 'openai': OpenAIProvider(),
            'serpro': SerproProvider(),
        }

    def get_provider(self, provider_name: str) -> Optional[LLMProvider]:
        """
        Get a provider by name.

        Args:
            provider_name: The name of the provider

        Returns:
            The provider instance or None if not found
        """
        return self.providers.get(provider_name.lower())

    def get_model(
        self, provider_name: str, model_name: str, **kwargs
    ) -> Optional[Runnable]:
        """Get a model from a specific provider.

        Args:
            provider_name: The name of the provider
            model_name: The name of the model
            **kwargs: Additional parameters to pass to the model constructor

        Returns:
            A runnable LLM model instance or None if provider not found
        """
        provider = self.get_provider(provider_name)
        if provider:
            return provider.get_model(model_name, **kwargs)
        return None

    def list_providers(self) -> List[str]:
        """List all available providers.

        Returns:
            List of provider names
        """
        return list(self.providers.keys())

    def list_models(self, provider_name: str) -> List[str]:
        """List all available models for a provider.

        Args:
            provider_name: The name of the provider

        Returns:
            List of model names or empty list if provider not found
        """
        provider = self.get_provider(provider_name)
        if provider:
            return provider.get_available_models()
        return []

    def add_provider(self, name: str, provider: LLMProvider) -> None:
        """Add a new provider to the factory.

        Args:
            name: The name for the provider
            provider: The provider instance
        """
        self.providers[name.lower()] = provider


if __name__ == "__main__":
    llm_factory = LLMFactory()
    print("Available providers: ", llm_factory.list_providers())
