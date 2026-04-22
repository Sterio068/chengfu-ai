# 承富 AI · Mac 原生安裝精靈

> Mac 原生 .app · 雙擊跑 · GUI 對話框引導 IT 輸入 .env · 不用碰 Terminal

---

## 給承富 IT(收到 .dmg 的人)

雙擊 **`ChengFu-AI-Installer.dmg`** · 從 Finder 視窗拖出 **`ChengFu-AI-Installer.app`** 到桌面或 `/Applications/`。

**雙擊 `.app` 啟動** · 跟隨對話框輸入(5 個問題):

| 對話框 | 輸入什麼 |
|---|---|
| 1/5 · Anthropic API Key | 從 <https://console.anthropic.com> 拿 · `sk-ant-xxx...` 格式(隱藏輸入) |
| 2/5 · 公司域名 | 例 `ai.chengfu.com.tw` · 留空用本機 `localhost` |
| 3/5 · 管理員 email | 預設 `sterio068@gmail.com` · 直接 Enter |
| 4/5 · NAS 路徑 | 例 `/Volumes/chengfu-nas/projects` · 留空用本機測試 |
| 5/5 · 確認啟動 | 確認設定 · 按「啟動安裝」 |

之後自動完成:
1. 寫入 macOS Keychain(API key + JWT + CREDS + Meili + Internal token 共 7 項)
2. 建 `.env` · 注入 prod fail-closed env(R7+R8)
3. 開 Terminal 視窗(讓 IT 看 docker 進度)
4. 抓 5 個 image @sha256 pinned
5. 啟動 6 容器
6. 等 healthz 回 200(最多 90s)
7. 跑 smoke test
8. **彈最終對話框** · 印維運手冊 + 開瀏覽器到 `http://localhost/`

**失敗了?** 重雙擊 `.app` · idempotent · 跳過已完成步驟。

---

## 給開發者(打包 .dmg 的人 · Sterio)

```bash
cd installer
./build.sh
```

產出:
- `installer/dist/ChengFu-AI-Installer.app` · 可直接 open 測試
- `installer/dist/ChengFu-AI-Installer.dmg` · 可 USB / mail / Slack 給 IT

**打包流程:**
1. `osacompile` 把 `ChengFu-AI-Installer.applescript` 轉成 .app
2. 套 icon(若有 `installer/icon.icns`)
3. 改 `Info.plist` 中文名 + 版本 1.1.0
4. `hdiutil create` 包成 .dmg(含 .app + 「讀我.txt」)

**測試:**
```bash
open installer/dist/ChengFu-AI-Installer.app
# 或
hdiutil attach installer/dist/ChengFu-AI-Installer.dmg
# 然後從 Finder 跑
```

---

## 為什麼 .app 不是 .pkg?

| | .pkg | .app(我們的選擇) |
|---|---|---|
| GUI 對話框 | 預設無 · 要寫 InstallerJS XML | ✅ AppleScript `display dialog` 原生 |
| 隱藏密碼輸入 | 麻煩 | ✅ `with hidden answer` 一鍵 |
| 改流程 | 改 XML + Distribution.dist | ✅ 改 .applescript 重 osacompile |
| 簽名 | 必 Apple Developer Cert($99/年) | ⚠️ 可不簽 · IT 第一次跑 GateKeeper 警告 |
| 體積 | ~2-5 MB | ~50 KB(.app) · 100 KB(.dmg) |
| 維護 | 高 · XML + JS + script | 低 · 一個 .applescript |
| 適合 | 大型企業 multi-host 部署 | 一台 Mac mini · 1 次安裝 |

承富場景 = 1 台 Mac mini · IT 跑 1 次 · `.app` 完勝。

---

## GateKeeper 警告處理

第一次雙擊 `.app` · macOS 會擋:

> 「ChengFu-AI-Installer.app」未經驗證 · 無法開啟

**繞法 A · IT 操作(推薦):**
1. 關掉警告
2. 系統設定 → 隱私權與安全性 → 拉到底找「ChengFu-AI-Installer.app 已被擋」
3. 按「強制打開」

**繞法 B · 終端機(Sterio 用):**
```bash
sudo xattr -dr com.apple.quarantine ~/Desktop/ChengFu-AI-Installer.app
```

**根治 · v1.2 sprint:** Apple Developer ID 簽名 + notarization($99/年)

---

## 檔案結構

```
installer/
├── README.md                          ← 你正在讀
├── ChengFu-AI-Installer.applescript   ← 安裝精靈原始碼(編 .app 來源)
├── build.sh                           ← 打包 → .app + .dmg
├── icon.icns                          ← (選填)承富 icon · 套到 .app
└── dist/                              ← build.sh 產出(.gitignore)
    ├── ChengFu-AI-Installer.app       ← Mac 雙擊跑
    └── ChengFu-AI-Installer.dmg       ← 分發給 IT
```

---

## 維護注意

- `.env` template 內容若改 · 同步改 `ChengFu-AI-Installer.applescript` 的 `envContent` block
- 5 個 docker image 名若改 · 不影響 .applescript(透過 docker-compose 抓)
- repo 路徑邏輯:精靈先試 `~/ChengFu` `~/Workspace/ChengFu` `~/Desktop/ChengFu` `~/Documents/ChengFu` · 找不到自動 clone
