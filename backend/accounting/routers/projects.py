"""
Projects router · v1.3 §11.1 B-10 · 從 main.py 抽出

涵蓋:
- /projects GET/POST · /projects/{id} PUT/DELETE
- /projects/{id}/handoff GET/PUT(B2 · 4 格卡 跨人 / 跨日交棒 artifact)

依賴:
- main.py(lazy)· projects_col / serialize
- 跟 routers/accounting.py 的 /projects/{id}/finance 共用 projects collection · 不衝突

注意:V1.1-SPEC §C handoff endpoint 獨立於 PUT /projects/{id} · 不全量更新
"""
import logging
from datetime import datetime, timezone
from typing import Optional, Literal

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from bson import ObjectId
from bson.errors import InvalidId

from ._deps import _is_admin_user, require_permission_dep, require_user_dep


# R27#2 · router-wide require login · nginx /api-accounting 公開 · 沒登入禁讀寫 project
router = APIRouter(tags=["projects"], dependencies=[require_user_dep()])
logger = logging.getLogger("chengfu")


def _project_oid(project_id: str) -> ObjectId:
    """R13#2 · ObjectId 解析統一處理 · 不誤吞 Mongo 寫入錯誤
    原 except Exception 太寬 · update_one 失敗也會誤回 400 'project_id 格式錯誤'
    """
    try:
        return ObjectId(project_id)
    except (InvalidId, TypeError):
        raise HTTPException(400, "project_id 格式錯誤")


# ============================================================
# Models
# ============================================================
class Project(BaseModel):
    name: str
    client: Optional[str] = None
    budget: Optional[float] = None
    deadline: Optional[str] = None
    description: Optional[str] = None
    status: Literal["active", "closed"] = "active"
    owner: Optional[str] = None
    collaborators: list[str] = Field(default_factory=list)
    next_owner: Optional[str] = None


class HandoffAssetRef(BaseModel):
    type: Literal["nas", "url", "file", "note"] = "note"
    label: str = ""
    ref: str = ""


class HandoffCard(BaseModel):
    goal: str = ""
    constraints: list[str] = Field(default_factory=list)
    asset_refs: list[HandoffAssetRef] = Field(default_factory=list)
    next_actions: list[str] = Field(default_factory=list)
    source_conversation_id: Optional[str] = None


class HandoffAppend(BaseModel):
    target: Literal["next_action", "asset_ref", "constraint", "goal"] = "asset_ref"
    text: str
    label: Optional[str] = None
    source_conversation_id: Optional[str] = None


def _asset_ref_dict(item) -> Optional[dict]:
    if hasattr(item, "model_dump"):
        item = item.model_dump()
    if not isinstance(item, dict):
        return None
    return {
        "type": item.get("type") or "note",
        "label": item.get("label") or "",
        "ref": item.get("ref") or "",
    }


def _same_asset_ref(a: dict, b: dict) -> bool:
    return (
        (a.get("type") or "note") == (b.get("type") or "note")
        and (a.get("label") or "") == (b.get("label") or "")
        and (a.get("ref") or "") == (b.get("ref") or "")
    )


def _is_site_asset_ref(ref: dict, system_refs: list[dict]) -> bool:
    label = ref.get("label") or ""
    if label.startswith("場勘彙整"):
        return True
    return any(_same_asset_ref(ref, s) for s in system_refs)


def _dedupe_asset_refs(refs: list) -> list[dict]:
    out = []
    seen = set()
    for item in refs or []:
        ref = _asset_ref_dict(item)
        if not ref:
            continue
        key = (ref["type"], ref["label"], ref["ref"])
        if key in seen:
            continue
        seen.add(key)
        out.append(ref)
    return out


def _dedupe_strings(items: list) -> list[str]:
    out = []
    seen = set()
    for item in items or []:
        if not isinstance(item, str):
            continue
        value = item.strip()
        if not value or value in seen:
            continue
        seen.add(value)
        out.append(value)
    return out


def _clean_emails(items: list[str]) -> list[str]:
    out = []
    seen = set()
    for item in items or []:
        value = (item or "").strip().lower()
        if not value or value in seen:
            continue
        seen.add(value)
        out.append(value)
    return out


