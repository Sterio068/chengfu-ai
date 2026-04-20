# LibreChat 升版 Checklist

> 當要從 LibreChat v0.8.4 升到新版(v0.8.5+ / v0.9+)時 · 照這份跑完再動。
> 目的:承富的 Route A + create-agents.py + SSE 串流依賴 LibreChat 內部行為,
>       升版可能 breaking · 這份 checklist 幫你在升版前後雙跑驗證。

---

## 📋 升版前(舊版基準快照)

### 0. 先 dump agents collection(確保 _id 在升版後沒被重建)
```bash
docker exec chengfu-mongo mongodump --db chengfu --collection agents \
    --archive=/tmp/agents-before.archive
docker cp chengfu-mongo:/tmp/agents-before.archive /tmp/
docker exec chengfu-mongo mongosh chengfu --quiet --eval \
    'JSON.stringify(db.agents.find({}, {_id:1, name:1}).toArray(), null, 2)' > /tmp/agents-before.json
cat /tmp/agents-before.json | head -20
```

### 1. 在舊版跑 smoke · 存基準
```bash
./scripts/smoke-librechat.sh > /tmp/smoke-before.log
cat /tmp/smoke-before.log  # 確認全 pass
```

### 2. 在舊版錄一次 SSE payload 供對比
```bash
# 登入取 token
TOKEN=$(curl -s -X POST http://localhost/api/auth/login \
  -H 'Content-Type: application/json' \
  -H 'User-Agent: Mozilla/5.0 Chrome/131' \
  -d '{"email":"sterio068@gmail.com","password":"<pwd>"}' \
  | python3 -c 'import sys,json;print(json.load(sys.stdin)["token"])')

AGENT_ID=$(curl -s http://localhost/api/agents \
  -H "Authorization: Bearer $TOKEN" \
  -H 'User-Agent: Mozilla/5.0 Chrome/131' \
  | python3 -c 'import sys,json;d=json.load(sys.stdin);print((d if isinstance(d,list) else d["data"])[0]["id"])')

# 錄 SSE 訊息 (5 秒取樣)
timeout 5 curl -N -X POST http://localhost/api/ask/agents \
  -H "Authorization: Bearer $TOKEN" \
  -H 'Content-Type: application/json' \
  -H 'User-Agent: Mozilla/5.0 Chrome/131' \
  -d "{\"agent_id\":\"$AGENT_ID\",\"conversationId\":\"new\",\"parentMessageId\":\"00000000-0000-0000-0000-000000000000\",\"text\":\"一句話介紹你自己\",\"endpoint\":\"agents\",\"messageId\":\"test-$(date +%s)\"}" \
  > /tmp/sse-before.jsonl 2>&1

head -20 /tmp/sse-before.jsonl  # 確認有 data: 事件
```

### 3. 備份 MongoDB
```bash
./scripts/backup.sh
```

---

## 🚀 升版執行

### 1. 改 pin 版本
```yaml
# config-templates/docker-compose.yml
librechat:
  image: ghcr.io/danny-avila/librechat:v0.8.5   # ← 改這行
```

### 2. Pull + up
```bash
cd config-templates
docker compose pull librechat
docker compose up -d librechat
sleep 30  # 等 startup
docker logs chengfu-librechat --tail 50
```

### 3. 確認服務 healthy
```bash
docker compose ps
curl -sI http://localhost/api/config  # 應 200
```

---

## ✅ 升版後(逐項驗 · 紅字 fail 就回滾)

### 1. smoke test 再跑
```bash
./scripts/smoke-librechat.sh > /tmp/smoke-after.log
diff /tmp/smoke-before.log /tmp/smoke-after.log
```
**預期:** 僅時間戳 / hostname 差異 · 全 pass。
**若 fail:** 哪條失敗就是 contract 被打破,見下方 troubleshoot。

### 2. uaParser 行為(`create-agents.py` 依賴)
```bash
# 無 User-Agent 應被擋
curl -s -X POST http://localhost/api/auth/login \
  -H 'Content-Type: application/json' \
  -d '{"email":"x@x.com","password":"xxxxxxxx"}' \
  | grep -q "Illegal request" && echo "✓ 仍靠 UA 擋" || echo "⚠ UA 擋法改變"

# 有瀏覽器 UA 應放行
curl -s -X POST http://localhost/api/auth/login \
  -H 'Content-Type: application/json' \
  -H 'User-Agent: Mozilla/5.0 Chrome/131' \
  -d '{"email":"nobody@x.com","password":"wrongpass"}' \
  | grep -qE "Email does not exist|Incorrect password" && echo "✓ UA 放行" || echo "⚠ UA 策略改變"
```

### 3. Agent 建立 API 仍可用
```bash
# dry-run 確認 payload schema 還相容
python3 scripts/create-agents.py --dry-run --tier core
```
若新版 agentCreateSchema 新增必填欄位,會出現 zod 驗證錯誤。

