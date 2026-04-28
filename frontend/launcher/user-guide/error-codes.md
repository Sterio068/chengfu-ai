# 智慧助理 · 常見錯誤訊息 → 解法表

> v1.3.0 · 2026-04-23 · 給同事自助 + Champion 排查用
> 看到紅色 / 橘色錯誤先翻這份 · 80% 問題自己能解

---

## 怎麼用這份

每筆格式:
```
[error code] 訊息 (你看到什麼)
└─ 原因 (為什麼)
└─ 解 1 / 解 2 / 解 3 (照順序試)
└─ 找誰 (還是不行 · 找 Champion / Sterio)
```

---

## 🔴 系統層(全員可能踩)

### `[E-001] 認證失敗 · 請重新登入`
- **原因**:cookie 過期 / 跨分頁登出
- **解 1**:點右上 → 登出 → 重新輸入 email + 密碼
- **解 2**:Cmd+Shift+Delete 清 librechat 域名 cookie
- **解 3**:換瀏覽器測(Chrome → Safari)
- **找誰**:還是 401 → Champion(可能 user 被 disable)

### `[E-002] 系統暫時有點問題 · 問題編號 rid-xxxxxxxx`
- **原因**:後端 unhandled exception · 後端 log 有完整 stack
- **解 1**:重新整理頁面試一次(transient 居多)
- **解 2**:換用相似 Agent / 換對話新建
- **找誰**:重複出現 → Champion · 報 rid 給 Sterio

### `[E-003] 載入中... 卡住超過 30 秒`
- **原因**:後端慢 / 網路斷 / docker 容器掛
- **解 1**:`docker ps` 看 company-ai-* 是否全 running
- **解 2**:`docker compose logs -f accounting` 看有無 error
- **解 3**:`./scripts/start.sh` 重啟全套
- **找誰**:Champion(看 §06-TROUBLESHOOTING)

### `[E-004] HTTP 502 Bad Gateway`
- **原因**:nginx 收到 request 但 upstream(librechat / accounting)沒回
- **解 1**:等 5 秒重試(可能 container restart 中)
- **解 2**:`docker compose restart accounting`(若 accounting 升版後 nginx 沒 re-resolve DNS)
- **找誰**:Champion(可能 image 沒 build / OOM)

---

## 🟡 對話 / Agent(LibreChat 層)

### `[E-101] 沒餘額了 · 本月已用 NT$ X / NT$ Y`
- **原因**:超 per-user 月上限(預設 NT$ 1200)
- **解 1**:換 Haiku 模型(成本 1/10)· model selector 選 claude-haiku-4.5
- **解 2**:看 `/admin/budget-status` 自己用量分布
- **找誰**:Champion 申請額度提升 · 或 Sterio 從 admin panel 加額

### `[E-102] Agent 不回 · 永久打字中`
- **原因**:Anthropic 偶發 timeout / 你 prompt 太長
- **解 1**:剛 paste 大文字 → 拆成 2 段送
- **解 2**:取消 streaming(右下 ⏹)再重送
- **找誰**:重現 → Champion · 帶截圖

### `[E-103] 模型不支援 · "model X not allowed"`
- **原因**:你選的 model 不在 librechat.yaml 白名單
- **解 1**:改用 sidebar 的 5 個正式 model(Haiku 4.5 / Sonnet 4.6 / Opus 4.7)
- **找誰**:Sterio(改 librechat.yaml)

---

## 🟢 v1.3 新功能專屬

### `[E-201] 會議速記 · audio mime 不接受`
- **原因**:你上傳的不是 .m4a / .mp3 / .wav / .webm
- **解 1**:iPhone 錄音 app 預設 .m4a · 若不是 → 從「檔案 app」分享 → 選音檔
- **解 2**:電腦用 QuickTime 錄 .m4a · 不要 .mov
- **找誰**:Champion(若一直 mime error)

### `[E-202] 會議速記 · audio > 25MB`
- **原因**:Whisper 上限 25MB(估 60 分鐘 m4a)
- **解 1**:用 ffmpeg 壓:`ffmpeg -i in.m4a -b:a 64k out.m4a`
- **解 2**:拆兩段(45 min × 2)分別跑
- **找誰**:沒 ffmpeg → Champion 幫壓

### `[E-203] 場勘 · HEIC 不支援`
- **原因**:iPhone 預設拍 HEIC 格式 · Claude Vision 不認
- **解 1**(永久)**:設定 → 相機 → 格式 → 「最相容」(改成 JPEG)
- **解 2**(臨時):照片 app → 分享 → 「另存成 JPEG」
- **解 3**(v1.3+):後端會自動轉 · 但失敗時請走解 1
- **找誰**:設定改了還 HEIC → Champion(可能 iCloud 同步舊照)

