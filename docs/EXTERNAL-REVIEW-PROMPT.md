# 承富 AI 系統 · 外部審查請求 (v9.0)

> **第 21 輪審查 · 2026-04-22 晚間 · v1.0 → v1.1 純工程強化版收尾**
> **本輪重點:** v1.1 release ready 確認 · 不再找紅 · 找剩餘黃線 + 給 v1.2 sprint 排序建議
> **17 輪 Codex audit(R5 → R16)修了 50+ 紅黃 · R16 達成 0 紅 0 patch · §11.1 全 11 router 完成 · main.py 從 ~2400 → 730(縮 70%)**

---

## ⚠️ **在你下筆之前 · 強制讀這段**

前 20 輪 reviewer 平均重複指出 70% **我們已修過的項目**。
**若你的報告出現下列「已修 65 項」任一條 · 該項直接視為 0 分。**

### 🚫 已修 65 項 · 嚴禁再指為紅線

#### Round 1-12 修的 51 項(列在 v8.1 prompt git log)
全部仍有效 · 不重複列。

#### Round 13(B-9/10/11 抽出 + R13 修)6 項
| # | 項目 | commit |
|---|---|---|
| 52 | §11.1 B-9 routers/crm.py(174 行 · 7 endpoint) | `584ea0e` |
| 53 | §11.1 B-10 routers/projects.py(125 行 · 6 endpoint · handoff B2) | `584ea0e` |
| 54 | §11.1 B-11 routers/memory.py(99 行 · 1 endpoint · Haiku summarize) | `584ea0e` |
| 55 | R13#1 · CRM update_lead 4 bug(stage validation / 404 / oid / history only on real change) | `67c479c` |
| 56 | R13#2 · projects.py except Exception 太寬 → _project_oid helper | `67c479c` |
| 57 | R13#3 · memory.py anthropic ImportError → 503 | `67c479c` |

#### Round 14-16 收尾(本輪終極驗證)8 項
| # | 項目 | commit |
|---|---|---|
| 58 | R14#1 · projects.py PUT/DELETE 補 _project_oid + 404(R13#2 只修一半) | `2beb7d1` |
| 59 | R14#2 · crm.py delete_lead/add_lead_note 補 _lead_oid + 404 | `2beb7d1` |
| 60 | R14#7 · ROADMAP §11.1 文件更新(7 → 11 router 實際數字) | `2beb7d1` |
| 61 | R15 · accounting.py DELETE /transactions/{tx_id} 同 ObjectId 家族 bug | `2beb7d1` |
| 62 | RELEASE-NOTES-v1.1.md · 老闆 1 頁 v1.0 → v1.1 工程進展 | (本輪) |
| 63 | EXTERNAL-REVIEW-PROMPT v9.0 · 給 reviewer 看 17 輪 audit 全貌 | (本輪) |
| 64 | R16 終極驗證 · 0 紅 0 patch needed("現階段完美"達成) | n/a |
| 65 | §11.1 完整收官 · 11 router(原預估 5-6 · 超額)+ _deps.py 集中 helper | `c119317`-`2beb7d1` |

**所以本輪 reviewer 不要再說** 「routers 沒抽 / cookie 假修 / ObjectId 沒擋 / nginx 沒 gate / monthly-report 沒認證 / rate limit 假裝 / X-Agent-Num 可 spoof / projects PUT 沒驗 / CRM stage 沒 enum / accounting DELETE 沒護」—— **全部已 push**。

---

### ✅ 第 21 輪 reviewer 該做的事 · v1.2 sprint 排序

**v1.1 release ready · 0 紅 0 patch · 不再找紅。**
**本輪變成:**

1. **R14 留下 4 黃** · v1.2 sprint 該怎麼排序?
   - R14#3 · 31 處 lazy `from main import` 可改 `_deps.get_db()`(一致性債 · 非 correctness · 改動風險高)
   - R14#4 · `_next_invoice_no` / `_next_quote_no` 多 worker race(workers=2 同時 issue 同號 · 已知)
   - R14#5 · CRM `list_leads` 無 pagination · `crm_stats` full-scan in-memory(100 leads OK · 1000 慢)
   - R14#6 · `test_main.py` 997 行可拆 `tests/test_routers/test_*.py`
