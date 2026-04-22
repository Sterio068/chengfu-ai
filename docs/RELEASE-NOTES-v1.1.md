# 承富 AI 系統 v1.1 · Release Notes

> **發布日期:** 2026-04-22(v1.0 → v1.1 純工程強化版)
> **對象:** 承富老闆 + Champion 看
> **3 分鐘讀完 · 給工程師看的版本看 §6 技術變更**

---

## 1. 一句話總結

**v1.0 已過 · 現 v1.1 把後端從「2400 行單檔 main.py」拆成 11 個小 router · 17 輪對抗式審查 · 修 50+ 紅黃線 · 更可靠 · 更好維護。**

對你(老闆)的意義:**Sterio 出國 2 週 · 系統故障由 Champion 找新工程師時 · 30 分鐘上手機率高很多。**

---

## 2. v1.0 → v1.1 改了什麼?

### ✅ 後端架構大改造(對你影響:無·純維護性)
- main.py 從 **2400 行 → 730 行**(縮 70%)
- 拆出 **11 個 router 檔**(safety / feedback / users / tenders / design / accounting / projects / memory / crm / knowledge / admin)
- 平均每檔 ~200 行 · 易讀易測

### ✅ 安全強化(對你影響:升 prod 模式更嚴謹)
- 認證機制重寫 · LibreChat refresh token + JWT 真比對(不再「假修一半」)
- `/admin/email/send` rate limit 真套上(20/hour · 防 SMTP 帳號被刷爆)
- `/admin/monthly-report` 補上認證(原本是 bug · 任何人能看月報)
- nginx auth_request 接 LibreChat `/api/ask` · 預算 gate 真擋(同事繞過 launcher 直打 LibreChat 也擋)
- X-Agent-Num 改 server-side 推導(同仁不能 spoof header 拿到沒授權的源)

### ✅ 可靠度(對你影響:同仁誤輸入不會 crash)
- 所有 ObjectId 路徑(/projects/{id} · /transactions/{id} · /crm/leads/{id})輸入錯回 400 不再 500
- 不存在 doc 回 404 不再 silent success(原本誤回 `{"deleted":0}`)
- Knowledge 搜尋 cache invalidation 跨 worker 即時(刪 source 後其他同仁立刻看不到)

### ✅ 部署 fail-closed(對你影響:勝過誤配 dev 模式上線)
- prod 啟動強制要 `ECC_ENV=production` + `JWT_REFRESH_SECRET` + `ECC_INTERNAL_TOKEN`
- 沒設容器啟不了 · 強迫 IT 補 env(總比悄悄退化成 dev 模式好)

---

## 3. v1.1 你會看到什麼差?(實際使用層)

| 場景 | v1.0 | v1.1 |
|---|---|---|
| 同仁打對話 | OK | 一樣 OK · 但偷偷加 quota gate 防爆預算 |
| 看月報 | 任何人 curl /admin/monthly-report 都看到 | 必須 admin |
| 設計助手生圖 | 同仁可繞 launcher 直打 | 必須登入 |
| 知識庫機敏案件 | X-Agent-Num: 11 偽造能看 | 從 LibreChat 對話自動推 · 不能改 |
| Champion 接手系統 | 開 main.py 看 2400 行抓不到頭 | 開 routers/ 看 11 個 200 行檔 |

---

## 4. 17 輪 Codex 對抗式審查 · 修了什麼?

從 v1.0 release(commit `cc47064`)到 v1.1(commit `2beb7d1`)中間:

