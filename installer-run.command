#!/bin/bash
export PATH=/opt/homebrew/bin:/usr/local/bin:/Applications/Docker.app/Contents/Resources/bin:$PATH
cd '/Users/sterio/Workspace/ChengFu'
echo '═══ 承富 AI 安裝 · 抓 image + 啟動容器 ═══'
cd config-templates && docker compose pull
cd ..
bash scripts/start.sh
bash scripts/smoke-test.sh
echo ''
echo '✅ 安裝完成 · 訪問 http://localhost/'
echo '可關閉此 Terminal 視窗 · 但不要關 Docker Desktop'

