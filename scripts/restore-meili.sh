#!/usr/bin/env bash
# ============================================================
# 企業 AI · Meilisearch 索引還原(Codex Round 10.5 紅)
# ============================================================
# 對應 scripts/backup.sh 的 Meili dump 備份
# 用法:
#   ./scripts/restore-meili.sh <meili-dump-gz-or-gpg>
#
# 範例:
#   # 從最新本機備份還原
#   LATEST=$(ls -1t ~/company-ai-backups/daily/company-ai-meili-*.tar.gz* | head -1)
#   ./scripts/restore-meili.sh "$LATEST"
#
#   # 從異機備份還原
#   rclone copy company-ai-offsite:company-ai-backup/meili/company-ai-meili-2026-04-21.tar.gz.gpg /tmp/
#   ./scripts/restore-meili.sh /tmp/company-ai-meili-2026-04-21.tar.gz.gpg
#
# ============================================================
set -euo pipefail

if [[ $# -ne 1 ]]; then
    echo "用法:$0 <path-to-meili-dump>"
    echo "檔名需為 company-ai-meili-YYYY-MM-DD.tar.gz 或 .tar.gz.gpg"
    exit 1
fi

INPUT="$1"
REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
MEILI_DATA="${REPO_ROOT}/config-templates/data/meili"
TMP_DIR=$(mktemp -d)
GPG_RECIPIENT="${COMPANY_AI_GPG_RECIPIENT:-company-ai}"
trap "rm -rf $TMP_DIR" EXIT

echo "[$(date +'%Y-%m-%d %H:%M:%S')] 開始 Meili 還原:$INPUT"

# 1. 若是 .gpg · 先解密(Codex R2.3 新檔名可能是 .dump.gpg · 也支援)
if [[ "$INPUT" == *.gpg ]]; then
    if ! command -v gpg > /dev/null; then
        echo "❌ 缺 gpg · brew install gnupg"
        exit 1
    fi
    if ! gpg --list-keys "$GPG_RECIPIENT" > /dev/null 2>&1; then
        echo "❌ 缺 ${GPG_RECIPIENT} GPG key · 無法解密"
        exit 1
    fi
    echo "  🔐 解密 .gpg..."
    DECRYPTED="${TMP_DIR}/$(basename "${INPUT%.gpg}")"
    gpg --batch --yes --decrypt --output "$DECRYPTED" "$INPUT"
    INPUT="$DECRYPTED"
fi

# 2. 判斷是 .tar.gz(舊版)還是 .dump(新 R2.3 單檔)
DUMP_FILE=""
if [[ "$INPUT" == *.tar.gz ]]; then
    echo "  📦 解壓 tar.gz..."
    tar -xzf "$INPUT" -C "$TMP_DIR"
    DUMP_FILE=$(find "$TMP_DIR/dumps" -name "*.dump" 2>/dev/null | head -1)
elif [[ "$INPUT" == *.dump ]]; then
    DUMP_FILE="$INPUT"
fi
if [[ -z "$DUMP_FILE" || ! -f "$DUMP_FILE" ]]; then
    echo "❌ 找不到 .dump 檔 · 輸入格式應為 .tar.gz 或 .dump(或其 .gpg)"
    exit 1
fi
echo "  📄 找到 dump: $(basename "$DUMP_FILE")"

# 3. 停 Meili · 清舊 data · 放 dump · 用 --import-dump 啟動
echo "  🛑 停 Meili..."
cd "$REPO_ROOT/config-templates"
docker compose stop meilisearch || true

# 把 dump 放到 bind-mount 內
mkdir -p "$MEILI_DATA/dumps"
cp "$DUMP_FILE" "$MEILI_DATA/dumps/"
DUMP_BASENAME=$(basename "$DUMP_FILE")

# 備份現有 data(以防還原失敗還有後路)
BACKUP_CURRENT="${MEILI_DATA}.before-restore-$(date +%Y%m%d-%H%M%S)"
if [[ -d "$MEILI_DATA/data.ms" ]]; then
    echo "  💾 備份現有 Meili 資料到 $BACKUP_CURRENT"
    mv "$MEILI_DATA/data.ms" "$BACKUP_CURRENT/data.ms" 2>/dev/null || \
        { mkdir -p "$BACKUP_CURRENT" && mv "$MEILI_DATA/data.ms" "$BACKUP_CURRENT/"; }
fi

# 4. Codex R2.4 · MEILI_IMPORT_DUMP 匯入完後 Meili 會繼續 serve · 不是 one-shot
#    用 temporary container 起來 · 等 ready · stop · 再正常啟動
echo "  ⚙  啟動暫時容器以 import-dump..."
TEMP_CID=$(docker run -d --rm --name company-ai-meili-import-tmp \
    -v "$(cd "$MEILI_DATA" && pwd):/meili_data" \
    -e MEILI_IMPORT_DUMP=/meili_data/dumps/${DUMP_BASENAME} \
    -e MEILI_NO_ANALYTICS=true \
    -e MEILI_MASTER_KEY="${MEILI_MASTER_KEY:-ci-placeholder-insecure-do-not-use}" \
    getmeili/meilisearch:v1.12.0)

# 等 Meili ready(poll /health)
echo "  ⏳  等匯入完成..."
READY=""
for i in $(seq 1 60); do  # 最多 5 分鐘
    HEALTH=$(docker exec company-ai-meili-import-tmp wget -qO- http://localhost:7700/health 2>/dev/null || echo "")
    if echo "$HEALTH" | grep -q 'available'; then
        READY="yes"
        break
    fi
    sleep 5
done
docker stop company-ai-meili-import-tmp 2>/dev/null || true
if [[ -z "$READY" ]]; then
    echo "  ❌ 匯入超時 · 從 $BACKUP_CURRENT 回復"
    rm -rf "$MEILI_DATA/data.ms"
    mv "$BACKUP_CURRENT/data.ms" "$MEILI_DATA/" 2>/dev/null || true
    exit 1
fi
echo "  ✅ 匯入完成 · 暫時容器已停"

# 5. 正常啟動
echo "  ▶  恢復正常 Meili..."
docker compose up -d meilisearch
sleep 8

# 6. 驗證
MEILI_KEY=$(docker exec company-ai-accounting printenv MEILI_MASTER_KEY 2>/dev/null || echo "")
if [[ -n "$MEILI_KEY" ]]; then
    STATS=$(docker exec company-ai-meili wget -qO- \
        --header="Authorization: Bearer ${MEILI_KEY}" \
        http://localhost:7700/indexes/company_ai_knowledge/stats 2>/dev/null || echo "")
    DOCS=$(echo "$STATS" | sed -n 's/.*"numberOfDocuments":\([0-9]*\).*/\1/p')
    echo "  ✅ 還原完成 · 目前索引 $DOCS 個文件"
    if [[ "$DOCS" == "0" || -z "$DOCS" ]]; then
        echo "  ⚠ 警告:文件數為 0 · 還原可能失敗 · 可從 $BACKUP_CURRENT 回復舊資料"
        exit 1
    fi
else
    echo "  ⚠ 無 MEILI_MASTER_KEY · 無法驗證 · 請手動確認"
fi

echo "[$(date +'%Y-%m-%d %H:%M:%S')] Meili 還原流程完成"
echo ""
echo "驗證:curl -H \"Authorization: Bearer \$MEILI_MASTER_KEY\" http://localhost:7700/indexes"