2. **多 worker quota gate 一致性** · 目前 `_AGENT_FORBIDDEN_CACHE` 跨 worker 用 sentinel doc · 但 `_USER_EMAIL_CACHE` 還是 each worker own · 60s TTL 是不是夠?
3. **routers/_auth.py 抽出可行性** · main.py 還能再縮到 ~530 行 · 但 SlowAPIMiddleware key_func 循環風險高 · 評估值不值得
4. **17 輪 audit 後 · 還有什麼盲點?** · 若你能找到第 18 輪沒人發現的紅線 · 你贏

**絕不做的事:**
- 不要再指「🚫 已修 65 項」
- 不要建議換框架 / 換 LibreChat / 加 k8s / 加 Redis
- 不要再說「該抽 router」(已 11 個 · 超額)
- 不要再說「ObjectId 沒擋」(全 4 router 都護過)
- 不要再說「routers 太多」(每檔 ~200 行 · 比原 2400 行單檔好維護)

---

## 🔗 0. 直接去讀

| 來源 | 位置 |
|---|---|
| **GitHub(public)** | <https://github.com/Sterio068/chengfu-ai> |
| **作者本機** | `/Users/sterio/Workspace/ChengFu` |
| **本機跑** | <http://localhost/> · <http://localhost/api-accounting/docs> |
| **commit 歷史** | `git log --oneline -50`(50+ commit · 21 輪審查) |
| **v1.0 → v1.1 範圍** | `git log --oneline cc47064..2beb7d1` 看 27 個 commit |

### 必讀 14 份(30 分鐘消化)

```
[v1.1 收尾文件](本輪重點)
1. docs/RELEASE-NOTES-v1.1.md           · 老闆 1 頁 v1.0 → v1.1 進展(本輪新)
2. docs/RELEASE-NOTES-v1.0.md           · 老闆 v1.0 簽收版(對比基準)
3. docs/EXTERNAL-REVIEW-PROMPT.md       · 你正在讀的(v9.0)

[完成的 §11.1 全 11 router]
4. backend/accounting/main.py           · 730 行(從 2400 縮 70%)
5. backend/accounting/routers/_deps.py  · 集中 helper(_serialize / get_db / 3 dep factory)
6. backend/accounting/routers/admin.py  · 563 行 · 13 endpoint
7. backend/accounting/routers/knowledge.py · 665 行 · 10 endpoint(最大)
8. backend/accounting/routers/accounting.py · 384 行 · 12 endpoint
9. backend/accounting/routers/{crm,projects,memory,design,feedback,users,tenders,safety}.py
   小 8 個 router · 共 ~770 行

[ROADMAP / DECISIONS]
10. docs/ROADMAP-v4.2.md §11.1          · 完整 11 router 列表 + 行數(本輪更新)
11. docs/DECISIONS.md                    · 12 項已決議

[基礎](Round 1-9 已過 · 不重審)
12. docs/PRE-DELIVERY-CHECKLIST.md       · Day -7 ~ Day +30
13. docs/DAY0-DRY-RUN.md                 · 9:00-17:00 現場腳本
14. backend/accounting/test_main.py      · 113 pytest + 2 skip
```

---

## 1. 客戶與專案(維持)

承富創意整合行銷 · 10 人 · 政府標案 / 公關 / 設計。
14 題老闆答覆未變(R10 prompt 已詳列)。

---

## 2. 技術棧(維持)

