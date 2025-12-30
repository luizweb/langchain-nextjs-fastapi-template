"""Service for PDF processing operations."""
from typing import Any, Dict, List

import pymupdf
import pymupdf4llm
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter

from app.services.embedding_service import EmbeddingService


class PDFProcessingService:
    """Service for processing PDF files."""

    @staticmethod
    def pdf_to_markdown(pdf_path: str) -> str:
        """Convert PDF file to Markdown format."""
        doc = pymupdf.open(pdf_path)
        try:
            md = pymupdf4llm.to_markdown(doc)
            return md
        finally:
            doc.close()

    @staticmethod
    def create_document(text: str, source: str) -> Document:
        """Create a LangChain Document."""
        return Document(
            page_content=text,
            metadata={"source": source}
        )

    @staticmethod
    def split_into_chunks(
        document: Document,
        chunk_size: int = 1000,
        chunk_overlap: int = 200,
    ) -> List[Document]:
        """Split document into smaller chunks."""
        splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            add_start_index=True,
        )

        if not isinstance(document, list):
            document = [document]

        return splitter.split_documents(document)

    @classmethod
    def process_pdf_file(
        cls,
        pdf_path: str,
        filename: str,
        project_id: int,
    ) -> List[Dict[str, Any]]:
        """
        Complete PDF processing pipeline.

        Args:
            pdf_path: Path to temporary PDF file
            filename: Original filename
            project_id: Project ID for association

        Returns:
            List of records ready for database insertion
        """
        # 1. Convert PDF to markdown
        markdown = cls.pdf_to_markdown(pdf_path)

        # 2. Create LangChain document
        document = cls.create_document(markdown, filename)

        # 3. Split into chunks
        chunks = cls.split_into_chunks(document)

        # 4. Prepare for database
        return cls._prepare_chunks_for_db(chunks, project_id)

    @staticmethod
    def _prepare_chunks_for_db(
        chunks: List[Document],
        project_id: int,
    ) -> List[Dict[str, Any]]:
        """
        Process chunks and generate embeddings.

        Uses batch processing for efficiency.
        """
        processed_records = []

        try:
            # Extract texts for batch embedding
            texts = [
                chunk.page_content.replace("\n", " ").strip()
                for chunk in chunks
            ]

            # Generate embeddings in batch (efficient!)
            embeddings = EmbeddingService.embed_documents(texts)

            # Create records
            for chunk, embedding in zip(chunks, embeddings):
                record = {
                    "project_id": project_id,
                    "file_metadata": {
                        "filename": chunk.metadata.get("source", "unknown"),
                    },
                    "content": chunk.page_content.strip(),
                    "embedding": embedding,
                }
                processed_records.append(record)

        except Exception as e:
            # Fallback to individual processing
            print(f"Batch processing failed: {e}. Trying individual...")

            for i, chunk in enumerate(chunks):
                try:
                    text = chunk.page_content.replace("\n", " ").strip()
                    embedding = EmbeddingService.embed_query(text)

                    record = {
                        "project_id": project_id,
                        "file_metadata": {
                            "filename": chunk.metadata.get(
                                "source", "unknown"
                            ),
                        },
                        "content": chunk.page_content.strip(),
                        "embedding": embedding,
                    }
                    processed_records.append(record)

                    if (i + 1) % 10 == 0:
                        print(f"Processed {i + 1}/{len(chunks)} chunks...")

                except Exception as chunk_error:
                    print(f"Error processing chunk {i}: {chunk_error}")
                    continue

        return processed_records
