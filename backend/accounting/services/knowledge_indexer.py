"""
知識庫增量索引器 · V1.1-SPEC §E-2
=====================================
每日凌晨 02:00 cron 跑 · 遍歷所有 enabled knowledge_sources · 各別增量 index 到 Meili
所有 source 共用一個 Meili index `chengfu_knowledge` · 透過 filterableAttributes 區隔

- 增量:比對 last_indexed_at · 只處理 mtime 之後的檔
- 排除:source.exclude_patterns + dir 結尾 / 斜線
- 限制:max_size_mb + mime_whitelist
- 失敗:單檔出錯 continue · 記 errors 計數

本模組只接 db + meili_client 參數 · 不 import main.py(services/__init__.py 設計原則)
"""
import os
import fnmatch
import hashlib
import pathlib
import logging
from datetime import datetime
from bson import ObjectId

from .knowledge_extract import extract

logger = logging.getLogger("chengfu.indexer")

MEILI_INDEX_NAME = "chengfu_knowledge"

# Meili index 設定(idempotent)· 索引不存在時會自動建
MEILI_SETTINGS = {
    "searchableAttributes": [
        "filename", "content_preview", "project", "source_name",
    ],
    "filterableAttributes": [
        "source_id", "source_name", "project", "type",
    ],
    "sortableAttributes": ["modified_at"],
}


def _match_excluded(rel_path: str, patterns: list[str]) -> bool:
    """支援:*.log(basename fnmatch) / /sensitive/*(目錄前綴)"""
    name = os.path.basename(rel_path)
    for p in patterns or []:
        if p.startswith("/"):
            if rel_path.startswith(p.lstrip("/").rstrip("*").rstrip("/")):
                return True
        elif fnmatch.fnmatch(name, p) or fnmatch.fnmatch(rel_path, p):
            return True
    return False


def _doc_id_for(source_id: str, rel_path: str) -> str:
    """Meili 文件 id · source_id + rel_path 決定唯一性 · 同檔修改 id 不變(覆蓋索引)"""
    return hashlib.md5(f"{source_id}::{rel_path}".encode()).hexdigest()


def _ensure_index(meili_client):
    """確保 index 存在、primaryKey 正確、settings 套用 · idempotent

    Meili 有個陷阱:第一次 update_settings 會 auto-create 無 primaryKey 的 index
    之後 add_documents 會因「多個 *_id 欄位」失敗(id / source_id 候選衝突)
    所以要先 explicit create_index(primaryKey='id') · 再 update_settings
    """
    try:
        # 先檢查 index 是否已存在且有 primary key
        info = meili_client.index(MEILI_INDEX_NAME).fetch_info()
        pk = getattr(info, "primary_key", None)
    except Exception:
        info, pk = None, None

    if info is None:
        # 不存在 · 建立(帶 primary key)
        meili_client.create_index(MEILI_INDEX_NAME, {"primaryKey": "id"})
    elif pk is None:
        # 存在但沒 primary key(先前 auto-create 的產物)· 砍掉重建
        logger.warning("[indexer] index %s 沒 primaryKey · 重建", MEILI_INDEX_NAME)
        meili_client.delete_index(MEILI_INDEX_NAME)
        meili_client.create_index(MEILI_INDEX_NAME, {"primaryKey": "id"})

    index = meili_client.index(MEILI_INDEX_NAME)
    index.update_settings(MEILI_SETTINGS)
    return index


