"""
双轨评测框架 — 合成集 (chunk_id 精确匹配) + 人工难题集 (四类指标)。

用法:
  cd backend
  py -m eval.benchmark.run_benchmark                     # 默认跑双轨
  py -m eval.benchmark.run_benchmark --track synthetic   # 仅合成集
  py -m eval.benchmark.run_benchmark --track hard        # 仅人工难题集
  py -m eval.benchmark.run_benchmark --verbose           # 逐条打印
"""
import argparse
import asyncio
import json
import math
import sys
import time
from pathlib import Path
from typing import Optional

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from app.services.rag_service import rag_service
from app.config import settings

BENCHMARK_DIR = Path(__file__).resolve().parent
SYNTHETIC_PATH = BENCHMARK_DIR / "synthetic_queries.json"
HARD_PATH = BENCHMARK_DIR / "hard_queries.json"
OUTPUT_PATH = BENCHMARK_DIR / "benchmark_results.json"


# ============================================================
# 指标函数
# ============================================================

def _fuzzy_match(retrieved_title: str, relevant_titles: set[str]) -> bool:
    """模糊子串匹配（兼容旧格式）。"""
    rt = retrieved_title.strip()
    for rel in relevant_titles:
        if rel and rel in rt:
            return True
    return False


def hit_at_k_chunk(target_idx: int, retrieved_indices: list[int], k: int) -> bool:
    """合成集 — chunk_id 精确命中。"""
    return target_idx in retrieved_indices[:k]


def recall_at_k(relevant_titles: set[str], retrieved_titles: list[str], k: int) -> float:
    """人工集 — 模糊标题匹配 Recall@K。"""
    if not relevant_titles:
        return 1.0
    found = sum(1 for t in retrieved_titles[:k] if _fuzzy_match(t, relevant_titles))
    return found / len(relevant_titles)


def recall_pair_at_k(relevant_titles: set[str], retrieved_titles: list[str], k: int) -> float:
    """人工集-多跳 — 所有标注标题都出现在 top-K。"""
    if not relevant_titles:
        return 1.0
    hit_all = all(
        any(_fuzzy_match(t, {rel}) for t in retrieved_titles[:k])
        for rel in relevant_titles
    )
    return 1.0 if hit_all else 0.0


def mrr(relevant_titles: set[str], retrieved_titles: list[str]) -> float:
    """Mean Reciprocal Rank。"""
    for i, title in enumerate(retrieved_titles, start=1):
        if _fuzzy_match(title, relevant_titles):
            return 1.0 / i
    return 0.0


def ndcg_at_k(relevant_titles: set[str], retrieved_titles: list[str], k: int) -> float:
    """Normalized DCG@K。"""
    top = retrieved_titles[:k]
    dcg = sum(
        1.0 / math.log2(i + 1)
        for i, t in enumerate(top, start=1) if _fuzzy_match(t, relevant_titles)
    )
    ideal_n = min(len(relevant_titles), k)
    idcg = sum(1.0 / math.log2(i + 1) for i in range(1, ideal_n + 1))
    return dcg / idcg if idcg > 0 else 0.0


# ============================================================
# 单轨评测
# ============================================================

