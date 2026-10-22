"""
单命令评测入口 — config 驱动 + P50/P95 延迟 + Markdown 表格输出。

用法:
  cd backend
  py -m eval.benchmark.run --config baseline       # 跑 baseline
  py -m eval.benchmark.run --config +rerank          # 跑实验
  py -m eval.benchmark.run --config baseline --verbose  # 逐条打印

配置:
  configs/*.yaml  — 通过 --config 指定（不含 .yaml 后缀）
  默认加载 configs/baseline.yaml

输出:
  - 终端 Markdown 表格（可直接贴简历）
  - snapshots/{config_name}/{timestamp}.json（归档可复现）
"""
import argparse
import asyncio
import json
import os
import statistics
import sys
import time
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Optional

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from app.services.rag_service import rag_service
from app.config import settings as app_settings

HERE = Path(__file__).resolve().parent
CONFIGS_DIR = HERE / "configs"
SNAPSHOTS_DIR = HERE / "snapshots"
SYNTHETIC_PATH = HERE / "synthetic_queries.json"
HARD_PATH = HERE / "hard_queries.json"

# 复用 run_benchmark 的核心评测函数
from eval.benchmark.run_benchmark import (
    eval_synthetic, eval_hard, print_summary,  # noqa: E402
)


# ============================================================
# Config
# ============================================================

def load_config(name: str) -> dict:
    """Load YAML config by name (without .yaml)."""
    path = CONFIGS_DIR / f"{name}.yaml"
    if not path.exists():
        raise FileNotFoundError(f"Config not found: {path}")
    with open(path, "r", encoding="utf-8") as f:
        cfg = yaml.safe_load(f)
    return cfg


# ============================================================
# Per-query 计时 + 延迟统计
# ============================================================

async def search_with_latency(query: str, top_k: int, score_threshold: float):
    """单条检索并记录耗时 (ms)。"""
    t0 = time.perf_counter()
    results = await rag_service.search(query, top_k=top_k, score_threshold=score_threshold)
    elapsed_ms = (time.perf_counter() - t0) * 1000
    return results, elapsed_ms