| 層 | 選擇 |
|---|---|
| 硬體 | Mac mini M4 24GB |
| AI Platform | LibreChat **v0.8.4 @sha256 pinned** |
| AI Model | Claude Opus 4.7 / Sonnet 4.6 / Haiku 4.5 |
| 後端 | FastAPI(`main.py` 730 + `routers/` 11 個 + `services/` 3 個) |
| 前端 | 原生 ES Modules · **無 build step** · 25 modules |
| 容器 | Docker Compose × 6 production · 5 image @sha256 pinned |
| Auth | refreshToken cookie + JWT_REFRESH_SECRET + ID lookup + LRU cache |
| 全文搜尋 | Meilisearch v1.12 + sentinel cache version(R10#2) |
| 抽字 | PyMuPDF + tesseract-chi-tra + python-docx/pptx/openpyxl/Pillow |

---

## 3. 當前狀態

### ✅ 程式碼:**100%**(R16 0 紅 0 patch · 史上最佳)

- 6 容器 healthy · accounting healthy
- **113 pytest pass + 2 skip · 8 smoke pass · 0 deprecation**
- **後端 endpoint:** ~75(11 router 分 + main.py /quota/* + /healthz)
- **routers/ 11 個** · 共 2619 行抽出
- **前端:** 25 個 ES modules
- **services/:** `admin_metrics.py` / `knowledge_extract.py` / `knowledge_indexer.py`
- **Cookie auth strategy:** refreshToken + JWT_REFRESH_SECRET + ID lookup + LRU cache · 跨 worker 用 sentinel doc invalidate
- **rate limit:** quota/preflight 60/min · admin/email/send 20/hour · 真套上 FastAPI route
- **nginx:** /api/ask auth_request gate 接 /quota/preflight · X-Agent-Num strip · X-User-Email LibreChat 區段 strip

### 🟡 部署落地:**45%**(維持 v1.0 數字)

- Mac mini 仍未上架
- Cloudflare Tunnel 仍未接
- knowledge-base/samples/ 仍空
- 10 帳號仍未建
- 2 場教育訓練仍未辦

### 📚 教材:**100%**

- 27 + 2 文件(本輪 RELEASE-NOTES-v1.1 + 本 prompt)

---

## 4. 我要你審什麼(本輪僅 §4.1-4.3)

### 4.1 R14 4 黃 · v1.2 sprint 該怎麼排?

**讀 4 個黃線描述 · 給 v1.2 sprint 排序(高 → 低 ROI):**

| # | 黃線 | 工時估 | 影響範圍 |
|---|---|---|---|
| R14#3 | 31 處 lazy import 改 _deps.get_db() | 4h | 4 router(accounting/crm/memory/projects)| 一致性 · 非 correctness |
| R14#4 | invoice/quote 多 worker race | 1d | 同時開 invoice 機率低 · 但發生會重號 · 加 atomic counter + 唯一 index |
| R14#5 | CRM list/stats 無 pagination | 4h | 100 leads OK · 1000 leads 慢 · 加 skip/limit + aggregation |
| R14#6 | test_main.py 997 行拆檔 | 6h | 測試可維護性 · 不影響 prod |

**輸出:** 排序 + 1 句理由 + 哪一個應該 v1.2 第 1 個做

### 4.2 多 worker cache 一致性審查

**現狀(workers=2):**
- `_AGENT_FORBIDDEN_CACHE` · 用 Mongo sentinel doc(R10#2 修)· 跨 worker 即時失效 ✅
- `_USER_EMAIL_CACHE` · OrderedDict LRU · 60s TTL · **each worker own** · admin 砍 user 後最多差 60s
- `_AGENT_NUM_FROM_CONVO_CACHE` · 同上 · 5min TTL · each worker own
- `_AGENT_FORBIDDEN_TTL` · 5min(被 sentinel 取代但仍存在 · dead code?)

**疑問:**
1. 60s TTL 對 LibreChat user delete 是否夠快?
2. 5min TTL 對 agent description 改名是否夠?(老闆很少改)
3. 該不該全部統一改 Mongo sentinel + version pattern?(R10#2 已示範)
4. _AGENT_FORBIDDEN_TTL 是 dead code · 該刪嗎?

### 4.3 routers/_auth.py 抽出可行性?

**現 main.py 730 行 · 可繼續抽:**
- `_verify_librechat_cookie` + `_lookup_user_email_cached` + `_USER_EMAIL_CACHE`(~70 行)
- `current_user_email` + `require_admin`(~50 行)
- `_user_or_ip` + `_secrets_equal` + `_is_prod` + `_legacy_auth_headers_enabled` + `_jwt_refresh_configured` + `_env_mode_configured`(~80 行)
- `_admin_allowlist` 設定(~5 行)

**抽出後:** main.py ~530 行(60% 從原 2400)
**循環風險:** _user_or_ip 給 SlowAPIMiddleware key_func 用 · `from main import _limiter` 必走 lazy
**收益 vs 成本:** 200 行 vs 11 router 都要改 import · 是否值得?

**輸出:** 該不該做 · 如果做 · 用什麼 pattern 避免循環?

---

## 5. 輸出要求

### 5.1 總論(150 字內)
1 句話評價 v1.1 release ready 程度 · 3 件 v1.2 sprint 該先做的事

### 5.2 §4.1-4.3 各出評分 + 1 個具體建議

```
審查項:4.1 / 4.2 / 4.3
評分:1-5 ⭐
v1.1 release ready 嗎:Y/N · 理由
最該補一件事:(file:line · 100 字內)
```

### 5.3 找到第 18 輪沒人發現的紅線(若有)
17 輪 audit 後仍找到的 · 你贏。

### 5.4 給作者的 3 個問題
下輪能更精準的話你想知道什麼?

---

## 6. 量化基準(本輪終極)

| 項目 | v8.1 (Round 12) | v9.0 (本輪 Round 21) | Δ |
|---|---|---|---|
| **GitHub commits** | 36 | **63** | +27(B-7/B-8/B-9-11/R13/R14/R15/v1.1 docs)|
| **pytest** | 100+2 | **113+2** | +13 |
| **smoke** | 8 | 8 | - |
| **main.py 行數** | 2270 | **730** | **-1540(-68%)** |
| **routers/ 抽出** | 5 | **11** | +6(admin/accounting/crm/projects/memory/knowledge)|
| **routers 總行數** | 545 | **2619** | +2074(從 main.py 搬)|
| **services/** | 3 | 3 | - |
| **後端 endpoint** | ~56 | ~75 | +19(本輪沒新增 · 重組)|
| **後端依賴** | 17 | 17 | - |
| **文件** | 27 | **29** | +2(RELEASE-NOTES-v1.1 + v9.0 prompt)|
| **Image @sha256 pinned** | 5 | 5 | - |
| **Cookie auth + nginx gate** | R7+R8 完成 | 同 | - |
| **legacy header gate** | env-driven | 同 | - |
| **ObjectId defense 全覆蓋** | 部分 | **全 4 router(projects/crm/accounting + main collections)** | 終極補完 |
| **Codex 全綠 audit 數** | R12 1 次 | **R12 + R16 共 2 次** | +1 |
| **意外驗證** | R7#1 LibreChat session.ts | **R14 收尾找 4 router 同家族 ObjectId bug · R15 找最後 1 處 · R16 0 紅** | "現階段完美" |
| **部署落地完成度** | 45% | 45% | - |

---

## 7. 最後提醒

- 這系統**已跑** · 6 production + 6 sandbox compose · 113 pytest pass · R16 0 紅
- Sterio 懂技術 · **承富內部人不懂** · 任何「只有 Sterio 能維護」= 技術債
- 已 21 輪審查 · **重複指 Section「🚫 已修 65 項」會被作者直接刪掉**
- 老闆要**省時 + 接案量** · 不是工程藝術
- v1.1 是純工程強化 · 不影響 v1.0 Day 0 部署 SOP
- **本輪 reviewer 請只審 §4.1-4.3 v1.2 sprint 排序 · 不再提工程改動(已 R16 0 紅)**

**直接開始審 §4 · 不用先確認。**
