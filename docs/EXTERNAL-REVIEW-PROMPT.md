# 承富 AI 系統 · 外部審查請求 (v6.0)

> **第 9 輪審查 · 2026-04-21 更新**
> 第 8 輪 reviewer 給的 A/B/C/D 4 大項規格全部已實作完成 · push 上 GitHub。
> 本輪重點:**審我做得對不對 · 找我漏掉的角度 · 預測上線後的死法**。

---

## ⚠️ **在你下筆之前 · 強制讀這段**

前 8 輪 reviewer 平均重複指出 70% **我們已修過的項目**。
**本輪開始 · 若你在報告出現下列「已修檔案+行號」的紅線指認 · 該項直接視為 0 分。**

### 🚫 已修 20 項 · 嚴禁再指為紅線

#### Round 1-7 修的(14 項 · 維持上輪清單)

| # | reviewer 常指的紅線 | 修在哪 | 驗證 commit |
|---|---|---|---|
| 1 | CRM 整區重繪長列表掉幀 | `frontend/launcher/modules/crm.js:86-108` 分批 render + idleCallback | `9903d55` |
| 2 | tenders 整區重繪 + 重綁 | `frontend/launcher/modules/tenders.js:47-85` event delegation | `9903d55` |
| 3 | chat.js renderMarkdown regex | `frontend/launcher/modules/chat.js:252-284` `vendor-marked.js` | `9903d55` |
| 4 | auth 401 沒 retry | `frontend/launcher/modules/auth.js:20-44` SessionExpiredError + Web Locks | `bedf413` |
| 5 | Day 0 登入卡關 | `docs/PRE-DELIVERY-CHECKLIST.md:112-125` 服務台 SOP | `9903d55` |
| 6 | Baseline 老闆答不出 | `docs/BASELINE.md:9-20` + `192-236` Champion 1 週日誌 | `9903d55` |
| 7 | per-user hard stop 只儀表 | `backend/accounting/main.py` `/quota/check` + `chat.js:160-175` 送前擋 | `9903d55` |
| 8 | transactions schema 默默回 0 | fingerprint + `/admin/budget-status` 黃牌降級 | `9903d55` |
| 9 | Route A hash router 未防 | `frontend/custom/librechat-relabel.js:14-70` listener + `_matchChatPath` | `9903d55` |
| 10 | on_event / .dict() deprecation | `main.py:54-77` lifespan + 全檔 model_dump() | `08cf827` |
| 11 | overpromise 文案 | `index.html:214/459/836` · QUICKSTART · BOSS 手冊三處 | `5b5859c` |
| 12 | split-brain(routers/ + auth.py) | `_unused_scaffold/` 已歸檔 · main.py 單一真相 | `5b5859c` |
| 13 | 密碼紙條沒銷毀 SOP | `PRE-DELIVERY-CHECKLIST.md:100-107` | `08cf827` |
| 14 | 備份沒異機、沒 restore 驗證 | `scripts/backup.sh:83-105` rclone + 月度 restore drill | `bedf413`/`08cf827` |

#### Round 8 真未解 4 項(A/B/C/D)現在**全部已實作**(6 項 · 詳見下節)

| # | reviewer 第 8 輪指的「真未解」 | 實作 commit | pytest | 程式行數 |
|---|---|---|---|---|
| 15 | **D · main.py 拆 services/admin_metrics.py** | `65de9bf` | +15 unit | -269 行(1721→1452) |
| 16 | **C · Projects drawer + Handoff 4 格卡** | `051dbed` | +3 integration | +542 行 |
| 17 | **A · Fal.ai Recraft v3 endpoint(num_images=3)** | `9dc7302` | +6 integration | +295 行 |
| 18 | **E-1 · 多來源知識庫 collection + CRUD**(老闆 Q3) | `fb84566` | +9 integration | +568 行 |
| 19 | **E-2 · 多格式抽字 + Meili 索引 cron** | `115f049` | +14 unit | +947 行 |
| 20 | **E-3 · 前端 Admin UI + 知識庫 view + ⌘K** | `8f91f76` | (前端,nodejs check) | +771 行 |

