from typing import List

from langchain_huggingface import HuggingFaceEmbeddings


class EmbeddingService:
    """Service for embedding operations."""

    _model = None

    @classmethod
    def get_model(cls) -> HuggingFaceEmbeddings:
        """Get or create singleton embedding model."""
        if cls._model is None:
            cls._model = HuggingFaceEmbeddings(
                model_name="BAAI/bge-m3",
                model_kwargs={"device": "cpu"},
                encode_kwargs={"normalize_embeddings": False}
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
