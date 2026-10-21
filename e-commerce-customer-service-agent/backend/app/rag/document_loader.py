"""
Document loader for the RAG pipeline.

Loads documents from various formats (JSON, Markdown, TXT) and
prepares them for ingestion into the knowledge base.
"""

import json
from pathlib import Path
from typing import Any

from app.utils.logger import setup_logger

logger = setup_logger(__name__)


class DocumentLoader:
    """Load documents from file system for knowledge base ingestion."""

    SUPPORTED_FORMATS = {".json", ".md", ".txt"}

    def load_file(self, file_path: str) -> list[dict[str, Any]]:
        """Load documents from a single file.

        Args:
            file_path: Path to the document file.

        Returns:
            List of document dicts with 'question' and 'answer' keys.
        """
        path = Path(file_path)

        if path.suffix not in self.SUPPORTED_FORMATS:
            raise ValueError(f"Unsupported format: {path.suffix}")

        if path.suffix == ".json":
            return self._load_json(path)
        elif path.suffix == ".md":
            return self._load_markdown(path)
        else:
            return self._load_text(path)

    def load_directory(self, directory: str) -> list[dict[str, Any]]:
        """Load all supported documents from a directory.

        Args:
            directory: Path to the directory.

        Returns:
            Combined list of documents from all files.
        """
        dir_path = Path(directory)
        documents: list[dict[str, Any]] = []

        for file_path in dir_path.rglob("*"):
            if file_path.suffix in self.SUPPORTED_FORMATS:
                try:
                    docs = self.load_file(str(file_path))
                    documents.extend(docs)
                    logger.info(f"Loaded {len(docs)} documents from {file_path.name}")
                except Exception as e:
                    logger.error(f"Failed to load {file_path}: {e}")

        return documents

    def _load_json(self, path: Path) -> list[dict[str, Any]]:
        """Load FAQ format JSON file."""
        with open(path, encoding="utf-8") as f:
            data = json.load(f)

        if isinstance(data, list):
            return data
        if isinstance(data, dict) and "faqs" in data:
            return data["faqs"]
        raise ValueError("Unsupported JSON structure")

    def _load_markdown(self, path: Path) -> list[dict[str, Any]]:
        """Parse markdown file into QA pairs.

        Splits on ## headers where each section is a Q&A pair.
        """
        with open(path, encoding="utf-8") as f:
            content = f.read()

        documents = []
        sections = content.split("\n## ")
        for section in sections[1:]:  # Skip preamble before first header
            lines = section.strip().split("\n", 1)
            question = lines[0].strip()
            answer = lines[1].strip() if len(lines) > 1 else ""
            documents.append({"question": question, "answer": answer})

        return documents

    def _load_text(self, path: Path) -> list[dict[str, Any]]:
        """Load plain text file as a single document."""
        with open(path, encoding="utf-8") as f:
            content = f.read().strip()
        return [{"question": path.stem, "answer": content}]
