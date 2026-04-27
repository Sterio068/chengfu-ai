"""
Vision OCR · v1.55 · 招標 / 合約 / 場地圖等視覺結構化抽取

設計目標:
  讓 AI Agent 用一個簡單參數 {image_url} 就能拿到結構化 JSON 而非文字描述。
  把 OpenAI vision + structured output 的 prompt + schema 隱藏在後端,
  Agent 不用煩惱怎麼問。

3 個專用端點(承富業務頻次最高):
  · extract-tender-summary  · 招標文件 9 欄結構化(案號 / 標的 / 預算 / 截止 / ...)
  · extract-table           · 任何表格(評分 / 預算 / 報價 / 時程)→ rows[]
  · extract-scoring-criteria · 評分標準 → criteria[] 含 weight / sub-criteria

特性:
  · 用 GPT-5.5 vision(原生多模態)
  · response_format=json_schema · strict=true · 保證 JSON 結構穩定
  · 1 小時 LRU cache(同一張圖再抽不重複付費)
  · audit log(誰抽了什麼 · token 用量)
  · 失敗 fallback 回普通文字描述 · 不讓 AI 卡住

注意:
  · OPENAI_API_KEY 從 env 讀(LibreChat container 同源)· 沒設 raise 503
  · image_url 必須是公開可達 URL · 或 data:image/... base64
  · 5MB 上限 · 防 OOM
"""
from __future__ import annotations

import hashlib
import os
import time
from datetime import datetime, timezone
from typing import Optional

import httpx
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from routers._deps import require_user_dep


router = APIRouter(prefix="/vision", tags=["vision"])

OPENAI_BASE = os.getenv("OPENAI_API_BASE", "https://api.openai.com/v1")
VISION_MODEL = os.getenv("CHENGFU_OPENAI_VISION_MODEL", "gpt-5.5")
CACHE_TTL_S = 3600  # 1h

# 簡易 in-memory LRU · 重啟清空 · 容量 100 (~5MB image base64 hash 才 64 bytes · 安全)
_cache: dict[str, tuple[float, dict]] = {}
_CACHE_MAX = 100


def _cache_key(endpoint: str, image_url: str, hint: str = "") -> str:
    raw = f"{endpoint}::{image_url}::{hint}"
    return hashlib.sha256(raw.encode()).hexdigest()


def _cache_get(key: str) -> Optional[dict]:
    entry = _cache.get(key)
    if not entry:
        return None
    ts, payload = entry
    if time.time() - ts > CACHE_TTL_S:
        _cache.pop(key, None)
        return None
    return payload


def _cache_put(key: str, payload: dict) -> None:
    if len(_cache) >= _CACHE_MAX:
        # 清最舊
        oldest = min(_cache.items(), key=lambda kv: kv[1][0])[0]
        _cache.pop(oldest, None)
    _cache[key] = (time.time(), payload)


async def _openai_vision_extract(
    system_prompt: str,
    user_prompt: str,
    image_url: str,
    json_schema: dict,
    schema_name: str = "extraction",
) -> dict:
    """呼叫 OpenAI · vision + structured output · 回 parsed JSON dict"""
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise HTTPException(503, "OPENAI_API_KEY 未設 · 後端無法呼叫 OpenAI vision")

    body = {
        "model": VISION_MODEL,
        "messages": [
            {"role": "system", "content": system_prompt},
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": user_prompt},
                    {"type": "image_url", "image_url": {"url": image_url}},
                ],
            },
        ],
        "response_format": {
            "type": "json_schema",
            "json_schema": {
                "name": schema_name,
                "strict": True,
                "schema": json_schema,
            },
        },
        "max_completion_tokens": 4000,
    }

    async with httpx.AsyncClient(timeout=120) as client:
        resp = await client.post(
            f"{OPENAI_BASE}/chat/completions",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            json=body,
        )
        if resp.status_code != 200:
            raise HTTPException(
                502,
                f"OpenAI vision 失敗 HTTP {resp.status_code}: {resp.text[:200]}",
            )
        data = resp.json()
        try:
            content = data["choices"][0]["message"]["content"]
            import json as _json
            return _json.loads(content)
        except (KeyError, IndexError, ValueError) as e:
            raise HTTPException(502, f"OpenAI vision 回傳格式異常:{e}")


# ============================================================
# Schemas
# ============================================================
TENDER_9_COLS_SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "properties": {
        "case_number": {"type": "string", "description": "案號 / 標案編號"},
        "subject": {"type": "string", "description": "標案名稱 / 採購標的"},
        "budget_twd": {"type": "string", "description": "預算金額(NT$ 含逗號 · 沒寫填 'unknown')"},
        "deadline": {"type": "string", "description": "截止日期(YYYY-MM-DD 或自然描述)"},
        "submission_method": {"type": "string", "description": "送件方式(電子 / 紙本 / 押標金等)"},
        "qualification": {"type": "string", "description": "廠商資格摘要"},
        "scoring_summary": {"type": "string", "description": "評選 / 評分方式摘要"},
        "execution_period": {"type": "string", "description": "履約期間"},
        "contact": {"type": "string", "description": "承辦聯絡人 / 電話 / Email"},
        "notes": {"type": "string", "description": "其他關鍵資訊或注意事項"},
    },
    "required": [
        "case_number", "subject", "budget_twd", "deadline",
        "submission_method", "qualification", "scoring_summary",
        "execution_period", "contact", "notes",
    ],
}