async def eval_synthetic(queries: list[dict], top_k: int, verbose: bool) -> dict:
    """合成集评测 — chunk_id 精确匹配。

    每条 query 格式: {"id": N, "query": "...", "chunk_index": 12345, "category": "disease"}
    """
    if not rag_service.index or rag_service.index.ntotal == 0:
        await rag_service.initialize()

    total_vectors = rag_service.index.ntotal if rag_service.index else 0
    ks = sorted(set([1, 3, 5, top_k]))
    search_k = max(ks) * 2

    totals = {f"hit@{k}": 0 for k in ks}
    totals["queries"] = 0
    per_query = []

    for q in queries:
        target_idx = q["chunk_index"]
        retrieved = await rag_service.search(q["query"], top_k=search_k, score_threshold=0.0)
        retrieved_indices = [r["index"] for r in retrieved]

        scores = {}
        for k in ks:
            scores[f"hit@{k}"] = 1.0 if hit_at_k_chunk(target_idx, retrieved_indices, k) else 0.0
            totals[f"hit@{k}"] += scores[f"hit@{k}"]
        totals["queries"] += 1

        if verbose:
            hit_k = next((k for k in ks if scores[f"hit@{k}"]), None)
            print(f"  Q{q['id']:03d} '{q['query'][:50]}' → "
                  f"{'HIT@'+str(hit_k) if hit_k else 'MISS'} | "
                  f"target=chunk#{target_idx}, top-3={retrieved_indices[:3]}")

        per_query.append({"id": q["id"], "query": q["query"], **scores})

    n = totals["queries"]
    summary = {"track": "synthetic", "n_queries": n, "faiss_vectors": total_vectors}
    for k in ks:
        summary[f"hit@{k}"] = totals[f"hit@{k}"] / n if n else 0.0

    return {"summary": summary, "per_query": per_query}


async def eval_hard(queries: list[dict], top_k: int, verbose: bool) -> dict:
    """人工难题集评测 — 四类分报告。

    每条 query 格式:
      {"id": N, "query": "...", "category": "...", "type": "...",
       "relevant_titles": [...] 或 [] (无答案类)}
    """
    if not rag_service.index or rag_service.index.ntotal == 0:
        await rag_service.initialize()

    total_vectors = rag_service.index.ntotal if rag_service.index else 0
    ks = sorted(set([1, 3, 5, top_k]))
    search_k = max(ks) * 2

    # 分类聚合
    by_type = {}  # type -> {metric: sum, queries: count}
    all_totals = {f"recall@{k}": 0.0 for k in ks}
    all_totals["mrr"] = 0.0
    for k in ks:
        all_totals[f"ndcg@{k}"] = 0.0
        all_totals[f"pair@{k}"] = 0.0
    all_totals["hits@1"] = 0
    all_totals["queries"] = 0
    # 无答案专用
    all_totals["abstention"] = 0
    all_totals["max_similarity_sum"] = 0.0

    per_query = []

    for q in queries:
        qtype = q.get("type", "synonym")
        relevant = set(q.get("relevant_titles", []))
        is_no_answer = (qtype == "no_answer")

        retrieved = await rag_service.search(q["query"], top_k=search_k, score_threshold=0.0)
        titles = [r.get("title", "") for r in retrieved]

        scores = {}
        if is_no_answer:
            # 无答案类：反向指标
            # Abstention: top-K 中确实无相关文档
            top_k_titles = titles[:top_k]
            any_relevant = any(_fuzzy_match(t, relevant) for t in top_k_titles)
            scores["abstention"] = 0.0 if any_relevant else 1.0
            all_totals["abstention"] += scores["abstention"]
            # 最高相似度分数
            max_sim = max((r.get("score", 0.0) for r in retrieved[:top_k]), default=0.0)
            scores["max_similarity"] = max_sim
            all_totals["max_similarity_sum"] += max_sim
        else:
            scores["abstention"] = 0.0
            scores["max_similarity"] = 0.0
            for k in ks:
                scores[f"recall@{k}"] = recall_at_k(relevant, titles, k)
                scores[f"ndcg@{k}"] = ndcg_at_k(relevant, titles, k)
                all_totals[f"recall@{k}"] += scores[f"recall@{k}"]
                all_totals[f"ndcg@{k}"] += scores[f"ndcg@{k}"]
                # 多跳类额外算 pair
                if qtype == "multi_hop":
                    scores[f"pair@{k}"] = recall_pair_at_k(relevant, titles, k)
                    all_totals[f"pair@{k}"] += scores[f"pair@{k}"]
            scores["mrr"] = mrr(relevant, titles)
            all_totals["mrr"] += scores["mrr"]
            if scores.get("recall@1", 0) > 0:
                all_totals["hits@1"] += 1
                scores["hits@1"] = 1.0
            else:
                scores["hits@1"] = 0.0

        all_totals["queries"] += 1

        # 按 type 聚合
        if qtype not in by_type:
            by_type[qtype] = {k: 0.0 for k in scores}
            by_type[qtype]["queries"] = 0
        for k, v in scores.items():
            by_type[qtype][k] = by_type[qtype].get(k, 0.0) + v
        by_type[qtype]["queries"] += 1

        if verbose:
            top3 = titles[:3]
            print(f"  Q{q['id']:03d} [{qtype}] '{q['query'][:50]}' → relevant={relevant}")
            print(f"       top-3: {top3}")
            for k in ks:
                if f"recall@{k}" in scores:
                    print(f"       Recall@{k}={scores[f'recall@{k}']:.2f}  "
                          f"NDCG@{k}={scores[f'ndcg@{k}']:.2f}", end="")
                    if f"pair@{k}" in scores:
                        print(f"  Pair@{k}={scores[f'pair@{k}']:.2f}", end="")
                    print()
            if is_no_answer:
                print(f"       Abstention={scores['abstention']:.0f}  "
                      f"MaxSim={scores['max_similarity']:.3f}", end="")
                if scores['abstention'] == 0:
                    print(" [HALLUCINATION RISK]")
                else:
                    print(" [OK: abstained]")
            print()

        per_query.append({"id": q["id"], "query": q["query"], "type": qtype, **scores})

    # 汇总
    n = all_totals["queries"]
    summary = {"track": "hard", "n_queries": n, "faiss_vectors": total_vectors}
    for k in ks:
        summary[f"recall@{k}"] = all_totals[f"recall@{k}"] / n if n else 0.0
    summary["mrr"] = all_totals["mrr"] / n if n else 0.0
    for k in ks:
        summary[f"ndcg@{k}"] = all_totals[f"ndcg@{k}"] / n if n else 0.0
    summary["hits@1"] = all_totals["hits@1"] / n if n else 0.0
    # 多跳专用
    for k in ks:
        pair_queries = by_type.get("multi_hop", {}).get("queries", 0)
        summary[f"pair@{k}"] = (all_totals[f"pair@{k}"] / pair_queries
                                if pair_queries else None)
    # 无答案专用
    no_answer_queries = by_type.get("no_answer", {}).get("queries", 0)
    summary["abstention_rate"] = (all_totals["abstention"] / no_answer_queries
                                  if no_answer_queries else None)
    summary["avg_max_similarity"] = (all_totals["max_similarity_sum"] / no_answer_queries
                                     if no_answer_queries else None)

    # 按 type 分报告
    type_reports = {}
    for t, agg in by_type.items():
        n_t = agg["queries"]
        rpt = {"queries": n_t}
        for metric, val in agg.items():
            if metric != "queries":
                rpt[metric] = val / n_t if n_t else 0.0
        type_reports[t] = rpt

    return {"summary": summary, "type_reports": type_reports, "per_query": per_query}