def _project_access_filter(project_id: str, email: str) -> dict:
    q = {"_id": _project_oid(project_id)}
    if not _is_admin_user(email):
        q["$or"] = [
            {"owner": email},
            {"collaborators": email},
            {"next_owner": email},
        ]
    return q


def _project_owner_filter(project_id: str, email: str) -> dict:
    q = {"_id": _project_oid(project_id)}
    if not _is_admin_user(email):
        q["owner"] = email
    return q


def _project_list_filter(email: str) -> dict:
    if _is_admin_user(email):
        return {}
    return {"$or": [
        {"owner": email},
        {"collaborators": email},
        {"next_owner": email},
    ]}


def _ensure_project_exists_or_forbidden(projects_col, oid: ObjectId):
    if projects_col.find_one({"_id": oid}, {"_id": 1}):
        raise HTTPException(403, "只能操作自己負責或協作中的專案")
    raise HTTPException(404, "專案不存在")


# ============================================================
# Endpoints · 專案 CRUD
# ============================================================
@router.get("/projects")
def list_projects(status: Optional[str] = None, email: str = require_user_dep()):
    from main import projects_col, serialize
    q = _project_list_filter(email)
    if status: q["status"] = status
    return serialize(list(projects_col.find(q).sort("updated_at", -1)))


@router.post("/projects")
def create_project(p: Project, email: str = require_permission_dep("project.create")):
    from main import projects_col
    data = p.model_dump()
    data["owner"] = data.get("owner") if _is_admin_user(email) and data.get("owner") else email
    data["collaborators"] = _clean_emails(data.get("collaborators") or [])
    if data.get("next_owner"):
        data["next_owner"] = data["next_owner"].strip().lower()
    data["created_at"] = datetime.now(timezone.utc)
    data["updated_at"] = datetime.now(timezone.utc)
    r = projects_col.insert_one(data)
    return {"id": str(r.inserted_id)}


@router.put("/projects/{project_id}")
def update_project(project_id: str, p: Project, email: str = require_user_dep()):
    """R14#1 · 用 _project_oid · 補 404 · bad id 不再 500"""
    from main import projects_col
    data = p.model_dump(exclude_unset=True)  # py-review #1 · pydantic v2 一致
    if not _is_admin_user(email):
        data.pop("owner", None)
    if "collaborators" in data:
        data["collaborators"] = _clean_emails(data.get("collaborators") or [])
    if data.get("next_owner"):
        data["next_owner"] = data["next_owner"].strip().lower()
    data["updated_at"] = datetime.now(timezone.utc)
    q = _project_owner_filter(project_id, email)
    r = projects_col.update_one(q, {"$set": data})
    if r.matched_count == 0:
        _ensure_project_exists_or_forbidden(projects_col, q["_id"])
    return {"updated": r.modified_count}


@router.delete("/projects/{project_id}")
def delete_project(project_id: str, email: str = require_user_dep()):
    """R14#1 · 用 _project_oid · 補 404"""
    from main import projects_col
    q = _project_owner_filter(project_id, email)
    r = projects_col.delete_one(q)
    if r.deleted_count == 0:
        _ensure_project_exists_or_forbidden(projects_col, q["_id"])
    return {"deleted": r.deleted_count}


