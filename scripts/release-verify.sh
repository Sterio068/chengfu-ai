#!/bin/bash
# ============================================================
# 企業 AI · 正式交付版總驗收
# ============================================================
# 用法:
#   ./scripts/release-verify.sh [base_url]
#
# 可用 env:
#   BASE_URL=http://localhost
#   RESET_LIBRECHAT=1      # 預設 1,跑 E2E 前重啟 LibreChat 清 in-memory login limiter
#   RUN_E2E=1              # 預設 1
# ============================================================

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
BASE_URL="${1:-${BASE_URL:-http://localhost}}"
RESET_LIBRECHAT="${RESET_LIBRECHAT:-1}"
RUN_E2E="${RUN_E2E:-1}"
STAMP="$(date +%Y-%m-%d-%H%M%S)"
REPORT_DIR="${ROOT_DIR}/reports/release"
MANIFEST="${REPORT_DIR}/release-manifest-${STAMP}.md"
DMG="${ROOT_DIR}/installer/dist/Company-AI-Installer.dmg"

mkdir -p "$REPORT_DIR"

PASS=0
FAIL=0
FAILED_STEPS=()

log() {
  echo "$@"
  echo "$@" >> "$MANIFEST"
}

run_step() {
  local name="$1"
  shift
  echo ""
  echo "═══ $name ═══"
  if "$@"; then
    echo "✅ $name"
    echo "- ✅ $name" >> "$MANIFEST"
    PASS=$((PASS + 1))
  else
    echo "❌ $name"
    echo "- ❌ $name" >> "$MANIFEST"
    FAILED_STEPS+=("$name")
    FAIL=$((FAIL + 1))
  fi
}

wait_lc_ready() {
  for _ in {1..60}; do
    if curl -sf "${BASE_URL}/api/config" >/dev/null 2>&1; then
      return 0
    fi
    sleep 2
  done
  return 1
}

reset_limiter_if_possible() {
  if [[ "$RESET_LIBRECHAT" != "1" ]]; then
    return 0
  fi
  if docker ps --filter name=company-ai-librechat --filter status=running -q | grep -q .; then
    docker restart company-ai-librechat >/dev/null
    wait_lc_ready
  fi
}

check_sensitive_files_absent() {
  local found=0
  for path in \
    "${ROOT_DIR}/scripts/passwords.txt" \
    "${ROOT_DIR}/config-templates/users.json"
  do
    if [[ -e "$path" ]]; then
      echo "敏感暫存檔不可存在:$path"
      found=1
    fi
  done
  return "$found"
}

scan_known_secret_literal() {
  local stored_password="${E2E_ADMIN_PASSWORD:-${LIBRECHAT_ADMIN_PASSWORD:-}}"
  if [[ -z "$stored_password" && "$(uname -s)" == "Darwin" ]]; then
    stored_password="$(security find-generic-password -s company-ai-admin-install-password -w 2>/dev/null || true)"
  fi

  if [[ -z "$stored_password" ]]; then
    echo "無可比對的 Keychain/E2E 密碼,跳過實值掃描"
    return 0
  fi

  local matches
  matches="$(rg -l --fixed-strings "$stored_password" "$ROOT_DIR" \
    --glob '!**/node_modules/**' \
    --glob '!config-templates/.env' \
    --glob '!reports/release/**' \
    --glob '!installer/dist/**' || true)"

  if [[ -n "$matches" ]]; then
    echo "$matches"
    return 1
  fi

  return 0
}

frontend_audit() {
  cd "${ROOT_DIR}/frontend/launcher"
  npm audit --omit=dev
}

e2e_audit() {
  cd "${ROOT_DIR}/tests/e2e"
  npm audit --omit=dev
}

frontend_build() {
  cd "${ROOT_DIR}/frontend/launcher"
  npm run build
}

backend_tests() {
  cd "$ROOT_DIR"
  # F-08 對應 · 確保 host python3 有齊全 test deps
  # 策略:
  # 1. 優先用既有 venv(.venv/bin/python · backend/accounting/.venv)
  # 2. 否則建一個 .venv-release-verify · 第一次跑慢 · 之後快
  # 3. macOS Python 3.13/3.14 PEP 668 不允許 pip install --user · 必走 venv
  local VENV=""
  if [ -d "$ROOT_DIR/.venv" ] && [ -x "$ROOT_DIR/.venv/bin/python" ]; then
    VENV="$ROOT_DIR/.venv"
  elif [ -d "$ROOT_DIR/backend/accounting/.venv" ] && [ -x "$ROOT_DIR/backend/accounting/.venv/bin/python" ]; then
    VENV="$ROOT_DIR/backend/accounting/.venv"
  else
    # 沒既有 venv · 自己建一個
    VENV="$ROOT_DIR/.venv-release-verify"
    if [ ! -x "$VENV/bin/python" ]; then
      local PY3=""
      for cand in python3.13 python3.12 python3.11 python3; do
        if command -v "$cand" >/dev/null 2>&1; then PY3="$cand"; break; fi
      done
      [ -z "$PY3" ] && { echo "❌ 找不到 python3"; return 1; }
      echo "  建 venv($($PY3 --version))..."
      "$PY3" -m venv "$VENV" 2>&1 | tail -3 || { echo "❌ venv 建立失敗"; return 1; }
    fi
  fi
  echo "  使用 venv:$VENV"
  "$VENV/bin/python" -m pip install --quiet --upgrade pip 2>/dev/null || true
  "$VENV/bin/python" -m pip install --quiet -r backend/accounting/requirements.txt 2>&1 | tail -3 || true
  "$VENV/bin/python" -m pytest -q
}

