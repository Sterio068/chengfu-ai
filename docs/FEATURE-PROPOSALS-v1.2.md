# 企業 AI v1.2+ 功能開發建議

> **時機:** v1.1 release ready(21 輪 audit / 11 router / 115 pytest pass)· 等 Mac mini 上架
> **對象:** Sterio + 本公司老闆共決
> **方法:** 按「ROI × 工時 × 差異化」排 · 不是按技術炫酷
> **決策:** 老闆選 Tier 1 至少 3 個 · 每個功能走 TDD · 下一輪 Codex audit 驗收

---

## 🎯 Tier 1 · 馬上做(高 ROI 短工時 · 每個 ≤ 3 天)

### 1. 🎤 會議速記自動化 · 錄音 → 逐字稿 → 結構化紀錄 · **2 天**

**為什麼:** PR 公司每週 8-12 場客戶會議 · 手打會議紀錄平均 40 分/場。10 人 × 月省 40 × 10 = **4000 分 / 月**(= 67 小時 · 超過 ROI 公式月省 57 小時)。

**流程:**
- iPhone 或 MacBook 錄音(既有 macOS Voice Memos · 匯出 m4a)
- Launcher「📣 公關」Workspace 上傳音檔 → Whisper STT(OpenAI · 本公司已有 key)
- Haiku 4.5 整理成結構化紀錄:決議 / 待辦 / 關鍵數字 / 下次會議
- 存進 projects handoff · 指派 next_actions 給相關同事

**實作:**
- `routers/memory.py` 加 `POST /memory/transcribe`
- `whisper-1` 模型 · 本公司 OPENAI_API_KEY 已可用(v1.2 新加 frontend_writable)
- launcher `modules/voice.js` 已存在(目前沒完整接)· 補 UI
- 測試:5 分鐘模擬音檔 · 驗 transcribe + 整理 < 20 秒

**Champion 推動難度:** 低 · 同事本來就錄音 · 現在「上傳 → 5 分鐘會議紀錄自動產出」

---

### 2. 📱 LINE Notify 推播 · 標案截止 / 預算警告 / 月報通知 · **半天**

**為什麼:** 本公司同事不常開電腦看 launcher · LINE 必看。標案截止前 3 天 / 客戶提案收件 / 本月預算 80% · 全部推 LINE · 不遺漏重要 deadline。

**流程:**
- 本公司註冊 LINE Notify(免費)· 每同事綁自己 token
- accounting `services/notify.py` · 3 種觸發:
  1. tender-monitor cron(每日跑)· 新標案符合關鍵字 → LINE
  2. quota 80% / 95% 觸發 → LINE admin
  3. 月報寄出時 → 同步 LINE summary

**實作:**
- `services/notify.py` + `db.user_prefs.line_token` 欄位
- `/admin/users/{email}/line-token` 同事自設 token
- 跟 send_email 同 pattern · 20/hour rate limit
- 測試:mock LINE Notify API + 觸發驗證 3 流程

**Champion 推動難度:** 極低 · 同事掃 QR 綁 token 就好

---

### 3. 🔒 PII 自動偵測 · 對話裡出現身分證 / 電話 · 彈警告 · **1 天**

**為什麼:** 本公司常幫政府做民調 · 對話裡可能貼受訪者身分證 / 電話。一旦送 Claude API = PDPA 法律風險。自動偵測 = 法務保險。

**流程:**
- launcher `modules/chat.js` 送前攔截 · regex 掃:
  - 身分證(`A123456789`)
  - 電話(`0912-345-678` / `02-12345678`)
  - Email(`name@domain`)
  - 信用卡 16 位數
- 命中 → 強迫使用者確認 · 「打碼後送 / 取消」
- 打碼用 `***` 或 `[身分證]` · 送出時已脫敏
- 後端 audit log 記錄觸發次數(不記 raw · PDPA)

**實作:**
- `modules/chat.js` 送前 detectPII 函式(50 行 regex)
- modal 警告 UI · 顯示偵測到什麼 · 提供一鍵遮罩按鈕
- 後端 `POST /safety/pii-audit` endpoint 記錄 · 月報整合

**Champion 推動難度:** 零 · 只有警告 · 同事仍能選擇原樣送(但有 audit)

---

## 🎯 Tier 2 · 這季做(中 ROI · 每個 2-5 天)

### 4. 📰 輿論監測 Daily Digest · 關鍵字 RSS → 每日摘要寄 admin · **2-3 天**

**為什麼:** 本公司很多客戶有 「替我監測市場動向」需求(政府選舉期 / 食品安全事件 / 競品新聞)。目前是人工 google · 一週 3 小時浪費。**每個監測議題 = 一個潛在附加價值 case**(外包可收 NT$ 5,000 / 月)。

