#!/usr/bin/env python3
"""
v2.0-β · 把 knowledge-base/skills/*.md 全 ingest 到 vector index

用法:
  ECC_INTERNAL_TOKEN=xxx python3 scripts/ingest-skills-to-vector.py
  · 增量(同 hash skip)· 重跑安全
  · 也適合丟 cron(每天 02:00)
"""
import json, os, pathlib, urllib.request, urllib.error

BASE = os.environ.get("COMPANY_AI_BACKEND_URL", "http://localhost:80/api-accounting")
TOKEN = os.environ.get("ECC_INTERNAL_TOKEN")
ADMIN = os.environ.get("COMPANY_AI_ADMIN_EMAIL", "sterio068@gmail.com")
SKILLS_DIR = pathlib.Path("knowledge-base/skills")
COMPANY_DIR = pathlib.Path("knowledge-base/company")

if not TOKEN:
    raise SystemExit("ECC_INTERNAL_TOKEN 必填")

def post_index(source_id: str, text: str):
    body = json.dumps({"source_id": source_id, "text": text}).encode()
    req = urllib.request.Request(
        f"{BASE}/vector-rag/index",
        data=body,
        method="POST",
        headers={
            "Content-Type": "application/json",
            "X-Internal-Token": TOKEN,
            "X-User-Email": ADMIN,
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            return json.loads(r.read().decode())
    except urllib.error.HTTPError as e:
        return {"status": "error", "code": e.code, "body": e.read().decode()[:200]}

count = {"indexed": 0, "skipped": 0, "error": 0}
for d in [SKILLS_DIR, COMPANY_DIR]:
    if not d.exists(): continue
    for path in sorted(d.glob("*.md")):
        text = path.read_text()
        source_id = f"{d.name}/{path.stem}"
        r = post_index(source_id, text)
        s = r.get("status", "error")
        count[s] = count.get(s, 0) + 1
        mark = {"indexed": "✓", "skipped": "—", "error": "✗"}.get(s, "?")
        print(f"  {mark} {source_id}: {r.get('reason') or r.get('vector_dim') or r.get('body','')}")

print(f"\n--- ✓ {count['indexed']}  — {count['skipped']}  ✗ {count['error']} ---")
