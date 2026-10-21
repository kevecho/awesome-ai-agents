#!/usr/bin/env python3
"""Import knowledge base documents into the vector store."""

import asyncio
import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.rag.document_loader import DocumentLoader
from app.rag.text_splitter import TextSplitter
from app.services.rag_service import RAGService


async def import_knowledge(directory: str):
    """Load documents and add them to the knowledge base."""
    loader = DocumentLoader()
    splitter = TextSplitter(chunk_size=500, chunk_overlap=50)
    rag_service = RAGService()

    documents = loader.load_directory(directory)
    print(f"Loaded {len(documents)} documents from {directory}")

    chunks = splitter.split_documents(documents)
    print(f"Split into {len(chunks)} chunks")

    for i, chunk in enumerate(chunks):
        try:
            vector_id = await rag_service.add_document(
                question=chunk.get("question", ""),
                answer=chunk.get("chunk_text", chunk.get("answer", "")),
                category=chunk.get("category", "general"),
                keywords=chunk.get("keywords", ""),
            )
            if (i + 1) % 10 == 0:
                print(f"  Imported {i + 1}/{len(chunks)} documents...")
        except Exception as e:
            print(f"  Error importing chunk {i}: {e}")

    print(f"Import complete. {len(chunks)} chunks processed.")


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Import knowledge base documents")
    parser.add_argument(
        "--directory", "-d",
        default="../knowledge_base/faqs",
        help="Directory containing knowledge base files",
    )
    args = parser.parse_args()

    directory = os.path.abspath(args.directory)
    if not os.path.isdir(directory):
        print(f"Error: Directory not found: {directory}")
        sys.exit(1)

    asyncio.run(import_knowledge(directory))
