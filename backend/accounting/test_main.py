"""
承富會計 + 統一後端 · 基礎測試
==================================
執行:
  cd backend/accounting
  pip install pytest mongomock fastapi httpx
  pytest test_main.py -v

或在 docker 環境:
  docker exec chengfu-accounting pytest /app/test_main.py -v
"""
import os
import pytest
from fastapi.testclient import TestClient
import mongomock
from unittest.mock import patch

# 用 mongomock 隔離真實 MongoDB(這個測試可在任何環境跑)
@pytest.fixture(scope="module")
def client():
    with patch("pymongo.MongoClient", mongomock.MongoClient):
        import importlib
        import main
        importlib.reload(main)
        c = TestClient(main.app)
        # 觸發 startup
        c.get("/healthz")
        yield c


# ============================================================
# A · 會計核心
# ============================================================
def test_health(client):
    r = client.get("/healthz")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


def test_seed_accounts(client):
    r = client.post("/accounts/seed")
    assert r.status_code == 200
    assert r.json()["total"] >= 20  # 台灣預設 25 個科目


def test_list_accounts(client):
    client.post("/accounts/seed")
    r = client.get("/accounts")
    assert r.status_code == 200
    data = r.json()
    assert len(data) >= 20
    # 必含常用科目
    codes = [a["code"] for a in data]
    assert "1102" in codes  # 銀行存款
    assert "4111" in codes  # 服務收入
    assert "5101" in codes  # 外包支出


def test_create_transaction(client):
    client.post("/accounts/seed")
    r = client.post("/transactions", json={
        "date": "2026-04-19",
        "memo": "測試:收環保局案期中款",
        "debit_account": "1102",
        "credit_account": "4111",
        "amount": 300000,
        "project_id": "proj_test",
        "customer": "環保局",
    })
    assert r.status_code == 200
    assert "id" in r.json()


def test_create_invoice(client):
    r = client.post("/invoices", json={
        "date": "2026-04-19",
        "customer": "環保局",
        "items": [
            {"description": "期中服務費", "quantity": 1, "unit_price": 300000}
        ],
        "tax_included": False,
    })
    assert r.status_code == 200
    body = r.json()
    assert body["invoice_no"].startswith("INV-26-")
    assert body["total"] == 315000  # 300000 × 1.05


def test_create_quote(client):
    r = client.post("/quotes", json={
        "date": "2026-04-19",
        "customer": "文化局",
        "items": [
            {"description": "活動策劃", "quantity": 1, "unit_price": 500000}
        ],
        "valid_until": "2026-05-19",
    })
    assert r.status_code == 200
    assert r.json()["quote_no"].startswith("Q-26-")


def test_pnl_report(client):
    r = client.get("/reports/pnl?date_from=2026-04-01&date_to=2026-04-30")
    assert r.status_code == 200
    body = r.json()
    assert "total_income" in body
    assert "total_expense" in body
    assert "net_profit" in body


# ============================================================
# B · 專案管理(取代 localStorage)
# ============================================================
def test_create_project(client):
    r = client.post("/projects", json={
        "name": "2026 環保局海洋案",
        "client": "環境部環境管理署",
        "budget": 3800000,
        "deadline": "2026-10-31",
        "status": "active",
    })
    assert r.status_code == 200


def test_list_projects(client):
    r = client.get("/projects")
    assert r.status_code == 200
    assert isinstance(r.json(), list)


