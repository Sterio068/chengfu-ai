"""
v1.6 · AI Suggestions endpoint(MVP stub)
=====================================
給前端 dashboard-fpp.js fetch · 提供「主管家建議」清單

MVP 實作:
  - 從 mongo conversations / projects 簡單 heuristic 算
  - 之後 v1.7 接真 LLM 觸發管線(deadline 偵測 / 待回信 / 停滯)

回傳格式(對齊前端 mock):
  {
    "suggestions": [
      {
        "id": int,
        "type": "deadline" | "reply" | "stale",
        "text": str,           // 顯示給用戶的描述
        "cta": str,            // 動作按鈕文字 · 例「排進日曆」「看草稿」
        "src": str,            // 來源對話 · 例「中秋禮盒 · 14:32」
        "confidence": float,   // 0.0 ~ 1.0
      }, ...
    ],
    "scanned_at": ISO string,
    "next_scan_at": ISO string,
  }
"""
from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import APIRouter

from .._deps import require_admin_dep


router = APIRouter(tags=["admin"])

# MVP · 用 mock 資料 · 後端 v1.7 接真 LLM
_MOCK_SUGGESTIONS = [
    {
        "id": 1,
        "type": "deadline",
        "text": "RFP 提到 3 個截止日 (5/15、5/22、6/01)",
        "cta": "排進日曆",
        "src": "中秋禮盒 · 14:32",
        "confidence": 0.92,
    },
    {
        "id": 2,
        "type": "reply",
        "text": "客戶 A 上週四問的 3 個問題還沒回",
        "cta": "看草稿",
        "src": "客戶 A · 4 天前",
        "confidence": 0.88,
    },
    {
        "id": 3,
        "type": "stale",
        "text": "春節提案 11 天沒動 · 要結案嗎?",
        "cta": "檢視",
        "src": "春節提案",
        "confidence": 0.71,
    },
]


@router.get("/admin/ai-suggestions")
def list_ai_suggestions(_admin: str = require_admin_dep()):
    """v1.6 · 列當前 AI 建議

    MVP 階段回 mock · 之後 v1.7 接真觸發管線:
      1. deadline · 從對話 NER 抽取日期 · 比對今日距離
      2. reply · 對話最後一條是「對方訊息」且超過 N 小時未回
      3. stale · 對話超過 7 天無動作 · 但有未結案標記

    觸發頻率:每 30 分鐘掃描一次(後端 cron · 此 endpoint 只讀 cache)
    抑制機制:user 點「不再提示這類」localStorage 記 · 前端過濾
    """
    now = datetime.now(timezone.utc)
    next_scan = now + timedelta(minutes=30)
    return {
        "suggestions": _MOCK_SUGGESTIONS,
        "scanned_at": now.isoformat(),
        "next_scan_at": next_scan.isoformat(),
        "stub": True,  # 提示前端「這還是 mock」· v1.7 移除
    }


# ============================================================
# v1.7 後續 endpoint 預留
# ============================================================
# POST /admin/ai-suggestions/{id}/execute  · 執行該建議的 cta(例排進 calendar)
# POST /admin/ai-suggestions/{id}/dismiss · 標記為「之後再說」(暫時隱藏 24h)
# POST /admin/ai-suggestions/suppress     · 「不再提示這類」(寫 user prefs)
