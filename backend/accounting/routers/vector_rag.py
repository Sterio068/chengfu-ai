"""
Vector RAG · v2.0-β · 知識庫語意搜尋升級
========================================
取代純 Meilisearch text-only · AI 用 OpenAI embedding 找意思相近的文件
而非只字面匹配。

架構決策:
  · 10 人公司規模 · 知識庫文件 < 1000 份 → mongo cosine 已足夠
    若擴到 100 人 / 萬份文件 · 升 pgvector / Meili vectorStore
  · embedding model: text-embedding-3-large (3072 維) · 中文表現遠勝 small
    若成本敏感 · 改 text-embedding-3-small (1536 維) · 約 1/4 成本

端點:
  POST /vector-rag/index/<source>  · 建/更新文件向量(管理員 / cron)
  POST /vector-rag/search          · 同事查詢 · 回 top-K 相近文件

mongo collection · knowledge_embeddings:
  { source_id, doc_id, content_hash, text_preview, embedding[3072], indexed_at }

cron 整合(可選):
  scripts/cron/refresh-vector-index.sh 每天 02:00 跑 · 增量建索引
"""
from __future__ import annotations

import hashlib
import math
import os
from datetime import datetime, timezone
from typing import Optional

import httpx
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from routers._deps import _is_admin_user, require_user_dep


router = APIRouter(prefix="/vector-rag", tags=["vector-rag"])

OPENAI_BASE = os.getenv("OPENAI_API_BASE", "https://api.openai.com/v1")
EMBEDDING_MODEL = os.getenv("COMPANY_AI_EMBEDDING_MODEL", "text-embedding-3-large")
EMBEDDING_DIM = int(os.getenv("COMPANY_AI_EMBEDDING_DIM", "3072"))


class IndexRequest(BaseModel):
    source_id: str = Field(..., description="來源 id · 例 'skills/01-政府標案結構分析'")
    text: str = Field(..., description="文件全文 · 由 caller 從檔案讀好")
    doc_id: Optional[str] = Field(None, description="文件唯一 key · 沒給用 hash")


class SearchRequest(BaseModel):
    query: str = Field(..., description="查詢自然語言 · 例「中秋節怎麼做活動?」")
    top_k: int = Field(5, ge=1, le=20)
    min_similarity: float = Field(
        0.3, ge=0.0, le=1.0,
        description="相似度下限 · 低於不返回 · 預設 0.3 寬鬆",
    )


async def _embed(text: str) -> list[float]:
    """呼叫 OpenAI embeddings · 回 vector"""
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise HTTPException(503, "OPENAI_API_KEY 未設 · 無法 embed")
    if len(text) > 8000:
        text = text[:8000]  # OpenAI input limit
    async with httpx.AsyncClient(timeout=30) as client:
        r = await client.post(
            f"{OPENAI_BASE}/embeddings",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            json={"model": EMBEDDING_MODEL, "input": text},
        )
        if r.status_code != 200:
            raise HTTPException(502, f"OpenAI embedding 失敗: {r.text[:200]}")
        return r.json()["data"][0]["embedding"]


def _cosine(a: list[float], b: list[float]) -> float:
    if len(a) != len(b):
        return 0.0
    dot = sum(x * y for x, y in zip(a, b))
    na = math.sqrt(sum(x * x for x in a))
    nb = math.sqrt(sum(y * y for y in b))
    if na == 0 or nb == 0:
        return 0.0
    return dot / (na * nb)


@router.post("/index")
async def index_document(
    req: IndexRequest,
    user_email: str = require_user_dep(),
):
    """建/更新文件向量 · admin only · 通常 cron 跑"""
    if not _is_admin_user(user_email) and not user_email.startswith("internal:"):
        raise HTTPException(403, "只有管理員 / cron 可建 vector index")

    from main import db
    content_hash = hashlib.sha256(req.text.encode()).hexdigest()
    doc_id = req.doc_id or hashlib.sha256(req.source_id.encode()).hexdigest()[:16]

    # idempotent · 同 hash 不重新 embed
    existing = db.knowledge_embeddings.find_one({"doc_id": doc_id})
    if existing and existing.get("content_hash") == content_hash:
        return {"status": "skipped", "reason": "content unchanged", "doc_id": doc_id}

    embedding = await _embed(req.text)
    db.knowledge_embeddings.update_one(
        {"doc_id": doc_id},
        {"$set": {
            "source_id": req.source_id,
            "doc_id": doc_id,
            "content_hash": content_hash,
            "text_preview": req.text[:300],
            "embedding": embedding,
            "indexed_at": datetime.now(timezone.utc),
            "embedding_model": EMBEDDING_MODEL,
        }},
        upsert=True,
    )
    return {
        "status": "indexed", "doc_id": doc_id,
        "source_id": req.source_id, "vector_dim": len(embedding),
    }


@router.post("/search")
async def search_vector(
    req: SearchRequest,
    user_email: str = require_user_dep(),
):
    """語意搜尋 · 同事用人話查 · 回 top-K 相近文件"""
    from main import db
    query_vec = await _embed(req.query)
    docs = list(db.knowledge_embeddings.find({}, {"_id": 0, "embedding": 1, "source_id": 1, "text_preview": 1, "doc_id": 1}))

    scored = []
    for d in docs:
        sim = _cosine(query_vec, d.get("embedding", []))
        if sim >= req.min_similarity:
            scored.append({
                "source_id": d["source_id"],
                "doc_id": d["doc_id"],
                "text_preview": d["text_preview"],
                "similarity": round(sim, 4),
            })
    scored.sort(key=lambda x: -x["similarity"])
    return {
        "query": req.query,
        "total_indexed": len(docs),
        "model": EMBEDDING_MODEL,
        "results": scored[:req.top_k],
    }


@router.get("/stats")
def index_stats(user_email: str = require_user_dep()):
    """index 統計 · admin / 任何 user 都可看"""
    from main import db
    total = db.knowledge_embeddings.count_documents({})
    by_source = list(db.knowledge_embeddings.aggregate([
        {"$group": {"_id": "$source_id", "count": {"$sum": 1}}},
        {"$sort": {"count": -1}},
        {"$limit": 30},
    ]))
    last = db.knowledge_embeddings.find().sort("indexed_at", -1).limit(1)
    last_doc = next(iter(last), None)
    return {
        "total_indexed": total,
        "embedding_model": EMBEDDING_MODEL,
        "by_source": [{"source_id": s["_id"], "count": s["count"]} for s in by_source],
        "last_indexed_at": last_doc.get("indexed_at").isoformat() if last_doc and last_doc.get("indexed_at") else None,
    }