def test_handoff_card_roundtrip(client):
    """B2 · Handoff 4 格卡 · 存 + 取 + 預設值"""
    # 建一個 project
    r = client.post("/projects", json={"name": "handoff test proj"})
    pid = r.json()["id"]

    # 初始 handoff 應該是空
    r = client.get(f"/projects/{pid}/handoff")
    assert r.status_code == 200
    body = r.json()
    assert body["project_name"] == "handoff test proj"
    assert body["handoff"] == {} or body["handoff"].get("goal", "") == ""

    # 存卡
    card = {
        "goal": "中秋節社群活動主視覺",
        "constraints": ["品牌色橘黃", "預算 5 萬", "3 天內"],
        "asset_refs": [
            {"type": "nas", "label": "客戶舊包裝", "ref": "/Volumes/NAS/x/"},
            {"type": "url", "label": "競品參考", "ref": "https://example.com"},
        ],
        "next_actions": ["設計師產 3 方向 · 週四前", "PM 排與客戶提案會議"],
    }
    r = client.put(
        f"/projects/{pid}/handoff",
        json=card,
        headers={"X-User-Email": "pm@chengfu.local"},
    )
    assert r.status_code == 200
    assert r.json()["ok"] is True

    # 取回來必一致
    r = client.get(f"/projects/{pid}/handoff")
    h = r.json()["handoff"]
    assert h["goal"] == "中秋節社群活動主視覺"
    assert len(h["constraints"]) == 3
    assert len(h["asset_refs"]) == 2
    assert h["asset_refs"][0]["type"] == "nas"
    assert h["updated_by"] == "pm@chengfu.local"
    assert "updated_at" in h


def test_handoff_card_project_not_found(client):
    """送到不存在的 id · 回 404"""
    fake_id = "6070" + "0" * 20  # 24 hex chars · 但無此 doc
    r = client.put(
        f"/projects/{fake_id}/handoff",
        json={"goal": "x"},
    )
    assert r.status_code == 404


def test_handoff_card_bad_project_id(client):
    """非 ObjectId 格式 · 回 400"""
    r = client.put("/projects/not-an-objectid/handoff", json={"goal": "x"})
    assert r.status_code == 400


# ============================================================
# C · 回饋收集
# ============================================================
def test_create_feedback(client):
    r = client.post("/feedback", json={
        "message_id": "msg_001",
        "agent_name": "🎯 投標顧問",
        "verdict": "up",
        "note": "建議書結構很清楚",
        "user_email": "test@chengfu.local",
    })
    assert r.status_code == 200


def test_feedback_stats(client):
    client.post("/feedback", json={"message_id": "m2", "agent_name": "A", "verdict": "up"})
    client.post("/feedback", json={"message_id": "m3", "agent_name": "A", "verdict": "down"})
    r = client.get("/feedback/stats")
    assert r.status_code == 200


# ============================================================
# D · 管理 Dashboard
# ============================================================
def test_admin_dashboard_requires_admin(client):
    """沒帶 X-User-Email → 403。驗證 RBAC 生效。"""
    r = client.get("/admin/dashboard")
    assert r.status_code == 403


def test_admin_dashboard_with_admin(client):
    """白名單 admin email → 200。"""
    r = client.get(
        "/admin/dashboard",
        headers={"X-User-Email": "sterio068@gmail.com"},
    )
    assert r.status_code == 200
    body = r.json()
    assert "accounting" in body
    assert "projects" in body
    assert "feedback" in body
    assert "conversations" in body


def test_admin_dashboard_rejects_non_admin(client):
    """非白名單 email → 403。"""
    r = client.get(
        "/admin/dashboard",
        headers={"X-User-Email": "random-staff@chengfu.local"},
    )
    assert r.status_code == 403


# ============================================================
# E · Level 03 classifier
# ============================================================
def test_l3_classifier_safe_content(client):
    r = client.post("/safety/classify", json={"text": "寫一則中秋節的祝賀訊息"})
    assert r.status_code == 200
    assert r.json()["level"] == "01"


def test_l3_classifier_detects_selection(client):
    r = client.post("/safety/classify", json={
        "text": "幫我分析這次選情,下次候選人策略要怎麼定"
    })
    assert r.status_code == 200
    assert r.json()["level"] == "03"
    assert len(r.json()["triggers"]) > 0


def test_l3_classifier_detects_phone(client):
    r = client.post("/safety/classify", json={
        "text": "客戶電話 0912345678 要 call"
    })
    assert r.status_code == 200
    assert r.json()["level"] == "03"


def test_l3_classifier_detects_unit_internal(client):
    r = client.post("/safety/classify", json={
        "text": "這個是未公告標案,評審名單我還沒查"
    })
    assert r.status_code == 200
    assert r.json()["level"] == "03"
