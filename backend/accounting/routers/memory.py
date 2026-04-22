"""
Memory router · v1.3 §11.1 B-11 · 從 main.py 抽出

涵蓋:
- /memory/summarize-conversation POST(Haiku 4.5 摘要 · 省 60% context)
- /memory/transcribe POST(v1.2 Feature #1 · Whisper STT + Haiku 結構化會議紀錄)
- /memory/meetings GET · /{id} · /{id}/push-to-handoff(會議 CRUD + 推到 project)

Feature #1 · 會議速記自動化(R14 · FEATURE-PROPOSALS v1.2):
- PR 公司每週 10 場客戶會議 · 手打 40 分/場 = 月省 67h / 10 人
- 流程:上傳音檔 → Whisper STT → Haiku 整理 → 結構化 → 自動填 handoff

依賴:
- anthropic(已有)· openai(Feature #1 新)
- main.py 的 db.messages / db.conversations(LibreChat 私有 schema)
"""
import hashlib
import logging
import os
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, BackgroundTasks, File, Form, HTTPException, Request, UploadFile
from pydantic import BaseModel
from bson import ObjectId
from bson.errors import InvalidId

from ._deps import require_user_dep


router = APIRouter(tags=["memory"])
logger = logging.getLogger("chengfu")


# Feature #1 · Whisper API 上限 25MB
WHISPER_MAX_BYTES = 25 * 1024 * 1024
ALLOWED_AUDIO_MIMES = {
    "audio/mpeg", "audio/mp3", "audio/mp4", "audio/m4a",
    "audio/wav", "audio/x-wav", "audio/webm", "audio/ogg",
    "audio/flac", "video/mp4",  # m4a 檔常被偵測為 video/mp4
}


def _meeting_oid(meeting_id: str) -> ObjectId:
    try:
        return ObjectId(meeting_id)
    except (InvalidId, TypeError):
        raise HTTPException(400, "meeting_id 格式錯誤")


class SummarizeRequest(BaseModel):
    conversation_id: str
    keep_recent: int = 10  # 保留最近 N 輪不摘要
    force: bool = False    # 強制摘要(即使未達門檻)


@router.post("/memory/summarize-conversation")
def summarize_conversation(req: SummarizeRequest):
    """對話超過 N 輪時用 Haiku 摘要前面的 · 存回 conversation metadata

    節省邏輯:
      - 20 輪對話 × 平均 1500 tokens = 30k tokens context
      - 摘要成 2k tokens + 保留最近 10 輪(10k) = 12k tokens
      - 每次呼叫省約 60% context
    """
    from main import db
    msgs_col = db.messages
    try:
        messages = list(msgs_col.find(
            {"conversationId": req.conversation_id}
        ).sort("createdAt", 1))
    except Exception as e:
        raise HTTPException(500, f"MongoDB 查詢失敗: {e}")

    if len(messages) <= req.keep_recent and not req.force:
        return {"summarized": False, "reason": f"對話僅 {len(messages)} 輪,未達門檻"}

    to_summarize = messages[:-req.keep_recent] if not req.force else messages
    if not to_summarize:
        return {"summarized": False, "reason": "無可摘要訊息"}

    # R13#3 · ImportError 應回 503(服務未配置)· 而非 500(內部錯誤)
    try:
        import anthropic
    except ImportError:
        raise HTTPException(503, "Anthropic SDK 未安裝 · 請 pip install anthropic")

    # 用 Anthropic Haiku 摘要
    try:
        client = anthropic.Anthropic()

        dialogue = "\n\n".join([
            f"{m.get('sender', m.get('role', 'user'))}: {(m.get('text') or '')[:500]}"
            for m in to_summarize
        ])

        summary_resp = client.messages.create(
            model="claude-haiku-4-5",
            max_tokens=1000,
            messages=[{
                "role": "user",
                "content": f"""把以下承富 AI 對話摘要成 200-400 字 · 保留關鍵事實 / 決議 / 待辦 · 繁中 · 台灣用語:\n\n{dialogue}"""
            }]
        )
        summary_text = summary_resp.content[0].text

        db.conversations.update_one(
            {"conversationId": req.conversation_id},
            {"$set": {
                "chengfu_summary": summary_text,
                "chengfu_summary_up_to": str(to_summarize[-1].get("_id", "")),
                "chengfu_summarized_at": datetime.utcnow(),
                "chengfu_summarized_messages": len(to_summarize),
            }}
        )

        return {
            "summarized": True,
            "messages_summarized": len(to_summarize),
            "summary_length": len(summary_text),
            "kept_recent": req.keep_recent,
            "estimated_tokens_saved": sum(len(m.get("text", "")) for m in to_summarize) // 4,
        }
    except Exception as e:
        raise HTTPException(500, f"摘要失敗: {e}")


# ============================================================
# Feature #1 · 會議速記自動化
# ============================================================
def _openai_key_for_stt() -> str:
    """Whisper STT key · 跟 design router 同 pattern(先 Mongo · fallback env)"""
    try:
        from main import db
        doc = db.system_settings.find_one({"name": "OPENAI_API_KEY"})
        if doc and doc.get("value"):
            return doc["value"].strip()
    except Exception:
        pass
    return os.getenv("OPENAI_API_KEY", "").strip()


