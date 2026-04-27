# 🎓 v1.3 新功能教育訓練(15 分鐘版)

> 給 Champion 帶教 · v1.3 ship 後 1 週內全員過一遍
> 對應 docs/03-TRAINING.md 補充 · v1.2 那份不變

---

## 教學目標

15 分鐘讓同事學會:
1. 用會議速記(取代手動逐字稿)
2. 用場勘 PWA(iPhone 拍 + audio + GPS · 推 Handoff)
3. 用媒體 CRM 匯出 CSV(寄外給合作夥伴)
4. 看自己用量(/admin/cost · 一般人也看得見 budget-status)

---

## ❶ 會議速記(3 分鐘)

### 為什麼用
週會錄音 1 小時 → 30 秒看完 + 4 個 action_items 自動進 project。

### 怎麼用
1. 開會前 · 把手機 / Mac QuickTime 開錄音
2. 會議結束 · 跳 launcher 🎤 會議速記 view(⌘5 或 sidebar)
3. 上傳音檔(m4a / mp3 / wav · 最多 25MB)
4. 等 30 秒(Whisper 跑 STT + Haiku 結構化)
5. 回去 · 看到:
   - 摘要(3-5 句)
   - 決策(誰決定了什麼)
   - action_items(誰 何時 做什麼)
   - 風險 / 觀察點

### 推到 project
- 會議綁了某 project_id
- 點「推到 Handoff」
- action_items append 到該 project.handoff.next_actions
- PM 接班直接看到該開哪 3 件事

### 限制
- 25MB 上限 → 60 分鐘 m4a
- > 60 分?拆兩半上傳 · 各別 push 到同 project

---

## ❷ 場勘 PWA(5 分鐘 · iPhone 帶現場)

### 為什麼用
場勘照片留在 PM 手機 · 沒人看到 · 設計師回去問東問西

### 怎麼用(iPhone)
1. 場勘前 · 在 iPhone 開 launcher(`https://ai.<chengfu>.com/`)
2. 加到主畫面(safari → 分享 → 加入主畫面)
3. 跳 📸 場勘 view
4. 點「加照片」 → 開相機 → 連拍 3-5 張
5. 點「取得 GPS」 → iOS 跳權限對話 → 允許
6. 填地址提示(可選)
7. 綁 project_id(可選 · 從 Projects 頁複製)
8. 「上傳 + AI 分析」 → 30 秒後看到結構化 brief

### v1.3 新 · audio note
- survey detail modal · 找「🎙 audio note」section
- 點 🎙 → 錄 30 秒(可手動 ⏹ 提前停)
- 上傳 → STT 完成 transcript 顯示
- 設計師事後重看 · 知道「光線/客戶口頭/廠商備忘」

### 推到 Handoff
- 點該 survey 「推到 Handoff」 · site_issues 自動進 constraints
- v1.3 改成 append · 不覆寫人工填的(R23#4)

### 必前置:iPhone 4 設定
參考 mobile-ios.md:
- 相機 → 格式 → 最相容(JPEG)
- Safari → 麥克風 → 允許
- 隱私權 → 定位 → Safari → 使用期間
- 加 launcher 到主畫面

---

## ❸ 媒體 CRM 匯出 CSV(2 分鐘 · admin)

### 為什麼用
老闆要寄媒體名單給合作夥伴 / 有時要 audit · 之前只能手動抄

### 怎麼用(admin)
1. 跳 🎬 媒體 CRM view
2. 上方「⬇ 匯出 CSV」按鈕
3. 自動下載 `chengfu-media-contacts-2026-04-23.csv`
4. Excel / Numbers 開(BOM 中文不亂碼)

### 安全
- admin only(含 PII email/phone)
- 寫 audit log:`media_export_csv`(每次都記)
- 預設不含軟刪(is_active=false)· `?include_inactive=true` 才含
- CSV injection 防(=/+/-/@ 開頭加 ' 前綴 · 防 Excel 公式注入)

---

## ❹ 看自己 / 看公司用量(2 分鐘)

### 一般同事
- 首頁 · 看右上「本月用量」進度條
- 綠 < 80% · 安心
- 橘 80-100% · 換 Haiku 模型
- 紅 > 100% · 已被擋(找 Champion 加額)

### Admin
- 跳 📊 admin → /admin/cost
- 看分項:
  - claude-haiku-4-5 · 1.25/Mtok · 90% 應該用這個
  - claude-sonnet-4-6 · 15/Mtok
  - claude-opus-4-7 · 75/Mtok(只決策用)
  - **whisper · v1.3 加** · $0.006/min · meetings + site_audio
- 預估月成本:Haiku 主力 + 10% Sonnet + 5% Opus + Whisper ≈ NT$ 8,000

---

## ❺ Onboarding tour(同事第一次登入)

第一次 launcher 自動跳 4 步引導:
1. 首頁 5 Workspace 介紹
2. ⌘K 全域搜尋
3. 試一個 Agent(打字觸發)
4. 鼓勵填一個 Handoff

走完 · localStorage 記 `chengfu-tour-done` · 不再跳。

**Champion 帶新人**:
- 不要跳過 tour(reset:browser console `localStorage.removeItem('chengfu-tour-done')` 重 open)
- 一起走一輪 · 5 分鐘
- 然後試 1 個 /命令(`/news` 寫新聞稿)· 養 5 分鐘習慣

---

## 試試看 · 三個情境(讓同事真做)

### 情境 A · 寫新聞稿
1. ⌘4(公關 workspace)
2. 開 04 新聞稿生成器
3. 「寫一段 200 字新聞稿 · 主題:公司加入 AI 工具 · 預計提升服務效率 30%」
4. 看 Agent 輸出 · 評估 prompt 該怎麼改

### 情境 B · 問 Go/No-Go
1. ⌘1(投標 workspace)
2. 開 25 標案 Go/No-Go 評估
3. 「貼最近一篇政府網站招標公告 · 問 Go/No-Go」
4. Agent 回 8 維度評分

### 情境 C · 場勘 demo
1. iPhone 跳 📸 場勘
2. 拍個假場勘(辦公室 3 張)
3. 等結果
4. 看 AI 怎麼描述

---

## 進階(Champion 帶)

- **Slash 命令**:slash-commands.md 完整表
- **知識庫**:knowledge-search.md 5 個範例
- **Handoff 4 格卡**:handoff-card.md
- **Mobile 設定**:mobile-ios.md
- **Admin 權限**:admin-permissions.md(看自己權限)

---

## 教完 checklist

- [ ] 同事跑過 1 個 Agent
- [ ] 同事用過 ⌘K palette
- [ ] iPhone 4 設定全做(若場勘 PM)
- [ ] 知道首頁進度條代表什麼
- [ ] 知道找 Champion / Sterio 的時機(`docs/04-OPERATIONS.md §7`)

---

## v1.3 新功能進度表

| 功能 | 完成度 | 備註 |
|---|---|---|
| 會議速記 | ✅ 100% | v1.2 ship |
| 場勘照片 + GPS + AI | ✅ 100% | v1.2 ship |
| 場勘 audio_note | ✅ 100% | **v1.3 B4 新** |
| 媒體 CRM CSV 匯出 | ✅ 100% | **v1.3 B3 新** |
| /admin/cost · Whisper 段 | ✅ 100% | **v1.3 B2 新** |
| LibreChat PDPA 整合 | ✅ 100% | **v1.3 B5 新**(離職一鍵清) |
| 社群排程 真 FB/IG/LinkedIn | ⏳ mock(等 v1.4) | OAuth infra 已 ready |
