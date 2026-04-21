# 承富 AI 系統 · 外部審查請求 (v5.2)

---

## ⚠️ **在你下筆之前 · 強制讀這段**

前 6 輪 reviewer 平均重複指出 70% **我們已修過的項目** · 讓 reviewer 報告變成雜訊。
**本輪開始 · 若你在報告出現下列「已修檔案+行號」的紅線指認 · 該項直接視為 0 分。**

### 🚫 已修 14 項 · 嚴禁再指為紅線

| # | reviewer 常指的紅線 | 修在哪 | 驗證 |
|---|---|---|---|
| 1 | CRM 整區重繪長列表掉幀 | `frontend/launcher/modules/crm.js:86-108` 分批 render 前 20 + requestIdleCallback | commit `9903d55` |
| 2 | tenders 整區重繪 + 重綁 listener | `frontend/launcher/modules/tenders.js:47-85` 分批 + root event delegation | commit `9903d55` |
| 3 | chat.js renderMarkdown regex parser | `frontend/launcher/modules/chat.js:252-284` 改用 `vendor-marked.js`(28KB) | commit `9903d55` |
| 4 | auth 401 沒自動 retry | `frontend/launcher/modules/auth.js:20-44` SessionExpiredError + Web Locks | commit `bedf413` |
| 5 | Day 0 登入最易卡住 | `docs/PRE-DELIVERY-CHECKLIST.md:112-125` Part 0 登入服務台 | commit `9903d55` |
| 6 | Baseline 老闆答不出 | `docs/BASELINE.md:9-20` + `:192-236` B 路 Champion 1 週日誌 + 抽 5 案 | commit `9903d55` |
| 7 | per-user hard stop 只儀表 | `backend/accounting/main.py:1155-1197` `/quota/check` · `chat.js:160-175` 送前擋送 | commit `9903d55` |
| 8 | transactions schema 默默回 0 | `backend/accounting/main.py:1095-1127` fingerprint + `/admin/budget-status` 黃牌降級 | commit `9903d55` |
| 9 | Route A hash router 未防護 | `frontend/custom/librechat-relabel.js:14-70` hash listener + `_matchChatPath` | commit `9903d55` |
| 10 | on_event / .dict() deprecation | `backend/accounting/main.py:49-82` lifespan + 全檔 model_dump() | commit `08cf827` |
| 11 | overpromise 文案(專案跟對話 / ⌘K 搜對話 / 超預算自動 email) | `frontend/launcher/index.html:214/459/836` · `docs/QUICKSTART.md:97` · `docs/HANDBOOK/01-BOSS.md:25` | commit `5b5859c` |
| 12 | split-brain(routers/ + auth.py 多套) | `backend/accounting/_unused_scaffold/` 已歸檔(main.py 為單一真相) | commit `5b5859c` |
| 13 | 密碼紙條沒銷毀 SOP | `docs/PRE-DELIVERY-CHECKLIST.md:100-107` | commit `08cf827` |
| 14 | 備份沒異機、沒 restore 驗證 | `scripts/backup.sh:83-105` rclone + `PRE-DELIVERY-CHECKLIST.md:170-202` 月度 restore | commit `bedf413`/`08cf827` |

### ✅ 你該聚焦的 4 項真未解(v1.1 大項目)

| # | 項目 | 已做 | 還沒做 | 預估工時 |
|---|---|---|---|---|
| A | **Fal.ai Recraft v3 真生圖** | action schema `fal-ai-image-gen.json` 已寫 | 後端 action handler + Launcher 選尺寸 UI + 重生按鈕 + failure path | 6-8h |
| B | **PDF 文字抽取 MVP** | 輸入框「長文件 3 步貼法」hover 提示(過渡) | PyMuPDF first / OCR fallback · 頁碼保留 | 8-12h |
| C | **跨助手 handoff 4 格卡** | ROADMAP 已描述 | project 層新欄位 + UI + 「插入對話」按鈕 | 6-8h |
| D | **main.py 拆 admin_metrics.py** | 程式碼在 main.py:760-1300 範圍 | 抽到 `services/admin_metrics.py` · 其他 handler 保留 | 6-8h |

**你的真正價值:** 對 A/B/C/D 四項給**具體實作細節**(資料結構、錯誤處理、降級策略),而不是再指出前 14 項「已修但你不知道」的紅線。

---

## 🔗 0. 直接去讀