### 4. SSE 串流格式沒變
```bash
# 錄新版 SSE 與舊版比對
TOKEN=...  # 同上
timeout 5 curl -N -X POST http://localhost/api/ask/agents \
  -H "Authorization: Bearer $TOKEN" \
  ...(同上)... > /tmp/sse-after.jsonl

# 對比 event 類型
grep -o '"type":"[^"]*"' /tmp/sse-before.jsonl | sort -u > /tmp/types-before
grep -o '"type":"[^"]*"' /tmp/sse-after.jsonl | sort -u > /tmp/types-after
diff /tmp/types-before /tmp/types-after
```
**預期:** 一致。
**若不同:** chat.js 的 SSE parser 需更新(見 `modules/chat.js` 的 `_stream()`)。

### 5a. Agent `_id` 穩定性(關鍵 · 若 `modelSpecs` 已 hard-pin id)
```bash
# 升版後再 dump 一次
docker exec chengfu-mongo mongosh chengfu --quiet --eval \
    'JSON.stringify(db.agents.find({}, {_id:1, name:1}).toArray(), null, 2)' > /tmp/agents-after.json
diff /tmp/agents-before.json /tmp/agents-after.json
```
**預期:** 無差異(或僅 field 順序)。
**若 _id 變了:** 所有指向 agent_id 的設定(launcher、modelSpecs、外部 bookmark)都要更新。此時要從 `/tmp/agents-before.archive` 還原舊 _id,或重新 POST create-agents.py 並手動把新 id 寫回設定。

### 5. projectIds 共享機制仍有效
```bash
docker exec chengfu-mongo mongosh chengfu --quiet --eval '
  const i = db.projects.findOne({name:"instance"})._id;
  const n = db.agents.countDocuments({projectIds: i});
  print(`共享 agents: ${n}`);
'
```
**預期:** 非零(應該 = 已建 Agent 總數)。
**若為 0:** LibreChat 可能改變 projectIds 語義,需重新 patch。

### 6. Launcher 端對話功能
手動 smoke:
- [ ] 瀏覽器開 <http://localhost/> · Login 成功
- [ ] 首頁 5 個工作區卡片顯示
- [ ] 按 ⌘1 打開投標助手對話
- [ ] 送一句訊息 · 有 SSE 串流回應
- [ ] 訊息下方 👍 / 👎 按鈕固定顯示
- [ ] 點 ⌘K palette · 可搜 Agent / 專案

---

## 🔴 Troubleshoot · 已知破綻

| 症狀 | 最可能原因 | 處理 |
|---|---|---|
| `/c/new` 不再 302 | nginx `location = /c/new` 被 LibreChat route 覆蓋 | 強制 `location = /c/new` in nginx |
| `create-agents.py` 回 `Illegal request` | uaParser 換了檢查邏輯 | 檢查 `/app/api/server/middleware/` · 更新 UA string |
| SSE event type 改變 (`delta.content` → 別名) | LibreChat SSE schema 升級 | 更新 `modules/chat.js _stream()` switch case |
| Agent POST body reject | `agentCreateSchema` 多必填欄位 | 看 `/app/packages/api/src/agents/validation.ts` · 補欄位 |
| projectIds 無效 | `checkGlobalAgentShare` 改用別 key | 看 `/app/api/server/controllers/agents/*.js` |
| Login 直接跳 `/api/auth/2fa` | 新版強制 2FA | env 加 `ALLOW_2FA_BYPASS` 或建 2FA 流程 |

---

## 📦 回滾流程(若升版後 smoke 大量 fail)

```bash
# 1. 改回舊版 image
sed -i 's|librechat:v0.8.5|librechat:v0.8.4|' config-templates/docker-compose.yml

# 2. Restart
docker compose -f config-templates/docker-compose.yml up -d --force-recreate librechat

# 3. 確認 · 再跑 smoke
./scripts/smoke-librechat.sh

# 4. 還原 MongoDB (若 schema 有改動)
# docker exec chengfu-mongo mongorestore ...
```

---

## 📌 版本決策紀錄

- **v0.8.4 (2026-03-20)** · 目前 pin 版本 · `projectIds` + `uaParser` + `SSE delta.content` 行為已驗
- **v0.8.5-rc1 (2026-04-10)** · pre-release · **不建議交付前追上**
- **v0.8.5 正式版** · 釋出後先在 sandbox 跑 checklist · 確認 pass 再推正式

---

## 🧪 自動化(選配)

CI 可每日跑 smoke 對 production URL,若失敗 PagerDuty/Slack 通知:

```yaml
# .github/workflows/smoke-daily.yml
name: LibreChat contract smoke
on:
  schedule: [{ cron: "0 9 * * *" }]  # 每天 9am UTC
jobs:
  smoke:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: ./scripts/smoke-librechat.sh --base ${{ secrets.PROD_URL }}
```
