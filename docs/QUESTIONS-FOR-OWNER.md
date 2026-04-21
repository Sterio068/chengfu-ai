# 帶去問承富老闆的問題

> Sterio 帶這份去跟承富老闆 + Champion 開 30 分鐘會議,把答案寫回每題下方,然後 v1.1 實作就有依據。

---

## 1. 老闆 5 題基礎答案(2026-04-21 已答 · 寫死路線圖)

| # | 題 | 老闆答案 |
|---|---|---|
| 1 | 每週 Top 3 任務 | 設計 / 提案撰寫 / 廠商聯繫 |
| 2 | 80% 原始檔在哪 | LINE 群組 + NAS(不是 Google Drive) |
| 3 | L3 機敏規則 | 先不考慮 |
| 4 | 老闆最在意 | 省時 + 接案量(不是風控) |
| 5 | 維運資源 | 外包 20h/週 Claude Code 遠端 + Champion 自主學習 |

---

## 2. v1.1 開工前需要老闆/Champion 答的 5 題(Round 8 reviewer 提)

### Q1. 承富常見招標 PDF · 掃描件 vs born-digital 比例?

**承富答(2026-04-21):** **OCR 要進容器** · 代表掃描件佔比不低(30%+)
**影響:** `accounting` Dockerfile 必須裝 `tesseract-ocr tesseract-ocr-chi-tra`(image +50MB)

### Q2. 設計師偏好「1 張慢慢重生」or「3 張挑方向」?

**承富答:** **一次 3 張挑方向**
**影響:** Fal.ai `num_images=3` · 成本 3 倍但符合設計師實際工作流
**UI 調整:** 3 張並排網格 + 「留這張」「全重生」「選中間一張重生」3 種動作

### Q3. 第一批 `knowledge-base/samples/` 能匿名提供哪 3 類?

**承富答(2 段):**
1. 第一波(2026-04-21):「建議書 + 標案需求檔 + **所有設計圖** · **各項專案分資料夾** · 希望系統能夠讀取所有類型資料」
2. 補充(2026-04-21):「**不只 NAS 要可以指定專案資料夾**」(支援多源)

**→ 這變成 v1.2 最大工程 · 升級為「多來源知識庫」(不只 NAS)**

**影響範圍:**
- 從「單一 NAS 路徑」→ **多 sources 機制**(NAS / 本機 / 外接 / 雲掛載點皆可)
- Admin 可動態加資料源(UI · 不寫死 env)
- 每個 source 獨立:enabled / exclude_patterns / agent_access / mime_whitelist
- 不只 PDF · 支援 DOCX / PPTX / XLSX / JPG / PNG metadata
- 工時從「2h 手動」→ **39-52h 多源知識庫完整整合**

### Q4. accounting 容器能加 PyMuPDF + Tesseract 嗎?

**Sterio 答:** **能接受**
**影響:** Dockerfile 加依賴 · image 從 ~200MB → ~280MB · 可接受

### Q5. 專案詳情 UI modal / drawer / expand?

**承富答:** **Drawer**(右側滑出 · 40% 寬 panel)
**影響:**
- `frontend/launcher/index.html` 加 `.project-drawer` 元素
- 點 project card → drawer 滑出 · 左邊 projects 列表仍可見
- Handoff 4 格在 drawer 內 · 預設收合 · 展開可填
- 類似 macOS Mail 點郵件的體感(資深同仁熟悉)

---

## 3. 老闆答完後,Sterio 要做的事

1. 把答案寫回上面 Q1-Q5
2. 更新 `docs/V1.1-IMPLEMENTATION-SPEC.md` 的對應段落(預設值換成老闆選擇)
3. v1.1 開工順序按 reviewer 推薦:**B PDF(8-12h) → A Fal.ai(6-8h) → D admin_metrics 拆(6-8h) → C handoff(6-8h v1.2)**
4. 每完成一項 commit + push + 更新 ROADMAP-v4.2.md

---

## 4. 已知會被 Champion 抗拒的問題(預留)

> v1.1 上線後可能會聽到的話 · 預先想好回應

- **「為什麼還是要複製貼上 PDF?」** → 「v1.1 開放真實 PDF 上傳,目前用『3 步貼法』過渡」
- **「為什麼 AI 給的圖跟我說的不一樣?」** → 「描述需要更抽象 · 看『AI 偏題時 5 句話救』教學」
- **「為什麼月底 AI 突然不能用?」** → 「per-user 預算 hard stop,找 Sterio 加 QUOTA_OVERRIDE」
- **「為什麼這個檔我從 NAS 找不到?」** → 「NAS 整合是 v1.2 · 目前要手動下載」

---

## 5. 開工前最後一道檢查

- [ ] 老闆答完 Q1-Q5
- [ ] Sterio 拿到 5-10 份 sample 檔(Q3)
- [ ] 預算批准(Q2 影響 Fal.ai 成本)
- [ ] FAL_API_KEY 申請好放 Keychain
- [ ] Champion 點頭願意當 v1.1 第一週 daily QA