async def eval_synthetic_with_latency(queries: list, top_k: int,
                                       score_threshold: float, verbose: bool) -> dict:
    """合成集评测 — 增强版：记录 per-query 延迟。"""
    from eval.benchmark.run_benchmark import hit_at_k_chunk

    if not rag_service.index or rag_service.index.ntotal == 0:
        await rag_service.initialize()

    total_vectors = rag_service.index.ntotal if rag_service.index else 0
    ks = sorted(set([1, 3, 5, 10, 20]))
    ks = [k for k in ks if k <= top_k]
    search_k = top_k * 2

    totals = {f"hit@{k}": 0 for k in ks}
    totals["queries"] = 0
    latencies = []
    per_query = []

    for q in queries:
        target_idx = q["chunk_index"]
        retrieved, elapsed_ms = await search_with_latency(q["query"], search_k,
                                                          score_threshold)
        latencies.append(elapsed_ms)
        retrieved_indices = [r["index"] for r in retrieved]

        scores = {}
        for k in ks:
            scores[f"hit@{k}"] = 1.0 if hit_at_k_chunk(target_idx, retrieved_indices, k) else 0.0
            totals[f"hit@{k}"] += scores[f"hit@{k}"]
        totals["queries"] += 1

        if verbose:
            hit_k = next((k for k in ks if scores.get(f"hit@{k}")), None)
            print(f"  Q{q['id']:03d} '{q['query'][:50]}' → "
                  f"{'HIT@'+str(hit_k) if hit_k else 'MISS'} | "
                  f"target=chunk#{target_idx} ({elapsed_ms:.0f}ms)")

        per_query.append({"id": q["id"], "query": q["query"], **scores,
                          "elapsed_ms": elapsed_ms})

    n = totals["queries"]
    summary = {"track": "synthetic", "n_queries": n, "faiss_vectors": total_vectors}
    for k in ks:
        summary[f"hit@{k}"] = totals[f"hit@{k}"] / n if n else 0.0
    # 延迟统计
    latencies.sort()
    summary["latency_p50_ms"] = latencies[len(latencies)//2] if latencies else 0
    summary["latency_p95_ms"] = latencies[int(len(latencies)*0.95)] if latencies else 0

    return {"summary": summary, "per_query": per_query}


async def eval_hard_with_latency(queries: list, top_k: int,
                                  score_threshold: float, verbose: bool) -> dict:
    """人工难题集评测 — 增强版：记录 per-query 延迟。"""
    from eval.benchmark.run_benchmark import (
        _fuzzy_match, recall_at_k, recall_pair_at_k, mrr, ndcg_at_k,
    )

    if not rag_service.index or rag_service.index.ntotal == 0:
        await rag_service.initialize()

    total_vectors = rag_service.index.ntotal if rag_service.index else 0
    ks = sorted(set([1, 3, 5, 10, 20]))
    ks = [k for k in ks if k <= top_k]
    search_k = top_k * 2

    by_type = {}
    all_totals = {f"recall@{k}": 0.0 for k in ks}
    all_totals["mrr"] = 0.0
    for k in ks:
        all_totals[f"ndcg@{k}"] = 0.0
        all_totals[f"pair@{k}"] = 0.0
    all_totals["hits@1"] = 0
    all_totals["queries"] = 0
    all_totals["abstention"] = 0
    all_totals["max_similarity_sum"] = 0.0
    latencies = []
    per_query = []

    for q in queries:
        qtype = q.get("type", "synonym")
        relevant = set(q.get("relevant_titles", []))
        is_no_answer = (qtype == "no_answer")

        retrieved, elapsed_ms = await search_with_latency(q["query"], search_k,
                                                          score_threshold)
        latencies.append(elapsed_ms)
        titles = [r.get("title", "") for r in retrieved]

        scores = {}
        if is_no_answer:
            top_k_titles = titles[:top_k]
            any_relevant = any(_fuzzy_match(t, relevant) for t in top_k_titles)
            scores["abstention"] = 0.0 if any_relevant else 1.0
            all_totals["abstention"] += scores["abstention"]
            max_sim = max((r.get("score", 0.0) for r in retrieved[:top_k]), default=0.0)
            scores["max_similarity"] = max_sim
            all_totals["max_similarity_sum"] += max_sim
        else:
            for k in ks:
                scores[f"recall@{k}"] = recall_at_k(relevant, titles, k)
                scores[f"ndcg@{k}"] = ndcg_at_k(relevant, titles, k)
                all_totals[f"recall@{k}"] += scores[f"recall@{k}"]
                all_totals[f"ndcg@{k}"] += scores[f"ndcg@{k}"]
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
        scores["elapsed_ms"] = elapsed_ms

        if qtype not in by_type:
            by_type[qtype] = {k: 0.0 for k in scores}
            by_type[qtype]["queries"] = 0
        for k, v in scores.items():
            by_type[qtype][k] = by_type[qtype].get(k, 0.0) + v
        by_type[qtype]["queries"] += 1

        if verbose:
            top3 = titles[:3]
            print(f"  Q{q['id']:03d} [{qtype}] '{q['query'][:60]}' ({elapsed_ms:.0f}ms)")
            print(f"       top-3: {top3}")
            for k in ks:
                if f"recall@{k}" in scores:
                    parts = [f"R@{k}={scores[f'recall@{k}']:.2f}"]
                    if f"pair@{k}" in scores:
                        parts.append(f"Pair@{k}={scores[f'pair@{k}']:.2f}")
                    print(f"       {' '.join(parts)}")
            if is_no_answer:
                print(f"       Abstention={scores['abstention']:.0f}  "
                      f"MaxSim={scores['max_similarity']:.3f}")
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
    for k in ks:
        pair_queries = by_type.get("multi_hop", {}).get("queries", 0)
        summary[f"pair@{k}"] = (all_totals[f"pair@{k}"] / pair_queries
                                if pair_queries else None)
    no_answer_queries = by_type.get("no_answer", {}).get("queries", 0)
    summary["abstention_rate"] = (all_totals["abstention"] / no_answer_queries
                                  if no_answer_queries else None)
    summary["avg_max_similarity"] = (all_totals["max_similarity_sum"] / no_answer_queries
                                     if no_answer_queries else None)
    # 延迟
    latencies.sort()
    summary["latency_p50_ms"] = latencies[len(latencies)//2] if latencies else 0
    summary["latency_p95_ms"] = latencies[int(len(latencies)*0.95)] if latencies else 0

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
# Markdown 表格
# ============================================================

def _fmt(v: Optional[float], precision: int = 2) -> str:
    if v is None:
        return "—"
    return f"{v:.{precision}f}"


def render_markdown_table(synthetic_summary: dict, hard_summary: dict,
                          hard_type_reports: dict, config_name: str,
                          config_desc: str) -> str:
    """生成双轨 Markdown 评测表格。"""

    syn = synthetic_summary
    hrd = hard_summary
    typ = hard_type_reports or {}
    syn_n = syn.get("n_queries", 0)
    hrd_n = hrd.get("n_queries", 0)

    # 类型报告方便取值
    def _tv(t: str, metric: str):
        return typ.get(t, {}).get(metric)

    def _syn(metric: str): return syn.get(metric)
    def _hrd(metric: str): return hrd.get(metric)

    # 加权总分
    syn_hit3 = syn.get("hit@3", 0.0)
    hrd_recall3 = hrd.get("recall@3", 0.0)
    hrd_pair3 = hrd.get("pair@3") or 1.0
    hrd_abst = hrd.get("abstention_rate") or 1.0
    weighted = 0.4 * syn_hit3 + 0.3 * hrd_recall3 + 0.2 * hrd_pair3 + 0.1 * hrd_abst

    tz = datetime.now(timezone(timedelta(hours=8)))
    ts = tz.strftime("%Y-%m-%d %H:%M")

    lines = []
    lines.append(f"## {config_name} — {config_desc}")
    lines.append(f"*{ts} CST | 合成集 n={syn_n}, 人工集 n={hrd_n}*")
    lines.append("")

    # 表头
    cols = [
        "指标",
        f"合成集<br>(n={syn_n})",
        f"人工-同义<br>(n={_tv('synonym','queries') or 8})",
        f"人工-多跳<br>(n={_tv('multi_hop','queries') or 8})",
        f"人工-约束<br>(n={_tv('constraint','queries') or 8})",
        f"人工-无答案<br>(n={_tv('no_answer','queries') or 6})",
        f"人工-总计<br>(n={hrd_n})",
    ]
    lines.append("| " + " | ".join(cols) + " |")
    sep = "|---:" * len(cols) + "|"
    lines.append(sep.replace("---", ":---:", 1))  # first col left-aligned

    def row(label, syn_key, hrd_key, *type_keys):
        vals = [label]
        # 合成集
        if syn_key:
            vals.append(_fmt(_syn(syn_key)))
        else:
            vals.append("—")
        # 四类
        for t, k in type_keys:
            if t == "no_answer":
                vals.append("—")
            elif k:
                vals.append(_fmt(_tv(t, k)))
            else:
                vals.append("—")
        # 总计
        if hrd_key:
            vals.append(_fmt(_hrd(hrd_key)))
        else:
            vals.append("—")
        lines.append("| " + " | ".join(vals) + " |")

    types = ["synonym", "multi_hop", "constraint", "no_answer"]

    # Recall@K
    for k in [1, 3, 5, 10, 20]:
        sk = f"hit@{k}" if k <= 5 else None  # 合成集只有 hit@1/3/5
        hk = f"recall@{k}"
        if sk:
            row(f"Recall/Hit@{k}", sk, hk,
                *[(t, hk) for t in types])
        else:
            # 合成集不显示 >5 的 hit@k
            vals = [f"Recall@{k}"]
            vals.append("—")  # 合成
            for t in types:
                if t == "no_answer":
                    vals.append("—")
                else:
                    vals.append(_fmt(_tv(t, hk)))
            vals.append(_fmt(_hrd(hk)))
            lines.append("| " + " | ".join(vals) + " |")

    # MRR
    row("MRR", None, "mrr",
        *[(t, "mrr") for t in types])

    # nDCG
    for k in [5, 10]:
        hk = f"ndcg@{k}"
        row(f"nDCG@{k}", None, hk,
            *[(t, hk) for t in types])

    # Pair@K (仅 multi_hop)
    pair_k = 5
    hk = f"pair@{pair_k}"
    vals = [f"Pair@{pair_k}"]
    vals.append("—")
    vals.append("—")
    vals.append(_fmt(_tv("multi_hop", hk)))
    vals.append("—")
    vals.append("—")
    vals.append(_fmt(_hrd(hk)))
    lines.append("| " + " | ".join(vals) + " |")

    # 拒答率
    hk = "abstention_rate"
    vals = ["拒答率"]
    vals.append("—")
    for t in types:
        if t == "no_answer":
            vals.append(_fmt(_tv(t, "abstention")))
        else:
            vals.append("—")
    vals.append(_fmt(_hrd(hk)))
    lines.append("| " + " | ".join(vals) + " |")

    # 延迟
    for lk, label in [("latency_p50_ms", "P50延迟"), ("latency_p95_ms", "P95延迟")]:
        vals = [label]
        vals.append(f"{_syn(lk):.0f}ms")
        vals.append("—")
        vals.append("—")
        vals.append("—")
        vals.append("—")
        vals.append(f"{_hrd(lk):.0f}ms")
        lines.append("| " + " | ".join(vals) + " |")

    lines.append("")
    lines.append(f"**加权总分: {weighted:.4f}** "
                 f"(0.4×合成Hit@3({syn_hit3:.2f}) + 0.3×人工Recall@3({hrd_recall3:.2f})"
                 f" + 0.2×人工Pair@3({hrd_pair3:.2f}) + 0.1×拒答率({hrd_abst:.2f}))")

    return "\n".join(lines)


# ============================================================
# 主入口
# ============================================================

async def main(config_name: str = "baseline", verbose: bool = False):
    cfg = load_config(config_name)
    params = cfg.get("params", {})
    top_k = params.get("top_k", 20)
    score_threshold = params.get("score_threshold", 0.0)
    name = cfg.get("name", config_name)
    desc = cfg.get("description", "")

    # 应用 BM25 参数到 rag_service
    if "bm25_k1" in params:
        rag_service._bm25_k1 = params["bm25_k1"]
    if "bm25_b" in params:
        rag_service._bm25_b = params["bm25_b"]
    if "use_stopwords" in params:
        rag_service._use_stopwords = params["use_stopwords"]
    # force rebuild BM25 on parameter change
    rag_service._bm25 = None
    # 应用 RRF k 值
    if "rrf_k" in params:
        import app.config as _cfg
        _cfg.settings.RRF_K = params["rrf_k"]
    # 应用 Rerank 参数
    if params.get("rerank_enabled"):
        _cfg.settings.RERANK_CANDIDATES = params.get("rerank_candidates", 50)
        _cfg.settings.RERANK_TOP_K = params.get("rerank_top_k", 10)
        _cfg.settings.RERANK_BATCH_SIZE = params.get("rerank_batch_size", 8)
    else:
        _cfg.settings.RERANK_CANDIDATES = 0  # 关闭
    # 应用 Query Expansion
    if "query_expansion" in params:
        _cfg.settings.QUERY_EXPANSION = params["query_expansion"]

    print("=" * 60)
    print(f"评测配置: {name}")
    print(f"参数: top_k={top_k}, score_threshold={score_threshold}")
    if "bm25_k1" in params:
        print(f"  BM25: k1={params.get('bm25_k1')}, b={params.get('bm25_b')}, "
              f"stopwords={params.get('use_stopwords')}")
    print("=" * 60)

    # --- 合成集 ---
    synthetic_result = None
    if SYNTHETIC_PATH.exists():
        with open(SYNTHETIC_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
            squeries = data.get("queries", data)
            if isinstance(squeries, dict):
                squeries = squeries.get("queries", [])
        if squeries:
            print(f"\n[合成集] {len(squeries)} 条 query...")
            t0 = time.time()
            synthetic_result = await eval_synthetic_with_latency(
                squeries, top_k, score_threshold, verbose)
            elapsed = round(time.time() - t0, 1)
            synthetic_result["summary"]["elapsed_s"] = elapsed
            print(f"  完成, 总耗时 {elapsed}s")
    else:
        print(f"\n⚠️  合成集不存在: {SYNTHETIC_PATH}")

    # --- 人工难题集 ---
    hard_result = None
    if HARD_PATH.exists():
        with open(HARD_PATH, "r", encoding="utf-8") as f:
            raw = json.load(f)
        hqueries = [q for q in raw if isinstance(q, dict) and "query" in q and q.get("query")]
        if hqueries:
            print(f"\n[人工难题集] {len(hqueries)} 条 query"
                  f" (原始 {len(raw)} 条, {len(raw) - len(hqueries)} 条注释)...")
            t0 = time.time()
            hard_result = await eval_hard_with_latency(
                hqueries, top_k, score_threshold, verbose)
            elapsed = round(time.time() - t0, 1)
            hard_result["summary"]["elapsed_s"] = elapsed
            print(f"  完成, 总耗时 {elapsed}s")
    else:
        print(f"\n⚠️  人工难题集不存在: {HARD_PATH}")

    # --- Markdown 表格 ---
    if synthetic_result and hard_result:
        print("\n" + "=" * 60)
        print("         评测结果")
        print("=" * 60 + "\n")
        table = render_markdown_table(
            synthetic_result["summary"],
            hard_result["summary"],
            hard_result.get("type_reports", {}),
            name, desc,
        )
        print(table)

    # --- 归档 snapshot ---
    if synthetic_result and hard_result:
        tz = datetime.now(timezone(timedelta(hours=8)))
        ts = tz.strftime("%Y-%m-%dT%H%M%S")
        snap_dir = SNAPSHOTS_DIR / config_name
        snap_dir.mkdir(parents=True, exist_ok=True)
        snap_path = snap_dir / f"{ts}.json"

        output = {
            "config_name": config_name,
            "config": cfg,
            "run_at": ts + " CST",
            "synthetic": synthetic_result,
            "hard": hard_result,
            "weighted_score": (
                0.4 * synthetic_result["summary"].get("hit@3", 0)
                + 0.3 * hard_result["summary"].get("recall@3", 0)
                + 0.2 * (hard_result["summary"].get("pair@3") or 1.0)
                + 0.1 * (hard_result["summary"].get("abstention_rate") or 1.0)
            ),
        }
        with open(snap_path, "w", encoding="utf-8") as f:
            json.dump(output, f, ensure_ascii=False, indent=2)
        print(f"\nSnapshot 已保存: {snap_path}")

        # 也保存到固定的 latest 引用
        latest_path = snap_dir / "latest.json"
        with open(latest_path, "w", encoding="utf-8") as f:
            json.dump(output, f, ensure_ascii=False, indent=2)

    print("\nDone.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="单命令评测入口 (config 驱动)")
    parser.add_argument("--config", type=str, default="baseline",
                        help="配置名 (对应 configs/<name>.yaml, 默认 baseline)")
    parser.add_argument("--verbose", action="store_true", help="逐条打印详情")
    args = parser.parse_args()

    asyncio.run(main(args.config, args.verbose))