def reindex_source(source_id: str, knowledge_sources_col, meili_client=None) -> dict:
    """對單一 source 增量索引。

    Parameters
    ----------
    source_id : str · MongoDB ObjectId string
    knowledge_sources_col : pymongo Collection
    meili_client : meilisearch.Client · None 則只抽字不上 Meili(測試用)

    Returns
    -------
    dict · {ok/skipped, file_count, index_seconds, errors, skipped_reasons}
    """
    try:
        _id = ObjectId(source_id)
    except Exception:
        return {"ok": False, "reason": f"source_id 格式錯誤: {source_id}"}

    src = knowledge_sources_col.find_one({"_id": _id})
    if not src:
        return {"ok": False, "reason": "資料源不存在"}
    if not src.get("enabled"):
        return {"ok": False, "skipped": True, "reason": "已停用"}

    started = datetime.utcnow()
    last_indexed = src.get("last_indexed_at")
    # 兩個修:
    # 1. TZ · datetime.utcnow() 是 naive · .timestamp() 會被當 local 轉 → 造成 8h 偏差
    #    用 calendar.timegm(utctimetuple()) 正確轉 UTC naive → epoch
    # 2. 精度 · mongomock / MongoDB 儲存 datetime 只保 ms · 而 st_mtime 有 ns/μs
    #    file_mtime = int(st.st_mtime) 後再比 · 避免邊界誤判
    import calendar
    if isinstance(last_indexed, datetime):
        since_mtime = calendar.timegm(last_indexed.utctimetuple())
    else:
        since_mtime = 0

    excludes = src.get("exclude_patterns", [])
    mime_white = src.get("mime_whitelist")  # None = 全收
    max_bytes = int(src.get("max_size_mb", 50)) * 1024 * 1024

    # Meili 若失敗(例如 key 錯)不擋索引流程 · 還是抽字 + 更新 last_indexed_at
    index = None
    meili_error = None
    if meili_client:
        try:
            index = _ensure_index(meili_client)
        except Exception as e:
            meili_error = f"{type(e).__name__}: {str(e)[:120]}"
            logger.warning("[indexer] Meili unavailable · continuing without search: %s", meili_error)

    docs_batch: list[dict] = []
    file_count = 0
    errors = 0
    skipped_excluded = 0
    skipped_unchanged = 0
    skipped_too_big = 0
    skipped_mime = 0

    base = src["path"]
    if not os.path.isdir(base):
        return {
            "ok": False,
            "reason": f"路徑不存在或不可讀: {base}",
        }

    for root, dirs, files in os.walk(base):
        # 修剪目錄 · 別走進排除的
        dirs[:] = [
            d for d in dirs
            if not _match_excluded(
                os.path.relpath(os.path.join(root, d), base),
                excludes,
            )
        ]
        for f in files:
            path = os.path.join(root, f)
            rel = os.path.relpath(path, base)
            if _match_excluded(rel, excludes):
                skipped_excluded += 1
                continue
            try:
                stat = os.stat(path)
            except OSError:
                errors += 1
                continue
            # 增量:只處理 mtime 之後 · file mtime 也 int 化(mongomock/Mongo 截 ms 精度)
            if int(stat.st_mtime) <= since_mtime:
                skipped_unchanged += 1
                continue
            if stat.st_size > max_bytes:
                skipped_too_big += 1
                continue
            ext = pathlib.Path(f).suffix.lower().lstrip(".")
            if mime_white and ext not in [w.lower().lstrip(".") for w in mime_white]:
                skipped_mime += 1
                continue

            try:
                doc = extract(path)
            except Exception as e:
                logger.warning("[indexer] extract fail %s: %s", path, e)
                errors += 1
                continue
            if doc.get("type") == "error":
                errors += 1
                # 還是 index 進去 · 讓使用者看得到「這檔讀失敗」
            # 衍生欄位給 Meili
            doc["id"] = _doc_id_for(str(src["_id"]), rel)
            doc["source_id"] = str(src["_id"])
            doc["source_name"] = src["name"]
            doc["rel_path"] = rel
            # 自動推 project · 若結構是 projects/<案>/...
            parts = rel.split(os.sep)
            if len(parts) > 1 and parts[0] == "projects":
                doc["project"] = parts[1]
            else:
                doc["project"] = None

            docs_batch.append(doc)
            file_count += 1

            # 批次送 Meili · 避免單次 payload 太大
            if index and len(docs_batch) >= 200:
                try:
                    index.add_documents(docs_batch)
                except Exception as e:
                    logger.error("[indexer] Meili add_documents fail: %s", e)
                    errors += len(docs_batch)
                docs_batch = []

    # flush 最後一批
    if index and docs_batch:
        try:
            index.add_documents(docs_batch)
        except Exception as e:
            logger.error("[indexer] Meili final add_documents fail: %s", e)
            errors += len(docs_batch)

    stats = {
        "ok": True,
        "file_count": file_count,
        "index_seconds": round((datetime.utcnow() - started).total_seconds(), 2),
        "errors": errors,
        "skipped": {
            "excluded": skipped_excluded,
            "unchanged": skipped_unchanged,
            "too_big": skipped_too_big,
            "wrong_mime": skipped_mime,
        },
        "meili": "indexed" if index else ("unavailable" if meili_error else "not_configured"),
    }
    if meili_error:
        stats["meili_error"] = meili_error
    # 寫回 source meta
    knowledge_sources_col.update_one(
        {"_id": src["_id"]},
        {"$set": {
            "last_indexed_at": datetime.utcnow(),
            "last_index_stats": stats,
        }},
    )
    logger.info(
        "[indexer] source=%s · files=%d · errors=%d · took=%.1fs",
        src["name"], file_count, errors, stats["index_seconds"],
    )
    return stats


def reindex_all(knowledge_sources_col, meili_client=None) -> dict:
    """cron 入口 · 所有 enabled sources 各跑一輪"""
    results = {}
    for src in knowledge_sources_col.find({"enabled": True}):
        sid = str(src["_id"])
        try:
            results[src["name"]] = reindex_source(sid, knowledge_sources_col, meili_client)
        except Exception as e:
            logger.exception("[indexer] reindex_all %s fail", src.get("name"))
            results[src["name"]] = {"ok": False, "reason": str(e)}
    return results


def delete_source_from_index(source_id: str, meili_client) -> dict:
    """source 被刪時 · 從 Meili 清掉所有該 source 的文件"""
    if not meili_client:
        return {"ok": False, "reason": "meili not configured"}
    try:
        index = meili_client.index(MEILI_INDEX_NAME)
        # Meili 支援 delete_documents(filter="...")
        task = index.delete_documents(filter=f'source_id = "{source_id}"')
        return {"ok": True, "task_uid": getattr(task, "task_uid", None)}
    except Exception as e:
        logger.warning("[indexer] Meili cleanup fail %s: %s", source_id, e)
        return {"ok": False, "reason": str(e)}


def search(meili_client, q: str, source_id: str = None, project: str = None,
           limit: int = 20) -> dict:
    """給 main.py /knowledge/search 用的包裝"""
    if not meili_client:
        return {"hits": [], "estimatedTotalHits": 0,
                "message": "Meili 未配置"}
    filters = []
    if source_id:
        filters.append(f'source_id = "{source_id}"')
    if project:
        filters.append(f'project = "{project}"')
    try:
        index = meili_client.index(MEILI_INDEX_NAME)
        return index.search(q, {
            "limit": max(1, min(100, limit)),
            "filter": " AND ".join(filters) if filters else None,
            "attributesToRetrieve": [
                "id", "filename", "rel_path", "source_id", "source_name",
                "project", "type", "content_preview", "modified_at",
            ],
        })
    except Exception as e:
        logger.warning("[indexer] search fail: %s", e)
        return {"hits": [], "estimatedTotalHits": 0,
                "message": f"搜尋失敗:{type(e).__name__}"}
