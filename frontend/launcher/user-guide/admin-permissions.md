# 🔐 Admin vs 一般同事 · 權限對照表

> v1.3.0 · 誰能看 / 操作什麼 · 權限邊界一覽

---

## 一句話原則

- **一般同事**:只能看 / 改 **自己的** 對話 / project / 場勘 / 會議
- **Admin**:可看 / 操作 **所有人**(離職資料刪除 / 用量 / 預算 / 系統設定)
- **匿名(沒登入)**:除 `/healthz` 外全擋

Admin 從哪定:`config-templates/.env` 的 `ADMIN_EMAIL=` · 多人逗號分隔

---

## 完整對照表

| 功能 | 匿名 | 一般同事 | Admin |
|---|---|---|---|
| **登入頁** | ✅ | ✅ | ✅ |
| **Launcher 首頁(dashboard)** | ❌ 401 | ✅ 看自己 | ✅ 看自己 + admin badge |
| **5 Workspace + Agent 對話** | ❌ | ✅ | ✅ |
| **Project CRUD(自己的)** | ❌ | ✅ | ✅ |
| **Project handoff 4 格卡** | ❌ | ✅ 改自己 | ✅ 改任何人 |
| **CRM 商機(自己 owner)** | ❌ | ✅ | ✅ |
| **CRM 商機(別人 owner)** | ❌ | 👀 看 · 不能改 | ✅ 全可改 |
| **會議速記上傳 + 看自己** | ❌ | ✅ | ✅ |
| **會議速記看別人** | ❌ | ❌ 403 | ✅ |
| **媒體 CRM 列表** | ❌ | ✅(phone 遮) | ✅(phone 顯) |
| **媒體 CRM 編輯 / 推薦 / 匯出 CSV** | ❌ | ❌ | ✅ |
| **場勘 PWA 拍照 + 看自己** | ❌ | ✅ | ✅ |
| **場勘看別人** | ❌ | ❌ 403 | ✅ |
| **場勘 audio_note(只 owner)** | ❌ | ✅ 自己的 survey | ✅ 任何 survey |
| **社群排程貼文(自己 author)** | ❌ | ✅ | ✅ |
| **社群排程看別人** | ❌ | ❌ | ✅ |
| **社群 OAuth 連 FB/IG/LinkedIn** | ❌ | ✅ 連自己 | ✅ |
| **社群 OAuth status(誰連了什麼)** | ❌ | ❌ | ✅ |
| **知識庫搜 / 讀** | ❌ | ✅ | ✅ |
| **知識庫管理(/admin/sources)** | ❌ | ❌ | ✅ |
| **回饋 👍👎** | ❌ | ✅ | ✅ |
| **回饋 stats** | ❌ | ❌ | ✅ |
| **設計助手生圖** | ❌ | ✅(用自己 quota) | ✅ |
| **設計助手 history** | ❌ | ✅ 自己 | ✅ |
| **/healthz** | ✅ | ✅ | ✅ |

---

## 🔴 Admin 專屬(同事看不到此選單)

| 功能 | endpoint | 用途 |
|---|---|---|
| **儀表板** | /admin/dashboard | 總覽 KPI |
| **本月成本** | /admin/cost | Anthropic + Whisper |
| **預算進度** | /admin/budget-status | 80% 警告線 |
| **用量 Top 10** | /admin/top-users | 誰花最多 |
| **採納率** | /admin/adoption | 同事真用沒 |
| **標案漏斗** | /admin/tender-funnel | 進入 → 提案 → 得標 |
| **LibreChat schema 驗** | /admin/librechat-contract | 升版後跑 |
| **匯出全資料** | /admin/export | 跨機遷移 |
| **匯入** | /admin/import | append 模式 |
| **demo 資料清** | DELETE /admin/demo-data | 上線前必跑 |
| **OCR 重 probe** | /admin/ocr/reprobe | tesseract 沒裝補 |
| **audit log 查** | /admin/audit-log | 維運看誰做了什麼 |
| **audit actions 列表** | /admin/audit-log/actions | dropdown 用 |
| **email 寄(rate limit)** | POST /admin/email/send | 月報外發 |
| **月報生成** | /admin/monthly-report | PDF 老闆看 |
| **Agent prompt 線上調** | /admin/agent-prompts | 不用改 JSON |
| **secret 管理** | /admin/secrets/* | FAL_API_KEY 等 |
| **PDPA delete-all(離職)** | POST /admin/users/{email}/delete-all | 跨 20+ collection 清 |
| **cron 跑紀錄** | /admin/cron-runs | 昨天 digest 有跑? |
| **社群 OAuth status** | /admin/social/oauth/status | 誰連了哪 platform |
| **社群 cron run-queue** | /admin/social/run-queue | 手動觸發發文 |
| **知識庫管理** | /admin/sources/* | CRUD source + reindex |

---

## 怎麼判斷自己是不是 admin?

打開 launcher · 看左上角:
- 🟢 admin · 名字旁邊有 `[admin]` badge · sidebar 多「📊 管理面板」
- 🟡 一般同事 · 沒 badge · sidebar 沒管理面板

或 console 跑:
```js
console.log(document.documentElement.dataset.role)
// "admin" 或 undefined
```

---

## 一般同事看到「權限不足」怎麼辦?

UI 不該顯示 admin 功能給你 · 若意外點到回 403:
1. 確認你的角色(看左上角)
2. 真要做 → 找 Champion / Sterio
3. 別 hack(不會給你過)

---

## Admin 升降權怎麼做?

**升新 admin**:
- Sterio 改 `config-templates/.env` ADMIN_EMAIL 加新 email
- `./scripts/start.sh` 重啟 accounting · 立即生效
- 該 user 重新整理 launcher · 看到管理面板

**降 admin**:
- 同上 · 移除 email
- 該 user 下次 request 即失去 admin 權

**完全移除帳號(離職)**:
- 走 `docs/05-SECURITY.md §5.4` 完整 SOP
- 含 LibreChat disable + Cloudflare 移白 + PDPA delete-all

---

## 安全護欄

- **admin 不能刪自己**(防 lockout · `[E-209]`)
- **PDPA delete 必 confirm_email 完整 type**(防 mis-click)
- **內部 token 只給 cron**(`X-Internal-Token` 跨 service)· user 不該知道
- **Webhook URL 必 https + 拒內網 IP**(R27#4 SSRF guard)
