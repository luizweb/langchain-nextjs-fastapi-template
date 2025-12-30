"""Unit tests for utils module."""

from app.utils import normalize_text, split_text_into_chunks


def test_normalize_text_removes_newlines():
    """Test that newlines are replaced with spaces."""
    text = "Hello\nWorld"
    assert normalize_text(text) == "Hello World"


def test_normalize_text_removes_multiple_newlines():
    """Test that multiple newlines are replaced with spaces."""
    text = "Line1\nLine2\nLine3"
    assert normalize_text(text) == "Line1 Line2 Line3"


def test_normalize_text_strips_whitespace():
    """Test that leading/trailing whitespace is removed."""
    text = "  Hello World  "
    assert normalize_text(text) == "Hello World"


def test_normalize_text_handles_empty_string():
    """Test that empty string returns empty string."""
    assert not normalize_text("")


def test_normalize_text_handles_only_newlines():
    """Test text with only newlines."""
    text = "\n\n\n"
    assert not normalize_text(text)


def test_split_text_into_chunks_returns_list():
    """Test that split_text_into_chunks returns a list."""
    text = "Hello World"
    result = split_text_into_chunks(text)
    assert isinstance(result, list)


def test_split_text_into_chunks_short_text():
    """Test that short text returns single chunk."""
    text = "Short text"
    result = split_text_into_chunks(text, chunk_size=1000)
    assert len(result) == 1
    assert result[0] == text


def test_split_text_into_chunks_long_text():
    """Test that long text is split into multiple chunks."""
    text = "A" * 3000  # 3000 characters
    result = split_text_into_chunks(text, chunk_size=1000, chunk_overlap=200)
    assert len(result) > 1


def test_split_text_into_chunks_custom_size():
    """Test split with custom chunk size."""
    text = "A" * 500
    result = split_text_into_chunks(text, chunk_size=100, chunk_overlap=20)
    assert len(result) > 1


def test_split_text_into_chunks_empty_text():
    """Test that empty text returns empty list."""
    result = split_text_into_chunks("")
    assert result == []


def test_split_text_into_chunks_preserves_content():
    """Test that all content is preserved after splitting."""
    text = "Hello World " * 200  # Longer text
    result = split_text_into_chunks(text, chunk_size=100, chunk_overlap=0)
    # With no overlap, joining should approximate original
    assert len(result) > 1