# ============================================================
# 打印与合并
# ============================================================

def print_summary(summary: dict, track_name: str):
    print(f"\n{'='*60}")
    print(f"  {track_name} (n={summary['n_queries']}, vectors={summary['faiss_vectors']})")
    print(f"{'='*60}")
    for k, v in summary.items():
        if k in ("track", "n_queries", "faiss_vectors"):
            continue
        if v is None:
            continue
        print(f"  {k:<22s} {v:>8.4f}")
    print(f"{'='*60}")


def compute_weighted_score(synthetic: dict, hard: dict) -> float:
    """加权总分：0.4×合成Hit@3 + 0.3×人工Recall@3 + 0.2×人工Pair@3 + 0.1×拒答率。"""
    syn_hit3 = synthetic.get("hit@3", 0.0)
    hard_recall3 = hard.get("recall@3", 0.0)
    hard_pair3 = hard.get("pair@3")
    hard_abstention = hard.get("abstention_rate")

    pair = hard_pair3 if hard_pair3 is not None else 1.0  # 无多跳数据时不算 penalize
    abst = hard_abstention if hard_abstention is not None else 1.0

    return 0.4 * syn_hit3 + 0.3 * hard_recall3 + 0.2 * pair + 0.1 * abst


# ============================================================
# 主入口
# ============================================================

