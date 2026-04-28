# 🔧 v1.3 新功能 · 故障排除

> v1.2 故障在 `docs/06-TROUBLESHOOTING.md`
> 此檔只列 v1.3 新功能的症狀

---

## 會議速記(Whisper STT · v1.2 + v1.3)

### 症狀 1 · 上傳後 status 永遠 processing
**原因**:Whisper API 沒回 / OpenAI key 沒設
**檢查**:
```bash
docker exec company-ai-accounting env | grep OPENAI
```
若 `OPENAI_API_KEY=` 空 → 沒設 · 跑 `setup-keychain.sh`

**真跑了沒回**:Whisper API 偶發 timeout · 等 2 分鐘還 processing 再點 detail · 看 status:
- `done` · 完成
- `failed` · 看 error 欄位
- `processing` 超過 5 分 → 重 upload

### 症狀 2 · transcript 中英混雜不準
**原因**:Whisper 對純中文最準 · 中英混差
**解**:沒辦法 · model layer · 之後可手動編輯(v1.4)

### 症狀 3 · push-to-handoff 後 project 沒更新
**檢查**:
- meeting 的 project_id 對嗎?
- project 真存在?(看 /projects)
- 你是 admin 或該 project owner 嗎?
**解**:對的話直跑 `mongosh company_ai --eval 'db.projects.findOne({_id:ObjectId(...)})'` 看 handoff 真值

---

## 場勘 PWA(Feature #7 · v1.2 + v1.3)

### 症狀 4 · iPhone 拍完上傳 400 「HEIC 不支援」
**參考**:`error-codes.md [E-203]` + `mobile-ios.md ❶`

### 症狀 5 · GPS 一直「取得中...」
**參考**:`error-codes.md [E-205]` + `mobile-ios.md ❸`

**進階**:確認 `https://` (localhost 才允 http · 域名必 https · iOS 才給 GPS)

### 症狀 6 · audio_note 錄完沒 transcript
**參考**:`audio-note-sop.md 坑 1`

**進階**:看 `db.site_surveys.audio_notes[].status`
- `failed` + error 「OpenAI key 未設」 → 同症狀 1
- `processing` 超過 2 分 → 重錄

### 症狀 7 · 5 張照片限制 · 拍多了
**現況**:單 survey 最多 5 張(防爆 image_b64 記憶體)
**解**:第 6 張拍另一個 survey · 或 v1.4 改 streaming(暫無)

---

## 媒體 CRM(Feature #6)

### 症狀 8 · CSV 匯入 100 行 · 只進 30
**原因**:email 重複 / email 格式錯
**檢查**:回應 body 的 `errors` array
**解**:errors 列出哪行 / 為什麼 · 修原 CSV 重 import

### 症狀 9 · CSV 匯出 Excel 開亂碼
**原因**:Excel 早期版本不認 UTF-8 BOM
**解 1**:Numbers / WPS / Google Sheets 開
**解 2**:Excel · 資料 → 從文字檔 → 65001 編碼

### 症狀 10 · 推薦回 0 結果
**原因**:topic tag 沒 match 任何記者的 beats
**解**:換用 records 的 beats 同名 tag · 或先建幾個記者標 beats

---

## 社群排程(Feature #5 + v1.3 A5)

### 症狀 11 · 排了貼文 · 5 分後沒 dispatch
**檢查**:
1. 看 db.scheduled_posts 該筆 status
2. status 還是 queued · cron 沒跑:
   ```bash
   launchctl list | grep social-scheduler
   tail -f ~/Library/Logs/company-ai-social-scheduler.log
   ```
3. status 是 publishing 卡住 · publishing_until 超 5 min · 下次 cron 重 claim(R22#1 設計)
4. status 是 failed · 看 error 欄(v1.3 mock 不該失敗)

### 症狀 12 · OAuth 連 FB · 跳轉後白屏
**原因**:Meta App ID 沒設 / redirect URI 沒對齊
**檢查**:
```bash
docker exec company-ai-accounting env | grep FACEBOOK_APP
```
若空 · 此功能 v1.3 是 mock · v1.4 補(`social-oauth-fallback.md`)

### 症狀 13 · OAuth callback 「state 過期」
**原因**:從 start 到 callback 超 10 分(用戶猶豫太久)
**解**:重新從「連 FB」按鈕開始

---

## LibreChat PDPA 整合(v1.3 B5)

### 症狀 14 · include_librechat=true · 「user_not_found」
**原因**:此 email 在 LibreChat users 沒登入過
**情境**:同事還沒第一次 login · 沒對應 LibreChat user_id
**解**:不用刪 · 沒資料

### 症狀 15 · 「archive_failed」 · 不繼續刪
**原因**:GPG 加密失敗(沒 'company_ai' key 或 disk full)
**安全機制**:刻意不刪(防 silent data loss)
**解**:
- 確認 GPG key 在:`gpg --list-keys company_ai`
- 沒就建:`gpg --full-generate-key`(name 設 'company_ai')
- 看 disk:`df -h ~/company-ai-backups/`

---

## Knowledge Hash(C3)

### 症狀 16 · cron 跑完 · file_count 都 0
**原因 A**:沒新檔(正常)
**原因 B**:hash 全 match · 都 skip(正常 · 預期)

**逼一次全重**:
```bash
python3 scripts/reembed-knowledge.py
```

---

## Real Mongo Test(C1)

### 症狀 17 · CI 卡在 「mongo:7.0 health check failed」
**原因**:GitHub Actions 偶發 mongo image pull 慢
**解**:重跑該 workflow · 通常第二次過

---

## Backup Offsite B2(A4)

### 症狀 18 · backup.sh 完成 · B2 端沒檔
**檢查**:
1. `rclone listremotes | grep company-ai-offsite`
2. `rclone ls company-ai-offsite:bucket-name | head`
3. backup.sh 結尾有 「☁ 已異機備份到 ...」?

**沒看到**:檢查 GPG key(只 .gpg 檔上傳 · 防明文外洩)

---

## OAuth Infra(A5)

### 症狀 19 · /social/oauth/start · 503
**原因**:`{PLATFORM}_APP_ID` 或 `_APP_SECRET` env 沒設
**解**:這是預期 · v1.3 沒接真 Meta App
參考 `social-oauth-fallback.md`

---

## Admin 拆檔(A1)

### 症狀 20 · admin endpoint URL 變了?
**沒變!**:routers/admin/__init__.py + routers/admin/dashboard.py
- 原 `/admin/dashboard` 仍在 `/admin/dashboard`
- include_router 把 sub-router 合併
- 對前端零影響

---

## esbuild Bundler(A3)

### 症狀 21 · launcher 進入慢 · 有 cutover 嗎?
**v1.3 沒 cutover**:nginx 仍 mount 原 `frontend/launcher/`(29 個 .js)
v1.4 才切 dist/ bundled
參考 `docs/04-OPERATIONS.md §6.4`

---

## 其他建議

### 截圖排錯
拍 3 張:
1. UI 看到的錯誤訊息
2. devtools network 那個 failed request
3. devtools console error stack

→ LINE / Slack Champion · 都看就懂哪裡

### 升級到 Sterio
**事故分級** `docs/04-OPERATIONS.md §7`:
- L5(全掛)立即
- L4(部分掛 > 3 人)2 小時
- L3(偶發 < 3 人)24 小時
- L2 / L1 月度收
