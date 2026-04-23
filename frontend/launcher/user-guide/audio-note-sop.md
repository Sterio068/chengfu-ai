# 🎙 場勘 audio_note 完整 SOP

> v1.3 B4 新增 · iPhone 場勘現場錄 30 秒 → Whisper 轉文字 → 設計師事後重看

---

## 為什麼有 audio_note?

**痛點**:設計師看場勘照片 · 想知道「光線怎樣」「客戶說想要什麼風格」 · 但 PM 已經回去了

**v1.3 解法**:每張照片旁可錄 30s 現場補述 · STT 轉文字存 db · 設計師事後逐字看

---

## 怎麼用(iPhone)

1. 進 launcher · 跳 📸 場勘 view(⌘ 沒對應 · 點 sidebar 或 #site)
2. 拍張照(已建好 survey)
3. 上傳 → AI 處理完 · 點 survey 卡片開 detail modal
4. 找「🎙 audio note」section · 點 **「🎙 錄 30 秒」**
5. iOS 跳麥克風權限 → 允許(第一次)
6. 開始錄 · 倒數計時 30 秒(可手動 ⏹ 提前停)
7. 停 → 自動上傳 → status「📤 上傳 · STT 中...」
8. 等 5-15 秒 · 重 open detail modal · 看到 transcript

---

## 麥克風卡關?

走 **mobile-ios.md §❷ 麥克風權限**

iOS 預設拒網頁取麥克風 · 必設定 → Safari → 麥克風 → 允許 / 詢問

---

## 限制

| 項目 | 上限 |
|---|---|
| 單檔大小 | 5 MB |
| 一張 survey 上限 | 10 個 audio note |
| 錄音長度 | 30 秒(MediaRecorder 強制 stop) |
| Mime | webm / mp4 / mp3 / wav / m4a / ogg |
| 只 owner 能錄 | 你不是該 survey 的 owner → 403 |

---

## 真實使用範例

### 範例 A · 場地光線
場勘下午 4 點 · 拍南面落地窗:
> 「這扇窗下午 3 點到 5 點直射 · 客戶想做品酒會 · 那個時段酒會反光 · 設計師考慮要拉布幔或挑早場」

設計師看完照片 · 自動知道避時段 · 不用問 PM。

### 範例 B · 客戶口頭限制
拍場地入口:
> 「客戶說一定要讓輪椅進得來 · 入口階梯這邊要做斜坡 · 預算多 5 萬」

PM 回去寫提案 · constraints 直接抄這段。

### 範例 C · 廠商備忘
拍舞台搭建區域:
> 「這個位置一年前舞美廠 X 公司搭過 · 報價約 8 萬 · 找 Sterio 拿他們電話」

回去就知道找誰報價。

---

## 後端怎麼處理(技術)

1. 上傳 multipart/form-data
   - `audio` file
   - `duration_sec`(前端錄了多少秒 · 給 cost 估算)
2. 後端寫 tmp 檔(streaming 64KB chunks)
3. BackgroundTask 跑 Whisper STT(`openai.audio.transcriptions`)
4. 結果 push 到 `db.site_surveys.audio_notes[]`
5. PDPA · 一律刪 tmp 檔(不論成敗)

**狀態**:
- `processing` · STT 跑中
- `done` · 完成 · 有 transcript
- `failed` · STT 失敗 · 有 error 訊息

---

## 推到 Project Handoff(v1.3)

survey detail 有「推到 Handoff」按鈕(已綁 project_id 才有)
按下:
- audio_notes[].transcript 自動 append 到 project.handoff.constraints
- site_issues 自動 append 到 constraints
- venue 進 asset_refs

接手的 PM 看 project · 直接看到 audio 內容(不用再點開 survey)

---

## 成本

- Whisper $0.006/min
- 30s = $0.003 = NT$ 0.10
- 一場 5-10 audio = NT$ 0.5-1
- 月 20 場場勘 = NT$ 10-20

進 /admin/cost 的 whisper.sources.site_audio 看實際

---

## 常見坑

### 坑 1 · 錄完沒有 transcript
- 看 audio_notes[].status · 「failed」表示 STT 失敗
- error 欄看原因(常是 Whisper API key 沒設)
- 重錄一次 · 通常 transient

### 坑 2 · transcript 中英混雜不準
- Whisper 對中英混雜支援普通 · 純中文比較準
- 可手動編輯 transcript(v1.4 加 UI · v1.3 沒)

### 坑 3 · audio note 順序亂
- 按 created_at 排 · 非按拍照順序
- 多 audio 對應同張照片時 · 每個 audio 補時間在 transcript 內(「下午 4:15 · 這個角度...」)
