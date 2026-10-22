"""
Bulk import script — AI Medical Consultant RAG knowledge base.

Input:
  data/diseases.json, data/drugs.json, data/exams.json  (structured JSON)
  data/pdfs/*.pdf                                        (clinical guidelines)

Output:
  FAISS index (IndexFlatL2) + DB (knowledge_documents table)

Usage:
  cd backend
  py -m data.import_bulk          # sample import (~1500 chunks)
  py -m data.import_bulk --all    # import ALL entries (slow on CPU)

Design notes:
  - Top-N by content length per category (longer = more info-dense for RAG)
  - PDF → pdfplumber → clean (headers/footers/line-merge) → chunk
  - Batch embedding (100/batch) to keep memory in check
  - Resets FAISS + DB before import (idempotent re-run safe)

Target:   800–1500 chunks  (default mode, ~2-3 min on CPU)
Full:     ~40K   chunks  (--all mode,   ~20-30 min depending on CPU)
"""

import argparse
import asyncio
import json
import re
import sys
import time
from pathlib import Path

import ijson

# Add backend to path (this file is at backend/data/import_bulk.py)
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.services.rag_service import rag_service
from app.models.database import KnowledgeDocument, SyncSessionLocal
from app.config import settings
from langchain.text_splitter import RecursiveCharacterTextSplitter
from loguru import logger

# ============================================================
# Paths & limits
# ============================================================

DATA_DIR = Path(__file__).resolve().parent
PDF_DIR = DATA_DIR / "pdfs"
BATCH_SIZE = 100

# Per-category sample sizes (default mode: ~1400 chunks)
SAMPLE_SIZES = {
    "disease": 500,
    "drug": 400,
    "exam": 200,
}

# ============================================================
# PDF cleaning
# ============================================================

def pdf_to_clean_text(pdf_path: Path) -> str:
    """Extract text from a medical guideline PDF and clean artifacts."""
    import pdfplumber

    with pdfplumber.open(str(pdf_path)) as pdf:
        pages_text = []
        for page in pdf.pages:
            t = page.extract_text()
            if t:
                pages_text.append(t)
        full_text = "\n".join(pages_text)

    # --- Page headers / footers ---
    full_text = re.sub(r'^\s*第\s*\d+\s*页\s*$', '', full_text, flags=re.MULTILINE)
    # Journal names & running heads
    full_text = re.sub(r'中华.*?杂志.*?\n', '', full_text)
    full_text = re.sub(r'Chin\s+J\s+\S+\s*,?\s*\w+\s*\d{4}.*?\n', '', full_text)
    # DOI / copyright lines
    full_text = re.sub(r'DOI:.*?\n', '', full_text)
    # Standalone numbers (page numbers that survived)
    full_text = re.sub(r'^\s*\d{1,4}\s*$', '', full_text, flags=re.MULTILINE)
    # "通信作者：" / "作者单位：" lines (short metadata, low RAG value)
    full_text = re.sub(r'^(通信作者|作者单位|基金项目|收稿日期)[：:].*$', '', full_text, flags=re.MULTILINE)

    # --- Merge broken lines ---
    # Strategy: collapse all newlines → re-split at sentence boundaries
    full_text = re.sub(r'\n{2,}', '\n\n', full_text)          # keep paragraph breaks
    text = re.sub(r'(?<!。)(?<!！)(?<!？)\n(?!\n)', '', full_text)  # merge intra-sentence breaks
    text = re.sub(r' {2,}', ' ', text)
    text = re.sub(r'\n{3,}', '\n\n', text)

    return text.strip()


def filter_chunks(chunks: list[str]) -> list[str]:
    """Remove TOC artifacts, pure-number lines, and ultra-short fragments."""
    out = []
    for c in chunks:
        c = c.strip()
        if len(c) < 20:
            continue
        # Ratio of meaningful characters (CJK + ASCII letters)
        meaningful = sum(1 for ch in c if '一' <= ch <= '鿿' or ch.isalpha())
        if meaningful / len(c) < 0.35:
            continue
        out.append(c)
    return out


# ============================================================
# Chunking
# ============================================================

def get_splitter() -> RecursiveCharacterTextSplitter:
    return RecursiveCharacterTextSplitter(
        chunk_size=settings.CHUNK_SIZE,
        chunk_overlap=settings.CHUNK_OVERLAP,
        separators=["\n\n", "\n", "。", "！", "？", "，", " ", ""],
    )


def make_chunks(content: str, title: str, category: str, source: str) -> list[dict]:
    """
    Split a single document into 1+ chunks.
    Returns list of {text, metadata} dicts.
    """
    if len(content) <= settings.CHUNK_SIZE:
        return [{"text": content, "metadata": {
            "title": title, "category": category, "source": source,
        }}]

    splitter = get_splitter()
    subs = filter_chunks(splitter.split_text(content))
    return [
        {"text": s, "metadata": {
            "title": f"{title} (第{i+1}段)",
            "category": category,
            "source": source,
        }}
        for i, s in enumerate(subs)
    ]


# ============================================================
# Import engine
# ============================================================

async def import_one_batch(chunks: list[dict], batch_no: int, total_batches: int, label: str) -> int:
    """Embed + FAISS add + DB insert for one batch."""
    if not chunks:
        return 0

    texts = [c["text"] for c in chunks]
    metadatas = [c["metadata"] for c in chunks]

    # FAISS (embeds internally)
    added = await rag_service.add_documents(texts, metadatas)

    # DB
    with SyncSessionLocal() as db:
        for c in chunks:
            db.add(KnowledgeDocument(
                title=c["metadata"]["title"],
                category=c["metadata"]["category"],
                content=c["text"],
                source=c["metadata"].get("source", ""),
            ))
        db.commit()

    ntotal = rag_service.index.ntotal if rag_service.index else 0
    print(f"  [{label}] batch {batch_no}/{total_batches}  +{added}  FAISS total={ntotal}")
    return added


