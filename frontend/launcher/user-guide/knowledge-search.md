# 📚 知識庫檢索 · 5 個真實範例

> 承富過往 500+ 建議書 / 結案報告 / brand book 全進 Meili index
> 不會用 = 浪費 · 看完此頁 5 分鐘上手

---

## 哪裡用?

3 個 entry:
1. **⌘K palette · 打字直接搜**(任何 view)
2. **📚 知識庫 view**(sidebar · 進階查詢)
3. **/know slash command**(對話內 inline 查)
4. **Agent 自動用**(file_search · 不用手動觸發)

---

## 範例 1 · 找過往建議書(投標 PM)

**情境**:接到環保署新標案 · 想看承富過往環保類提案怎麼寫

**做**:
1. ⌘K
2. 打「環保 提案」
3. 看「📚 知識庫」結果
4. 點開「2024 環保署海洋廢棄物提案.pdf」
5. 跳 detail · 看 chunk + relevance score

**進階**:在 📚 知識庫 view · filter by:
- Source(只看 historical/建議書)
- Project(2024 EPA 全部)
- Type(pdf · docx)

---

## 範例 2 · 公司禁用詞 / brand voice(寫手)

**情境**:寫新聞稿 · 不確定承富禁用什麼字

**做**:
1. /know workspace 隨 prompt
2. 打:「承富禁用詞有哪些?」
3. Agent 自動 file_search → 找 `company/02-forbidden-words.md`
4. 引用回:「視頻 → 影片 / 數據 → 資料 / 雲 → 雲」

**或直接 ⌘K「禁用詞」** → 跳該檔

---

## 範例 3 · 找 client 過往合作(業務)

**情境**:某 client 詢價 · 想看以前報過多少 / 做過什麼

**做**:
1. ⌘K → 打 client 公司名(支援中英)
2. 看跳出的:
   - 📁 Projects · 跟該 client 的 active project
   - 📚 知識庫 · 過往 quote / 結案報告
   - 💼 CRM · 該 client 在 pipeline 哪階段
3. 點 quote · 看 NTD 範圍
4. 點結案 · 看當時做了什麼 · 滿意度

---

## 範例 4 · 找場地過往報價(活動 PM)

**情境**:辦 150 人晚宴 · 想知道過往同類場地行情

**做**:
1. ⌘K「150 人 晚宴」or 「圓桌晚宴」
2. 知識庫跳:
   - 「2023 X 公司年會結案.pdf」
   - 「2024 Y 客戶頒獎晚宴 quote.xlsx」
3. 看 quote 內「場地費 NT$ XX」「布置 NT$ XX」「每人餐 NT$ XX」
4. 自己同類算 baseline

**用 Agent 加值**:
- /quote
- 「給我 150 人晚宴的 baseline 報價 · 參考公司過往 3 個」
- Agent 自動 file_search 撈 + 算

---

## 範例 5 · 找 SOP / 內部流程

**情境**:新人問「報帳流程怎麼走?」

**做**:
1. /know
2. 「報帳 SOP」
3. Agent 找 `company/04-format-rules.md` 或 `historical/SOP/`
4. 回流程 + 截圖 reference

---

## ⚠ 沒結果怎辦?

### 原因 A · 尚未 index
- 新加的檔 · cron 隔天 02:00 才掃
- Admin 可手動:POST `/admin/sources/{id}/reindex`

### 原因 B · 排除 pattern 擋了
- 看 source 的 exclude_patterns(`*.log`、`.git/*` 等)
- 你要找的檔不在白名單 → admin 改 source 設定

### 原因 C · mtime 沒變(C3 hash 比對)
- 檔案內容真改了但 git checkout 後 mtime 沒動
- v1.3 C3 已 cover · hash 比對會抓
- 強迫:`/admin/sources/{id}/reindex?force=true`

### 原因 D · agent_access 限制(R10#2)
- 該 source 設了 `agent_access` 白名單 · 你開的 Agent 不在
- /admin/sources 看設定 · 必要時開放

---

## Admin · 知識庫管理

### 加新 source
1. 跳 📊 admin → /admin/sources(POST)
2. body:
   ```json
   {
     "name": "2024 EPA 案結案",
     "type": "local",
     "path": "/Volumes/NAS/2024/EPA/結案報告",
     "exclude_patterns": ["*.log", ".DS_Store"],
     "max_size_mb": 50,
     "agent_access": []  // 空 = 所有 Agent 都讀
   }
   ```
3. 自動 cron 隔天 index · 或手動 reindex

### 刪 source
- DELETE `/admin/sources/{id}`
- Mongo + Meili 都清

### Reindex 強制全重
- POST `/admin/sources/{id}/reindex?force=true`
- 跳過 hash 比對 · 全檔重 OCR
- 用情境:brand-voice 改詞 · 想全部重 embed

### 整庫強制重(罕用)
- `python3 scripts/reembed-knowledge.py`
- 2-3 小時 · 跑前 stop knowledge-cron

---

## 查 audit log(誰搜了什麼)

`/admin/audit-log?action=knowledge_read`

PDPA 紀錄 · 90 天自動清(TTL)
- user · 誰
- resource · 哪個 source / 檔案
- created_at · 什麼時候

---

## 常見問

### Q · Agent 怎知該 search?
- 系統 prompt 內 instruction:「先查公司知識庫 · 沒有再臆測」
- Agent 自動 trigger file_search · 不用提醒

### Q · 我 search 跟 Agent file_search 結果不同?
- file_search 用 vector(embedding)· 你 ⌘K 用 Meili 全文(BM25)
- 兩種正交 · 看你需求:語意相近用 Agent · 關鍵字命中用 ⌘K

### Q · 找不到的 · 真的沒上傳?
- 看 /admin/sources 列表 · 有對應 source 嗎?
- source enabled=true 嗎?
- last_indexed_at 是不是夠新?

### Q · 知識庫太大 · search 變慢?
- /admin/sources/health 看 chengfu_knowledge index size
- > 100k docs 開始慢 · 評估歸檔老檔到另一 index