### `[E-204] 場勘 · 麥克風權限被拒`
- **原因**:iOS Safari 拒絕麥克風 · audio_note 無法錄
- **解 1**:設定 → Safari → 麥克風 → 允許 / 詢問
- **解 2**:重 open launcher · 跳權限對話 → 允許
- **找誰**:還是不行 → Champion

### `[E-205] 場勘 · GPS 取不到 · "User denied geolocation"`
- **原因**:同上 · iOS Safari 定位被拒
- **解 1**:設定 → 隱私權與安全性 → 定位服務 → Safari → 使用 App 期間
- **解 2**:`launcher.local` 一定要 https(localhost 才允 http)· 看你怎麼進的

### `[E-206] 社群排程 · webhook 綁定失敗`
- **原因**:Slack/Discord/Telegram URL 寫錯 · 或內網 IP 被擋
- **解 1**:URL 一定要 `https://` 開頭
- **解 2**:不能用 localhost / 192.168.x.x / 10.x.x.x(R27#4 SSRF guard)
- **解 3**:Slack:從 Slack app → Apps → Incoming Webhooks 重新建一個 URL
- **找誰**:URL 對的還擋 → Champion(看 SSRF log)

### `[E-207] 媒體 CRM · email 重複 · 409`
- **原因**:你要建的 email 已存在 unique index
- **解 1**:搜該 email · 編輯既有那筆(別建新的)
- **解 2**:若舊筆已軟刪 · 改用新 email(故意分版本)

### `[E-208] knowledge 搜尋 · 沒結果`
- **原因**:尚未 index / mtime 沒更新 / 排除 pattern 擋了
- **解 1**:Admin · POST `/admin/sources/{id}/reindex`
- **解 2**:Admin · POST `/admin/sources/{id}/reindex?force=true`(強制全重)
- **解 3**:檢查 source 的 exclude_patterns

### `[E-209] PDPA delete-all · "admin 不能刪自己"`
- **原因**:防誤觸 lock 自己出去
- **解**:換另一位 admin 操作該 user 刪除

### `[E-210] PDPA · "confirm_email 不匹配"`
- **原因**:防 mis-click · body 的 confirm_email 必須 type 完整等於 path
- **解**:URL 是 `alice@x.com` · body 也要寫 `"confirm_email": "alice@x.com"`

---

## 🔵 Admin 專屬

### `[E-301] Admin endpoint 403 · "X-User-Email header 單獨不足以授權"`
- **原因**:你用 X-User-Email curl · 但這 endpoint 要求 cookie 或 X-Internal-Token
- **解 1**:先 launcher 登入 · 從瀏覽器 fetch · cookie 帶進
- **解 2**:用 X-Internal-Token(從 keychain 拿:`security find-generic-password -s 'company-ai-internal-token' -w`)

### `[E-302] /admin/cost · "anthropic_error LibreChat schema 異常"`
- **原因**:LibreChat 升版後 transactions schema 改了
- **解 1**:檢 `/admin/librechat-contract` 看 fingerprint 變化
- **找誰**:Sterio 看 services/admin_metrics.py probe_tx_schema

### `[E-303] dr-drill --from-offsite · "rclone unreachable"`
- **原因**:B2 連不上 / app key revoked
- **解 1**:`rclone listremotes` 看 company-ai-offsite 在不在
- **解 2**:`rclone ls company-ai-offsite:bucket-name` 試連
- **解 3**:重跑 `./scripts/setup-rclone-b2.sh`

---

## 🟣 部署 / Mac mini

### `[E-401] start.sh · "Docker Desktop 未安裝或未啟動"`
- **原因**:Docker Desktop 沒開 / install 損壞
- **解 1**:Applications → Docker · 雙擊開啟 · 等 menu bar 鯨魚變綠
- **解 2**:`brew install --cask docker` 重裝
- **找誰**:仍 fail → Sterio(可能 macOS 版本不相容)

### `[E-402] Keychain · "company-ai-anthropic-key 未設定"`
- **原因**:首次部署沒跑 setup-keychain.sh
- **解**:`./scripts/setup-keychain.sh`(會問各 API key)

### `[E-403] COMPANY_AI_INTERNAL_TOKEN 沒 export`
- **原因**:start.sh 沒從 Keychain 抓 internal-token
- **解**:重跑 `./scripts/setup-keychain.sh` + `./scripts/start.sh`

---

## 找不到對應錯誤?

1. **看 `docker compose logs -f` 找關鍵字**(rid-xxxx 或 ERROR)
2. **截圖 + 帶 rid · 給 Champion**(LINE / Slack / 親到桌邊)
3. **Champion 也排不出 · 升 Sterio**(`docs/04-OPERATIONS.md §7 事故分級`)

---

**最後更新**:2026-04-23 · v1.3.0 ship
**回報新錯誤**:Champion 收集 → 月度 update 此檔