async def import_stream(chunks: list[dict], label: str) -> int:
    """Batch-import a list of chunks with progress."""
    total_batches = (len(chunks) + BATCH_SIZE - 1) // BATCH_SIZE
    total = 0
    for i in range(0, len(chunks), BATCH_SIZE):
        batch = chunks[i:i + BATCH_SIZE]
        total += await import_one_batch(batch, i // BATCH_SIZE + 1, total_batches, label)
    return total


# ============================================================
# Main
# ============================================================

async def main(sample: bool):
    t0 = time.time()

    print("=" * 60)
    print("Medical RAG — Bulk Import")
    print(f"Mode: {'sample (~1500 chunks)' if sample else 'FULL (all entries)'}")
    print("=" * 60)

    # --- Init ---
    print("\n[Init] Loading embedding model...")
    await rag_service.initialize()
    print(f"  Model loaded. Existing FAISS vectors: "
          f"{rag_service.index.ntotal if rag_service.index else 0}")

    # --- Reset ---
    print("\n[Init] Resetting index + DB for clean import...")
    rag_service.index = None
    rag_service.documents = []
    rag_service.metadata = []
    with SyncSessionLocal() as db:
        n = db.query(KnowledgeDocument).delete()
        db.commit()
        print(f"  DB: deleted {n} stale rows")

    grand_total = 0
    chunk_lengths = []   # for stats

    # ================================================================
    # Phase 1 — Structured JSON
    # ================================================================
    json_sources = [
        ("diseases.json", "disease"),
        ("drugs.json",    "drug"),
        ("exams.json",    "exam"),
    ]

    for filename, category in json_sources:
        path = DATA_DIR / filename
        if not path.exists():
            print(f"\n[JSON] {filename}: NOT FOUND — skip")
            continue

        print(f"\n[JSON] Loading {filename}...")

        # Stream-load to avoid OOM on 96MB files
        entries = []
        with open(path, "r", encoding="utf-8") as f:
            for obj in ijson.items(f, "item"):
                entries.append(obj)
        print(f"  Loaded {len(entries)} raw entries")

        # Sample: pick longest articles (most information-dense)
        if sample and category in SAMPLE_SIZES:
            limit = SAMPLE_SIZES[category]
            entries.sort(key=lambda e: len(e.get("content", "")), reverse=True)
            entries = entries[:limit]
            print(f"  Sampled top {limit} by content length")
        else:
            print(f"  All {len(entries)} entries")

        # Chunk each entry
        all_chunks = []
        for e in entries:
            all_chunks.extend(make_chunks(
                content=e.get("content", ""),
                title=e.get("title", ""),
                category=category,
                source=e.get("source", ""),
            ))
        print(f"  {len(all_chunks)} chunks ready")

        imported = await import_stream(all_chunks, filename)
        grand_total += imported
        chunk_lengths.extend(len(c["text"]) for c in all_chunks)

    # ================================================================
    # Phase 2 — PDF guidelines
    # ================================================================
    pdf_files = sorted(PDF_DIR.glob("*.pdf")) if PDF_DIR.exists() else []
    if pdf_files:
        print(f"\n[PDF] {len(pdf_files)} file(s) found")
        for pdf_path in pdf_files:
            print(f"\n[PDF] {pdf_path.name}")
            try:
                text = pdf_to_clean_text(pdf_path)
                print(f"  Cleaned text: {len(text)} chars")
            except Exception as exc:
                print(f"  SKIP — extraction failed: {exc}")
                continue

            pdf_chunks = make_chunks(
                content=text,
                title=pdf_path.stem,
                category="guideline",
                source=pdf_path.name,
            )
            print(f"  {len(pdf_chunks)} chunks ready")

            imported = await import_stream(pdf_chunks, pdf_path.name)
            grand_total += imported
            chunk_lengths.extend(len(c["text"]) for c in pdf_chunks)
    else:
        print("\n[PDF] No PDFs found — skip")

    # ================================================================
    # Summary
    # ================================================================
    elapsed = time.time() - t0
    print("\n" + "=" * 60)
    print(f"Import finished in {elapsed:.0f}s")
    print(f"  Total chunks  : {grand_total}")
    print(f"  FAISS vectors : {rag_service.index.ntotal if rag_service.index else 0}")

    # DB breakdown
    with SyncSessionLocal() as db:
        from sqlalchemy import func
        rows = db.query(
            KnowledgeDocument.category,
            func.count(KnowledgeDocument.id),
        ).group_by(KnowledgeDocument.category).all()
        db_total = sum(c for _, c in rows)
        print(f"  DB rows       : {db_total}")
        for cat, cnt in rows:
            print(f"    {cat:12s} {cnt:>6}")

    # Chunk length stats
    if chunk_lengths:
        chunk_lengths.sort()
        print(f"  Chunk length  : min={chunk_lengths[0]}  "
              f"max={chunk_lengths[-1]}  "
              f"mean={sum(chunk_lengths)//len(chunk_lengths)}  "
              f"median={chunk_lengths[len(chunk_lengths)//2]}")
    print("=" * 60)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Bulk-import medical knowledge into FAISS + DB")
    parser.add_argument("--all", action="store_true", help="Import ALL entries (default: sample)")
    args = parser.parse_args()
    asyncio.run(main(sample=not args.all))