def _anthropic_key() -> str:
    return os.getenv("ANTHROPIC_API_KEY", "").strip()


def _process_meeting(meeting_id_str: str):
    """BackgroundTasks 跑的 STT + Haiku 結構化 pipeline

    不 raise(background 錯沒人收)· 失敗寫 meeting.status=failed + error 欄位
    """
    from main import db
    try:
        meeting = db.meetings.find_one({"_id": ObjectId(meeting_id_str)})
        if not meeting:
            logger.error("[meeting] process _id=%s 不存在", meeting_id_str)
            return
        audio_path = meeting.get("_tmp_audio_path")
        if not audio_path or not os.path.exists(audio_path):
            db.meetings.update_one(
                {"_id": ObjectId(meeting_id_str)},
                {"$set": {"status": "failed", "error": "tmp audio 不見",
                          "updated_at": datetime.utcnow()}},
            )
            return

        # Step 1 · Whisper STT
        try:
            import openai
        except ImportError:
            db.meetings.update_one(
                {"_id": ObjectId(meeting_id_str)},
                {"$set": {"status": "failed", "error": "OpenAI SDK 未裝",
                          "updated_at": datetime.utcnow()}},
            )
            return

        client = openai.OpenAI(api_key=_openai_key_for_stt())
        try:
            with open(audio_path, "rb") as af:
                tr = client.audio.transcriptions.create(
                    model="whisper-1",
                    file=af,
                    language="zh",  # 承富繁中
                )
            transcript = tr.text
        except Exception as e:
            logger.error("[meeting] Whisper 失敗 id=%s · %s", meeting_id_str, e)
            db.meetings.update_one(
                {"_id": ObjectId(meeting_id_str)},
                {"$set": {"status": "failed", "error": f"STT 失敗: {str(e)[:200]}",
                          "updated_at": datetime.utcnow()}},
            )
            return

        db.meetings.update_one(
            {"_id": ObjectId(meeting_id_str)},
            {"$set": {
                "transcript": transcript,
                "status": "structuring",
                "updated_at": datetime.utcnow(),
            }},
        )

        # Step 2 · Haiku 結構化
        try:
            import anthropic
            a_client = anthropic.Anthropic(api_key=_anthropic_key())
            prompt = f"""把以下繁中會議逐字稿整理成結構化 JSON · 只回 JSON · 不要任何說明文字:

{{
  "title": "會議標題(從內容判)",
  "attendees": ["與會者 1", "與會者 2"],
  "decisions": ["決議 1", "決議 2"],
  "action_items": [
    {{"who": "負責人", "what": "待辦內容", "due": "期限(若提到 · 無則空)"}}
  ],
  "key_numbers": [
    {{"label": "預算", "value": "NT$ 50 萬"}}
  ],
  "next_meeting": "下次會議(若提到 · 無則空)"
}}

逐字稿:
{transcript[:15000]}"""  # 限 15k 字避免 context 爆

            resp = a_client.messages.create(
                model="claude-haiku-4-5",
                max_tokens=2000,
                messages=[{"role": "user", "content": prompt}],
            )
            raw = resp.content[0].text

            # Parse JSON · 容忍 ```json fence
            import re, json
            m = re.search(r"\{[\s\S]*\}", raw)
            if not m:
                raise ValueError("Haiku 沒回 JSON")
            structured = json.loads(m.group(0))
        except Exception as e:
            logger.error("[meeting] Haiku 結構化失敗 id=%s · %s", meeting_id_str, e)
            db.meetings.update_one(
                {"_id": ObjectId(meeting_id_str)},
                {"$set": {"status": "failed", "error": f"結構化失敗: {str(e)[:200]}",
                          "updated_at": datetime.utcnow()}},
            )
            return

        # Step 3 · 刪除 tmp audio(PDPA · 不留 raw 錄音)
        try:
            os.remove(audio_path)
        except Exception:
            pass

        db.meetings.update_one(
            {"_id": ObjectId(meeting_id_str)},
            {"$set": {
                "structured": structured,
                "status": "done",
                "updated_at": datetime.utcnow(),
            },
             "$unset": {"_tmp_audio_path": ""}},
        )
        logger.info("[meeting] done id=%s · %d 決議 / %d 待辦",
                    meeting_id_str,
                    len(structured.get("decisions", [])),
                    len(structured.get("action_items", [])))
    except Exception as e:
        logger.error("[meeting] 非預期失敗 id=%s · %s", meeting_id_str, e)