# ============================================================
# B2 · Handoff 4 格卡(跨助手 · 跨人 · 跨日的交棒 artifact)
# V1.1-SPEC §C · 獨立 endpoint 不用 PUT /projects/{id} 全量更新
# ============================================================
@router.put("/projects/{project_id}/handoff")
def update_handoff(project_id: str, card: HandoffCard, email: str = require_user_dep()):
    """PM 存完 · 多分頁 BroadcastChannel 會通知其他同仁 re-render.

    只更新 4 格人工欄位,避免洗掉 site survey / meeting / workflow 等機器寫入欄位。
    """
    from main import projects_col
    now = datetime.now(timezone.utc)
    q = _project_access_filter(project_id, email)
    existing = projects_col.find_one(q, {"handoff": 1})
    if not existing:
        _ensure_project_exists_or_forbidden(projects_col, q["_id"])
    existing_handoff = existing.get("handoff") or {}
    card_data = card.model_dump()
    site_asset_refs = _dedupe_asset_refs(existing_handoff.get("site_asset_refs", []))
    legacy_site_refs = [
        ref for ref in _dedupe_asset_refs(existing_handoff.get("asset_refs", []))
        if (ref.get("label") or "").startswith("場勘彙整")
    ]
    system_asset_refs = _dedupe_asset_refs([*site_asset_refs, *legacy_site_refs])
    meeting_next_actions = _dedupe_strings(existing_handoff.get("meeting_next_actions", []))
    incoming_refs = _dedupe_asset_refs(card_data.get("asset_refs", []))
    incoming_actions = _dedupe_strings(card_data.get("next_actions", []))
    manual_refs = [ref for ref in incoming_refs if not _is_site_asset_ref(ref, system_asset_refs)]
    manual_actions = [a for a in incoming_actions if a not in set(meeting_next_actions)]
    update_doc = {"$set": {
        "handoff.goal": card_data.get("goal", ""),
        "handoff.constraints": card_data.get("constraints", []),
        "handoff.asset_refs": manual_refs,
        "handoff.next_actions": manual_actions,
        "handoff.source_conversation_id": card_data.get("source_conversation_id"),
        "handoff.updated_by": email,
        "handoff.updated_at": now,
        "updated_at": now,
    }}
    if system_asset_refs:
        update_doc["$addToSet"] = {"handoff.site_asset_refs": {"$each": system_asset_refs}}

    # R13#2 · _project_oid raise 400 為唯一 · update_one 失敗 → 真 500(Mongo 異常)
    # Round 2 · 人工欄位可刪;系統欄位分流 site_asset_refs / meeting_next_actions,避免並發覆蓋。
    r = projects_col.update_one(
        q,
        update_doc,
    )
    return {"ok": True, "updated_at": now.isoformat()}


@router.get("/projects/{project_id}/handoff")
def get_handoff(project_id: str, email: str = require_user_dep()):
    from main import projects_col
    q = _project_access_filter(project_id, email)
    doc = projects_col.find_one(q, {"handoff": 1, "name": 1})
    if not doc:
        _ensure_project_exists_or_forbidden(projects_col, q["_id"])
    h = doc.get("handoff") or {}
    h["asset_refs"] = _dedupe_asset_refs([
        *(h.get("asset_refs") or []),
        *(h.get("site_asset_refs") or []),
    ])
    h["next_actions"] = _dedupe_strings([
        *(h.get("next_actions") or []),
        *(h.get("meeting_next_actions") or []),
    ])
    if isinstance(h.get("updated_at"), datetime):
        h["updated_at"] = h["updated_at"].isoformat()
    return {"project_name": doc.get("name", ""), "handoff": h}


@router.post("/projects/{project_id}/handoff/append")
def append_handoff(project_id: str, item: HandoffAppend, email: str = require_user_dep()):
    """Append AI/chat outputs into handoff without overwriting existing manual/system fields."""
    from main import projects_col
    text = (item.text or "").strip()
    if not text:
        raise HTTPException(400, "text 不可空白")
    now = datetime.now(timezone.utc)
    q = _project_access_filter(project_id, email)
    update_doc = {"$set": {
        "handoff.updated_by": email,
        "handoff.updated_at": now,
        "updated_at": now,
    }}
    if item.source_conversation_id:
        update_doc["$set"]["handoff.source_conversation_id"] = item.source_conversation_id

    if item.target == "next_action":
        update_doc["$addToSet"] = {"handoff.next_actions": text}
    elif item.target == "constraint":
        update_doc["$addToSet"] = {"handoff.constraints": text}
    elif item.target == "goal":
        existing = projects_col.find_one(q, {"handoff.goal": 1})
        if not existing:
            _ensure_project_exists_or_forbidden(projects_col, q["_id"])
        current_goal = ((existing.get("handoff") or {}).get("goal") or "").strip()
        update_doc["$set"]["handoff.goal"] = text if not current_goal else f"{current_goal}\n{text}"
    else:
        ref = {
            "type": "note",
            "label": (item.label or "AI 回答摘要").strip() or "AI 回答摘要",
            "ref": text,
        }
        update_doc["$addToSet"] = {"handoff.asset_refs": ref}

    r = projects_col.update_one(q, update_doc)
    if r.matched_count == 0:
        _ensure_project_exists_or_forbidden(projects_col, q["_id"])
    return {"ok": True, "updated_at": now.isoformat(), "target": item.target}
