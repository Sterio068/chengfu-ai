#!/usr/bin/env bash
# ============================================================
# 企業 AI · 卸載 launchd 定時工作
# ============================================================
set -euo pipefail

PLIST_DST="${HOME}/Library/LaunchAgents"

echo "[$(date +'%Y-%m-%d %H:%M:%S')] 卸載 launchd 定時工作..."

for plist_file in "$PLIST_DST"/tw.company-ai.*.plist; do
    if [[ ! -f "$plist_file" ]]; then continue; fi
    name=$(basename "$plist_file")
    echo "  📄 卸載 ${name}"
    launchctl unload "$plist_file" 2>/dev/null || echo "     (可能本來就沒 load)"
    rm "$plist_file"
    echo "     ✅ 刪除 ${plist_file}"
done

echo ""
echo "驗證:"
launchctl list | grep tw.company-ai && echo "  ⚠ 還有殘留 · 手動 launchctl remove" || echo "  ✅ 無殘留"
