"""
Social scheduler router · Feature #5(FEATURE-PROPOSALS v1.2)

FB / IG / LinkedIn 貼文排程 · mock 實作 · 真 API 等 developer app 審核

涵蓋 7 endpoint:
- /social/posts GET · POST · PUT · DELETE
- /social/posts/{id}/publish-now POST(繞過排程立刻發)
- /admin/social/run-queue POST · internal-token · cron 每 5 分鐘掃

Collection · scheduled_posts:
{
  _id, author: email, platform: fb|ig|linkedin,
  content: str, image_url?, schedule_at: UTC datetime,
  status: queued|publishing|published|failed|cancelled,
  attempts: 0, last_error?,
  platform_post_id?, platform_url?,
  created_at, updated_at, dispatched_at?, published_at?
}
"""
import logging
from datetime import datetime, timedelta
from typing import Literal, Optional

from fastapi import APIRouter, Header, HTTPException, Query
from pydantic import BaseModel, Field
from bson import ObjectId
from bson.errors import InvalidId

from ._deps import require_admin_dep, require_user_dep
from services.social_providers import PublishError, publish


router = APIRouter(tags=["social"])
logger = logging.getLogger("chengfu")

MAX_RETRIES = 3
PLATFORMS = ("facebook", "instagram", "linkedin")


def _oid(post_id: str) -> ObjectId:
    try:
        return ObjectId(post_id)
    except (InvalidId, TypeError):
        raise HTTPException(400, "post_id 格式錯誤")


class ScheduledPost(BaseModel):
    platform: Literal["facebook", "instagram", "linkedin"]
    content: str = Field(min_length=1, max_length=3000)
    schedule_at: datetime  # UTC
    image_url: Optional[str] = None


class ScheduledPostPatch(BaseModel):
    content: Optional[str] = Field(default=None, min_length=1, max_length=3000)
    schedule_at: Optional[datetime] = None
    image_url: Optional[str] = None


# ============================================================
# CRUD
# ============================================================
@router.post("/social/posts")
def create_post(p: ScheduledPost, email: str = require_user_dep()):
    from main import db

    if p.platform == "instagram" and not p.image_url:
        raise HTTPException(400, "Instagram 需要 image_url(IG 硬規定)")
    if p.schedule_at < datetime.utcnow() - timedelta(minutes=5):
        raise HTTPException(400, "schedule_at 不能在過去")

    doc = {
        "author": email,
        "platform": p.platform,
        "content": p.content,
        "image_url": p.image_url,
        "schedule_at": p.schedule_at,
        "status": "queued",
        "attempts": 0,
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow(),
    }
    r = db.scheduled_posts.insert_one(doc)
    return {"post_id": str(r.inserted_id), "status": "queued"}


@router.get("/social/posts")
def list_posts(
    status: Optional[str] = None,
    platform: Optional[str] = None,
    limit: int = Query(default=50, ge=1, le=500),
    skip: int = Query(default=0, ge=0),
    email: str = require_user_dep(),
):
    """同事只看自己的 · admin 看全部(以後加 /admin/social/posts)"""
    from main import db, serialize
    q = {"author": email}
    if status:
        q["status"] = status
    if platform:
        q["platform"] = platform
    cursor = db.scheduled_posts.find(q).sort("schedule_at", -1).skip(skip).limit(limit)
    items = serialize(list(cursor))
    total = db.scheduled_posts.count_documents(q)
    return {"items": items, "total": total, "skip": skip, "limit": limit,
            "has_more": (skip + len(items)) < total}


@router.get("/social/posts/{post_id}")
def get_post(post_id: str, email: str = require_user_dep()):
    from main import db, serialize
    doc = db.scheduled_posts.find_one({"_id": _oid(post_id)})
    if not doc:
        raise HTTPException(404, "貼文不存在")
    if doc["author"] != email:
        raise HTTPException(403, "只能看自己的貼文")
    return serialize(doc)


@router.put("/social/posts/{post_id}")
def update_post(post_id: str, p: ScheduledPostPatch, email: str = require_user_dep()):
    """只能改 queued 狀態 · 已 publish 過不能改"""
    from main import db
    oid = _oid(post_id)
    existing = db.scheduled_posts.find_one({"_id": oid})
    if not existing:
        raise HTTPException(404, "貼文不存在")
    if existing["author"] != email:
        raise HTTPException(403, "只能改自己的貼文")
    if existing["status"] != "queued":
        raise HTTPException(409, f"狀態 {existing['status']} 不能改 · 只有 queued 可改")

    updates = {k: v for k, v in p.model_dump(exclude_unset=True).items() if v is not None}
    if not updates:
        raise HTTPException(400, "沒有可更新欄位")
    if "schedule_at" in updates and updates["schedule_at"] < datetime.utcnow():
        raise HTTPException(400, "schedule_at 不能在過去")
    updates["updated_at"] = datetime.utcnow()
    db.scheduled_posts.update_one({"_id": oid}, {"$set": updates})
    return {"updated": True}


