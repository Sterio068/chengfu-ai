#!/usr/bin/env bash
# ============================================================
# 承富 AI · 安裝 launchd 定時工作(Codex Round 10.5 黃 8)
# ============================================================
# 用途:把 config-templates/launchd/ 的 plist 範本 · 替換 USERNAME 後
#       放進 ~/Library/LaunchAgents/ · 並載入 launchctl
#
# 執行:./scripts/install-launchd.sh
# 卸載:./scripts/uninstall-launchd.sh
#
# 驗證:
#   launchctl list | grep tw.chengfu
#   cat ~/Library/LaunchAgents/tw.chengfu.*.plist
# ============================================================
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PLIST_SRC="${REPO_ROOT}/config-templates/launchd"
PLIST_DST="${HOME}/Library/LaunchAgents"
LOG_DIR="${HOME}/Library/Logs"

mkdir -p "$PLIST_DST" "$LOG_DIR"

echo "[$(date +'%Y-%m-%d %H:%M:%S')] 安裝 launchd 定時工作..."

for plist_file in "$PLIST_SRC"/*.plist; do
    if [[ ! -f "$plist_file" ]]; then continue; fi
    name=$(basename "$plist_file")
    dst="${PLIST_DST}/${name}"
    # 把 USERNAME 替換成當前使用者 · 否則 launchd 不認
    sed "s|/Users/USERNAME/|${HOME}/|g" "$plist_file" > "$dst"
    chmod 644 "$dst"
    echo "  📄 安裝 ${name}"
    # 若已 load 過 · 先 unload
    launchctl unload "$dst" 2>/dev/null || true
    launchctl load "$dst"
    echo "     ✅ launchctl load 成功"
done

echo ""
echo "已安裝的工作:"
launchctl list | grep "^-\|^[0-9]" | grep -i tw.chengfu || echo "  (尚無 · 檢查上方錯誤)"

echo ""
echo "Log 位置:"
echo "  ~/Library/Logs/chengfu-backup.log"
echo "  ~/Library/Logs/chengfu-knowledge-cron.log"

echo ""
echo "✅ 安裝完成"
echo "   卸載請跑:./scripts/uninstall-launchd.sh"