async def main(track: str = "both", top_k: int = 5, verbose: bool = False):
    print("=" * 60)
    print("双轨评测框架")
    print("=" * 60)

    synthetic_result = None
    hard_result = None

    if track in ("synthetic", "both"):
        if not SYNTHETIC_PATH.exists():
            print(f"\n⚠️  合成集不存在: {SYNTHETIC_PATH}")
            print("   请先运行: py -m eval.benchmark.generate_synthetic")
        else:
            with open(SYNTHETIC_PATH, "r", encoding="utf-8") as f:
                data = json.load(f)
                queries = data.get("queries", data)  # 兼容嵌套和数组
                if isinstance(queries, dict):
                    queries = queries.get("queries", [])
            print(f"\n[合成集] 加载 {len(queries)} 条 query...")
            t0 = time.time()
            synthetic_result = await eval_synthetic(queries, top_k, verbose)
            synthetic_result["summary"]["elapsed_s"] = round(time.time() - t0, 1)
            print_summary(synthetic_result["summary"], "合成集")

    if track in ("hard", "both"):
        if not HARD_PATH.exists():
            print(f"\n⚠️  人工难题集不存在: {HARD_PATH}")
            print("   骨架已创建，请手动填充 query 和 relevant_titles")
        else:
            with open(HARD_PATH, "r", encoding="utf-8") as f:
                raw = json.load(f)
            # 过滤掉注释条目（仅有 _注释/_说明 字段的）和 invalid 条目
            queries = [q for q in raw if isinstance(q, dict) and "query" in q and q.get("query")]
            if queries:
                print(f"\n[人工难题集] 加载 {len(queries)} 条 query"
                      f"（原始 {len(raw)} 条，含 {len(raw) - len(queries)} 条注释）...")
                t0 = time.time()
                hard_result = await eval_hard(queries, top_k, verbose)
                hard_result["summary"]["elapsed_s"] = round(time.time() - t0, 1)
                print_summary(hard_result["summary"], "人工难题集")

                # 分类报告
                if hard_result.get("type_reports"):
                    print(f"\n--- 按类型分报告 ---")
                    for t, rpt in hard_result["type_reports"].items():
                        print(f"  [{t}] n={rpt['queries']}")
                        for mk, mv in rpt.items():
                            if mk not in ("queries", "abstention", "max_similarity",
                                          "hits@1", "mrr"):
                                print(f"    {mk}: {mv:.4f}")

    # 加权总分
    if synthetic_result and hard_result:
        syn_sum = synthetic_result["summary"]
        hard_sum = hard_result["summary"]
        score = compute_weighted_score(syn_sum, hard_sum)
        print(f"\n{'='*60}")
        print(f"  加权总分: {score:.4f}")
        print(f"    0.4×合成Hit@3({syn_sum.get('hit@3',0):.2f})"
              f" + 0.3×人工Recall@3({hard_sum.get('recall@3',0):.2f})"
              f" + 0.2×人工Pair@3({hard_sum.get('pair@3',1.0):.2f})"
              f" + 0.1×拒答率({hard_sum.get('abstention_rate',1.0):.2f})")
        print(f"{'='*60}")

    # 保存
    output = {
        "run_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "config": {"top_k": top_k, "track": track},
        "synthetic": synthetic_result,
        "hard": hard_result,
        "weighted_score": (
            compute_weighted_score(synthetic_result["summary"], hard_result["summary"])
            if (synthetic_result and hard_result) else None
        ),
    }
    BENCHMARK_DIR.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
    print(f"\n结果已保存: {OUTPUT_PATH}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="双轨评测")
    parser.add_argument("--track", choices=["synthetic", "hard", "both"],
                        default="both", help="评测轨道 (默认 both)")
    parser.add_argument("--top-k", type=int, default=5, help="top-K 参数 (默认 5)")
    parser.add_argument("--verbose", action="store_true", help="逐条打印详情")
    args = parser.parse_args()

    asyncio.run(main(args.track, args.top_k, args.verbose))
