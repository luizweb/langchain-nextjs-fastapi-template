"""Unit tests for RAG agent."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.agents.rag import (
    SYSTEM_PROMPT,
    ProjectContext,
    search_project_documents,
)


def test_project_context_dataclass():
    """Test ProjectContext dataclass creation."""
    mock_session = MagicMock()
    project_id = 42

    context = ProjectContext(project_id=project_id, session=mock_session)

    assert context.project_id == project_id
    assert context.session == mock_session


def test_project_context_with_different_values():
    """Test ProjectContext with various project IDs."""
    mock_session = MagicMock()
    project_id_1 = 1
    project_id_2 = 100

    context1 = ProjectContext(project_id=project_id_1, session=mock_session)
    context2 = ProjectContext(project_id=project_id_2, session=mock_session)

    assert context1.project_id == project_id_1
    assert context2.project_id == project_id_2


def test_system_prompt_exists():
    """Test that system prompt is defined."""
    assert SYSTEM_PROMPT is not None
    assert isinstance(SYSTEM_PROMPT, str)
    assert len(SYSTEM_PROMPT) > 0


def test_system_prompt_contains_tool_reference():
    """Test that system prompt references the search tool."""
    assert "search_project_documents" in SYSTEM_PROMPT


@pytest.mark.asyncio
@patch("app.agents.rag.FileContentService")
async def test_search_project_documents_calls_service(mock_file_service):
    """Test search_project_documents calls FileContentService."""
    mock_file_service.search_similar = AsyncMock(return_value=[
        {"content": "test", "similarity_score": 0.9, "metadata": {}}
    ])
    mock_file_service.format_for_llm.return_value = "Formatted content"

    mock_session = AsyncMock()
    project_id = 1
    query = "test query"

    context = ProjectContext(project_id=project_id, session=mock_session)
    mock_runtime = MagicMock()
    mock_runtime.context = context

    result = await search_project_documents.coroutine(mock_runtime, query)

    mock_file_service.search_similar.assert_called_once_with(
        query=query,
        session=mock_session,
        project_id=project_id
    )
    mock_file_service.format_for_llm.assert_called_once()
    assert result == "Formatted content"


@pytest.mark.asyncio
@patch("app.agents.rag.FileContentService")
async def test_search_project_documents_empty_results(mock_file_service):
    """Test search_project_documents with no results."""
    mock_file_service.search_similar = AsyncMock(return_value=[])
    mock_file_service.format_for_llm.return_value = (
        "Nenhum conteúdo relevante encontrado."
    )

    mock_session = AsyncMock()
    context = ProjectContext(project_id=1, session=mock_session)
    mock_runtime = MagicMock()
    mock_runtime.context = context

    result = await search_project_documents.coroutine(mock_runtime, "query")

    assert result == "Nenhum conteúdo relevante encontrado."


@pytest.mark.asyncio
@patch("app.agents.rag.FileContentService")
async def test_search_project_documents_formats_results(mock_file_service):
    """Test that search results are formatted for LLM."""
    search_results = [
        {
            "content": "Document content",
            "similarity_score": 0.95,
            "metadata": {"filename": "test.pdf"}
        }
    ]
    mock_file_service.search_similar = AsyncMock(return_value=search_results)
    mock_file_service.format_for_llm.return_value = "[Documento 1]\nContent"

    mock_session = AsyncMock()
    context = ProjectContext(project_id=1, session=mock_session)
    mock_runtime = MagicMock()
    mock_runtime.context = context

    result = await search_project_documents.coroutine(mock_runtime, "query")

    mock_file_service.format_for_llm.assert_called_once_with(search_results)
    assert "[Documento 1]" in result