| 來源 | 位置 |
|---|---|
| **GitHub(public · 免認證)** | <https://github.com/Sterio068/chengfu-ai> |
| **Clone** | `git clone https://github.com/Sterio068/chengfu-ai.git && cd chengfu-ai` |
| **作者本機** | `/Users/sterio/Workspace/ChengFu` |
| **本機跑起來** | <http://localhost/>(主入口)· <http://localhost/api-accounting/docs>(API) |
| **commit 歷史** | `git log --oneline -20`(10 個 commit / 7 輪審查 / 40+ 紅線修正) |

### 必讀 6 份(15 分鐘消化)

```
1. CLAUDE.md                                   · 專案目標 + 12 項決議
2. docs/ROADMAP-v4.2.md                        · 對齊老闆 5 題的路線圖
3. docs/PRE-DELIVERY-CHECKLIST.md              · 揭露部署完成度 35%
4. backend/accounting/main.py                  · 後端 FastAPI 50+ endpoints(1800+ 行 · 待拆的就是這個)
5. frontend/launcher/app.js + modules/*.js     · 前端 21 檔(已修的 marked/Route A/quota 都在)
6. docs/CASES/01-海廢案端到端.md                · 系統實際怎麼用
```

---

## 1. 客戶與專案

### 客戶
- **承富創意整合行銷有限公司**(台灣 · 10 人公關行銷公司)
- 主要業務:政府標案、公關活動、設計案
- 2-3 位資深者對 AI 抗拒

### 老闆親答 5 題(優先級依據)
1. **每週 Top 3:** 設計 / 提案撰寫 / 廠商聯繫
2. **80% 原始檔:** LINE 群組 + NAS(**不是** Google Drive)
3. **L3 機敏:** **先不考慮**
4. **最在意:** 省時 + 接案量(不是風控)
5. **維運:** 外包 20h/週 Claude Code 遠端 · Champion 自主學習

→ **偏離這 5 題的建議會被否決**

### 預算 / 時程
- AI 月預算 NT$ 12,000(buffer 後 NT$ 8,000)· 4 週交付 · Mac mini 未上架

---

## 2. 技術棧(不可替換)

| 層 | 選擇 |
|---|---|
| 硬體 | Mac mini M4 24GB |
| AI Platform | LibreChat **v0.8.4 pinned** |
| AI Model | Claude Opus 4.7 / Sonnet 4.6 / Haiku 4.5 |
| 後端 | FastAPI 單檔(1800+ 行 · 拆 admin_metrics 是 v1.1 項) |
| 前端 | 原生 ES Modules + 單 CSS · **無 build step** |
| 容器 | Docker Compose × 6 |
| 對外 | Cloudflare Tunnel + Access(未架) |
| 機密 | macOS Keychain |

**不接受:** k8s / Redis / Kafka / GraphQL / 換框架 / SaaS / 改 10 助手 / 改 5 工作區 / 改主色

---

## 3. 當前狀態