**所以本輪 reviewer 不要再說「Fal.ai 還沒做 / Handoff 卡只是談的 / NAS 整合是 v2」**——全部已 push。

---

### ✅ 第 9 輪 reviewer 該做的事

1. **審我做得對不對**(下節 §4 我會列每個批次的關鍵設計選擇 · 你來挑戰)
2. **找我漏掉的角度**(performance / security / UX / 教材未覆蓋的)
3. **預測上線後的死法**(技術 + 人為)
4. **質疑具體決策**(e.g. 「num_images=3 月成本估算合理嗎」「indexer 50k 檔會 OOM 嗎」)

**不要做的事:**
- 不要再指 §「🚫 已修 20 項」
- 不要再給 A/C/D/E 的「初版實作建議」(已實作 · 重複只稀釋訊號)
- 不要建議換框架 / 換 LibreChat / 加 k8s

---

## 🔗 0. 直接去讀

| 來源 | 位置 |
|---|---|
| **GitHub(public · 免認證)** | <https://github.com/Sterio068/chengfu-ai> |
| **Clone** | `git clone https://github.com/Sterio068/chengfu-ai.git && cd chengfu-ai` |
| **作者本機** | `/Users/sterio/Workspace/ChengFu` |
| **本機跑** | <http://localhost/>(launcher)· <http://localhost/api-accounting/docs>(API) |
| **commit 歷史** | `git log --oneline -25`(16+ commit / 8 輪審查 / 50+ 紅線修正) |
| **6 個新 commit(本輪要審)** | `git log --oneline 51d7a1a..HEAD` 看本輪實作的 D/C/A/E-1/E-2/E-3 |

### 必讀 8 份(20 分鐘消化)

```
1. CLAUDE.md                                     · 專案目標 + 12 項決議
2. docs/V1.1-IMPLEMENTATION-SPEC.md              · A/C/D + E-1/2/3 完整 spec(已實作的 source of truth)
3. docs/PRE-DELIVERY-CHECKLIST.md                · 部署完成度 35%
4. backend/accounting/main.py                    · FastAPI · 50+ endpoint · 1700+ 行
5. backend/accounting/services/                  · 拆出來的純 function(admin_metrics / knowledge_*)
6. frontend/launcher/modules/knowledge.js        · §E-3 新模組(370 行)
7. frontend/launcher/app.js + modules/*.js       · 前端 23 檔 ES modules(原 21 + knowledge + 改 palette)
8. docs/CASES/01-海廢案端到端.md                  · 系統實際怎麼用
```

---

## 1. 客戶與專案(維持)

### 客戶
- **承富創意整合行銷有限公司**(台灣 · 10 人)
- 政府標案 / 公關活動 / 設計案
- 2-3 位資深者對 AI 抗拒

### 老闆親答 5 題(優先級依據)
1. **每週 Top 3:** 設計 / 提案撰寫 / 廠商聯繫
2. **80% 原始檔:** LINE 群組 + NAS(**不是** Google Drive)
3. **L3 機敏:** **先不考慮**
4. **最在意:** 省時 + 接案量(不是風控)
5. **維運:** 外包 20h/週 Claude Code 遠端 · Champion 自主學習

### 老闆 v1.1 新答 5 題(2026-04-21)
| # | 問題 | 答 | 影響 |
|---|---|---|---|
| Q1 | 標案 PDF 多少是掃描 | **高比例 · OCR 必須在容器** | E-2 加 pymupdf OCR fallback |
| Q2 | 設計師偏好一次幾張 | **3 張挑方向**(原 reviewer 建議 1) | A `num_images=3` |
| Q3 | NAS scope | **整個 NAS · 所有類型 · 分專案** | E 從「5 sample」升為「多來源管理」 |
| Q4 | accounting 容器加 OCR/抽字 | **可接受** | E-2 加 pymupdf/docx/pptx/xlsx/Pillow |
| Q5 | 專案詳情 UI | **Drawer**(模態 vs drawer vs 展開三選) | C `project-drawer` |

→ **偏離這 10 題的建議會被否決**

---

## 2. 技術棧(不可替換)

