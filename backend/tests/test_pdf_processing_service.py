"""Unit tests for PDFProcessingService."""

from unittest.mock import MagicMock, patch

from langchain_core.documents import Document

from app.services.pdf_processing_service import PDFProcessingService


def test_create_document():
    """Test creating a LangChain Document."""
    text = "Test content"
    source = "test.pdf"

    result = PDFProcessingService.create_document(text, source)

    assert isinstance(result, Document)
    assert result.page_content == text
    assert result.metadata["source"] == source


def test_create_document_empty_text():
    """Test creating a document with empty text."""
    result = PDFProcessingService.create_document("", "test.pdf")

    assert not result.page_content
    assert result.metadata["source"] == "test.pdf"


def test_split_into_chunks_short_document():
    """Test splitting a short document returns single chunk."""
    doc = Document(
        page_content="Short content",
        metadata={"source": "test.pdf"}
    )

    result = PDFProcessingService.split_into_chunks(doc, chunk_size=1000)

    assert len(result) == 1


def test_split_into_chunks_long_document():
    """Test splitting a long document returns multiple chunks."""
    doc = Document(page_content="A" * 3000, metadata={"source": "test.pdf"})

    result = PDFProcessingService.split_into_chunks(
        doc, chunk_size=1000, chunk_overlap=200
    )

    assert len(result) > 1


def test_split_into_chunks_preserves_metadata():
    """Test that metadata is preserved in chunks."""
    doc = Document(page_content="A" * 2000, metadata={"source": "test.pdf"})

    result = PDFProcessingService.split_into_chunks(doc, chunk_size=500)

    for chunk in result:
        assert chunk.metadata["source"] == "test.pdf"


def test_split_into_chunks_accepts_list():
    """Test that split_into_chunks accepts a list of documents."""
    num_docs = 2
    docs = [
        Document(page_content="A" * 2000, metadata={"source": "test1.pdf"}),
        Document(page_content="B" * 2000, metadata={"source": "test2.pdf"}),
    ]

    result = PDFProcessingService.split_into_chunks(docs, chunk_size=500)

    assert len(result) > num_docs


@patch("app.services.pdf_processing_service.pymupdf4llm")
@patch("app.services.pdf_processing_service.pymupdf")
def test_pdf_to_markdown(mock_pymupdf, mock_pymupdf4llm):
    """Test PDF to markdown conversion."""
    mock_doc = MagicMock()
    mock_pymupdf.open.return_value = mock_doc
    mock_pymupdf4llm.to_markdown.return_value = "# Title\n\nContent"

    result = PDFProcessingService.pdf_to_markdown("/path/to/test.pdf")

    assert result == "# Title\n\nContent"
    mock_pymupdf.open.assert_called_once_with("/path/to/test.pdf")
    mock_pymupdf4llm.to_markdown.assert_called_once_with(mock_doc)
    mock_doc.close.assert_called_once()


@patch("app.services.pdf_processing_service.EmbeddingService")
def test_prepare_chunks_for_db(mock_embedding_service):
    """Test preparing chunks for database insertion."""
    mock_embedding_service.embed_documents.return_value = [
        [0.1, 0.2, 0.3],
        [0.4, 0.5, 0.6],
    ]

    chunks = [
        Document(page_content="Chunk 1", metadata={"source": "test.pdf"}),
        Document(page_content="Chunk 2", metadata={"source": "test.pdf"}),
    ]

    result = PDFProcessingService._prepare_chunks_for_db(chunks, project_id=1)

    assert len(result) == len(chunks)
    assert result[0]["project_id"] == 1
    assert result[0]["content"] == "Chunk 1"
    assert result[0]["embedding"] == [0.1, 0.2, 0.3]
    assert result[0]["file_metadata"]["filename"] == "test.pdf"


@patch("app.services.pdf_processing_service.EmbeddingService")
def test_prepare_chunks_for_db_fallback(mock_embedding_service):
    """Test fallback to individual processing when batch fails."""
    mock_embedding_service.embed_documents.side_effect = Exception(
        "Batch failed"
    )
    mock_embedding_service.embed_query.return_value = [0.1, 0.2, 0.3]

    chunks = [
        Document(page_content="Chunk 1", metadata={"source": "test.pdf"}),
    ]

    result = PDFProcessingService._prepare_chunks_for_db(chunks, project_id=1)

    assert len(result) == len(chunks)
    mock_embedding_service.embed_query.assert_called_once()


@patch("app.services.pdf_processing_service.EmbeddingService")
@patch("builtins.print")
def test_prepare_chunks_for_db_fallback_progress(
    mock_print,
    mock_embedding_service
):
    """Test fallback prints progress every 10 chunks."""
    mock_embedding_service.embed_documents.side_effect = Exception(
        "Batch failed"
    )
    mock_embedding_service.embed_query.return_value = [0.1, 0.2, 0.3]

    num_chunks = 15
    chunks = [
        Document(page_content=f"Chunk {i}", metadata={"source": "test.pdf"})
        for i in range(num_chunks)
    ]

    result = PDFProcessingService._prepare_chunks_for_db(chunks, project_id=1)

    assert len(result) == num_chunks
    # Should print progress at chunk 10 (index 9)
    progress_calls = [
        call for call in mock_print.call_args_list
        if "Processed" in str(call)
    ]
    assert len(progress_calls) == 1


@patch("app.services.pdf_processing_service.EmbeddingService")
@patch("builtins.print")
def test_prepare_chunks_for_db_fallback_chunk_error(
    mock_print, mock_embedding_service
):
    """Test fallback continues when individual chunk fails."""
    mock_embedding_service.embed_documents.side_effect = Exception(
        "Batch failed"
    )
    # First call fails, second succeeds
    mock_embedding_service.embed_query.side_effect = [
        Exception("Chunk error"),
        [0.1, 0.2, 0.3],
    ]

    chunks = [
        Document(page_content="Chunk 0", metadata={"source": "test.pdf"}),
        Document(page_content="Chunk 1", metadata={"source": "test.pdf"}),
    ]

    result = PDFProcessingService._prepare_chunks_for_db(chunks, project_id=1)

    # Only 1 record should be created (second chunk)
    assert len(result) == 1
    # Should have printed error for first chunk
    error_calls = [
        call for call in mock_print.call_args_list
        if "Error processing chunk" in str(call)
    ]
    assert len(error_calls) == 1


@patch.object(PDFProcessingService, "pdf_to_markdown")
@patch.object(PDFProcessingService, "_prepare_chunks_for_db")
def test_process_pdf_file(mock_prepare, mock_to_markdown):
    """Test complete PDF processing pipeline."""
    mock_to_markdown.return_value = "# Title\n\nTest content"
    expected_result = [{"project_id": 1, "content": "chunk"}]
    mock_prepare.return_value = expected_result

    result = PDFProcessingService.process_pdf_file(
        pdf_path="/path/to/test.pdf",
        filename="test.pdf",
        project_id=1,
    )

    mock_to_markdown.assert_called_once_with("/path/to/test.pdf")
    assert result == expected_result
