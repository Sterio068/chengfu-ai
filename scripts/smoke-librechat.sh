#!/bin/bash
# ========================================
#  承富 AI · LibreChat 契約 smoke test
#  ========================================
#  驗證 Route A 所依賴的 nginx 路由 + LibreChat API 行為在升版前後一致。
#
#  何時跑:
#    - LibreChat 升版前(驗舊版基準)
#    - 升版後(驗新版沒 breaking change)
#    - CI(每次 push · fast smoke)
#
#  用法:
#    ./scripts/smoke-librechat.sh
#    ./scripts/smoke-librechat.sh --base https://ai.chengfu.com  # 對遠端
# ========================================
set -uo pipefail
BASE="${1:-http://localhost}"
if [[ "${1:-}" == "--base" && -n "${2:-}" ]]; then BASE="$2"; fi

UA="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 Chrome/131.0.0.0"
PASS=0; FAIL=0
log_pass() { echo "  ✅ $1"; PASS=$((PASS+1)); }
log_fail() { echo "  ❌ $1"; FAIL=$((FAIL+1)); }

expect_status() {
    # expect_status NAME URL EXPECTED [METHOD] [EXTRA_CURL_ARGS]
    local name="$1" url="$2" expected="$3" method="${4:-GET}"
    shift 4 2>/dev/null || shift 3
    local actual
    actual=$(curl -sI -X "$method" -H "User-Agent: $UA" "$@" -o /dev/null -w "%{http_code}" "$BASE$url")
    if [[ "$actual" == "$expected" ]]; then
        log_pass "$name · $url → $actual"
    else
        log_fail "$name · $url → $actual (expected $expected)"
    fi
}

echo "============================================"
echo "  Route A 契約 smoke test · $BASE"
echo "============================================"

echo "[1] Launcher 入口 · 必須是承富 Launcher 不是 LibreChat"
expect_status "launcher root"          "/"           "200"
expect_status "kill-sw.js"             "/sw.js"      "200"
expect_status "launcher.css"           "/static/launcher.css" "200"
expect_status "app.js module"          "/static/app.js"       "200"

echo ""
echo "[2] LibreChat SPA 路徑必被 302 轉回 Launcher(Route A)"
redir=$(curl -sI -H "User-Agent: $UA" -o /dev/null -w "%{http_code}|%{redirect_url}" "$BASE/c/new")
if echo "$redir" | grep -q "^302"; then
    log_pass "/c/new → 302 to launcher"
else
    log_fail "/c/new expected 302, got: $redir"
fi

echo ""
echo "[3] LibreChat API 仍可達(nginx 代理)"
expect_status "config"                "/api/config"     "200"
expect_status "healthz"               "/healthz"        "200"
expect_status "accounting healthz"    "/api-accounting/healthz" "200"

echo ""
echo "[4] 認證:無 token 訪問受保護 API 應回 401"
expect_status "agents (no auth)"      "/api/agents"     "401"

echo ""
echo "[5] uaParser 不再擋非瀏覽器 UA(只要 User-Agent 有 Chrome/Mozilla)"
# 先登入取 JWT
login_resp=$(curl -s -X POST "$BASE/api/auth/login" \
    -H "Content-Type: application/json" \
    -H "User-Agent: $UA" \
    -d '{"email":"nobody@smoke.test","password":"wrongpassword123"}' || true)
if echo "$login_resp" | grep -qE "Email does not exist|Incorrect password"; then
    log_pass "uaParser 放行瀏覽器 UA (得到 login error 而非 Illegal request)"
elif echo "$login_resp" | grep -q "Illegal request"; then
    log_fail "uaParser 擋掉 · LibreChat 升版可能改了 UA 檢查邏輯 · 見 create-agents.py"
else
    log_fail "login response unexpected: $login_resp"
fi

echo ""
echo "[6] 自訂 CSS/JS 注入 (nginx sub_filter)"
if curl -s -H "User-Agent: $UA" "$BASE/login" | grep -q "librechat-relabel.js"; then
    log_pass "relabel.js injected to /login"
else
    log_fail "relabel.js missing in /login"
fi

echo ""
echo "[7] SSE contract · /api/ask/agents(需 admin credentials · 可 skip)"
if [[ -n "${SMOKE_ADMIN_EMAIL:-}" && -n "${SMOKE_ADMIN_PASSWORD:-}" ]]; then
    TOKEN=$(curl -s -X POST "$BASE/api/auth/login" \
        -H "Content-Type: application/json" -H "User-Agent: $UA" \
        -d "{\"email\":\"$SMOKE_ADMIN_EMAIL\",\"password\":\"$SMOKE_ADMIN_PASSWORD\"}" \
        | python3 -c 'import sys,json;print(json.load(sys.stdin).get("token",""))' 2>/dev/null)
    if [[ -z "$TOKEN" ]]; then
        log_fail "登入取 token 失敗(密碼錯?)"
    else
        AGENT_ID=$(curl -s "$BASE/api/agents" \
            -H "Authorization: Bearer $TOKEN" -H "User-Agent: $UA" \
            | python3 -c 'import sys,json;d=json.load(sys.stdin);a=d if isinstance(d,list) else d.get("data",[]);print(a[0]["id"] if a else "")' 2>/dev/null)
        if [[ -z "$AGENT_ID" ]]; then
            log_fail "無 Agent · 請先跑 create-agents.py"
        else
            # SSE 取 3 秒樣本 · 看有沒有 data: 事件
            SSE=$(timeout 5 curl -sN -X POST "$BASE/api/ask/agents" \
                -H "Authorization: Bearer $TOKEN" -H "User-Agent: $UA" \
                -H "Content-Type: application/json" \
                -d "{\"agent_id\":\"$AGENT_ID\",\"conversationId\":\"new\",\"parentMessageId\":\"00000000-0000-0000-0000-000000000000\",\"text\":\"hi\",\"endpoint\":\"agents\",\"messageId\":\"smoke-$(date +%s)\"}" 2>/dev/null || true)
            if echo "$SSE" | grep -q "^data: "; then
                log_pass "SSE 串流正常 · 有 data: 事件"
            else
                log_fail "SSE 無 data: 事件 · LibreChat SSE 格式可能變了"
            fi

            # 歷史對話 endpoint
            CONVOS_CODE=$(curl -s -o /dev/null -w "%{http_code}" "$BASE/api/convos?pageSize=1" \
                -H "Authorization: Bearer $TOKEN" -H "User-Agent: $UA")
            if [[ "$CONVOS_CODE" == "200" ]]; then
                log_pass "/api/convos 歷史讀取 200"
            else
                log_fail "/api/convos → $CONVOS_CODE"
            fi
        fi
    fi
else
    echo "  ⏭  SKIP · 設 SMOKE_ADMIN_EMAIL + SMOKE_ADMIN_PASSWORD env 才會跑 SSE 測試"
fi

echo ""
echo "============================================"
echo "  結果:$PASS pass / $FAIL fail"
echo "============================================"
[[ $FAIL -eq 0 ]] && exit 0 || exit 1
