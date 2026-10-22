"""
合成评测集生成器 — 从 FAISS 知识库自动生成 100 条 query。

原理:
  对每个 sampled chunk 调用 LLM 反向生成用户问题，chunk_id 即 ground truth。
  评测时用精确 chunk_id 匹配而非模糊标题匹配，干净且自动化。

用法:
  cd backend
  py -m eval.benchmark.generate_synthetic              # 默认 100 条
  py -m eval.benchmark.generate_synthetic --count 50   # 自定义数量
  py -m eval.benchmark.generate_synthetic --dry-run    # 预览不调用 LLM
"""
import argparse
import asyncio
import json
import random
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from app.services.rag_service import rag_service
from app.services.llm_service import LLMService
from app.config import settings

OUTPUT_PATH = Path(__file__).resolve().parent / "synthetic_queries.json"

SYNTHETIC_PROMPT = """你是一位医学知识库评测员。下面是一段医学知识，请你生成一个普通患者可能输入的问题，这个问题的最佳答案就在这段文字中。

要求：
- 口语化，像百度或搜索引擎里的自然语言提问
- 不要照搬文档中的术语，用患者自己的话表达
- 只输出问题本身，不要加引号、编号或任何说明

知识内容：{chunk}"""


def sample_chunks(documents: list, metadata: list, count: int, min_len: int = 100):
    """分层随机采样：按 category 比例抽取，过滤过短 chunk。

    Returns:
        list of {"chunk_index": int, "text": str, "category": str, "title": str}
    """
    # 统计各分类数量
    from collections import Counter
    cat_counts = Counter(m.get("category", "unknown") for m in metadata)
    total = sum(cat_counts.values())

    # 计算每类应采数量（按比例，至少 1 条）
    per_cat = {}
    remaining = count
    cats_sorted = sorted(cat_counts.keys())
    for cat in cats_sorted[:-1]:
        n = max(1, int(count * cat_counts[cat] / total))
        per_cat[cat] = min(n, cat_counts[cat])
        remaining -= per_cat[cat]
    per_cat[cats_sorted[-1]] = min(remaining, cat_counts[cats_sorted[-1]])

    print(f"采样配置 (目标 {count} 条):")
    for cat, n in per_cat.items():
        print(f"  {cat}: {n} / {cat_counts[cat]}")

    # 按分类索引
    cat_indices = {}
    for i, m in enumerate(metadata):
        c = m.get("category", "unknown")
        if len(documents[i]) >= min_len:
            cat_indices.setdefault(c, []).append(i)

    sampled = []
    rng = random.Random(42)  # 固定种子可复现
    for cat, n in per_cat.items():
        pool = cat_indices.get(cat, [])
        chosen = rng.sample(pool, min(n, len(pool)))
        for idx in chosen:
            sampled.append({
                "chunk_index": idx,
                "text": documents[idx],
                "category": cat,
                "title": metadata[idx].get("title", ""),
                "source": metadata[idx].get("source", ""),
            })

    rng.shuffle(sampled)
    return sampled[:count]


async def generate_one(llm: LLMService, chunk_text: str, chunk_index: int,
                       category: str, sem: asyncio.Semaphore,
                       retries: int = 2):
    """对单个 chunk 生成 query，含重试和信号量限流。"""
    async with sem:
        for attempt in range(1 + retries):
            try:
                msg = [{"role": "user", "content": SYNTHETIC_PROMPT.format(chunk=chunk_text)}]
                raw = await llm.chat(msg, temperature=0.8, max_tokens=120)
                query = raw.strip().strip('"').strip("'").strip("。").strip()
                if len(query) < 5:
                    raise ValueError(f"Query too short: {query!r}")
                return {
                    "id": None,
                    "query": query,
                    "chunk_index": chunk_index,
                    "category": category,
                }
            except Exception as exc:
                if attempt < retries:
                    wait = 2 ** attempt
                    print(f"  [retry {attempt+1}/{retries}] chunk {chunk_index}: {exc}, "
                          f"sleeping {wait}s")
                    await asyncio.sleep(wait)
                else:
                    print(f"  [FAIL] chunk {chunk_index}: {exc}")
                    return None


async def generate_synthetic(count: int = 100, concurrency: int = 5,
                             dry_run: bool = False):
    """主流程：加载索引 → 采样 → LLM 批量生成 → 保存。"""
    print("=" * 60)
    print("合成评测集生成器")
    print("=" * 60)

    # 1. 加载索引（离线模式：不加载 embedding 模型，只读 JSON）
    print("\n[1/4] 加载文档数据（离线模式，跳过 embedding）...")
    import json as _json
    docs_path = Path(__file__).resolve().parent.parent.parent / "data/faiss_index/documents.json"
    if not docs_path.exists():
        print(f"  ERROR: {docs_path} 不存在，请先运行 py -m data.import_bulk")
        return
    with open(docs_path, "r", encoding="utf-8") as f:
        data = _json.load(f)
    documents = data["documents"]
    metadata = data["metadata"]
    total = len(documents)
    print(f"  已加载: {total} chunks（跳过 embedding 模型加载）")

    # 2. 采样
    print(f"\n[2/4] 分层采样...")
    samples = sample_chunks(documents, metadata, count)
    print(f"  实际采样: {len(samples)} 条 (min_len >= 100)")

    if dry_run:
        print("\n[dry-run] 预览前 5 条:")
        for s in samples[:5]:
            print(f"  [{s['chunk_index']}] {s['category']} | "
                  f"{s['title'][:40]} | {s['text'][:60]}...")
        return

    # 3. LLM 生成
    print(f"\n[3/4] LLM 生成 query (concurrency={concurrency})...")
    llm = LLMService()
    sem = asyncio.Semaphore(concurrency)

    tasks = [
        generate_one(llm, s["text"], s["chunk_index"], s["category"], sem)
        for s in samples
    ]
    t0 = time.time()
    raw_results = await asyncio.gather(*tasks)
    elapsed = time.time() - t0

    results = [r for r in raw_results if r is not None]
    for i, r in enumerate(results):
        r["id"] = i + 1

    fail = len(raw_results) - len(results)
    print(f"  成功: {len(results)}, 失败: {fail}, 耗时: {elapsed:.0f}s")

    # 4. 保存
    print(f"\n[4/4] 保存到 {OUTPUT_PATH}")
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump({
            "meta": {
                "total": len(results),
                "categories": {},
                "generated_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
                "config": {"count": count, "concurrency": concurrency},
            },
            "queries": results,
        }, f, ensure_ascii=False, indent=2)

    # 统计
    from collections import Counter
    cat_dist = Counter(r["category"] for r in results)
    print(f"  分类分布: {dict(cat_dist)}")
    print("=" * 60)
    print("完成。运行评测: py -m eval.benchmark.run_benchmark")
    return results


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="生成合成评测集")
    parser.add_argument("--count", type=int, default=100, help="生成 query 数量 (默认 100)")
    parser.add_argument("--concurrency", type=int, default=5, help="LLM 并发数 (默认 5)")
    parser.add_argument("--dry-run", action="store_true", help="仅预览采样，不调用 LLM")
    parser.add_argument("--seed", type=int, default=42, help="随机种子 (默认 42)")
    args = parser.parse_args()

    random.seed(args.seed)
    asyncio.run(generate_synthetic(args.count, args.concurrency, args.dry_run))
