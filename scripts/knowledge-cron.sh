#!/usr/bin/env bash
# ============================================================
# 知識庫每日增量索引 cron
# ============================================================
# V1.1-SPEC §E-2
# macOS launchd 或 cron 每日 02:00 跑
# 會進 accounting 容器 · 呼叫 reindex_all() · 寫 log 到 scripts/knowledge-cron.log
#
# launchd plist 範例:
#   ~/Library/LaunchAgents/tw.chengfu.knowledge-cron.plist
#   ProgramArguments: ["/bin/bash", "<repo>/scripts/knowledge-cron.sh"]
#   StartCalendarInterval: { Hour: 2, Minute: 0 }
# ============================================================
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
LOG="$REPO_ROOT/scripts/knowledge-cron.log"

echo "===== $(date '+%Y-%m-%d %H:%M:%S') knowledge-cron start =====" >>"$LOG"

# 容器名可由 env 覆蓋(dev 可能不同)
CONTAINER="${CHENGFU_ACCOUNTING_CONTAINER:-chengfu-accounting}"

if ! docker ps --format '{{.Names}}' | grep -qx "$CONTAINER"; then
    echo "[cron] accounting 容器 $CONTAINER 未運行 · skip" >>"$LOG"
    exit 0
fi

# 在容器內跑 reindex_all · 取 stats 回來存 log
# C3(v1.3)· file_hashes_col 啟動 · 內容 hash 比對 · mtime 變但內容沒變不重 extract
docker exec "$CONTAINER" python -c "
import json, sys
from services import knowledge_indexer
from main import knowledge_sources_col, db, _get_meili_client

meili = _get_meili_client()
stats = knowledge_indexer.reindex_all(
    knowledge_sources_col, meili,
    file_hashes_col=db.knowledge_file_hashes,
)
print(json.dumps(stats, ensure_ascii=False, indent=2, default=str))
" >>"$LOG" 2>&1

echo "===== $(date '+%Y-%m-%d %H:%M:%S') knowledge-cron done =====" >>"$LOG"
echo "" >>"$LOG"