@router.delete("/social/posts/{post_id}")
def cancel_post(post_id: str, email: str = require_user_dep()):
    """軟刪 · status=cancelled · 已 publish 過不給刪"""
    from main import db
    oid = _oid(post_id)
    existing = db.scheduled_posts.find_one({"_id": oid})
    if not existing:
        raise HTTPException(404, "貼文不存在")
    if existing["author"] != email:
        raise HTTPException(403, "只能改自己的貼文")
    if existing["status"] == "published":
        raise HTTPException(409, "已發出 · 不能 cancel · 到 FB/IG/LinkedIn 自行刪")

    db.scheduled_posts.update_one(
        {"_id": oid},
        {"$set": {"status": "cancelled", "updated_at": datetime.utcnow()}},
    )
    return {"cancelled": True}


@router.post("/social/posts/{post_id}/publish-now")
def publish_now(post_id: str, email: str = require_user_dep()):
    """繞過排程立刻發 · 內部呼 provider"""
    from main import db
    oid = _oid(post_id)
    existing = db.scheduled_posts.find_one({"_id": oid})
    if not existing:
        raise HTTPException(404, "貼文不存在")
    if existing["author"] != email:
        raise HTTPException(403, "只能發自己的貼文")
    if existing["status"] not in ("queued", "failed"):
        raise HTTPException(409, f"狀態 {existing['status']} 不能立刻發")

    return _dispatch_one(oid, existing)


# ============================================================
# Dispatcher(cron 呼 admin endpoint · 掃 queue)
# ============================================================
def _dispatch_one(oid: ObjectId, doc: dict) -> dict:
    """把一筆 post 送去 provider · 更新 status · 失敗重排"""
    from main import db

    # Atomic claim · 防兩個 worker 同時 dispatch 同筆
    r = db.scheduled_posts.update_one(
        {"_id": oid, "status": {"$in": ["queued", "failed"]}},
        {"$set": {"status": "publishing", "dispatched_at": datetime.utcnow(),
                  "updated_at": datetime.utcnow()}},
    )
    if r.modified_count == 0:
        return {"skipped": "already dispatched by another worker"}

    try:
        result = publish(doc["platform"], doc["content"], doc.get("image_url"))
        db.scheduled_posts.update_one(
            {"_id": oid},
            {"$set": {
                "status": "published",
                "platform_post_id": result["post_id"],
                "platform_url": result["url"],
                "published_at": datetime.utcnow(),
                "updated_at": datetime.utcnow(),
                "last_error": None,
            }},
        )
        return {"published": True, **result}
    except PublishError as e:
        attempts = doc.get("attempts", 0) + 1
        new_status = "failed" if attempts >= MAX_RETRIES else "queued"
        # Retry 間隔 · exp backoff 寫進 schedule_at
        if new_status == "queued":
            next_try = datetime.utcnow() + timedelta(minutes=2 ** attempts)
        else:
            next_try = doc["schedule_at"]
        db.scheduled_posts.update_one(
            {"_id": oid},
            {"$set": {
                "status": new_status,
                "attempts": attempts,
                "last_error": str(e)[:300],
                "schedule_at": next_try,
                "updated_at": datetime.utcnow(),
            }},
        )
        # final fail 通知 admin(audit log)
        if new_status == "failed":
            try:
                db.audit_log.insert_one({
                    "action": "social_publish_fail",
                    "user": doc["author"],
                    "resource": str(oid),
                    "details": {"platform": doc["platform"], "error": str(e)[:300],
                                "attempts": attempts},
                    "created_at": datetime.utcnow(),
                })
            except Exception:
                pass
        return {"published": False, "attempts": attempts, "status": new_status,
                "error": str(e)[:300]}


@router.post("/admin/social/run-queue")
def run_queue(
    x_internal_token: Optional[str] = Header(default=None),
    limit: int = Query(default=20, ge=1, le=100),
):
    """cron 每 5 分鐘打 · 撈 schedule_at <= now 的 queued/failed · 逐筆 dispatch

    走 internal-token · 不走 admin cookie(cron 沒登入)
    """
    import os, hmac
    expected = os.getenv("ECC_INTERNAL_TOKEN", "").strip()
    provided = (x_internal_token or "").strip()
    if not expected or not provided or not hmac.compare_digest(provided, expected):
        raise HTTPException(403, "internal token invalid")

    from main import db
    now = datetime.utcnow()
    to_dispatch = list(db.scheduled_posts.find(
        {"status": {"$in": ["queued", "failed"]},
         "schedule_at": {"$lte": now},
         "attempts": {"$lt": MAX_RETRIES}},
        sort=[("schedule_at", 1)],
        limit=limit,
    ))

    results = []
    for doc in to_dispatch:
        r = _dispatch_one(doc["_id"], doc)
        results.append({"post_id": str(doc["_id"]), **r})

    return {"dispatched": len(results), "results": results}