| 層 | 選擇 |
|---|---|
| 硬體 | Mac mini M4 24GB |
| AI Platform | LibreChat **v0.8.4 pinned** |
| AI Model | Claude Opus 4.7 / Sonnet 4.6 / Haiku 4.5 |
| 後端 | FastAPI(`main.py` 1700+ 行 + `services/` 3 模組) |
| 前端 | 原生 ES Modules + 單 CSS · **無 build step** |
| 容器 | Docker Compose × 6(librechat / mongo / meili / accounting / nginx / uptime) |
| 對外 | Cloudflare Tunnel + Access(未架) |
| 機密 | macOS Keychain |
| 全文搜尋 | **Meilisearch v1.12**(E-2 接入) |
| 抽字 | **PyMuPDF / python-docx / python-pptx / openpyxl / Pillow**(E-2 新增) |

**不接受:** k8s / Redis / Kafka / GraphQL / 換框架 / SaaS / 改 10 助手 / 改 5 工作區 / 改主色

---

## 3. 當前狀態

### ✅ 程式碼:99%(本輪 +1%)

- 6 容器 healthy
- **65 pytest pass · 11 smoke pass · 0 deprecation**(原 18 + 47 新增)
  - `tests/test_admin_metrics.py` · 15 unit
  - `tests/test_knowledge_indexer.py` · 14 unit + 2 skip(於選裝 pdf/docx lib)
  - `test_main.py` · 36 integration(原 18 + 18 新)
