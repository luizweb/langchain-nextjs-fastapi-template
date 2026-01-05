"""Base provider interface for LLM models"""

from abc import ABC, abstractmethod
from typing import List

from langchain_core.runnables import Runnable


class LLMProvider(ABC):
    """Abstract base class for LLM providers"""

    @abstractmethod
    def get_model(self, model_name: str, **kwargs) -> Runnable:
        """
        Return a model instance for the specified model name.

        Args:
            model_name: The name of the model to create
            **kwargs: Additional parameters to pass to the model constructor

        Returns:
            A runnable LLM model instance

        """
        pass

    @abstractmethod
    def get_available_models(self) -> List[str]:
        """
        Return a list of available models for this provider.
        """
        pass
