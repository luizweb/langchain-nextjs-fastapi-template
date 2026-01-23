from typing import List

from langchain_ollama import OllamaEmbeddings

from app.settings import Settings


class EmbeddingService:
    """Service for embedding operations."""

    _model = None

    @classmethod
    def get_model(cls) -> OllamaEmbeddings:
        """Get or create singleton embedding model."""
        if cls._model is None:
            settings = Settings()
            cls._model = OllamaEmbeddings(
                model='bge-m3',
                base_url=settings.OLLAMA_BASE_URL
            )
        return cls._model

    @classmethod
    def embed_query(cls, text: str) -> List[float]:
        """Generate embedding for a single text query."""
        model = cls.get_model()
        return model.embed_query(text)

    @classmethod
    def embed_documents(cls, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for multiple documents in batch."""
        model = cls.get_model()
        return model.embed_documents(texts)