**流程:**
- admin 加關鍵字到 watchlist(e.g. 「海洋廢棄物」「減塑政策」)
- cron 每日 07:00:
  1. 抓 Google News RSS · Yahoo! News RSS · PTT(選擇性)
  2. 去重 + 相似度聚合(Haiku 4.5 判重)
  3. 每主題摘要 3-5 則 · 含連結
  4. 寄 email + LINE(若 Tier 1#2 完成)
- launcher 新 view「📰 輿論雷達」· admin 看 historical

**實作:**
- `routers/watchlist.py` · CRUD 關鍵字 + 每日結果
- `scripts/watchlist-cron.py` · 排 launchd 07:00
- feedparser(RSS 解析 · 15k stars)· 加進 requirements.txt
- 測試:mock RSS · 驗去重 + 摘要格式

**Champion 推動難度:** 中 · 需要 admin 每週 review watchlist · 補關鍵字

---

### 5. 📅 社群貼文排程 · FB / IG / LinkedIn 排程發布 · **3-5 天**

**為什麼:** 本公司目前「04 新聞稿生成器 / 05 社群貼文生成器」只寫 · 沒排程發。PM 每週 2 小時手動發 · 錯時間 · 打掉重寫。排程 = 每週省 2h × 3 PM = **6 小時 / 週**。

**流程:**
- launcher「📣 公關」Workspace 加「排程區」
- 寫完貼文 → 選平台 + 時間 + 圖片 → 存 queue
- accounting `services/social_scheduler.py` cron 每 5 分鐘掃 queue
- 到時間 → call Meta Graph API / LinkedIn API · 發布 + 記 post_id + 狀態
- 失敗 retry 3 次後通知 admin

**實作:**
- Meta Graph API(FB / IG)· LinkedIn Share API
- 需本公司註冊 Meta / LinkedIn developer app(1 天 · 老闆配合審核)
- `routers/social.py` · scheduler + history + retry
- 測試:mock Meta API · 驗 scheduler + failure 通知

**Champion 推動難度:** 高 · 跟 Meta 審核 = 跟老闆走流程 1 週

---

### 6. 📇 媒體 CRM · 記者 / 主編資料庫 + 發稿歷史 · **2 天**

**為什麼:** 本公司現在 CRM 是標案 pipeline(B2B)· 沒管記者。發新聞稿是「想到誰就寄誰」· 搞不清每位記者發過幾次 / 哪些主題接受。整合後:PM 寫完新聞稿 → 自動推薦 TOP 10 相關記者(按歷史接受率)。

**流程:**
- 新 collection `media_contacts`:姓名 / 媒體 / 負責主題 / email / 手機 / 發過幾次 / 接受率
- launcher CRM 加「記者」tab · import from CSV(初始匯入本公司現有名單)
- 每次 04 新聞稿生成 · 送前顯示推薦名單 + 一鍵寄 Email(經 send_email · rate limit)
- 發稿後追蹤:24h 內 Google News 搜到 = 接受(手動 mark)

**實作:**
- 複用 `routers/crm.py` pattern · 加 `media_contacts` collection + endpoints
- 推薦:主題 + 記者負責主題 match 分數
- 測試:匯入 100 筆 · 推薦 TOP 10 驗證 match 邏輯

**Champion 推動難度:** 中 · 初期要手動建資料(100 筆 · 1 天工)

---

## 🎯 Tier 3 · 下半年做(低 ROI 但差異化 · 每個 3-7 天)

### 7. 📸 場勘表單 PWA · 活動現場 iPhone 拍照 + GPS + AI · **3-5 天**

**為什麼:** 本公司接活動案 · 場勘現場目前用 iPhone 拍照 + 手寫筆記 · 回辦公室用 Word 整理 2 小時。用 PWA:現場拍照 + 語音註記 + GPS → AI 整理成結構化 brief → 存進專案 handoff。

**流程:**
- launcher 已是 PWA(有 sw.js)· 加「場勘」路由
- iPhone Safari 加主畫面 → 全螢幕 · 拍照 API · Geolocation API · MediaRecorder
- 上傳時進 accounting · 每張照片跑 Vision(Haiku multimodal)產圖說
- 整合 GPS + 照片 + 語音 → 結構化 JSON(場地寬 / 高 / 光線 / 入口數 / 洗手間位置 ...)
- 結構化 brief 自動填進「🎪 活動」Workspace handoff B2

**實作:**
- frontend PWA 加離線支援(service worker 已有)
- `routers/site_survey.py` · multipart upload + Claude vision
- 測試:mock photo upload · 驗 vision 回正確結構

**Champion 推動難度:** 中 · 老闆買 iPad Pro 給現場 PM(NT$ 20k)

---

### 8. 📊 季度策略 AI 分析 · 老闆 quarterly review 自動產出 · **1-2 天**

**為什麼:** 本公司老闆每季看「標案勝率 / 案量 / 利潤」· 人工做一次 4 小時 × 4 季 = 16 小時 / 年。用 AI 做:「比 Q2 我們勝率 63% → Q3 47% · 下降主因:連 3 次競標都輸給同一對手 XX 公司 · 建議調整 pricing / service mix」。

**流程:**
- `/admin/quarterly-review?q=2026-Q3` endpoint
- 撈 3 個月的:
  - CRM leads pipeline(won/lost ratio)· 標案漏斗(tender_alerts → interested → won)
  - 會計 pnl 分專案(margin 分布)
  - feedback stats(哪些 agent 被讚 / 被抱怨)
- 丟 Opus 4.7 跑 5000-token 分析 · 回結構化 JSON
- 產 PDF 或 markdown · 寄 admin

**實作:**
- `routers/admin.py` 加 `/admin/quarterly-review` · 撈資料 + Opus call
- 模板 prompt 寫在 `knowledge-base/skills/quarterly-review.md`
- 測試:seed 3 個月 demo data · 驗 prompt 輸出有「勝率趨勢 / 建議 / 風險」三段

**Champion 推動難度:** 零 · 老闆自用

---

## 📊 ROI 總表

| # | 功能 | 工時 | 月省時間 / 10 人 | 差異化 | 優先度 |
|---|---|---|---|---|---|
| 1 | 會議速記自動化 | 2 天 | **67h** | 中 | ⭐⭐⭐⭐⭐ |
| 2 | LINE Notify | 0.5 天 | 低(防漏) | 低 | ⭐⭐⭐⭐⭐ |
| 3 | PII 偵測 | 1 天 | 法律保險 | 高(PDPA) | ⭐⭐⭐⭐⭐ |
| 4 | 輿論雷達 | 2-3 天 | 12h + 附加價值 | 高(PR 獨有) | ⭐⭐⭐⭐ |
| 5 | 社群排程 | 3-5 天 | **24h** | 中 | ⭐⭐⭐⭐ |
| 6 | 媒體 CRM | 2 天 | 8h + 勝率 | 高(PR 獨有) | ⭐⭐⭐ |
| 7 | 場勘 PWA | 3-5 天 | 8h + 客戶印象 | 高(活動獨有) | ⭐⭐⭐ |
| 8 | 季度策略 AI | 1-2 天 | 4h(老闆自用) | 中 | ⭐⭐⭐ |

**Tier 1(1-3)合計:** ~3.5 天 · 每月省 67+h + 法律保險 + 防漏

**全 8 個做完:** ~20 天 · 每月省 **120+h**(等於 0.75 個全職)

---

## 🏁 建議 v1.2 Sprint 規劃

### Week 1(Mac mini 上架後第 1 週 · 驗收基線 T0)
- Day 0 教育訓練(v1.0 SOP 不動)
- 本公司老闆選 Tier 1 #1 / #2 / #3 走哪個
- Sterio 實作第 1 個(推薦 #1 會議速記)

### Week 2(v1.2.1)
- 完成 Tier 1 三個
- R17 Codex audit
- 修紅黃 → push

### Week 3-4(v1.2.2)
- 老闆選 Tier 2 一個(推薦 #5 社群排程 · ROI 明確)
- R18 audit

### Month 2(v1.3)
- Tier 2 其他 + Tier 3 優先
- 配合 Mac mini 上架 + Cloudflare + 10 同仁教育

### Month 3(v1.4 + v1.2 技術債)
- R14 黃線修(invoice race / CRM pagination / test 拆檔 / _auth 抽)
- 老闆簽收 4 週驗收(v1.0 定義)

---

## 🚫 **不建議做的**(清單外的 FOMO)

1. ❌ **RAG vector embedding** · 本公司知識庫 ~500 份 · Meilisearch BM25 夠用 · 加 pgvector = 複雜度暴增
2. ❌ **自訓 LLM fine-tune** · 成本 USD $5k + GPU · 本公司規模不值
3. ❌ **多節點 HA Kubernetes** · 10 人公司 1 台 Mac mini 死 = 1 小時回復 · 不需 HA
4. ❌ **自建 SSO(Okta/Auth0)** · LibreChat 的帳號密碼 + 2FA 已足
5. ❌ **自開發 mobile native app** · PWA 完全夠 · iOS / Android 原生 = 2 個月工程

---

## 📋 老闆決策單(Sterio 問老闆)

> 老闆 · v1.2 sprint 您想優先哪 3 個?(每個 1-3 天)
>
> □ #1 會議速記(10 人月省 67 小時 · ROI 最高)
> □ #2 LINE 推播(同事不漏截止 / 預算)
> □ #3 PII 偵測(PDPA 法律保險)
> □ #4 輿論雷達(PR 差異化 · 可轉客戶附加案)
> □ #5 社群排程(PM 月省 24h)
> □ #6 媒體 CRM(記者推薦 · 提升發稿接受率)
> □ #7 場勘 PWA(活動 PM 現場神器)
> □ #8 季度策略 AI(老闆自用)
>
> 推薦組合:**#1 + #2 + #3**(3.5 天 · 覆蓋痛點最大)
> 或:**#1 + #4 + #5**(PR 行業完整流程 · 8 天)
