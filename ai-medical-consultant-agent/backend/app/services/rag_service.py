# ============================================================
# AI Medical Consultant - RAG Service (检索增强生成)
# ============================================================
# 基于文档 3.1.2 RAG核心代码逻辑 实现
# ============================================================
import os
import json
import pickle
import numpy as np
from typing import List, Optional, Dict
from loguru import logger

from app.config import settings


class RAGService:
    """
    RAG检索增强生成服务

    核心流程:
    1. 离线阶段: 文档 → 分块 → Embedding → FAISS索引
    2. 在线阶段: 用户Query → 问题改写 → 多路检索 → 融合排序 → 上下文组装
    """

    def __init__(self):
        self.embedding_model = None
        self.index = None  # FAISS index
        self.documents: List[str] = []       # 文档内容
        self.metadata: List[Dict] = []       # 文档元数据
        self._dimension = None  # 从第一次 embedding 自动探测
        self._bm25 = None       # BM25Index (lazy init)
        self._bm25_k1 = 1.2     # BM25 TF 饱和参数
        self._bm25_b = 0.75     # BM25 长度归一化参数
        self._use_stopwords = True
        self._reranker = None   # CrossEncoder (lazy init)

    @staticmethod
    def _cuda_available() -> bool:
        """Check if CUDA GPU is available for embedding inference."""
        try:
            import torch
            return torch.cuda.is_available()
        except Exception:
            return False

    # ==================== 初始化 ====================

    async def initialize(self):
        """初始化RAG服务 - 加载Embedding模型和已有索引"""
        # Map known embedding model names to local SentenceTransformer models
        _LOCAL_MODEL_MAP = {
            "text-embedding-v1": "BAAI/bge-small-zh-v1.5",
            "text-embedding-v2": "BAAI/bge-large-zh-v1.5",
        }

        local_model_name = _LOCAL_MODEL_MAP.get(
            settings.EMBEDDING_MODEL,
            settings.EMBEDDING_MODEL
        )

        self.embedding_model = None
        try:
            from sentence_transformers import SentenceTransformer
            self.embedding_model = SentenceTransformer(
                local_model_name,
                device="cuda" if self._cuda_available() else "cpu",
            )
            logger.info(f"Embedding model loaded locally: {local_model_name} -> {settings.EMBEDDING_MODEL}"
                        f" (device={'cuda' if self._cuda_available() else 'cpu'})")
        except Exception as e:
            logger.warning(f"Local embedding model load failed, will use API: {e}")
            self.embedding_model = None

        self._load_index()

    def _load_index(self):
        """加载已有FAISS索引"""
        try:
            import faiss
            index_path = os.path.join(settings.FAISS_INDEX_PATH, "medical.index")
            docs_path = os.path.join(settings.FAISS_INDEX_PATH, "documents.json")

            if os.path.exists(index_path) and os.path.exists(docs_path):
                self.index = faiss.read_index(index_path)
                with open(docs_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self.documents = data.get("documents", [])
                    self.metadata = data.get("metadata", [])
                logger.info(f"Loaded FAISS index: {self.index.ntotal} vectors")
            else:
                logger.info("No existing FAISS index found, starting fresh")
        except Exception as e:
            logger.error(f"Failed to load FAISS index: {e}")

    # ==================== 离线索引构建 ====================

    async def add_documents(
        self,
        texts: List[str],
        metadatas: Optional[List[Dict]] = None
    ) -> int:
        """
        添加文档到知识库（离线操作）

        流程:
        1. content_hash 去重（跳过已存在的文档）
        2. embedding_model.encode(texts): 将文本转为N维向量
        3. index.add(vectors): 添加到FAISS索引
        4. 保存原始文档和元数据
        """
        import hashlib

        if metadatas is None:
            metadatas = [{} for _ in texts]

        # Step 0: 去重 — 基于 content SHA256
        existing_hashes = {
            hashlib.sha256(d.encode("utf-8")).hexdigest()
            for d in self.documents
        }
        deduped_texts = []
        deduped_metas = []
        skipped = 0
        for text, meta in zip(texts, metadatas):
            h = hashlib.sha256(text.encode("utf-8")).hexdigest()
            if h in existing_hashes:
                skipped += 1
                continue
            existing_hashes.add(h)
            deduped_texts.append(text)
            deduped_metas.append(meta)

        if skipped:
            logger.info(f"Skipped {skipped} duplicate document(s), "
                        f"processing {len(deduped_texts)} new")

        if not deduped_texts:
            return 0

        # Step 0.5: 文本切分（统一入口，所有调用路径共用 CHUNK_SIZE/OVERLAP）
        from langchain.text_splitter import RecursiveCharacterTextSplitter
        splitter = RecursiveCharacterTextSplitter(
            chunk_size=settings.CHUNK_SIZE,
            chunk_overlap=settings.CHUNK_OVERLAP,
            separators=["\n\n", "\n", "。", "！", "？", "，", " ", ""],
        )
        chunked_texts = []
        chunked_metas = []
        for text, meta in zip(deduped_texts, deduped_metas):
            chunks = splitter.split_text(text)
            for ci, chunk in enumerate(chunks):
                if len(chunk) < settings.CHUNK_MIN_SIZE:
                    continue
                chunked_texts.append(chunk)
                chunked_metas.append({**meta, "chunk_index": ci, "chunk_count": len(chunks)})
            # 如果所有 chunk 都被过滤掉了（短文本），保留原文本
            if chunks and not any(
                c for c in chunks if len(c) >= settings.CHUNK_MIN_SIZE
            ):
                chunked_texts.append(text)
                chunked_metas.append(meta)
                logger.info(
                    f"Short text kept as-is (len={len(text)} < CHUNK_MIN_SIZE={settings.CHUNK_MIN_SIZE}): "
                    f"{text[:60]}..."
                )
        deduped_texts, deduped_metas = chunked_texts, chunked_metas

        if not deduped_texts:
            logger.warning(f"All texts filtered out after chunking (min_size={settings.CHUNK_MIN_SIZE})")
            return 0

        # Step 1: 文本向量化
        embeddings = await self._embed_texts(deduped_texts)
        embeddings = np.array(embeddings).astype("float32")
        if embeddings.ndim == 1:
            embeddings = embeddings.reshape(1, -1)

        # Step 2: 添加到FAISS索引
        import faiss
        if self.index is None:
            self._dimension = embeddings.shape[1]
            self.index = faiss.IndexFlatL2(self._dimension)

        self.index.add(embeddings)

        # Step 3: 保存原始文档
        self.documents.extend(deduped_texts)
        self.metadata.extend(deduped_metas)

        # Step 4: 持久化保存
        self._save_index()

        logger.info(f"Added {len(deduped_texts)} documents, total: {self.index.ntotal}")
        return len(deduped_texts)

    async def _embed_texts(self, texts: List[str]) -> List[List[float]]:
        """文本向量化 - 支持本地模型和DashScope API"""
        if self.embedding_model is not None:
            # 本地模型
            return self.embedding_model.encode(texts, show_progress_bar=False).tolist()

        # 使用DashScope API
        import dashscope
        from dashscope import TextEmbedding

        embeddings = []
        for text in texts:
            resp = TextEmbedding.call(
                model=settings.EMBEDDING_MODEL,
                input=text,
                api_key=settings.EMBEDDING_API_KEY,
            )
            if resp.status_code == 200:
                embeddings.append(resp.output["embeddings"][0]["embedding"])
            else:
                raise RuntimeError(
                    f"Embedding API failed for text [{text[:80]}...]: "
                    f"status={resp.status_code}, message={resp.message}"
                )

        return embeddings

    # ==================== 真 BM25 检索 ====================

    # --- 中文停用词表（精简版，覆盖最高频无意义词）---
    _STOPWORDS: set = None

    @classmethod
    def _get_stopwords(cls) -> set:
        if cls._STOPWORDS is not None:
            return cls._STOPWORDS
        cls._STOPWORDS = {
            "的", "了", "在", "是", "我", "有", "和", "就", "不", "人", "都", "一",
            "一个", "上", "也", "很", "到", "说", "要", "去", "你", "会", "着",
            "没有", "看", "好", "自己", "这", "他", "她", "它", "们", "那", "些",
            "所", "为", "所以", "因为", "但是", "然而", "不过", "如果", "虽然",
            "可以", "这个", "那个", "什么", "怎么", "哪", "吗", "啊", "哦", "吧",
            "呢", "能", "能够", "可能", "应该", "需要", "可以", "会", "该", "等",
            "及", "或", "且", "与", "从", "以", "之", "其", "被", "把", "让",
            "对", "向", "往", "朝", "由", "沿", "按", "按照", "根据", "用",
            "中", "里", "外", "内", "前", "后", "左", "右", "上", "下",
            "还", "更", "最", "非常", "比较", "真", "太", "极", "很",
            "只", "仅", "光", "单", "就", "才", "刚", "已", "曾经", "将",
            "正在", "一直", "总是", "还是", "只是", "除了", "包括",
        }
        return cls._STOPWORDS

    @staticmethod
    def _tokenize(text: str, use_stopwords: bool = True) -> List[str]:
        """jieba 中文分词 + 可选停用词过滤。"""
        try:
            import jieba
        except ImportError:
            # fallback to character-level
            return list(text)
        tokens = jieba.lcut(text)
        if not use_stopwords:
            return [t.strip() for t in tokens if t.strip()]
        stopwords = RAGService._get_stopwords()
        return [t.strip() for t in tokens
                if t.strip() and t.strip() not in stopwords]

    def _build_bm25(self, force: bool = False):
        """构建/加载 BM25 索引（pickle 持久化）。"""
        if self._bm25 is not None and not force:
            return

        import hashlib
        from rank_bm25 import BM25Okapi

        # 用 documents 内容哈希判断是否需要重建
        doc_hash = hashlib.sha256(
            "".join(self.documents[-100:]).encode()
        ).hexdigest()[:12]

        bm25_path = os.path.join(settings.FAISS_INDEX_PATH, "bm25_index.pkl")
        bm25_hash_path = os.path.join(settings.FAISS_INDEX_PATH, "bm25_hash.txt")

        # 尝试加载缓存
        if not force and os.path.exists(bm25_path) and os.path.exists(bm25_hash_path):
            try:
                with open(bm25_hash_path, "r") as f:
                    cached_hash = f.read().strip()
                if cached_hash == doc_hash:
                    with open(bm25_path, "rb") as f:
                        self._bm25 = pickle.load(f)
                    logger.info(f"BM25 index loaded from cache ({len(self.documents)} docs)")
                    return
            except Exception:
                pass

        # 重建
        tokenized = [
            self._tokenize(doc, self._use_stopwords)
            for doc in self.documents
        ]
        self._bm25 = BM25Okapi(tokenized, k1=self._bm25_k1, b=self._bm25_b)

        # 持久化
        try:
            with open(bm25_path, "wb") as f:
                pickle.dump(self._bm25, f)
            with open(bm25_hash_path, "w") as f:
                f.write(doc_hash)
        except Exception as e:
            logger.warning(f"BM25 cache save failed: {e}")

        logger.info(f"BM25 index built ({len(self.documents)} docs, "
                     f"k1={self._bm25_k1}, b={self._bm25_b})")

    def _bm25_search(self, query: str, top_k: int, threshold: float = 0.0) -> List[Dict]:
        """真 BM25 检索 — jieba 分词 + IDF + TF饱和 + 长度归一。"""
        if not self.documents:
            return []

        self._build_bm25()
        tokenized_query = self._tokenize(query, self._use_stopwords)
        scores = self._bm25.get_scores(tokenized_query)

        # scores 是原始 BM25 分数（≥0），用 sigmoid 归一化到 (0,1) 便于与稠密分数比较
        # 注意: 此分数仅用于 threshold 过滤, RRF 融合只用排名
        def _sigmoid(x): return 1.0 / (1.0 + np.exp(-x))
        norm_scores = _sigmoid(scores / (np.std(scores) + 1e-8))

        results = []
        # 取 top_k*2 候选再排序（BM25 get_scores 已排序？不，需要自己取 top）
        top_indices = np.argsort(scores)[::-1][:top_k * 2]
        for idx in top_indices:
            score = float(norm_scores[idx])
            if threshold > 0 and score < threshold:
                continue
            if idx >= len(self.metadata):
                continue
            meta = self.metadata[idx]
            results.append({
                "content": self.documents[idx],
                "score": score,
                "method": "bm25",
                "index": int(idx),
                "category": meta.get("category", ""),
                "title": meta.get("title", ""),
                "source": meta.get("source", ""),
            })

        return sorted(results, key=lambda x: x["score"], reverse=True)[:top_k]

    def _save_index(self):
        """保存 FAISS 索引和文档到磁盘"""
        os.makedirs(settings.FAISS_INDEX_PATH, exist_ok=True)
        index_path = os.path.join(settings.FAISS_INDEX_PATH, "medical.index")
        docs_path = os.path.join(settings.FAISS_INDEX_PATH, "documents.json")

        if self.index is not None:
            import faiss
            faiss.write_index(self.index, index_path)

        with open(docs_path, "w", encoding="utf-8") as f:
            json.dump({
                "documents": self.documents,
                "metadata": self.metadata,
            }, f, ensure_ascii=False, indent=2)

    # ==================== 问题改写 (Query Expansion) ====================

    async def _expand_query(self, query: str) -> str:
        """Query Expansion — dict fallback, LLM (delegated to RAGService instance), or none."""
        method = getattr(settings, 'QUERY_EXPANSION', 'dict')
        if method == 'llm':
            return await self._llm_expand_query(query)
        elif method == 'dict':
            return self._dict_expand_query(query)
        return query

    def _dict_expand_query(self, query: str) -> str:
        """硬编码医学同义词映射。"""
        synonyms = {
            "头痛": "头疼", "肚子疼": "腹痛", "发烧": "发热",
            "胃疼": "胃痛 胃部疼痛", "咳嗽": "咳嗽 咳痰",
            "拉肚子": "腹泻", "感冒": "上呼吸道感染 感冒",
            "睡不着": "失眠 睡眠障碍", "胸闷": "胸闷 胸痛 心慌",
            "头晕": "头晕 眩晕 头昏",
        }
        expanded_terms = [query]
        for key, val in synonyms.items():
            if key in query:
                expanded_terms.append(val)
        return " ".join(expanded_terms)

    async def _llm_expand_query(self, query: str) -> str:
        """LLM 口语→医学术语改写。"""
        from app.services.llm_service import LLMService
        llm = LLMService()
        prompt = (
            "你是医学搜索引擎查询改写器。将用户的日常口语query改写成适合搜索医学知识库的术语式query。"
            "只输出改写后的query，不要加任何解释或标点。\n"
            f"用户query: {query}"
        )
        try:
            result = await llm.chat(
                [{"role": "user", "content": prompt}],
                temperature=0.2, max_tokens=80
            )
            return result.strip().strip("\"'。.")
        except Exception:
            return query

    # ==================== 多路检索 ====================

    async def search(
        self,
        query: str,
        top_k: int = None,
        score_threshold: float = None,
        category: Optional[str] = None,
    ) -> List[Dict]:
        """
        向量相似度检索（在线操作）+ 关键词检索 + RRF融合

        流程:
        1. 问题改写 (Query Expansion)
        2. 稠密检索 (Dense - FAISS向量相似度)
        3. 稀疏检索 (Sparse - BM25关键词)
        4. RRF融合排序 (Reciprocal Rank Fusion)
        5. 返回Top-K结果
        """
        if top_k is None:
            top_k = settings.TOP_K_RETRIEVAL

        if score_threshold is None:
            score_threshold = settings.SCORE_THRESHOLD

        if self.index is None or self.index.ntotal == 0:
            return []

        # Step 1: 问题改写
        expanded_query = await self._expand_query(query)

        # Step 2: 稠密检索 - FAISS向量相似度
        dense_results = await self._dense_search(expanded_query, top_k * 2, score_threshold)

        # Step 3: 稀疏检索 - BM25关键词 (真 BM25: jieba分词 + IDF + TF饱和 + 长度归一)
        sparse_results = self._bm25_search(query, top_k * 2, score_threshold)

        # Step 4: RRF融合排序 (k 值可配，默认 60)
        rrf_k = getattr(settings, 'RRF_K', 60)
        fused = self._rrf_fusion(dense_results, sparse_results, top_k, k=rrf_k)

        # Step 5: 按分类过滤
        if category:
            fused = [r for r in fused if r.get("category") == category]

        # Step 6: Rerank (可选)
        rerank_candidates = getattr(settings, 'RERANK_CANDIDATES', 0)
        if rerank_candidates > 0:
            fused = self._rerank(query, fused[:rerank_candidates],
                                 getattr(settings, 'RERANK_TOP_K', top_k))

        return fused[:top_k]

    # ==================== CrossEncoder Rerank ====================

    def _load_reranker(self):
        """懒加载 CrossEncoder 重排序模型。"""
        if self._reranker is not None:
            return
        from sentence_transformers import CrossEncoder
        model_name = getattr(settings, 'RERANK_MODEL', 'BAAI/bge-reranker-base')
        device = "cuda" if self._cuda_available() else "cpu"
        self._reranker = CrossEncoder(model_name, device=device)
        logger.info(f"Reranker loaded: {model_name} (device={device})")

    def _rerank(self, query: str, candidates: List[Dict], top_k: int) -> List[Dict]:
        """CrossEncoder 精排——对 query-doc pair 重新打分。"""
        if not candidates:
            return []
        self._load_reranker()
        pairs = [[query, c["content"]] for c in candidates]
        batch_size = getattr(settings, 'RERANK_BATCH_SIZE', 8)
        scores = self._reranker.predict(pairs, batch_size=batch_size,
                                         show_progress_bar=False)
        # 更新 score 并排序
        for c, s in zip(candidates, scores):
            c["score"] = float(s)
            c["method"] = "rerank"
        return sorted(candidates, key=lambda x: x["score"], reverse=True)[:top_k]

    async def _dense_search(self, query: str, top_k: int, threshold: float = 0.0) -> List[Dict]:
        """稠密检索 - FAISS向量搜索"""
        query_vec = await self._embed_texts([query])
        query_vec = np.array(query_vec).astype("float32")

        distances, indices = self.index.search(query_vec, min(top_k, self.index.ntotal))

        results = []
        for dist, idx in zip(distances[0], indices[0]):
            if idx < len(self.documents) and idx >= 0:
                # Convert L2 distance to similarity score
                score = 1.0 / (1.0 + float(dist))
                if threshold > 0 and score < threshold:
                    continue
                meta = self.metadata[idx] if idx < len(self.metadata) else {}
                results.append({
                    "content": self.documents[idx],
                    "score": score,
                    "method": "dense",
                    "index": int(idx),
                    "category": meta.get("category", ""),
                    "title": meta.get("title", ""),
                    "source": meta.get("source", ""),
                })

        return sorted(results, key=lambda x: x["score"], reverse=True)

    def _sparse_search(self, query: str, top_k: int, threshold: float = 0.0) -> List[Dict]:
        """稀疏检索 - BM25关键词匹配风格"""
        query_terms = set(query)
        scored = []

        for i, doc in enumerate(self.documents):
            # Simple keyword overlap scoring
            doc_lower = doc.lower()
            matches = sum(1 for term in query_terms if term in doc_lower)
            if matches > 0:
                score = matches / len(query_terms)
                if threshold > 0 and score < threshold:
                    continue
                meta = self.metadata[i] if i < len(self.metadata) else {}
                scored.append({
                    "content": doc,
                    "score": score,
                    "method": "sparse",
                    "index": i,
                    "category": meta.get("category", ""),
                    "title": meta.get("title", ""),
                    "source": meta.get("source", ""),
                })

        return sorted(scored, key=lambda x: x["score"], reverse=True)[:top_k]

    def _rrf_fusion(
        self,
        dense_results: List[Dict],
        sparse_results: List[Dict],
        top_k: int,
        k: int = 60,
    ) -> List[Dict]:
        """
        RRF (Reciprocal Rank Fusion) 融合排序

        RRF_score = Σ 1/(k + rank_i)
        - k=60 是推荐参数
        - 综合多路检索结果
        - 去除重复/低相关
        """
        scores = {}
        docs = {}

        # Dense rankings
        for rank, item in enumerate(dense_results, start=1):
            idx = item["index"]
            scores[idx] = scores.get(idx, 0) + 1.0 / (k + rank)
            docs[idx] = item

        # Sparse rankings
        for rank, item in enumerate(sparse_results, start=1):
            idx = item["index"]
            scores[idx] = scores.get(idx, 0) + 1.0 / (k + rank)
            if idx not in docs:
                docs[idx] = item

        # Sort by RRF score
        sorted_items = sorted(scores.items(), key=lambda x: x[1], reverse=True)

        result = []
        for idx, rrf_score in sorted_items[:top_k]:
            item = docs[idx].copy()
            item["rrf_score"] = rrf_score
            result.append(item)

        return result

    # ==================== 上下文组装 ====================

    async def build_context(
        self,
        query: str,
        top_k: int = None,
        conversation_history: Optional[List[Dict]] = None,
    ) -> Dict:
        """
        上下文组装 (Context Assembly)

        组装内容:
        - System Prompt (角色设定)
        - Retrieved Docs (检索到的医学知识)
        - User Question (用户问题)
        - Chat History (对话历史)
        """
        retrieved = await self.search(query, top_k=top_k)

        # 构建检索知识文本（编号引用 + 末尾出处）
        knowledge_texts = []
        references = []
        for i, doc in enumerate(retrieved, start=1):
            knowledge_texts.append(f"[{i}] {doc['content']}")
            source = doc.get("source", "")
            title = doc.get("title", "")
            if source or title:
                parts = [p for p in [source, title] if p]
                references.append(f"[{i}] {' — '.join(parts)}")

        context = "\n\n".join(knowledge_texts)
        if references:
            context += "\n\n---\n参考文献:\n" + "\n".join(references)

        return {
            "query": query,
            "retrieved_docs": retrieved,
            "knowledge_context": context,
            "conversation_history": conversation_history or [],
            "retrieved_count": len(retrieved),
        }

    # ==================== 知识库管理 ====================

    async def delete_by_title(self, title: str) -> int:
        """按标题删除 FAISS 向量（需重建索引）

        因为 FAISS IndexFlatL2 不支持选择性删除：
        1. 在 metadata 中按 title 匹配所有索引位置
        2. 从 documents/metadata 列表中过滤掉
        3. 重建整个 FAISS 索引
        返回删除的向量数
        """
        to_remove = {
            i for i, meta in enumerate(self.metadata)
            if meta.get("title") == title
        }
        if not to_remove:
            return 0

        self.documents = [
            d for i, d in enumerate(self.documents) if i not in to_remove
        ]
        self.metadata = [
            m for i, m in enumerate(self.metadata) if i not in to_remove
        ]
        await self._rebuild_index()
        return len(to_remove)

    async def _rebuild_index(self):
        """重建FAISS索引"""
        import faiss
        if not self.documents:
            self.index = None
        else:
            embeddings = await self._embed_texts(self.documents)
            embeddings = np.array(embeddings).astype("float32")
            self.index = faiss.IndexFlatL2(embeddings.shape[1])
            self.index.add(embeddings)
        self._save_index()

    @property
    def document_count(self) -> int:
        return len(self.documents)


# Global instance
rag_service = RAGService()