@router.post("/memory/transcribe")
async def transcribe_audio(
    background: BackgroundTasks,
    audio: UploadFile = File(...),
    project_id: Optional[str] = Form(default=None),
    email: str = require_user_dep(),
):
    """上傳音檔 · 回 meeting_id + status=transcribing · 前端 polling /memory/meetings/{id}

    Feature #1 · 會議速記自動化(R14 FEATURE-PROPOSALS v1.2)
    - 限 25MB(Whisper API 上限)
    - 限 audio/* mime
    - 非同步 · BackgroundTasks 跑 STT + Haiku
    - PDPA:處理完刪 tmp audio raw · 只留 transcript + structured
    """
    from main import db

    # 驗 mime + size
    mime = (audio.content_type or "").lower()
    if mime not in ALLOWED_AUDIO_MIMES:
        raise HTTPException(400, f"音檔格式不支援 · {mime} · 請用 mp3/m4a/wav/flac")

    content = await audio.read()
    size = len(content)
    if size > WHISPER_MAX_BYTES:
        raise HTTPException(413, f"音檔 {size // 1024 // 1024}MB 超過 25MB 上限 · 請先剪短")
    if size < 1024:
        raise HTTPException(400, "音檔太小 · 可能空檔")

    sha256 = hashlib.sha256(content).hexdigest()[:16]
    # 存 tmp · BackgroundTasks 讀後刪
    import tempfile
    fd, tmp_path = tempfile.mkstemp(prefix=f"chengfu-meeting-{sha256}-", suffix=".bin")
    try:
        os.write(fd, content)
    finally:
        os.close(fd)

    doc = {
        "owner": email,
        "project_id": project_id,
        "audio_sha256": sha256,
        "audio_size": size,
        "audio_mime": mime,
        "transcript": "",
        "structured": {},
        "status": "transcribing",
        "_tmp_audio_path": tmp_path,
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow(),
    }
    r = db.meetings.insert_one(doc)
    mid = str(r.inserted_id)

    # 丟 background 處理 · 不 block response
    background.add_task(_process_meeting, mid)

    return {
        "meeting_id": mid,
        "status": "transcribing",
        "size_mb": round(size / 1024 / 1024, 2),
    }


@router.get("/memory/meetings/{meeting_id}")
def get_meeting(meeting_id: str, email: str = require_user_dep()):
    """Polling 狀態 + 結構化結果"""
    from main import db
    doc = db.meetings.find_one({"_id": _meeting_oid(meeting_id)})
    if not doc:
        raise HTTPException(404, "會議紀錄不存在")
    if doc.get("owner") != email:
        # admin 另走 /admin/meetings(v1.3)· 非 owner 拒絕
        raise HTTPException(403, "只能看自己的會議")
    return {
        "meeting_id": meeting_id,
        "status": doc.get("status"),
        "structured": doc.get("structured", {}),
        "transcript_preview": (doc.get("transcript") or "")[:500],
        "transcript_length": len(doc.get("transcript") or ""),
        "error": doc.get("error"),
        "project_id": doc.get("project_id"),
        "created_at": doc["created_at"].isoformat() if doc.get("created_at") else None,
    }


@router.get("/memory/meetings")
def list_meetings(
    limit: int = 20,
    project_id: Optional[str] = None,
    email: str = require_user_dep(),
):
    """我的會議列表 · 不含 transcript(省 bandwidth)"""
    from main import db
    q = {"owner": email}
    if project_id:
        q["project_id"] = project_id
    cursor = db.meetings.find(
        q,
        {"transcript": 0, "_tmp_audio_path": 0},  # 不 project
    ).sort("created_at", -1).limit(min(limit, 100))
    items = []
    for doc in cursor:
        items.append({
            "meeting_id": str(doc["_id"]),
            "status": doc.get("status"),
            "title": (doc.get("structured") or {}).get("title", "(未命名)"),
            "project_id": doc.get("project_id"),
            "created_at": doc["created_at"].isoformat() if doc.get("created_at") else None,
            "action_items_count": len((doc.get("structured") or {}).get("action_items", [])),
        })
    return {"items": items, "count": len(items)}


@router.post("/memory/meetings/{meeting_id}/push-to-handoff")
def push_to_handoff(meeting_id: str, email: str = require_user_dep()):
    """把 action_items 推到 project.handoff.next_actions · 一鍵交棒"""
    from main import db
    doc = db.meetings.find_one({"_id": _meeting_oid(meeting_id)})
    if not doc:
        raise HTTPException(404, "會議紀錄不存在")
    if doc.get("owner") != email:
        raise HTTPException(403, "只能推自己的會議")
    if doc.get("status") != "done":
        raise HTTPException(400, "會議還沒處理完 · 等 status=done")
    project_id = doc.get("project_id")
    if not project_id:
        raise HTTPException(400, "此會議沒綁 project_id · 上傳時要填")

    action_items = (doc.get("structured") or {}).get("action_items", [])
    next_actions = [
        f"{a.get('what', '')} · {a.get('who', '')}" + (f" · 期限 {a['due']}" if a.get("due") else "")
        for a in action_items
    ]

    try:
        p_oid = ObjectId(project_id)
    except Exception:
        raise HTTPException(400, "project_id 格式錯")

    r = db.projects.update_one(
        {"_id": p_oid},
        {"$set": {
            f"handoff.next_actions": next_actions,
            f"handoff.source_meeting_id": meeting_id,
            f"handoff.updated_by": email,
            f"handoff.updated_at": datetime.utcnow(),
        }},
    )
    if r.matched_count == 0:
        raise HTTPException(404, "project 不存在")
    return {"pushed": True, "next_actions_count": len(next_actions)}
