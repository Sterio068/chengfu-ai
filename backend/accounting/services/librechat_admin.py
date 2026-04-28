"""
v1.3 B5 · LibreChat 跨 collection PDPA 操作

LibreChat 跟 accounting 共用 company_ai db(同 mongo)· 但 collections 是 LibreChat 自己 schema
PDPA delete-on-request 必須跨這些 collection 一起清:
- users(刪本人)
- conversations / messages / files / sharedlinks(對話)
- presets / promptgroups / prompts(自定)
- sessions / tokens / pluginauths(認證)
- balances / toolcalls / memoryentries(usage / log)
- conversationtags(分類 tag)

注意:
- LibreChat user 識別用 ObjectId(_id)· 不是 email
- 必先 find_one({email}) 拿 _id 再去刪相關 doc
- archive 必先(法務保留期內可還)· archive 失敗禁止刪除
- agents / assistants 暫不刪(全公司共用 · 同事不該擁有)
"""
import gzip
import json
import logging
import os
import subprocess
from datetime import datetime, timezone
from typing import Optional

from bson import ObjectId

logger = logging.getLogger("company_ai")


# LibreChat 使用者擁有的 collections + 對應 user 欄位名
USER_OWNED_COLLECTIONS = [
    ("conversations", "user"),
    ("messages", "user"),
    ("files", "user"),
    ("sharedlinks", "user"),
    ("presets", "user"),
    ("conversationtags", "user"),
    ("sessions", "user"),
    ("tokens", "userId"),
    ("pluginauths", "userId"),
    ("promptgroups", "author"),
    ("prompts", "author"),
    ("toolcalls", "user"),
    ("balances", "user"),
    ("memoryentries", "userId"),
]


class LibreChatNotFound(Exception):
    """email 在 LibreChat users 找不到 · 可能還沒登入過"""


def find_librechat_user_id(db, email: str) -> Optional[ObjectId]:
    """case-insensitive email → user._id · 沒找到回 None
    用 LibreChat 自己的 users collection · 不是 _users_col(同表 · 但 lazy import 防 cycle)"""
    import re
    pattern = {"$regex": f"^{re.escape(email.strip())}$", "$options": "i"}
    user = db.users.find_one({"email": pattern}, {"_id": 1})
    return user["_id"] if user else None


def count_librechat_data(db, user_id: ObjectId) -> dict:
    """數該 user 在 LibreChat 各 collection 的 doc 數 · dry_run 用"""
    counts = {}
    for col_name, field in USER_OWNED_COLLECTIONS:
        try:
            counts[col_name] = db[col_name].count_documents({field: user_id})
        except Exception as e:
            logger.warning("[librechat-pdpa] count %s fail: %s", col_name, e)
            counts[col_name] = -1  # 標 error
    return counts


def archive_librechat_data(db, user_id: ObjectId, email: str,
                            archive_dir: str = None) -> str:
    """歸檔 user 全 LibreChat 資料為 GPG 加密 JSON.gz
    法務保留期內可還(訴訟 / 稽核)
    回 archive 檔絕對路徑 · 失敗 raise

    格式:~/company-ai-backups/offboarding/{email}-{date}/librechat-{user_id}.json.gz.gpg
    """
    archive_dir = archive_dir or os.path.expanduser(
        f"~/company-ai-backups/offboarding/{email}-{datetime.now(timezone.utc).strftime('%Y-%m-%d')}"
    )
    os.makedirs(archive_dir, exist_ok=True)

    payload = {
        "exported_at": datetime.now(timezone.utc).isoformat(),
        "user_id": str(user_id),
        "email": email,
        "schema_version": "librechat-v0.8.4",
        "collections": {},
    }

    # 撈 user 本人 doc(不刪 password hash · 但留 metadata 給法務)
    try:
        user_doc = db.users.find_one({"_id": user_id}, {"password": 0})
        if user_doc:
            user_doc["_id"] = str(user_doc["_id"])
            payload["user"] = json.loads(json.dumps(user_doc, default=str))
    except Exception as e:
        logger.warning("[librechat-pdpa] archive user doc fail: %s", e)

    for col_name, field in USER_OWNED_COLLECTIONS:
        try:
            docs = list(db[col_name].find({field: user_id}))
            for d in docs:
                d["_id"] = str(d["_id"])
            payload["collections"][col_name] = json.loads(json.dumps(docs, default=str))
        except Exception as e:
            logger.warning("[librechat-pdpa] archive %s fail: %s", col_name, e)
            payload["collections"][col_name] = {"_error": str(e)[:200]}

    # 寫 gzip JSON
    raw_path = os.path.join(archive_dir, f"librechat-{user_id}.json.gz")
    with gzip.open(raw_path, "wt", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)

    # GPG 加密(若 'company_ai' key 存在)· 防 archive 明文洩
    gpg_path = raw_path + ".gpg"
    has_gpg = subprocess.run(
        ["gpg", "--list-keys", "company_ai"],
        capture_output=True,
    ).returncode == 0
    if has_gpg:
        try:
            subprocess.run(
                ["gpg", "--batch", "--yes", "--encrypt",
                 "--recipient", "company_ai",
                 "--output", gpg_path, raw_path],
                check=True, capture_output=True,
            )
            os.remove(raw_path)  # 刪明文 · 只留 .gpg
            return gpg_path
        except Exception as e:
            logger.error("[librechat-pdpa] GPG encrypt fail: %s", e)
            raise RuntimeError(f"archive GPG 加密失敗 · 不繼續刪除:{e}")
    else:
        logger.warning("[librechat-pdpa] 'company_ai' GPG key 缺 · archive 未加密(.json.gz)")
        return raw_path


def delete_librechat_data(db, user_id: ObjectId) -> dict:
    """跨 LibreChat collection 刪該 user 全資料 + 刪 user 本人 doc
    回 {col_name: deleted_count, _failed: [...]} · 失敗 col 標 -1

    v1.3 batch6 · CRITICAL · partial fail 時不刪 users doc
    避免 conversations / messages 殘留但 user 已刪 · PDPA 合規漏洞"""
    counts = {}
    failed = []
    for col_name, field in USER_OWNED_COLLECTIONS:
        try:
            r = db[col_name].delete_many({field: user_id})
            counts[col_name] = r.deleted_count
        except Exception as e:
            logger.error("[librechat-pdpa] delete %s fail: %s", col_name, e)
            counts[col_name] = -1
            failed.append(col_name)

    # v1.3 batch6 · CRITICAL · 任何 collection 失敗 · 不刪 users doc
    # 留著 user 才能下次 retry · 否則資料變孤兒(user_id 找不到對應 user)
    if failed:
        logger.error(
            "[librechat-pdpa] %d collection 刪除失敗 · 跳過 users 刪除 · 需手動 retry: %s",
            len(failed), failed,
        )
        counts["users"] = "skipped_due_to_partial_failure"
        counts["_failed"] = failed
        return counts

    # 全部 collection 都成功 · 才刪 users
    try:
        r = db.users.delete_one({"_id": user_id})
        counts["users"] = r.deleted_count
    except Exception as e:
        logger.error("[librechat-pdpa] delete user fail: %s", e)
        counts["users"] = -1
        counts["_failed"] = ["users"]
    return counts
