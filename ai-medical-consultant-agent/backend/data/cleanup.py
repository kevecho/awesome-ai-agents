"""
One-shot cleanup — remove test/debug artifacts from FAISS + DB.

Run once, no args:
  cd backend
  py -m data.cleanup
"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.services.rag_service import rag_service
from app.models.database import KnowledgeDocument, SyncSessionLocal


STALE_TITLES = [
    "Test Disease",
    "__TEST_DEDUP_1__",
    "__TEST_DEDUP_2__",
]


async def cleanup():
    await rag_service.initialize()

    n_before = rag_service.index.ntotal if rag_service.index else 0
    doc_before = len(rag_service.documents)
    print(f"FAISS before: {n_before} vectors, {doc_before} documents")

    # --- FAISS cleanup ---
    to_remove = set()
    for i, meta in enumerate(rag_service.metadata):
        if meta.get("title") in STALE_TITLES:
            to_remove.add(i)

    if not to_remove:
        print("No stale FAISS entries found.")
    else:
        print(f"Removing {len(to_remove)} FAISS entries: {to_remove}")
        rag_service.documents = [
            d for i, d in enumerate(rag_service.documents) if i not in to_remove
        ]
        rag_service.metadata = [
            m for i, m in enumerate(rag_service.metadata) if i not in to_remove
        ]
        await rag_service._rebuild_index()
        print(f"FAISS after: {rag_service.index.ntotal} vectors")

    # --- DB cleanup ---
    with SyncSessionLocal() as db:
        for title in STALE_TITLES:
            n = db.query(KnowledgeDocument).filter(
                KnowledgeDocument.title == title
            ).delete()
            if n:
                print(f"DB: deleted {n} rows (title='{title}')")
        db.commit()

    # Final stats
    with SyncSessionLocal() as db:
        from sqlalchemy import func
        db_total = db.query(func.count()).select_from(KnowledgeDocument).scalar()
    print(f"\nFinal: FAISS={rag_service.index.ntotal if rag_service.index else 0}, DB={db_total}")


if __name__ == "__main__":
    asyncio.run(cleanup())