### ✅ 程式碼:98%
- 6 容器 healthy · 10 助手 + `instance` 共享
- **18 pytest pass · 11 smoke pass · 0 deprecation**
- 前端:21 檔 ES modules + marked vendor · 長列表分批 · hash router 防護
- 後端:13 個 /admin/* 全 RBAC · `/quota/check` 送前擋送 · schema fingerprint + 黃牌降級

### 🔴 部署落地:35%(Sterio 交付週手動做)
- Mac mini 未上架 · Cloudflare Tunnel 未接
- `knowledge-base/samples/` 空(Round 6 警告:**不灌 = 上線第 2 週 generic 感放棄**)
- 10 帳號未建 · 密碼 reset SOP 未寫
- 2 場教育訓練未辦
- T0 baseline B 路未跑(模板已備)

### 📚 教材:88%
3 完整案例 + 4+1 角色手冊 + QUICKSTART + Pre-Delivery + Baseline + Upgrade。

---

## 4. 我要你審什麼(聚焦 A/B/C/D 4 項真未解)

### 4.A Fal.ai Recraft v3 實作(老闆 top 1 · 體感 gap 最大)
- 承富老闆的客戶多是政府機關 / 老品牌 · Fal.ai moderation 會不會卡到?降級策略?
- 失敗時(API 掛 / 超時)· 錯誤訊息怎麼給資深設計師看才不像「科技用語嚇人」?
- 1 次 1 張圖 vs 1 次 3 張給挑 · 哪個在 UI 上更自然?
- fal-ai schema 已寫好 · **後端 action handler 的最小 Python 實作**?要呼叫 fal-client 還是直接 httpx?

### 4.B PDF 文字抽取 MVP(老闆 top 2 · 70 頁痛)
- PyMuPDF vs pdfplumber vs pdfminer.six · 哪個對台灣政府 PDF 最穩?(中文 + 表格 + 浮水印)
- 頁碼保留的資料結構:`{page, text}` list 還是大字串帶 marker?
- 文字密度 threshold(走 OCR 的條件)怎麼設?
- 前端怎麼塞進現有 chat 輸入?新 endpoint `/pdf/extract` 還是 chat 送 multipart form?

### 4.C 跨助手 Handoff 4 格卡(真正跨日跨人的 artifact)
- 放 `project metadata` 的資料結構建議?(MongoDB doc schema)
- UI:project 詳情頁獨立 section · 還是側邊 drawer · 還是 chat pane 左側?
- 「插入對話」按鈕把 4 格卡轉為對話 prompt · prompt 模板怎寫才有效?
- 如何避免 4 格卡被當「又一個要填的表單」而被忽略?

### 4.D main.py 拆 services/admin_metrics.py(降低外包接手成本)
- 當前 admin endpoints 散在 main.py 四處 · 拆法用 FastAPI `APIRouter` 還是純 function import?
- `_ANTHROPIC_PRICING_USD` + `_LC_TX_SCHEMA_CHECKED` + helpers 一起搬嗎?
- pytest `importlib.reload(main)` 策略下 · 拆後測試要怎麼 refactor?
- 只拆一區會不會形成新 split-brain?拆完後的 main.py 會有多少行?

### 4.E(可選 · 若你還有餘力)上線第 2 週的死法
Round 6 說是「generic 感」(知識庫沒灌)· 你同意嗎?還有別的嗎?怎麼在 Day 0 當場就降低這風險?

---

## 5. 輸出要求

### 5.1 總論(150 字內)
一句話評價 + 3 件最該做的事(A/B/C/D 裡挑 · 或指出第 5 項你認為更急的)

### 5.2 針對 A/B/C/D 各出一份技術規格(400-600 字)

```
項目:A/B/C/D
現狀:[哪部分已做 · 哪部分沒做]
建議實作:
  - 資料結構 / API schema
  - 最小 Python/JS 代碼示意(20 行內)
  - 失敗路徑 / 降級策略
  - 測試 / 驗收條件
風險:
工時:
```

### 5.3 路線圖

| 階段 | 目標 | 關鍵行動 | 工時 | CP 值 |
|---|---|---|---|---|
| P0 本週 | 只列部署紅線(Sterio 手動) | - |
| P1 2 週內 | 4 項 A/B/C/D 的哪幾個? | - |
| P2 v1.1 | - | - |

### 5.4 給作者的 3-5 個問題
下輪審查能更精準的話,你想知道什麼?

---

## 6. 格式要求

- 繁體中文(技術詞 API/JWT/SSE 保留)
- 避免大陸用語
- 金額:`NT$ X,XXX`
- 日期:`2026 年 4 月 21 日`
- **檔案位置絕對路徑 + 行號**(`/Users/sterio/Workspace/ChengFu/xxx.py:123`)

---

## 7. 量化基準

- **GitHub:** <https://github.com/Sterio068/chengfu-ai>(10 commit · 7 輪審查 · 40+ 紅線修正)
- **測試:** 18 pytest / 11 smoke / 0 Pydantic deprecation / 0 startup warnings
- **後端:** `main.py` 46953 → 60000+ bytes(14 個 /admin/* + `/quota/check` + fingerprint + adapter + lifespan + indexes)
- **前端:** `app.js` 2064 行單檔 → 560 行 orchestrator + 21 modules(含 vendor-marked)
- **架構:** `_unused_scaffold/` 歸檔 · main.py 單一真相
- **文件:** `docs/` 9 → 21 檔(3 完整案例 / 4+1 角色手冊 / 2 SPEC / Pre-Delivery / Baseline / Upgrade / Review)
- **意外驗證:** 第 5 輪後 MongoDB journal 損壞 · `mongod --repair` 修回 · 證實月度 restore 制度的必要

---

## 8. 最後提醒

- 這系統**已跑** · `./scripts/start.sh` 一行起
- Sterio 懂技術 · **承富內部人不懂** · 任何「只有 Sterio 能維護」= 技術債
- 已 7 輪審查 · **重複指 Section「🚫 已修 14 項」的建議會被作者直接刪掉**
- 老闆要**省時 + 接案量** · 不是工程藝術

**直接開始審 A/B/C/D · 不用先確認。**
