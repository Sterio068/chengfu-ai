"""
ROADMAP §11.1 · routers/ · main.py 拆解後的 domain 模組

每個 router 獨立 file · main.py 用 app.include_router(...) 串起來
共用依賴在 _deps.py + _db.py(避免循環 import)

拆解順序(由小到大):
1. safety.py     · L3 classifier (50 行)
2. feedback.py   · 👍👎 + stats
3. users.py      · preferences
4. tenders.py    · g0v alerts
5. design.py     · Fal Recraft
6. knowledge.py  · multi-source KB
7. admin.py      · /admin/*

保留在 main.py:
- App init / lifespan / middleware / CORS
- accounts / transactions / invoices / quotes(會計核心 · 強耦合 _account_type_map)
- projects / handoff(專案核心)
- crm(domain 重 · v1.2 才拆)
- /healthz / /safety
- orchestrator router include
"""