| Round | 修了 | 重點 |
|---|---|---|
| R5(7 紅黃) | cookie / internal token / cache version / per-file timeout | 認證假修第 1 次發現 |
| R6(5 紅黃) | refreshToken cookie 真驗 + slowapi 真用 user | 認證假修第 2 次發現 |
| R7(5 紅黃) | refresh payload `{id, sessionId}` 真反查 + nginx auth_request | 認證假修第 3 次(終於修對) |
| R8(6 紅黃) | LRU cache + hmac.compare_digest + compose env | timing attack 防護 |
| R9(3 紅黃) | launcher 帶 conversation_id + nginx strip X-Agent-Num | 前後端閉環 |
| R10(2 紅) | knowledge router PermissionError + cache cross-worker | refactor 引入 regression |
| R11(2 紅) | rate limit 真套上 + monthly-report 補 admin | refactor 引入 regression |
| R12(0 紅) | — | 第 1 次全綠 |
| R13(3 紅) | CRM update_lead 4 bugs + projects/memory | 抽 router 引入 |
| R14(3 紅) | projects/crm ObjectId 防護 | 收尾 |
| R15(1 紅) | accounting DELETE transaction | 終極漏洞 |
| **R16(0 紅)** | **— · 0 patch needed** | **「現階段完美」達成** |

---

## 5. 接下來呢?(v1.2 路線圖)

不影響 v1.1 部署 · 但 v1.2 sprint 候選:

1. **多 worker 流水號 atomic counter** · 目前 invoice/quote 序號高並發有重複風險(已知 · 1 人 work 不會撞)
2. **CRM pagination** · 目前 list_leads 全撈 · 100 筆內 OK · 1000 筆會慢
3. **test_main.py 拆檔** · 現 997 行 · 拆 tests/test_routers/test_*.py 增加維護性
4. **Auth helper 抽 routers/_auth.py** · main.py 還能再縮到 ~530 行
5. **/quota/check + /quota/preflight 重設計** · 多 worker 預算 gate 一致性(目前各 worker 自己 cache)

---

## 6. 給工程師的技術變更清單

```
backend/accounting/
├── main.py                       2400 → 730 行(-70%)
└── routers/
    ├── _deps.py                  102 行(集中 _serialize / get_db / 3 dep factory)
    ├── safety.py                  56(L3 classifier)
    ├── feedback.py                91(👍👎 + admin-only stats)
    ├── users.py                   77(同事偏好)
    ├── tenders.py                 48(g0v 標案監測)
    ├── design.py                 235(Fal.ai Recraft + history)
    ├── accounting.py             384(accounts/tx/invoice/quote/pnl/aging)
    ├── projects.py               125(/projects CRUD + handoff B2)
    ├── memory.py                  99(Haiku 摘要 · 省 60% token)
    ├── crm.py                    174(Kanban 8 stage + import-from-tenders)
    ├── knowledge.py              665(§E 多源知識庫 + §10.3 derive)
    └── admin.py                  563(dashboard / cost / monthly-report)
                                ─────
TOTAL routers/                   2619 行抽出
測試:                           113 pytest pass + 2 skip
smoke:                          8/8 pass
docker:                         5 image @sha256 pinned · accounting healthy
```

主要 commit 標記(2026-04-21 → 2026-04-22):
- `c119317` ~ `c9e572e` · §11.1 B-1 ~ B-5(safety/feedback/users/tenders/design)
- `54d4955` · R7 cookie + ID lookup + nginx gate
- `44e1212` · R8 真 LRU + hmac + compose env
- `707c677` · B-6 knowledge(665 行 · 最大)
- `69a7732` · B-7 admin(13 endpoint)
- `74ee89a` · B-8 accounting(會計核心)
- `584ea0e` · B-9/10/11 一次推完 crm/projects/memory
- `2beb7d1` · R14+R15 收尾 ObjectId defense

---

## 7. Day 0 部署仍是 v1.0 流程

v1.1 是純後端強化 · 不影響 launcher / 訓練 / Day 0 SOP。
看 `docs/PRE-DELIVERY-CHECKLIST.md` 的 Day -7 ~ Day +30 清單。

---

## 8. 老闆驗收標準(維持 v1.0)

- 第 4 週同仁每人省 ≥ 5h/月 → ROI ≥ 2x · 簽收 ✅
- 5/10 → 警告 · 跟 Champion 一週調整週期
- < 5/10 → 重新 review Day 0 演練腳本

---

**簽收欄:** ☐ 老闆確認 v1.1 工程強化已 review · 不影響 v1.0 驗收
