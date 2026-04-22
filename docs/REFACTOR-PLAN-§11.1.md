# main.py 拆 routers/ · v1.2 重構 plan

> **ROADMAP §11.1**(senior-architect 建議 1)
> **預估工時:** 8-12h
> **本輪未動 · 給 v1.2 接手者用**(風險高 / 工時長 / 不該在 audit batch 同時做)

---

## 1. 為什麼必拆

| 現狀 | 痛點 |
|---|---|
| `main.py` 2400+ 行 / 70+ endpoint | 新 endpoint 撞 merge conflict |
| 7 個 domain 混在一起 | Onboarding 要讀整檔 |
| services/ 已抽 3 模組 · 證明拆是對的 | 但 endpoint 仍黏 main.py |
| §10.2 全 endpoint cookie/JWT auth 重構 | 不拆會撞 merge hell |

---

## 2. 拆法 · FastAPI APIRouter

**目標結構:**

```
backend/accounting/
├── main.py                      ← <200 行 · 只負責 app init + middleware + include_router
├── orchestrator.py              ← 已存在 · 主管家
├── services/                    ← 已存在 · 純 function
│   ├── admin_metrics.py
│   ├── knowledge_extract.py
│   └── knowledge_indexer.py
└── routers/                     ← 新 · 按 domain 拆
    ├── __init__.py
    ├── accounts.py              ← 帳號 / 交易 / 發票 / 報價(會計核心 ~400 行)
    ├── projects.py              ← Project CRUD + Handoff(~200 行)
    ├── crm.py                   ← lead pipeline(~300 行)
    ├── tenders.py               ← 標案 alerts + g0v(~150 行)
    ├── feedback.py              ← 👍 👎 + stats(~80 行)
    ├── admin.py                 ← /admin/* 全收(~400 行)
    ├── knowledge.py             ← sources CRUD + read/list/search(~400 行)
    ├── design.py                ← Fal Recraft + history(~250 行)
    ├── safety.py                ← L3 classifier(~50 行)
    └── users.py                 ← preferences(~100 行)
```

**main.py 留下的:**
```python
from fastapi import FastAPI
from contextlib import asynccontextmanager
from routers import accounts, projects, crm, tenders, feedback, admin, knowledge, design, safety, users

@asynccontextmanager
async def lifespan(app: FastAPI):
    # indexes / OCR probe / orchestrator load
    ...
    yield

app = FastAPI(..., lifespan=lifespan)

# CORS / RequestID / SlowAPI middleware
app.add_middleware(...)

# Routers
app.include_router(accounts.router, tags=["accounts"])
app.include_router(projects.router, tags=["projects"])
# ...

@app.get("/healthz")
def healthz(): ...
```

---

## 3. 拆解步驟(逐步 · 每步驗 92 pytest)

### Step 1 · 建立 routers/ 結構(10 min)
```bash
mkdir backend/accounting/routers
touch backend/accounting/routers/__init__.py
```

### Step 2 · 抽 1 個小 router 試 pattern(safety.py · ~50 行 · 30 min)
```python
# routers/safety.py
from fastapi import APIRouter
from pydantic import BaseModel
import re

router = APIRouter(prefix="/safety", tags=["safety"])

LEVEL_3_PATTERNS = [...]  # 從 main.py 搬

class ContentCheck(BaseModel):
    text: str

@router.post("/classify")
def classify_level(payload: ContentCheck, request):
    ...
```

main.py:
```python
from routers import safety
app.include_router(safety.router)
# 刪掉 main.py 內 LEVEL_3_PATTERNS / classify_level
```

驗:`pytest test_main.py::test_l3_classifier_*` 仍 pass

### Step 3 · 依序抽其他 router(每個 30-60 min)
順序(由小到大):
1. `safety.py`(50 行 · 已試)
2. `feedback.py`(80 行)
3. `users.py`(100 行)
4. `tenders.py`(150 行)
5. `projects.py`(200 行)
6. `design.py`(250 行)
7. `crm.py`(300 行)
8. `admin.py`(400 行)
9. `accounts.py`(400 行 · 注意 _account_type_map 共用)
10. `knowledge.py`(400 行)

每抽一個:
- pytest pass(92/92 維持)
- smoke pass(11/11 維持)
- commit + push 一個 commit · 失敗可單獨 revert

### Step 4 · 共用依賴抽到 deps.py(30 min)
```python
# routers/_deps.py
from fastapi import Depends, Request, Header, HTTPException
from typing import Optional

# 從 main.py 搬:
def current_user_email(...) -> Optional[str]: ...
def require_admin(...) -> str: ...
def _verify_librechat_cookie(...) -> Optional[str]: ...
```

各 router import:
```python
from ._deps import current_user_email, require_admin
```

### Step 5 · 共用 Mongo collections 抽到 db.py(20 min)
```python
# routers/_db.py
from pymongo import MongoClient
import os

_client = MongoClient(os.getenv("MONGO_URI", "mongodb://localhost:27017/chengfu"))
db = _client.get_default_database()

accounts_col = db.accounting_accounts
transactions_col = db.accounting_transactions
# ...
```

### Step 6 · 收尾(1h)
- main.py 應該剩 < 200 行(import + lifespan + middleware + include_router + healthz)
- pytest 92/92 + smoke 11/11
- 跑 docker rebuild 驗 production 行為一致

---

## 4. 風險 · 怎麼避

| 風險 | 緩解 |
|---|---|
| 模組循環 import | _deps.py + _db.py 為 leaf · 不 import router |
| Pydantic models 在 main.py 散落 | 同 router 內定義 · 不共用就不 export |
| pytest fixture 失敗 | importlib.reload 路徑可能要更新 · 一個一個改 |
| 效能 regression | uvicorn 啟動順序變(import 先) · benchmark startup |
| middleware 順序 | main.py 一處集中宣告 · 不要散到 router |

---

## 5. 不要做的事

- ❌ 一次重構全部 · 不可能 review · 不可能 revert
- ❌ 引入新 framework(starlette / litestar 都不需要)
- ❌ 改 endpoint URL · 維持向後相容 · 前端不動
- ❌ 改業務邏輯 · 純結構搬移
- ❌ 動 services/(已拆好)

---

## 6. 完成後 ROI

- main.py 從 2400 行 → 200 行
- 7 個 router 各 50-400 行 · 新人 onboarding 1 個 router 即懂 1 domain
- §10.2 全 endpoint auth 重構 · 改 _deps.py 一處 · 全 router 自動套用
- §11.15 全 endpoint async 重構 · 同樣集中改
- merge conflict 機率降 80%(預估 10 人 PR 並行的場景)

---

## 7. v1.2 排程建議

- 第 1 天 · Step 1-3(抽 5 個小 router · 累積信心)
- 第 2 天 · Step 3 剩 5 個 + Step 4-5
- 第 3 天 · Step 6 + 跑 codex round 5 audit + 修

**3 天工時 = 1 個 sprint** · 老闆批准排 v1.2 第 1 個 sprint
