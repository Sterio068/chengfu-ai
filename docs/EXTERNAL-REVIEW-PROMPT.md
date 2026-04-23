# 承富 AI 系統 · 外部審查請求 (v9.1)

> **第 26 輪審查 · 2026-04-23 · v1.2 收尾完成**
> **本輪重點:** v1.2 全部上線 · 4 新功能 + 4 補功能 + 17 優化 + 9 輪 audit · 0 紅
> **9 輪 Codex audit(R17-R25)修了 18 紅 + 12 黃 · v1.0/v1.1/v1.2 共 23 輪 audit 修 80+**

---

## ⚠️ **強制讀這段**

前 25 輪 reviewer 平均重複指出 70% **我們已修過的**。
**若報告出現下列「已修 80+ 項」任一條 · 該項視為 0 分。**

### 🚫 已修分類

#### v1.0 / v1.1(已修 51 項 · v8.1 詳列)
- 11 router 抽出 + cookie auth + nginx gate + ObjectId defense + ...

#### v1.2 後端(已修 23 項 · v9.0 詳列)
- 4 新功能 (#1 #5 #6 #7) + R20-R23 audit 修

#### v1.2 收尾(本輪 +18 項)
| # | 項目 | commit |
|---|---|---|
| 64 | 4 frontend modules(meeting/media/social/site_survey) | `9de181c` |
| 65 | sidebar 4 入口 + view containers + help.js v1.2 段 | `9de181c` |
| 66 | R24#1 · social datetime-local 偏 8h(toISOString 轉錯) | `62d95d3` |
| 67 | R24#6 · site_survey objectURL 取代 dataURL(memory −33%) | `62d95d3` |
| 68 | R24 P1 · hash whitelist 加 5 view(/#social 重整能進) | `62d95d3` |
| 69 | Feature #2 · LINE Notify(services + endpoint) | `a91cdb0` |
| 70 | Feature #3 · PII 偵測(7 patterns + chat.js 攔截) | `a91cdb0` |
| 71 | Day 2.3 · HEIC 自動轉 JPEG(pillow-heif) | `a91cdb0` |
| 72 | Day 2.4 · social-scheduler launchd plist | `a91cdb0` |
| 73 | R25#1 · LINE token preview-only(GET prefs 不露原值) | `ce01112` |
| 74 | R25#2 · HEIC streaming tmp(64KB chunked + file path) | `ce01112` |
| 75 | installer .app v1.2(加 OpenAI key + LINE 提示) | (本輪) |

**所以本輪 reviewer 不要再說** 「meeting 沒前端 / media 沒 view / social 沒列表 / 場勘沒 PWA / LINE 沒推播 / PII 沒偵測 / iPhone HEIC 擋 / cron 沒排 / installer 過時 / token 明文 / HEIC 吃記憶體」—— **全部已 push**。

---

### ✅ 第 26 輪 reviewer 該做的事 · 「真上線前」最終驗證

1. **Day 0 部署 SOP 重新跑一次**(Mac mini 上架前最後檢查)
2. **4 新功能 E2E 真跑**(會議速記真錄音、媒體推薦真 CSV、社群排程真排程到 5 分鐘後、場勘 iPhone 真拍照)
3. **R24-R25 修是否真完整**(其他類似 race condition / leak 散落?)
4. **若你能找到第 26 輪沒人發現的紅線 · 你贏**

**絕不做的事:**
- 不要再指「🚫 已修 75+ 項」
- 不要建議換框架 / 加 k8s / 加 Redis
- 不要再指 routers / cookie / ObjectId / pagination(已修透)
- 不要再說「該抽 router」(11 → 14 已超額)

---

## 🔗 必讀(35 分鐘消化)

```
[v1.2 4 新功能](本輪重點)
1. backend/accounting/routers/{memory,media,social,site_survey}.py
2. frontend/launcher/modules/{meeting,media,social,site_survey}.js
3. backend/accounting/services/{social_providers,line_notify}.py

[v1.2 補功能 + 優化]
4. backend/accounting/routers/safety.py(PII detect/audit)
5. backend/accounting/routers/users.py(LINE token + preview)
6. scripts/social-scheduler-cron.sh + config-templates/launchd/*social*.plist
7. backend/accounting/config.py(R14#6 集中 settings)

[Release / Installer]
8. docs/RELEASE-NOTES-v1.2.md(本輪更新)
9. installer/ChengFu-AI-Installer.applescript(v1.2 · 6 步對話框)

[已穩固](Round 1-12 過了 · 不重審)
10. backend/accounting/main.py(1105 行 · 14 router include)
11. routers/_deps.py + accounting/admin/knowledge/crm/projects/feedback/users/tenders/design/safety
12. docs/RELEASE-NOTES-v1.0.md + v1.1.md
```

---

## 4. 我要你審什麼(本輪僅 §4.1-4.3)

### 4.1 Day 0 部署 SOP 真實壓力測試

**讀 docs/DAY0-DRY-RUN.md + scripts/install-launchd.sh(現含 5 個 cron):**
- 5 個 cron 在 Mac mini 上同時跑 · 有 race?
- ChengFu-AI-Installer.app v1.2 對 IT 真會 OpenAI key 必填嗎?
- HEIC 轉 JPEG 在生產 OOM 風險(老闆 iPhone 拍 5 張 20MB HEIC)?

### 4.2 4 新功能 E2E 真路徑

挑一個跑全:
- **會議速記** · 真上傳 5 分鐘 m4a · Whisper STT 多久?Haiku 結構化會吐 valid JSON?
- **媒體 CRM** · 100 筆 CSV import 多久?推薦 10 個記者多久?
- **社群排程** · 排程 5 分鐘後 · cron 真會掃到嗎?(launchd interval=300)
- **場勘** · iPhone 真拍 HEIC 上傳 · 後端轉 JPEG 後給 Vision · 全程 < 30 秒嗎?

### 4.3 第 26 輪沒人發現的紅線

23 輪 audit 後仍有的 · 你贏。

---

## 5-7 同 v9.0(略)

## 8. 量化基準

| 項目 | v9.0 (R16) | v9.1 (本輪) | Δ |
|---|---|---|---|
| **GitHub commits** | 63 | **75+** | +12(Day 1+2+3 + R24+R25) |
| **pytest** | 100+2 | **149+2** | +49(4 features × ~8 tests) |
| **smoke** | 8/0 | 8/0 | - |
| **main.py 行數** | 730 | **1105** | +375(4 router include + lifespan recover) |
| **routers/** | 11 | **14** | +3(media/social/site_survey) |
| **services/** | 3 | **5** | +2(line_notify/social_providers) |
| **後端 endpoint** | ~75 | **~95** | +20(4 features × ~5 endpoint) |
| **frontend modules** | 25 | **29** | +4(meeting/media/social/site_survey) |
| **launchd cron** | 4 | **5** | +1(social-scheduler) |
| **後端依賴** | 17 | **19** | +2(openai SDK · pillow-heif) |
| **Codex 全綠 audit** | R12 + R16 | **R12 + R16 + 待 R26** | +1 待 |
| **意外驗證** | R7#1 LibreChat session | **R24#1 datetime-local 偏 8h** | - |
| **部署落地** | 45% | **45%** | 待 Mac mini 上架 |

---

**直接開始審 §4.1-4.3 · 不用先確認。找到紅就 patch · 全綠請說「現階段完美」。**
