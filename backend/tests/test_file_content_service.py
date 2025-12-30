"""Unit tests for FileContentService."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from sqlalchemy.exc import SQLAlchemyError

from app.services.file_content_service import FileContentService


@pytest.fixture
def mock_session():
    """Create a mock async session."""
    return AsyncMock()


@pytest.mark.asyncio
async def test_bulk_create_empty_records(mock_session):
    """Test bulk_create with empty list returns 0."""
    result = await FileContentService.bulk_create([], mock_session)

    assert result == 0
    mock_session.execute.assert_not_called()


@pytest.mark.asyncio
async def test_bulk_create_inserts_records(mock_session):
    """Test bulk_create inserts records and returns count."""
    records = [
        {"content": "test1", "project_id": 1},
        {"content": "test2", "project_id": 1},
    ]

    result = await FileContentService.bulk_create(records, mock_session)

    assert result == len(records)
    mock_session.execute.assert_called_once()
    mock_session.commit.assert_called_once()


@pytest.mark.asyncio
async def test_search_similar_empty_query_raises(mock_session):
    """Test that empty query raises ValueError."""
    with pytest.raises(ValueError, match="Query cannot be empty"):
        await FileContentService.search_similar(
            query="",
            session=mock_session,
            project_id=1,
        )


@pytest.mark.asyncio
async def test_search_similar_whitespace_query_raises(mock_session):
    """Test that whitespace-only query raises ValueError."""
    with pytest.raises(ValueError, match="Query cannot be empty"):
        await FileContentService.search_similar(
            query="   ",
            session=mock_session,
            project_id=1,
        )


@pytest.mark.asyncio
@patch("app.services.file_content_service.EmbeddingService")
async def test_search_similar_returns_results(
    mock_embedding_service, mock_session
):
    """Test search_similar returns formatted results."""
    mock_embedding_service.embed_query.return_value = [0.1, 0.2, 0.3]

    expected_id = 1
    expected_content = "test content"
    expected_metadata = {"filename": "test.pdf"}
    expected_score = 0.9567

    mock_row = MagicMock()
    mock_row.id = expected_id
    mock_row.content = expected_content
    mock_row.file_metadata = expected_metadata
    mock_row.similarity_score = expected_score

    mock_result = MagicMock()
    mock_result.all.return_value = [mock_row]
    mock_session.execute.return_value = mock_result

    results = await FileContentService.search_similar(
        query="test query",
        session=mock_session,
        project_id=1,
        limit=5,
    )

    assert len(results) == 1
    assert results[0]["id"] == expected_id
    assert results[0]["content"] == expected_content
    assert results[0]["similarity_score"] == expected_score


@pytest.mark.asyncio
@patch("app.services.file_content_service.EmbeddingService")
async def test_search_similar_database_error(
    mock_embedding_service, mock_session
):
    """Test that database errors are raised."""
    mock_embedding_service.embed_query.return_value = [0.1, 0.2, 0.3]
    mock_session.execute.side_effect = SQLAlchemyError("DB error")

    with pytest.raises(SQLAlchemyError):
        await FileContentService.search_similar(
            query="test",
            session=mock_session,
            project_id=1,
        )


@pytest.mark.asyncio
@patch("app.services.file_content_service.EmbeddingService")
async def test_search_similar_with_similarity_threshold(
    mock_embedding_service, mock_session
):
    """Test search_similar with similarity_threshold parameter."""
    mock_embedding_service.embed_query.return_value = [0.1, 0.2, 0.3]

    expected_id = 1
    expected_content = "test content"
    expected_score = 0.85

    mock_row = MagicMock()
    mock_row.id = expected_id
    mock_row.content = expected_content
    mock_row.file_metadata = {"filename": "test.pdf"}
    mock_row.similarity_score = expected_score

    mock_result = MagicMock()
    mock_result.all.return_value = [mock_row]
    mock_session.execute.return_value = mock_result

    results = await FileContentService.search_similar(
        query="test query",
        session=mock_session,
        project_id=1,
        limit=5,
        similarity_threshold=0.8,
    )

    assert len(results) == 1
    assert results[0]["similarity_score"] == expected_score
    # Verify execute was called (query was built with threshold)
    mock_session.execute.assert_called_once()


def test_format_result():
    """Test formatting a database row."""
    expected_id = 42
    expected_content = "Sample content"
    expected_metadata = {"filename": "doc.pdf"}
    input_score = 0.87654
    expected_score = round(input_score, 4)

    mock_row = MagicMock()
    mock_row.id = expected_id
    mock_row.content = expected_content
    mock_row.file_metadata = expected_metadata
    mock_row.similarity_score = input_score

    result = FileContentService._format_result(mock_row)

    assert result["id"] == expected_id
    assert result["content"] == expected_content
    assert result["metadata"] == expected_metadata
    assert result["similarity_score"] == expected_score


def test_format_for_llm_empty_list():
    """Test formatting empty results."""
    result = FileContentService.format_for_llm([])

    assert result == "Nenhum conteúdo relevante encontrado."


def test_format_for_llm_single_result():
    """Test formatting a single result."""
    file_contents = [
        {
            "content": "Test content",
            "metadata": {"filename": "test.pdf"},
            "similarity_score": 0.95,
        }
    ]

    result = FileContentService.format_for_llm(file_contents)

    assert "[Documento 1]" in result
    assert "Arquivo: test.pdf" in result
    assert "95.00%" in result
    assert "Test content" in result


def test_format_for_llm_multiple_results():
    """Test formatting multiple results."""
    file_contents = [
        {
            "content": "Content 1",
            "metadata": {"filename": "file1.pdf"},
            "similarity_score": 0.9,
        },
        {
            "content": "Content 2",
            "metadata": {"filename": "file2.pdf"},
            "similarity_score": 0.8,
        },
    ]

    result = FileContentService.format_for_llm(file_contents)

    assert "[Documento 1]" in result
    assert "[Documento 2]" in result
    assert "file1.pdf" in result
    assert "file2.pdf" in result
    assert "---" in result


def test_format_for_llm_missing_metadata():
    """Test formatting when metadata is missing."""
    file_contents = [
        {
            "content": "Test",
            "metadata": {},
            "similarity_score": 0.5,
        }
    ]

    result = FileContentService.format_for_llm(file_contents)

    assert "Arquivo: unknown" in result
