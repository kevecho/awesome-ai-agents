"""
Retrieval evaluation — Recall@K, MRR, NDCG@K on labeled queries.

The eval loads the real FAISS index and runs actual vector + sparse search
(no mocking), then scores against human-labeled relevant titles.

Usage:
  cd backend
  py -m eval.eval_retrieval               # default: @1, @3, @5
  py -m eval.eval_retrieval --top-k 10    # extend to @10
  py -m eval.eval_retrieval --verbose     # per-query breakdown
"""

import argparse
import asyncio
import json
import math
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.services.rag_service import rag_service
from app.config import settings


# ============================================================
# Metrics
# ============================================================

def _any_relevant(retrieved_title: str, relevant_titles: set[str]) -> bool:
    """Check if a retrieved chunk title matches any relevant label (fuzzy substring)."""
    rt = retrieved_title.strip()
    for rel in relevant_titles:
        if rel in rt:
            return True
    return False


def recall_at_k(relevant_titles: set[str], retrieved_titles: list[str], k: int) -> float:
    """Fraction of relevant docs found in top-K results (fuzzy title match)."""
    if not relevant_titles:
        return 1.0
    top_k_titles = retrieved_titles[:k]
    found = sum(1 for t in top_k_titles if _any_relevant(t, relevant_titles))
    return found / len(relevant_titles)


def mrr(relevant_titles: set[str], retrieved_titles: list[str]) -> float:
    """Mean Reciprocal Rank — 1/rank of first relevant hit, or 0."""
    for i, title in enumerate(retrieved_titles, start=1):
        if _any_relevant(title, relevant_titles):
            return 1.0 / i
    return 0.0


def ndcg_at_k(relevant_titles: set[str], retrieved_titles: list[str], k: int) -> float:
    """Normalized DCG — penalizes relevant docs appearing late."""
    top_k_titles = retrieved_titles[:k]
    # DCG
    dcg = 0.0
    for i, title in enumerate(top_k_titles, start=1):
        if _any_relevant(title, relevant_titles):
            dcg += 1.0 / math.log2(i + 1)
    # IDCG (ideal: all relevant docs ranked first)
    ideal_n = min(len(relevant_titles), k)
    idcg = sum(1.0 / math.log2(i + 1) for i in range(1, ideal_n + 1))
    return dcg / idcg if idcg > 0 else 0.0


# ============================================================
# Title matching (fuzzy — substrings for chunk names like "高血压 (第3段)")
# ============================================================

def match_title(retrieved_title: str, relevant_titles: set[str]) -> bool:
    """Check if a retrieved chunk title matches any relevant label."""
    rt = retrieved_title.strip()
    for rel in relevant_titles:
        if rel in rt:
            return True
    return False


def extract_titles(results: list[dict]) -> list[str]:
    """Pull title strings from search result dicts."""
    return [r.get("title", "") for r in results]


# ============================================================
# Eval runner
# ============================================================

async def run_eval(queries: list[dict], top_k: int, verbose: bool) -> dict:
    """Run all queries through the real RAG pipeline and score."""

    await rag_service.initialize()
    print(f"FAISS index: {rag_service.index.ntotal if rag_service.index else 0} vectors\n")

    ks = [1, 3, 5]
    if top_k > 5:
        ks.append(top_k)
    # Ensure search returns enough results
    search_k = max(top_k, 10)

    totals = {f"recall@{k}": 0.0 for k in ks}
    totals["mrr"] = 0.0
    for k in ks:
        totals[f"ndcg@{k}"] = 0.0
    totals["hits@1"] = 0

    results = []

    for q in queries:
        qid = q["id"]
        query = q["query"]
        relevant = set(q["relevant_titles"])

        t0 = time.time()
        fetched = await rag_service.search(query, top_k=search_k)
        elapsed = time.time() - t0

        titles = extract_titles(fetched)

        scores = {}
        for k in ks:
            scores[f"recall@{k}"] = recall_at_k(relevant, titles, k)
            scores[f"ndcg@{k}"] = ndcg_at_k(relevant, titles, k)
        scores["mrr"] = mrr(relevant, titles)
        scores["hits@1"] = 1.0 if scores["recall@1"] > 0 else 0.0

        for metric, val in scores.items():
            if metric in totals:
                totals[metric] += val

        if verbose:
            print(f"Q{qid:02d} '{query}'")
            print(f"     relevant: {relevant}")
            print(f"     top-3:    {titles[:3]}")
            for k in ks:
                print(f"     Recall@{k}: {scores[f'recall@{k}']:.2f}  "
                      f"NDCG@{k}: {scores[f'ndcg@{k}']:.2f}")
            print(f"     MRR: {scores['mrr']:.3f}  ({elapsed*1000:.0f}ms)")
            print()

        results.append({"id": qid, "query": query, **scores})

    # Average
    n = len(queries)
    summary = {m: v / n for m, v in totals.items()}

    print("=" * 60)
    print(f"{'Metric':<16} {'Score':>8}")
    print("-" * 28)
    for k in ks:
        print(f"{'Recall@'+str(k):<16} {summary[f'recall@{k}']:>8.4f}")
    print(f"{'MRR':<16} {summary['mrr']:>8.4f}")
    for k in ks:
        print(f"{'NDCG@'+str(k):<16} {summary[f'ndcg@{k}']:>8.4f}")
    print(f"{'Hit@1':<16} {summary['hits@1']:>8.4f}")
    print("=" * 60)

    return {"per_query": results, "summary": summary, "n_queries": n}


# ============================================================
# Main
# ============================================================

async def main(top_k: int, verbose: bool):
    eval_path = Path(__file__).resolve().parent / "eval_queries.json"
    if not eval_path.exists():
        print(f"ERROR: {eval_path} not found — run from backend/ directory")
        sys.exit(1)

    with open(eval_path, "r", encoding="utf-8") as f:
        queries = json.load(f)

    print(f"Loaded {len(queries)} labeled queries from eval_queries.json")
    print(f"Categories: {set(q.get('category','?') for q in queries)}")
    print()

    output = await run_eval(queries, top_k, verbose)

    # Save detailed results
    out_path = Path(__file__).resolve().parent / "eval_results.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
    print(f"\nDetailed results saved to {out_path}")

    return output


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="RAG retrieval evaluation")
    parser.add_argument("--top-k", type=int, default=5, help="Max K for Recall/NDCG (default: 5)")
    parser.add_argument("--verbose", action="store_true", help="Print per-query breakdown")
    args = parser.parse_args()
    asyncio.run(main(args.top_k, args.verbose))