- 後端:13 /admin/* RBAC · `/quota/check` 送前擋 · schema fingerprint
- 後端新:`/projects/{id}/handoff` · `/design/recraft` · `/admin/sources` × 4 · `/knowledge/{list,read,search}`
- 前端:23 檔 ES modules(原 21 + knowledge + modal 增強)· marked vendor · hash router 防護
- services/:`admin_metrics.py` / `knowledge_extract.py` / `knowledge_indexer.py` 純 function

### 🔴 部署落地:35%(維持 · Sterio 交付週手動做)

- Mac mini 未上架 · Cloudflare Tunnel 未接
- `knowledge-base/samples/` 空(老闆 Q3 答後 · scope 升為「整個 NAS」 · Sterio Day 0 仍會放 5-10 份 sample 暖系統)
- 10 帳號未建 · 密碼 reset SOP 未寫
- 2 場教育訓練未辦
- T0 baseline B 路未跑(模板已備)
- **NAS 掛載 SMB Keychain 未配**(E 上線前置)
- **knowledge-cron.sh 未排 launchd**(scripts 已寫 · launchd plist 待 Sterio 寫)
- **FAL_API_KEY 未設**(/design/recraft 會 503 友善提示 · 不擋其他)

### 📚 教材:88%(維持)

3 完整案例 + 4+1 角色手冊 + QUICKSTART + Pre-Delivery + Baseline + Upgrade。

---

## 4. 我要你審什麼(本輪 6 批新工作 · 一個一個挑戰)

### 4.1 Batch D · `services/admin_metrics.py` 拆分(commit `65de9bf`)

**做了什麼:**
- `main.py` 從 1721 → 1452 行(-269)
- 抽 11 個 pure function 到 `services/admin_metrics.py`
- FastAPI route decorator **保留在 main.py**(避免 split-brain)· service 只接 db/collection/settings
- 加 `tests/test_admin_metrics.py` 15 個 unit · 用 mongomock 不依賴 TestClient

**設計選擇 · 你來挑戰:**
1. 我用 `from services import admin_metrics` 而不是 `APIRouter` · 你會選哪個?為什麼 reviewer Round 8 偏好 APIRouter 我反而走 function?
2. `_SCHEMA_CACHED` 從 module-level 移到 services 內 · 但 cache 仍是 process global · 多 worker 會重複跑 schema probe · 是 bug 嗎?
3. 還有哪些區塊應該拆?(`main.py` 還有 1452 行 · 候選:tenders、CRM、L3 classifier)

### 4.2 Batch C · Projects Drawer + Handoff 4 格卡(commit `051dbed`)

**做了什麼:**
- 點 project card 從開 modal → 滑出 drawer(右側 42% · 手機 90%)
- Drawer 顯示:基本資訊(永遠) + 描述(有才顯) + Handoff 4 格(預設收合)
- 4 格:goal / constraints / asset_refs / next_actions
- 「📨 插入對話」按鈕 → 4 格轉為 prompt + clipboard + 開新對話
- BroadcastChannel · PM 存完設計師另一分頁即時更新
- 後端 `PUT /projects/{id}/handoff` 獨立 endpoint(不全量更新)

**設計選擇 · 你來挑戰:**
1. **Adoption 風險:** 4 格卡會不會被當「又一個要填的表單」就沒人填?「預設收合 + 一秒插入對話」夠不夠?
2. asset_refs 我自動推類型(`http*` → url、`/Volumes/` → nas、其他 → note)· 太簡單嗎?
3. 「插入對話」現在開 `/c/new` + clipboard · 但同仁可能不知道要貼上 · 是否該寫進 LocalStorage 給下一個 chat session 自動帶入?
4. drawer 寬度 42% 在 1280 螢幕(MacBook Pro 13 內建)會不會壓到主 list 太多?

### 4.3 Batch A · Fal.ai Recraft v3 endpoint(commit `9dc7302`)

**做了什麼:**
- `POST /design/recraft` · `num_images=3`(老闆 Q2)
- async poll 12 秒(可調)· 三態:done / pending / rejected
- 五段錯誤分類:`unconfigured`(無 key 503)/ `auth_error` / `service_error` / `timeout` / `rejected`
- 全中文 friendly_message · **完全不暴露** Fal 原文 stack trace
- `design_jobs` collection 留 log · 圖檔留在 Fal CDN 不存 Mongo
- 6 個 pytest 含 mock httpx · 驗成功 / moderation / 短 prompt / unknown size

**設計選擇 · 你來挑戰:**
1. **成本:** 3 張 × USD 0.04 = USD 0.12/次 × 32.5 = NT$ 4 · 老闆預算 NT$ 12,000/月 → 月 100 次內 OK · 但如果同仁愛重生(平均 3 次)月 NT$ 1200 · 是否該加每月配額?
2. moderation 訊息「描述太像真人、官方標誌或敏感文字 · 請改成抽象視覺描述」· 對承富實際 case(政府標案 + KV)夠精準嗎?
3. 12 秒未完成回 `pending` + job_id · 但前端目前**沒接 polling**(E-3 沒做)· 是不是該補?還是用 WebSocket 推?
4. `regenerate_of` 欄位收進來但**沒實作邏輯**(只記到 design_jobs)· 算 dead code 嗎?

### 4.4 Batch E-1 · 多來源知識庫 CRUD(commit `fb84566`)

**做了什麼:**
- `knowledge_sources` collection · `unique(path)` 防重複
- Admin CRUD 4 endpoint:GET / POST / PATCH / DELETE
- 公開讀取 3 endpoint:`/knowledge/list` / `/knowledge/read` / `/knowledge/search`
- **路徑白名單** · `KNOWLEDGE_ALLOWED_ROOTS` env(預設 `/Volumes,/Users,/mnt,/data`)
- **Path traversal 防護** · `os.path.abspath` + `startswith(base + os.sep)`
- **agent_access 白名單** · `X-Agent-Num` header 比對
- **knowledge_audit collection** · 誰/哪 Agent 讀什麼檔(PDPA)
- 9 個 pytest 含 traversal / exclude / agent whitelist 三層防護驗

**設計選擇 · 你來挑戰:**
1. **白名單 vs 黑名單:** 用 allowed roots 白名單(預設 4 個前綴)· 老闆要的「指定專案資料夾」會不會頂到?(e.g. 用 iCloud `/Users/X/Library/Mobile Documents/...`)
2. `unique(path)` 不允許同路徑兩個 source(e.g. 同 NAS 兩種權限)· 過嚴嗎?
3. `agent_access: []` 表示「所有 Agent 可讀」· 但 LibreChat Agent ID 是 UUID 不是「01-09」· 我用編號是基於 `config-templates/presets/` 命名 · reviewer 會覺得脆嗎?
4. audit log 寫到 `knowledge_audit` collection 但沒設 TTL · 1 年下來會多大?(粗估 10 人 × 50 次/天 × 365 = 182k doc)

### 4.5 Batch E-2 · 多格式抽字 + Meili 增量索引(commit `115f049`)

**做了什麼:**
- `services/knowledge_extract.py` · 副檔名路由器
  - PDF(pymupdf · text density < 120 字 + 有圖時 OCR fallback)
  - DOCX(python-docx · 段落 + 表格)
  - PPTX(python-pptx · 每投影片 shapes.text)
  - XLSX(openpyxl · 前 3 sheet × 前 20 行)
  - 圖片(Pillow EXIF + 尺寸)
  - 文字(.txt/.md/.csv · 多編碼試 utf-8/big5/cp950)
  - lazy import · 缺 lib 不 raise(回 type=error)
- `services/knowledge_indexer.py` · Meili 增量索引
  - `reindex_source` · `mtime` 比對增量
  - `reindex_all` · cron 入口
  - `delete_source_from_index` · source 刪時清 Meili
- 修兩個踩坑:
  - **Meili primaryKey 推斷失敗**(`id` 與 `source_id` 兩候選)· `_ensure_index` explicit `create_index({"primaryKey": "id"})` + 砍重建
  - **TZ 偏差** · `datetime.utcnow().timestamp()` 被當 local 轉 → 8h 偏差 · 改用 `calendar.timegm(utctimetuple())` + `int(st.st_mtime)` 對齊精度
- `scripts/knowledge-cron.sh` · launchd / cron wrapper(每日 02:00)
- 14 個 pytest 含 incremental 二跑 skip 全部 / dir prefix exclude / project auto-tag

**設計選擇 · 你來挑戰:**
1. **規模測試:** 我只在 3-5 檔測過 · 老闆 NAS 真實規模約多少?5k? 50k? 索引 50k 檔內存會不會炸?(目前 batch 200 doc 一次)
2. **OCR fallback** 條件 `text < 120 字 + 有圖` · 對承富政府 PDF(常掃描蓋章)合理嗎?還是該無條件 OCR?
3. **PyMuPDF 內建 tesseract OCR** 需 tessdata · Dockerfile 沒裝 · 我寫 try/except 降級。要不要在 Dockerfile 加 `apt-get install tesseract-ocr-chi-tra`?
4. **單 Meili index** 所有 source 共用 · 用 `source_id` filter 區隔 · 50k+ 文件後 search latency 預估?要不要 per-source index?
5. 增量比 mtime 不比 hash · NAS 上有人用 `touch` 不改檔內容 · 會浪費 reindex · 該擋嗎?

### 4.6 Batch E-3 · 前端 Admin UI + 知識庫 view + ⌘K(commit `8f91f76`)

**做了什麼:**
- `modules/knowledge.js`(370 行 · 完全新模組)
- Admin 頁 + 「📚 知識庫資料源」section(list / 建立 modal / 重索引 / 暫停 / 刪除)
- 新 view 「知識庫」 · sidebar nav · 列 sources → 點展開列 entries → 點檔 modal preview
- ⌘K palette `addAsyncSource` · debounce 300ms · 知識庫結果加分隔線
- modal.js 增 `show({bodyHTML, onSubmit})` 與 `openForm` 別名
- 點資料夾 reuse §C drawer pattern(隱藏 handoff)
- CSS 約 +180 行(`.source-card` / `.kb-*` / `.modal2-form`)

**設計選擇 · 你來挑戰:**
1. 「知識庫」 view 對所有人開(不是只 Admin)· 但讀檔可看到任何 enabled source · 是否該在公司內加 group 權限?
2. ⌘K 多源搜尋 debounce 300ms · 但 launcher 自身 source 是即時 filter · 兩段 latency 差會不會混亂?
3. 重索引 button 同步等(call `/admin/sources/{id}/reindex`)· 大 source 會卡前端幾分鐘 · 該改 background task + progress 嗎?
4. Admin 建立 modal 用 free-text input 接路徑 · 不能瀏覽檔案系統(因為 sandbox)· 會不會 admin 一直貼錯路徑?

### 4.E(可選 · 若你還有餘力)上線第 2 週的死法

Round 6 說是「generic 感」(知識庫沒灌)· 現在 E 已上線 · 你同意還是這個 risk top 1 嗎?
**新 candidate:**
- **NAS 掛載斷線** · macOS SMB autofs 會在 sleep 後失效 · 索引 cron 跑時掛掉 → 整個 source 看似空
- **Drawer + Handoff 4 格** · 沒人填(全靠 PM 主動 · PM 忙起來最先省)
- **設計師對 3 張圖不滿意** · 真實重生率可能 5+ 次/案 · 月成本爆預算
- **Meili index 損毀** · `data/meili/` 沒 backup pipeline(只 mongo 有)

---

## 5. 輸出要求

### 5.1 總論(150 字內)

一句話評價 + 3 件最該補的事(可從 §4.1-4.6 + §4.E 任挑)

### 5.2 針對 D/C/A/E-1/E-2/E-3 各出評分 + 1 個可改建議

```
批次:D / C / A / E-1 / E-2 / E-3
評分:1-5 ⭐
做對了什麼:
  - [點 1]
  - [點 2]
最該補一件事:
  - [具體可動作的修改 · file:line · 不超過 100 字]
風險:
  - [上線後最可能踩的坑]
```

### 5.3 路線圖

| 階段 | 目標 | 關鍵行動 | 工時 | CP 值 |
|---|---|---|---|---|
| P0 本週 | 部署紅線(Sterio 手動) | NAS 掛載 + launchd cron + FAL_API_KEY | - |
| P1 2 週內 | 你認為 §4 哪幾項最該補 | - |
| P2 v1.2 | - | - |

### 5.4 給作者的 3-5 個問題

下輪審查能更精準的話 · 你想知道什麼?
(具體 e.g.「老闆 NAS 實際幾 GB」「設計師重生平均次數」)

---

## 6. 格式要求

- 繁體中文(技術詞 API/JWT/SSE 保留)
- 避免大陸用語
- 金額:`NT$ X,XXX`
- 日期:`2026 年 4 月 21 日`
- **檔案位置絕對路徑 + 行號**(`/Users/sterio/Workspace/ChengFu/xxx.py:123`)

---

## 7. 量化基準(本輪更新)

| 項目 | 上輪 (v5.3) | 本輪 (v6.0) | Δ |
|---|---|---|---|
| **GitHub commits** | 10 | 16 | +6 |
| **pytest** | 18 pass | 65 pass + 2 skip | +47 |
| **smoke** | 11 pass | 11 pass(未動) | - |
| **main.py 行數** | ~1800 | 1452 + E/A/handoff 加回 ≈1700 | -100(淨) |
| **services/ 模組** | 0 | 3(admin_metrics / extract / indexer) | +3 |
| **後端新 endpoint** | - | +9(`/projects/{id}/handoff` × 2 / `/design/*` × 2 / `/admin/sources` × 4 / `/knowledge/*` × 3) |
| **前端 modules** | 21 | 23(+ knowledge / 改 modal/palette) | +2 |
| **後端依賴** | 11 | 17(+pymupdf/docx/pptx/openpyxl/Pillow/meilisearch) | +6 |
| **CSS 新增** | - | +400 行(drawer / sources / kb-*) | - |
| **文件** | 21 | 21(本輪沒加文件 · 只實作) | 0 |
| **意外驗證** | mongo journal | E-2 踩 Meili primaryKey 雙候選 / TZ 偏差 兩 bug 修完 | - |

---

## 8. 最後提醒

- 這系統**已跑** · 6 容器 + Meili index + 4 個新 view
- Sterio 懂技術 · **承富內部人不懂** · 任何「只有 Sterio 能維護」= 技術債
- 已 8 輪審查 · **重複指 Section「🚫 已修 20 項」的建議會被作者直接刪掉**
- 老闆要**省時 + 接案量** · 不是工程藝術
- 6 個批次都已 push · **本輪請挑戰我的設計選擇 · 不是要我重做**

**直接開始審 §4 6 個批次 · 不用先確認。**
