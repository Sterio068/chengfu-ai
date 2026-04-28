# 🚀 v1.3 快速開始 · 5 分鐘上手

> 全公司新 / 老人 · 看完此頁 · 立刻開始用

---

## ❶ 第一次登入(2 分鐘)

1. 瀏覽器開 `http://localhost/`(本機 dev)或 `https://ai.<company_ai>.com/`(prod)
2. LibreChat 登入頁 · 用管理員給的 email + 密碼
3. 自動跳 launcher · 看到 5 個 Workspace 卡片
4. 第一次自動跳 onboarding tour 4 步 · 跟著做

---

## ❷ 學會 ⌘K(全域跳轉)

任何時候按 `⌘K` · 打字 fuzzy search:
- 「投標」→ 跳 🎯 投標 workspace
- 「環保」→ 找 project / 知識庫含此字
- 「邦邦」→ 找 user

---

## ❸ 試一個 Agent(2 分鐘)

最簡單 · 寫新聞稿:
1. ⌘4 跳 📣 公關溝通
2. 開 04 新聞稿生成器
3. 對話框打:
   ```
   寫一段 200 字新聞稿 ·
   主題:公司整合 AI 工具 ·
   預估同事每月省 12 小時
   ```
4. Enter · 看 Agent 30 秒寫完
5. 不滿意 · 對話框打:「精簡到 100 字 · 加數字」 · 再 Enter

---

## ❹ 5 Workspace 是什麼

| ⌘ | Workspace | 用途 |
|---|---|---|
| ⌘1 | 🎯 投標 | 招標解析 / Go-NoGo / 建議書 |
| ⌘2 | 🎪 活動執行 | 場勘 / 動線 / 預算 |
| ⌘3 | 🎨 設計協作 | Brief / 視覺發想 / Recraft 生圖 |
| ⌘4 | 📣 公關溝通 | 新聞稿 / 社群貼文 / Email |
| ⌘5 | 📊 營運後勤 | 結案報告 / 報價 / CRM |

每個 workspace 進去看到該領域 5-7 個 Agent · 跟對話流程 SOP。

---

## ❺ v1.2 / v1.3 4 大新功能(7 分鐘上手 1 個)

### 🎤 會議速記
- 上傳 m4a/mp3/wav (≤25MB)
- 30 秒 STT + 結構化:摘要 / 決策 / action_items
- 推到 project Handoff(⏱ training-v1.3.md ❶)

### 📸 場勘 PWA(iPhone)
- 拍 1-5 張 + GPS + audio note
- AI 自動產 brief
- 推到 project Handoff(⏱ training-v1.3.md ❷)

### 🎬 媒體 CRM
- 記者資料庫 + 推薦
- v1.3 加 CSV 匯出(admin only)

### 📅 社群排程
- 排 FB/IG/LinkedIn 貼文
- v1.3 OAuth infra ready · 真 Meta API v1.4 切

---

## ❻ 出錯怎麼辦

優先順序:
1. **看 error-codes.md**(常見 30+ 解法)
2. **找 Champion**(公司指定 1 位)
3. **升 Sterio**(L3 以上)

---

## ❼ 進階學習路徑

5 分鐘上手後:
- **15 分鐘**:training-v1.3.md(教育訓練)
- **跨工作協作**:handoff-card.md(4 格卡)
- **iPhone 必看**:mobile-ios.md(4 設定)
- **快捷鍵省時**:slash-commands.md
- **想搜公司過往案**:knowledge-search.md(5 範例)
- **看自己 / 公司用量**:dashboard-metrics.md
- **是 admin?**:admin-permissions.md

---

## ❽ 求救通道

| 等級 | 找誰 | 工具 |
|---|---|---|
| L1 觀察 / 問題 | 自己 | 此 user-guide / help.js |
| L2 一般 bug | Champion | LINE / Slack |
| L3 警示(< 3 人) | Champion → Sterio | LINE |
| L4 嚴重(≥ 3 人) | Champion + Sterio | 電話 |
| L5 緊急(全掛) | Sterio 立即 | 任何方式 |

---

## ❾ 公司原則(必記)

### 資料分級
- **Level 01 公開** · 標案公告 / 結案 · 隨便用
- **Level 02 一般** · 客戶 email / 簡訊 · 對 LibreChat 用 OK
- **Level 03 機敏** · 選情 / 對手情報 / 個資 · **不能送 LibreChat**(走 Ollama 本地)

### 用量
- 月 cap NT$ 1,200 / 人(預設)
- 80% Champion email · 100% hard_stop 擋
- Haiku 主用(成本 1/10) · Opus 只重大決策

### PDPA
- 客戶 email / 電話 · 用 PII detect 先洗
- 寄外用內建 anonymize
- 同事離職 · admin 走 PDPA delete-all 跨 20+ collection 清

---

**版本**:v1.3.0(2026-04-23 ship)
**問題回報**:Champion 月度收集 → Sterio
