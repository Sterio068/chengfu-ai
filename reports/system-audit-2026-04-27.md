# 承富 AI · 系統完成度審計 + 升級路徑

**日期**:2026-04-27
**版本基準**:v1.49(commit 8ce77aa)
**審計範圍**:前端模組 + AI 工作流 + 後端 FastAPI + MCP/Action + 維運
**目的**:盤點當前已完成的功能、識別下一步優先順序

---

## 📊 完成度總覽

| 層級 | 完成度 | 已驗證 | 主要落差 |
|---|---|---|---|
| **前端 macOS UX** | 🟢 92% | 沙箱實際運行 | 大檔拆分、雙模組整合 |
| **前端模組(13 個)** | 🟢 95% | 各 view 互動正常 | 已修 P0 listener 累積、SEGMENTS mutation、⌘1-5 雙觸發、a11y |
| **AI 對話 (chat.js)** | 🟢 98% | SSE 串流、附件、回饋、歷史 | DOM 查詢可緩存(P1) |
| **後端 FastAPI** | 🟢 88% | 354 tests pass · Mongo + Meili 真實接 | social_providers mock(待 Meta 審核) |
| **10 Agent system prompt** | 🟢 100% | JSON 完整 | — |
| **AI Action(Fal.ai/PCC/會計)** | 🔴 30% | schema 已定義 | **未掛載到任何 Agent**(P0) |
| **3 個閉環 workflow** | 🟡 70% | orchestrator 已寫定義 | execution gate 預設 false(設計性 draft-first) |
| **MCP 整合(Drive/Gmail)** | 🔴 0% | — | v1.0 預定 Drive · 尚未實作 |
| **維運自動化(launchd)** | 🟡 60% | 7 個 plist 模板 | 未自動安裝 · DEPLOY.md 未涵蓋 |
| **測試覆蓋** | 🟢 80% | 354 backend tests | orchestrator + social_providers 缺測 |

---

## 🔴 P0 · 阻擋業主價值的缺口(優先 1-2 週)

### 1. Action 沒掛到任何 Agent · AI 不會生圖、不會查標案、不會記帳

**現況**:
- `config-templates/actions/fal-ai-image-gen.json`(Recraft v3)寫好
- `config-templates/actions/pcc-tender.json`(g0v 政府電子採購網)寫好
- `config-templates/actions/accounting-internal.json` 寫好
- 但 `config-templates/presets/0*.json` 全部 `tools: []`、`action_ids: []`
- `config-templates/librechat.yaml` 沒有 `actions:` 區塊

**業主感受**:
> 「設計協作 Agent 不能直接生圖,我貼提示詞他只回文字描述」
> 「投標 Agent 不會查 g0v API,要我自己去網站貼回給他」
> 「會計記帳 Agent 不會新增交易」

**修正路徑**(預估 3 天):
1. `librechat.yaml` 加 `actions:` 區塊指向 `/config-templates/actions/*.json`
2. `scripts/create-agents.py` 建 Agent 時 POST `action_ids`(LibreChat API)
3. 重建 5 個吃 action 的 Agent:設計、投標、活動、財務、新聞
4. smoke-test:每個 Agent 在對話框試「生圖」、「查標案」、「記一筆」

### 2. Orchestrator workflow execution 預設關閉

**現況**:
- `backend/accounting/orchestrator.py:140` `_workflow_execution_enabled() → False`
- `POST /orchestrator/workflow/run` 永遠回 403
- 三個閉環(投標 / 活動 / 新聞)的多 Agent 串接無法跑

**業主感受**:
> 「按『投標全流程』只給我草稿,沒有真的順著問下去」

**修正路徑**(預估 1 天):
1. 確認業主接受多 Agent 自動串接 vs draft-first 哪個值
2. 若要開:設 `ORCHESTRATOR_EXECUTION_ENABLED=1` env var · 加 token budget guard
3. 若維持 draft-first:在 Launcher 的 workflow 卡片明確標「下一步建議」非「自動執行」

---

## 🟡 P1 · 高價值優化(2-4 週)

### 前端

| 項目 | 檔案 | 預估 | 影響 |
|---|---|---|---|
| chat.js DOM 查詢緩存(20+ 處)| `modules/chat.js` | 4h | 每次 send/stream/render 省 ~20 query |
| chat.js 串流時 scroll 用 RAF | `modules/chat.js:749,785,805` | 1h | 每秒省 60+ forced layout |
| history modal 雙 innerHTML 重構 | `modules/chat.js:1005-1046` | 3h | 修 fragile `setTimeout(50)` re-bind |
| 拆 app.js(1983 行)→ `views/` | `app.js` | 1d | 600 LOC × 3 modules · 可維護性 |
| 拆 chat.js(1304 行)→ 子模組 | `modules/chat.js` | 1d | streaming / attachments / history 分檔 |
| 共享常數抽 `modules/config.js` | app.js / chat.js attachment limits | 1h | 修 copy-paste 漂移 |
| theme/fullscreen/logout 共用 | shortcuts.js / control-center.js / menubar.js | 2h | 修三方狀態不同步 |
| dock keydown delegation | `modules/macos/dock.js:161-193` | 1h | 取代每 icon 一個 closure |
| NC fetch cache(30s 內)| `modules/macos/notification-center.js` | 1h | 開關 NC 不再重 fetch 三個 health |
| dashboard tablist 正確 aria | `modules/macos/dashboard-fpp.js` | 1h | SR 可導航 segments |
| window.minimize 加恢復路徑 | `modules/macos/window.js:144` | 2h | 目前最小化 = 永遠消失 |

