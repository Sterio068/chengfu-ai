"""
Feedback router · 👍👎 集中收集 + stats(per-agent 滿意率)

ROADMAP §11.1 B-2 · 從 main.py 抽出
- 對應 Champion 一週日誌「Top 滿意度低 agent」資料來源
- /feedback/stats 給 admin dashboard 用
"""
from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional, Literal
from datetime import datetime
from bson import ObjectId


router = APIRouter(tags=["feedback"])


class Feedback(BaseModel):
    message_id: str
    conversation_id: Optional[str] = None
    agent_name: Optional[str] = None
    verdict: Literal["up", "down"]
    note: Optional[str] = None
    user_email: Optional[str] = None


def _serialize(doc):
    """從 main.py 暫時複製 serialize · v1.2 全 router 抽完後改 _deps.py 共用"""
    if isinstance(doc, list):
        return [_serialize(d) for d in doc]
    if isinstance(doc, dict):
        return {k: _serialize(v) for k, v in doc.items()}
    if isinstance(doc, ObjectId):
        return str(doc)
    if isinstance(doc, datetime):
        return doc.isoformat()
    return doc


@router.post("/feedback")
def create_feedback(fb: Feedback):
    from main import feedback_col
    data = fb.model_dump()
    data["created_at"] = datetime.utcnow()
    feedback_col.update_one(
        {"message_id": fb.message_id, "user_email": fb.user_email},
        {"$set": data},
        upsert=True,
    )
    return {"ok": True}


@router.get("/feedback")
def list_feedback(verdict: Optional[str] = None, agent: Optional[str] = None, limit: int = 100):
    from main import feedback_col
    q = {}
    if verdict:
        q["verdict"] = verdict
    if agent:
        q["agent_name"] = {"$regex": agent, "$options": "i"}
    return _serialize(list(feedback_col.find(q).sort("created_at", -1).limit(limit)))


@router.get("/feedback/stats")
def feedback_stats():
    """👍 / 👎 比率 by agent。"""
    from main import feedback_col
    pipeline = [
        {"$group": {
            "_id": "$agent_name",
            "up":    {"$sum": {"$cond": [{"$eq": ["$verdict", "up"]}, 1, 0]}},
            "down":  {"$sum": {"$cond": [{"$eq": ["$verdict", "down"]}, 1, 0]}},
            "total": {"$sum": 1},
        }},
    ]
    stats = list(feedback_col.aggregate(pipeline))
    return [
        {"agent": s["_id"] or "unknown",
         "up": s["up"], "down": s["down"], "total": s["total"],
         "score": round(s["up"] / s["total"] * 100, 1) if s["total"] > 0 else 0}
        for s in stats
    ]