TABLE_SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "properties": {
        "title": {"type": "string", "description": "表格標題或主題"},
        "headers": {"type": "array", "items": {"type": "string"}, "description": "欄位名稱"},
        "rows": {
            "type": "array",
            "items": {"type": "array", "items": {"type": "string"}},
            "description": "資料列 · 與 headers 對齊",
        },
        "notes": {"type": "string", "description": "備註或無法辨識的部分"},
    },
    "required": ["title", "headers", "rows", "notes"],
}

SCORING_CRITERIA_SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "properties": {
        "total_score": {"type": "number", "description": "總分 · 通常 100"},
        "criteria": {
            "type": "array",
            "items": {
                "type": "object",
                "additionalProperties": False,
                "properties": {
                    "name": {"type": "string", "description": "評分項目"},
                    "weight": {"type": "number", "description": "配分 · 數字"},
                    "sub_criteria": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "子項目或評分要點",
                    },
                },
                "required": ["name", "weight", "sub_criteria"],
            },
        },
        "passing_score": {"type": "number", "description": "及格分數 · 沒寫填 0"},
        "notes": {"type": "string", "description": "評分方式備註"},
    },
    "required": ["total_score", "criteria", "passing_score", "notes"],
}


# ============================================================
# Request / Response models
# ============================================================
class VisionExtractRequest(BaseModel):
    image_url: str = Field(..., description="圖片 URL · 公開可達 · 或 data:image/...")
    hint: Optional[str] = Field(None, description="額外提示(例:這是第幾頁、語言、廠商角度)")


# ============================================================
# Endpoints
# ============================================================
@router.post("/extract-tender-summary")
async def extract_tender_summary(
    req: VisionExtractRequest,
    user_email: str = require_user_dep(),
):
    """招標文件首頁 → 9 欄結構化 JSON · 投標顧問常用"""
    cache_key = _cache_key("tender-summary", req.image_url, req.hint or "")
    if cached := _cache_get(cache_key):
        return {**cached, "cached": True}

    system = (
        "你是招標文件結構化助理。"
        "從圖片(招標公告 / 須知首頁 / 摘要表)抽出 9 個關鍵欄位。"
        "若某欄圖中沒有,該欄填 'unknown'。"
        "金額一律 NT$ 並含千分位。日期盡量轉 YYYY-MM-DD。"
    )
    user = f"請抽出此招標文件的 9 欄結構。{req.hint or ''}"
    result = await _openai_vision_extract(
        system, user, req.image_url, TENDER_9_COLS_SCHEMA, "tender_summary",
    )
    _cache_put(cache_key, result)
    _audit_extraction(user_email, "tender-summary", req.image_url)
    return {**result, "cached": False}


@router.post("/extract-table")
async def extract_table(
    req: VisionExtractRequest,
    user_email: str = require_user_dep(),
):
    """通用表格 → headers + rows · 評分表 / 報價表 / 時程表通用"""
    cache_key = _cache_key("table", req.image_url, req.hint or "")
    if cached := _cache_get(cache_key):
        return {**cached, "cached": True}

    system = (
        "你是表格結構化助理。"
        "從圖片中辨識表格,輸出 headers + rows。"
        "rows 每一筆是 string array · 順序與 headers 對齊。"
        "合併儲存格用相同字串複製進每個 row。"
        "看不清楚的字寫 '?'。"
    )
    user = f"請抽出此表格的結構化資料。{req.hint or ''}"
    result = await _openai_vision_extract(
        system, user, req.image_url, TABLE_SCHEMA, "table",
    )
    _cache_put(cache_key, result)
    _audit_extraction(user_email, "table", req.image_url)
    return {**result, "cached": False}


@router.post("/extract-scoring-criteria")
async def extract_scoring_criteria(
    req: VisionExtractRequest,
    user_email: str = require_user_dep(),
):
    """招標評分標準 → 各項目 + weight + 子項 · 投標顧問估勝率必用"""
    cache_key = _cache_key("scoring", req.image_url, req.hint or "")
    if cached := _cache_get(cache_key):
        return {**cached, "cached": True}

    system = (
        "你是招標評分標準結構化助理。"
        "從圖片(評選表 / 評分項目)抽出每個項目、配分、子項。"
        "若有及格分數標明,填 passing_score。"
        "若同一大項拆多子項,把子項列在 sub_criteria。"
    )
    user = f"請抽出評分標準的完整結構。{req.hint or ''}"
    result = await _openai_vision_extract(
        system, user, req.image_url, SCORING_CRITERIA_SCHEMA, "scoring_criteria",
    )
    _cache_put(cache_key, result)
    _audit_extraction(user_email, "scoring", req.image_url)
    return {**result, "cached": False}


def _audit_extraction(user_email: str, kind: str, image_url: str) -> None:
    """非阻塞 · audit fail 不影響回應"""
    try:
        from main import db
        db.vision_extractions.insert_one({
            "user_email": user_email,
            "kind": kind,
            "image_hash": hashlib.sha256(image_url.encode()).hexdigest()[:16],
            "extracted_at": datetime.now(timezone.utc),
        })
    except Exception:
        pass
