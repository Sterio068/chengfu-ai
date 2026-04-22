"""
ROADMAP §11.1 · routers/ · main.py 拆解後的 domain 模組

每個 router 獨立 file · main.py 用 app.include_router(...) 串起來
v1.1 已抽 5 個 router · v1.2 補 knowledge + admin

進度(2026-04-22):
✅ 1. safety.py     · L3 classifier (56 行 · commit c119317)
✅ 2. feedback.py   · 👍👎 + stats (82 行 · commit 99308f3)
✅ 3. users.py      · preferences (80 行 · commit 309e104)
✅ 4. tenders.py    · g0v alerts (59 行 · commit 4b82533)
✅ 5. design.py     · Fal Recraft + history (226 行 · commit c9e572e)
🟡 6. knowledge.py  · 留 v1.2(600 行 · 10 endpoint · 跨 helper 多)
🟡 7. admin.py      · 留 v1.2(700 行 · dashboard/cost/adoption/audit/agent-prompts)

main.py 行數變化:
- 拆前:2400 行
- 拆 5 router 後:2192 行(-208)
- 預估全拆完:< 600 行(目標 v1.2)

保留在 main.py:
- App init / lifespan / middleware / CORS / SlowAPI
- accounts / transactions / invoices / quotes(會計核心 · 強耦合 _account_type_map)
- projects / handoff(專案核心)
- crm(domain 重 · v1.2 拆)
- knowledge / admin(待 v1.2 拆 · 跨 helper 過多)
- /healthz / context summary / orchestrator router include

為什麼 knowledge / admin 留 v1.2:
- knowledge 含 _AGENT_FORBIDDEN_CACHE + _invalidate_sources_cache + _validate_source_path
  + _path_is_excluded · 全是 module-level state · 抽分散容易 race
- admin 含 dashboard / monthly-report / cost / adoption / sources / audit-log / agent-prompts
  · 多 endpoint 互相依賴 · 一次抽全 200+ change 風險高
- 兩個都應該配合「_deps.py + _db.py 共用基礎」一起做 · 列為 v1.2 第 1 個 sprint
- 詳細 step-by-step · 見 docs/REFACTOR-PLAN-§11.1.md
"""
