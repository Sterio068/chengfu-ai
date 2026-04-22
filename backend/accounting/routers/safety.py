"""
Safety router · L3 機敏內容分級檢查

ROADMAP §11.1 · 從 main.py 抽出的第一個 router(最孤立 · 證明 pattern)
- 老闆 Q3 答「先不考慮 L3 硬擋」· 但這個 endpoint 仍可用為 prompt 預掃
- 前端 chat.js 在送出前可選擇呼叫 /safety/classify · 跳警告 modal(Playwright §11.13)
"""
from fastapi import APIRouter, Request
from pydantic import BaseModel
import re


router = APIRouter(prefix="/safety", tags=["safety"])


LEVEL_3_PATTERNS = [
    # 選情 / 政治
    r"選情", r"民調", r"政黨內部", r"候選人(策略|規劃)",
    # 未公告標案
    r"未公告.{0,10}標", r"內定.{0,5}廠商", r"評審.{0,5}名單",
    # 個資(強 pattern)
    r"\b[A-Z]\d{9}\b",  # 身份證
    r"\b\d{10}\b",      # 手機號
    r"\b\d{3}-\d{3}-\d{3}\b",
    # 客戶機敏
    r"客戶.{0,5}(帳戶|密碼|財務狀況)",
    # 競爭對手情報
    r"(對手|競品).{0,5}(內部|機密|計畫)",
]


class ContentCheck(BaseModel):
    text: str


@router.post("/classify")
def classify_level(payload: ContentCheck, request: Request):
    """Level 03 keyword classifier · 在 Agent 處理前預掃。

    rate limit 由 main.py app 級別 limiter 套用(SlowAPIMiddleware 自動)
    """
    hits = []
    for pattern in LEVEL_3_PATTERNS:
        matches = re.findall(pattern, payload.text)
        if matches:
            hits.extend(matches if isinstance(matches[0], str) else [str(m) for m in matches])
    level = "03" if hits else ("02" if len(payload.text) > 500 else "01")
    return {
        "level": level,
        "triggers": hits[:10],  # 最多回 10 個命中
        "recommendation": {
            "01": "可直接處理",
            "02": "建議去識別化(客戶名/金額)後處理",
            "03": "❌ 禁止送 AI,請改人工處理或待階段二本地模型",
        }[level],
    }