### 後端

| 項目 | 檔案 | 預估 | 影響 |
|---|---|---|---|
| orchestrator 測試覆蓋 | `tests/test_orchestrator.py`(新)| 4h | preset adoption / workflow gate 0 → 80% |
| social_providers 測試 | `tests/test_social_providers.py`(新)| 3h | mock 行為 + 錯誤路徑 |
| smart_folders / update 不要靜默回 [] | `routers/admin/{smart_folders,update}.py` | 2h | 錯誤回 5xx · caller 看得到問題 |
| L3 classifier 升 LLM(可選)| `routers/safety.py` | 1d | 中文機敏語境準確度 |

### 維運

| 項目 | 檔案 | 預估 | 影響 |
|---|---|---|---|
| launchd plist 自動安裝 | `DEPLOY.md` Phase 4 + `smoke-test.sh` | 2h | 7 個 cron 確實生效 |
| monthly-report cron entry | `config-templates/launchd/monthly-report.plist`(新)| 30min | 月初自動寄給管理員 |
| `propose-skill.py` 排程 | 同上 | 30min | AI 自動發現新 skill 提議 |

---

## 🟢 P2 · Nice-to-Have(視 v1.1 規劃)

- MCP Gmail / Calendar(D-007 v1.1 預定)
- AI 機敏分類升級為 Ollama 本地推論(D-006 階段二)
- Chrome Extension(D-012 預定)
- dock.js drag-reorder 改 IntersectionObserver
- 動態 segment count(目前是 hardcode `全部 24`)
- meta tag tabs/aria-controls 正確指向 #fpp-main

---

## ✅ 已完成(本日 v1.48 + v1.49 提交)

### v1.48(commit 516061a)
- ✅ chat 對話框左緣 6px 拖曳調寬(360–視窗寬,localStorage 記憶)
- ✅ chat 全螢幕模式按鈕 ⛶ + ⌘⇧F 快捷鍵(localStorage 記憶)
- ✅ chat textarea `resize: vertical` + ResizeObserver 偵測手動拖
- ✅ 雙擊 textarea 右下還原 auto-grow
- ✅ main padding-right 跟 chat-pane 寬度動
- ✅ 修側欄無法下滑(`overflow:hidden` → `overflow-x:hidden, y:auto`)

### v1.49(commit 8ce77aa)
- ✅ menubar.js listener 累積:`engine-changed` 移到 init · `setInterval` 用模組層 var
- ✅ menubar.js init guard:`_initialized` 防多次 init 疊聽
- ✅ ⌘1-5 雙觸發:keyboard.js 為 canonical · shortcuts.js 移除 ⌘0/⌘P/⌘1-5/⌘N 重複
- ✅ dashboard-fpp SEGMENTS const 不再 mutate · `_state.segment` 為 source
- ✅ chat-messages 加 `role="log"` `aria-live="polite"` `aria-relevant="additions text"`

---

## 🗺️ 建議升級順序(向業主提案)

```
Week 0–1  · P0 阻擋  → AI 真的會用工具
  Day 1-2 │ librechat.yaml actions 區塊 + create-agents.py 掛 action_ids
  Day 3   │ smoke test 5 個 Agent(設計生圖 / 投標查 PCC / 會計記帳 / 新聞 / 活動)
  Day 4   │ 跟業主決定 orchestrator execution gate 開或關
  Day 5   │ 補 orchestrator + social_providers 測試

Week 2-3  · P1 體驗
  - chat.js DOM 緩存 + scroll RAF
  - app.js / chat.js 拆檔
  - 共用 actions.js(theme/fullscreen/logout)
  - launchd plist 自動安裝 + monthly-report cron
  - dashboard tablist 正確 aria

Week 4    · P1 收尾 + v1.1 規劃
  - window.minimize 恢復路徑
  - dock keydown delegation
  - NC fetch cache
  - v1.1 路線評估:Gmail/Calendar MCP · Chrome Extension · L3 LLM 分類

Phase 2(等業主開 Tier 2 預算 + Meta 審核)
  - social_providers 真實 publish
  - L3 classifier 升 Ollama
  - 主管家 orchestrator 真實多 Agent 執行(若 Day 4 業主同意)
```

---

## 📍 風險與取捨

1. **Action 掛載需 LibreChat 重啟 + token 預算試跑** · 建議在 Mac mini 部署後跟業主同步,避免在 dev 環境耗 demo 額度
2. **orchestrator execution 開啟 = 多 Agent 串接 = token 用量翻 3-5 倍** · 必須先設 budget guard
3. **拆 app.js / chat.js** 是純粹維護性投資 · 業主感受不到,但下次重大功能會省 1 週
4. **social_providers 解 mock 卡 Meta** · 已知阻塞,不在 ChengFu side

---

**結論**:系統核心(對話、知識庫、會計、UX)已可交付,但「AI 真的會用工具」是業主體感最強的最後一里。建議 Week 0-1 集中火力把 Action 掛上,其餘 P1 跟著節奏迭代。
