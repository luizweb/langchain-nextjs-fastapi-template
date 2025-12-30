"""Utility functions - generic helpers only."""
from typing import List

from langchain_text_splitters import RecursiveCharacterTextSplitter


def normalize_text(text: str) -> str:
    """Normalize text by removing extra whitespace."""
    return text.replace("\n", " ").strip()


def split_text_into_chunks(
    text: str,
    chunk_size: int = 1000,
    chunk_overlap: int = 200,
) -> List[str]:
    """Split text into chunks using RecursiveCharacterTextSplitter."""
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
    )
    return splitter.split_text(text)