e2e_tests() {
  if [[ "$RUN_E2E" != "1" ]]; then
    echo "RUN_E2E!=1,skip"
    return 0
  fi
  cd "${ROOT_DIR}/tests/e2e"
  npm test -- --reporter=line
}

smoke_main() {
  cd "$ROOT_DIR"
  ./scripts/smoke-test.sh "$BASE_URL"
}

smoke_lc() {
  cd "$ROOT_DIR"
  ./scripts/smoke-librechat.sh "$BASE_URL"
}

installer_build() {
  cd "$ROOT_DIR"
  ./installer/build.sh
}

inspect_dmg() {
  [[ -f "$DMG" ]] || return 1
  local mount_dir
  local result=0
  mount_dir="$(mktemp -d /tmp/company-ai-release-dmg.XXXXXX)"
  if ! hdiutil attach -quiet -nobrowse -readonly -mountpoint "$mount_dir" "$DMG"; then
    rmdir "$mount_dir" >/dev/null 2>&1 || true
    return 1
  fi

  if [[ ! -f "$mount_dir/CompanyAI-source.tar.gz" ]] || [[ ! -f "$mount_dir/讀我.txt" ]]; then
    result=1
  elif ! grep -Eq '右鍵|Control' "$mount_dir/讀我.txt"; then
    echo "讀我.txt 缺 Gatekeeper 右鍵開啟說明"
    result=1
  elif tar -tzf "$mount_dir/CompanyAI-source.tar.gz" | grep -E \
    '(^\./config-templates/\.env$|(^|/)passwords\.txt$|(^|/)users\.json$|^\./config-templates/uploads/|^\./config-templates/images/|^\./reports/|test-results)' \
    | head -20; then
    result=1
  fi

  hdiutil detach -quiet "$mount_dir" >/dev/null 2>&1 || true
  rmdir "$mount_dir" >/dev/null 2>&1 || true
  return "$result"
}

diff_check() {
  cd "$ROOT_DIR"
  git diff --check -- frontend/launcher backend/accounting scripts installer tests/e2e config-templates reports
}

write_header() {
  cat > "$MANIFEST" <<EOF
# 企業 AI · 正式交付版驗收 Manifest

時間:$(date '+%Y-%m-%d %H:%M:%S %Z')
Base URL:${BASE_URL}
Git HEAD:$(git -C "$ROOT_DIR" rev-parse --short HEAD 2>/dev/null || echo unknown)
Reset LibreChat limiter:${RESET_LIBRECHAT}
Run E2E:${RUN_E2E}

## 驗收步驟
EOF
}

write_footer() {
  {
    echo ""
    echo "## 結果"
    echo ""
    echo "- Passed:${PASS}"
    echo "- Failed:${FAIL}"
    if [[ -f "$DMG" ]]; then
      echo "- DMG:installer/dist/Company-AI-Installer.dmg"
      echo "- DMG Size:$(du -h "$DMG" | awk '{print $1}')"
      echo "- DMG SHA-256:$(shasum -a 256 "$DMG" | awk '{print $1}')"
    fi
    if [[ ${#FAILED_STEPS[@]} -gt 0 ]]; then
      echo "- Failed Steps:${FAILED_STEPS[*]}"
      echo ""
      echo "結論:不可交付,請先修復失敗步驟。"
    else
      echo ""
      echo "結論:正式交付版驗收通過。"
    fi
  } >> "$MANIFEST"
}

write_header

run_step "敏感暫存檔不存在" check_sensitive_files_absent
run_step "已知密碼字串不在 source" scan_known_secret_literal
run_step "frontend npm audit" frontend_audit
run_step "e2e npm audit" e2e_audit
run_step "frontend build" frontend_build
run_step "backend pytest" backend_tests
run_step "重置 LibreChat login limiter" reset_limiter_if_possible
run_step "Playwright E2E" e2e_tests
run_step "主系統 smoke" smoke_main
run_step "LibreChat route contract smoke" smoke_lc
run_step "installer build" installer_build
run_step "DMG 內容與敏感檔抽查" inspect_dmg
run_step "git diff whitespace check" diff_check

write_footer

echo ""
echo "============================================"
echo "  正式交付驗收結果:$PASS passed / $FAIL failed"
echo "  Manifest:$MANIFEST"
echo "============================================"

if [[ "$FAIL" -gt 0 ]]; then
  exit 1
fi
