#!/usr/bin/env python3
"""
v1.3 C3 · 強制重 embed 全知識庫

正常 cron(scripts/knowledge-cron.sh)走增量 + hash 比對 · 不重複 OCR
但有些情境必須全重:
- brand-voice / 禁用詞 / 稱謂規則大改 · 需重新 embed 影響語境
- knowledge_file_hashes 表壞了 / 想 reset
- 升級換 extract 邏輯(OCR 模型 / chunking)

用法:
    # 跑前先 stop 平日 cron 防衝突
    launchctl unload ~/Library/LaunchAgents/tw.chengfu.knowledge-cron.plist

    # 然後跑(會在 chengfu-accounting 容器內執行)
    python3 scripts/reembed-knowledge.py

    # 跑完重 load cron
    launchctl load ~/Library/LaunchAgents/tw.chengfu.knowledge-cron.plist

驗收:每個 source stats.skipped_unchanged 應為 0(全重 extract)
時間預估:50k 檔含 5k OCR · 2-3 小時(同首次 reindex)· 跑前評估
"""
import sys
import json
import subprocess

CONTAINER = "chengfu-accounting"


def main():
    print("=" * 60)
    print("承富 AI 知識庫 · 強制重 embed")
    print("=" * 60)
    print()
    print("⚠ 此操作會重跑 OCR + Meili index 全檔(可能 2-3 小時)")
    print("⚠ 完成前建議先 stop knowledge-cron · 避免衝突")
    print()
    confirm = input("確定?(輸入 'YES I UNDERSTAND' 確認): ")
    if confirm != "YES I UNDERSTAND":
        print("已取消")
        sys.exit(0)

    # 容器內跑(同 knowledge-cron.sh pattern · force=True)
    # R33#黃1 修 · _get_meili_client 在 routers.knowledge 不在 main
    # R33#黃2 修 · 內層檢查每 source stats · Meili 失敗 sys.exit(1) 讓操作員重跑
    cmd = [
        "docker", "exec", CONTAINER, "python", "-c",
        """
import json, sys
from services import knowledge_indexer
from main import knowledge_sources_col, db
from routers.knowledge import _get_meili_client

meili = _get_meili_client()
stats = knowledge_indexer.reindex_all(
    knowledge_sources_col, meili,
    file_hashes_col=db.knowledge_file_hashes,
    force=True,  # C3 · 強制重 extract
)
print(json.dumps(stats, ensure_ascii=False, indent=2, default=str))

# R33#黃2 · 任一 source Meili 失敗 → exit 1 · 防外層誤以為成功
fail_count = 0
for name, s in stats.items():
    if not isinstance(s, dict):
        continue
    if s.get('ok') is False:
        fail_count += 1
        print(f'[FAIL] {name}: {s.get(\"reason\", \"unknown\")}', file=sys.stderr)
        continue
    # search_progress_advanced 三狀態:True OK / False Meili 掛 / None 無 Meili
    spa = s.get('search_progress_advanced')
    if spa is False:  # 真有 Meili 但這輪沒前進
        fail_count += 1
        print(f'[FAIL] {name}: Meili 寫入失敗 · errors={s.get(\"errors\", 0)}', file=sys.stderr)
if fail_count > 0:
    print(f'\\n{fail_count} source 失敗 · 請檢查並重跑', file=sys.stderr)
    sys.exit(1)
""",
    ]

    print("→ 執行中...(stdout 即時印 · 失敗會 raise · 中斷可 ⌃C 停 · 已 indexed 不會回滾)")
    result = subprocess.run(cmd, check=False)

    if result.returncode == 0:
        print()
        print("✅ 完成 · 看 ~/Library/Logs/chengfu-knowledge-cron.log 詳細")
    else:
        print()
        print(f"❌ 失敗 · exit code {result.returncode}")
        print("   檢查 docker logs chengfu-accounting --tail 50")
        sys.exit(result.returncode)


if __name__ == "__main__":
    main()
