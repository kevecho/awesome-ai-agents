"""
Text splitter for chunking long documents.

Splits documents into smaller chunks while preserving semantic boundaries
for more effective embedding and retrieval.
"""

from typing import Any

from app.utils.logger import setup_logger

logger = setup_logger(__name__)


class TextSplitter:
    """Split long text into overlapping chunks.

    Uses a recursive character-based approach with configurable
    chunk size and overlap.
    """

    def __init__(
        self,
        chunk_size: int = 500,
        chunk_overlap: int = 50,
        separators: list[str] | None = None,
    ):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.separators = separators or ["\n\n", "\n", ". ", " ", ""]

    def split_text(self, text: str) -> list[str]:
        """Split text into overlapping chunks.

        Args:
            text: Input text to split.

        Returns:
            List of text chunks.
        """
        if len(text) <= self.chunk_size:
            return [text]

        chunks: list[str] = []
        for separator in self.separators:
            if separator in text:
                parts = text.split(separator)
                break
        else:
            parts = [text]

        current_chunk = ""
        for part in parts:
            if (
                len(current_chunk) + len(part) + len(separator) <= self.chunk_size
                or not current_chunk
            ):
                current_chunk += (separator if current_chunk else "") + part
            else:
                if current_chunk:
                    chunks.append(current_chunk)
                current_chunk = part

        if current_chunk:
            chunks.append(current_chunk)

        return chunks

    def split_documents(
        self, documents: list[dict[str, Any]]
    ) -> list[dict[str, Any]]:
        """Split a list of documents into chunked sub-documents.

        Args:
            documents: List of dicts with at minimum an 'answer' key.

        Returns:
            List of chunked document dicts with added chunk metadata.
        """
        chunked = []
        for doc in documents:
            text = f"Q: {doc.get('question', '')}\nA: {doc.get('answer', '')}"
            chunks = self.split_text(text)

            for i, chunk in enumerate(chunks):
                chunked.append({
                    **doc,
                    "chunk_index": i,
                    "chunk_text": chunk,
                    "total_chunks": len(chunks),
                })

        return chunked
