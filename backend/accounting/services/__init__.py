"""
承富 AI · services · pure business logic · 不直接定義 FastAPI endpoint

設計原則(Round 8 reviewer + 作者決策):
- 拆 service 不是拆 router · FastAPI 註冊點仍只有 main.py 一個
- service 只接 db / collection / settings 參數 · 不 import main
- test_main.py endpoint integration 測試保留 · 額外在 tests/ 加 unit test
"""
