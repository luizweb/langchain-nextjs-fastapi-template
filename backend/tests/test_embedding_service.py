"""Unit tests for EmbeddingService."""

from unittest.mock import MagicMock, patch

import pytest

from app.services.embedding_service import EmbeddingService


@pytest.fixture(autouse=True)
def reset_singleton():
    """Reset the singleton model before each test."""
    EmbeddingService._model = None
    yield
    EmbeddingService._model = None


@patch("app.services.embedding_service.HuggingFaceEmbeddings")
def test_get_model_creates_singleton(mock_embeddings_class):
    """Test that get_model creates a singleton instance."""
    mock_model = MagicMock()
    mock_embeddings_class.return_value = mock_model

    # First call should create the model
    result1 = EmbeddingService.get_model()
    assert result1 == mock_model
    mock_embeddings_class.assert_called_once_with(
        model_name="BAAI/bge-m3",
        model_kwargs={"device": "cpu"},
        encode_kwargs={"normalize_embeddings": False}
    )

    # Second call should return the same instance
    result2 = EmbeddingService.get_model()
    assert result2 == mock_model
    # Should still be called only once
    assert mock_embeddings_class.call_count == 1


@patch("app.services.embedding_service.HuggingFaceEmbeddings")
def test_embed_query(mock_embeddings_class):
    """Test embed_query returns embedding for single text."""
    mock_model = MagicMock()
    mock_embedding = [0.1, 0.2, 0.3, 0.4, 0.5]
    mock_model.embed_query.return_value = mock_embedding
    mock_embeddings_class.return_value = mock_model

    result = EmbeddingService.embed_query("test query")

    assert result == mock_embedding
    mock_model.embed_query.assert_called_once_with("test query")


@patch("app.services.embedding_service.HuggingFaceEmbeddings")
def test_embed_documents(mock_embeddings_class):
    """Test embed_documents returns embeddings for multiple texts."""
    mock_model = MagicMock()
    mock_embeddings = [
        [0.1, 0.2, 0.3],
        [0.4, 0.5, 0.6],
        [0.7, 0.8, 0.9]
    ]
    mock_model.embed_documents.return_value = mock_embeddings
    mock_embeddings_class.return_value = mock_model

    texts = ["doc1", "doc2", "doc3"]
    result = EmbeddingService.embed_documents(texts)

    assert result == mock_embeddings
    mock_model.embed_documents.assert_called_once_with(texts)


@patch("app.services.embedding_service.HuggingFaceEmbeddings")
def test_embed_documents_empty_list(mock_embeddings_class):
    """Test embed_documents with empty list."""
    mock_model = MagicMock()
    mock_model.embed_documents.return_value = []
    mock_embeddings_class.return_value = mock_model

    result = EmbeddingService.embed_documents([])

    assert result == []
    mock_model.embed_documents.assert_called_once_with([])


@patch("app.services.embedding_service.HuggingFaceEmbeddings")
def test_embed_query_empty_string(mock_embeddings_class):
    """Test embed_query with empty string."""
    mock_model = MagicMock()
    mock_embedding = [0.0, 0.0, 0.0]
    mock_model.embed_query.return_value = mock_embedding
    mock_embeddings_class.return_value = mock_model

    result = EmbeddingService.embed_query("")

    assert result == mock_embedding
    mock_model.embed_query.assert_called_once_with("")
