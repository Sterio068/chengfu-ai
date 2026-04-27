# 📋 Handoff 4 格卡 · 跨 Workspace 協作核心

> v1.1 加 · 跨人 / 跨日 / 跨 workspace 的「交棒 artifact」
> 最常用 · 最容易填空 · 5 分鐘看完

---

## 為什麼有 4 格卡?

公司痛點:
- PM 接到客戶需求 → 要丟給設計師 → 設計師問東問西 30 分鐘
- 招標看完 → 要請會計試算 → 會計問:預算多少?需要含稅?
- 場勘回來 → 要做提案 → 沒人記場地有 3 根柱子

**4 格卡解法**:每個 project 一張卡 · 接手的人看一眼就懂

---

## 4 格內容

### 1️⃣ Goal · 目標(一句話)
**寫什麼**:這 project 終極要交付什麼?
**好範例**:
- 「中秋節 KOL 合作 · 9 月 15 日前產 5 篇貼文 · 各平台適配」
- 「環保署海洋廢棄物提案 · 10/31 前送件 · 預算上限 NT$ 350 萬」
- 「台北 101 跨年活動 · 12/15 開放報名 · 預期 500 人」

**爛範例**:
- 「弄一個東西」 ← 接手的人霧煞煞
- 「做企劃」 ← 沒交付物 / 沒時間
- 「跟 X 客戶聊一下」 ← 不是 project · 是 task

---

### 2️⃣ Constraints · 限制(列點 · 越具體越好)
**寫什麼**:錢 / 時間 / 規格 / 客戶不能踩的紅線
**好範例**:
```
- 預算上限 NT$ 35 萬(含稅 · 含設計外包)
- 客戶要求品牌色橘黃 #FFA500 · 不接受其他
- 9/12 前要客戶 final check · 留 3 天緩衝
- 不能用「環保」字樣(競品已註冊)
- 場地必須無階梯(客戶有輪椅 VIP)
```

**爛範例**:
```
- 要好看
- 預算合理
- 別出包
```
↑ 這些不是 constraints · 是廢話

---

### 3️⃣ Asset Refs · 參考資料(連結 / NAS path / 過往案)
**寫什麼**:接手者需要的資料 · 別讓他重新搜
**3 類常用**:
- `nas`(內網檔案):`/Volumes/NAS/2024/環保署/結案報告.pdf`
- `url`(網路連結):`https://drive.google.com/file/d/...`
- `note`(純文字提醒):「客戶 LINE 群組:聯絡 Sterio 拿邀請」

**好範例**:
```
[nas]   客戶 brand-book          /Volumes/NAS/clients/X/brand.pdf
[url]   競品分析 Notion          https://notion.so/abcd
[url]   過往合作 IG 範例          https://instagram.com/p/xyz/
[nas]   2023 同類案結案報告       /Volumes/NAS/2023/Y-event.pdf
[note]  客戶不喜歡卡通風格 · 偏質感攝影
```

---

### 4️⃣ Next Actions · 下一步(誰 / 何時 / 做什麼)
**寫什麼**:接手後 24 小時內最該做的 1-3 件
**好範例**:
```
1. PM 9/2 前打給客戶確認 brand-book 最新版(brand.pdf 是 2023 老的)
2. 設計師 9/3 前產 3 個視覺方向(用 nas 的 brand)
3. 會計 9/3 前報初版 quote(NT$ 35 萬框內配置)
```

**爛範例**:
```
1. 加油
2. 看著辦
3. 再說
```

---

## 介面位置

1. 進 **📁 Projects** workspace
2. 點任何 project → 右側 drawer 開
3. 「📋 Handoff 4 格卡」section
4. 4 個欄位填完 → 點「儲存 Handoff」

---

## 跨 workspace 自動帶進去(v1.3)

如果你在 **🎤 會議速記** view · 開該會議 detail · 有「推到 Handoff」按鈕
→ AI 會把會議 action_items 自動 append 到該 project 的 next_actions

如果你在 **📸 場勘** view · 一樣有「推到 Handoff」
→ AI 把 site_issues + venue 推到 constraints + asset_refs

**這兩個會 append · 不覆寫**(R23#4 修)· 你已填的 constraints 不會被洗掉

---

## 跨人交接 SOP

### 場景 A · 你今天請假 · 同事接
1. 上班前 5 分:點該 project · 確認 4 格卡是新的
2. updated_at 必 < 24 小時 · 否則同事看是過期的
3. LINE 同事:「project ID xxx 卡片已更新 · 你直接看」

### 場景 B · 你離職交接
1. 把所有 owner=你 的 project 一個一個過卡片
2. constraints 寫得越細越好(離職者沒法問你)
3. asset_refs 確認 NAS 連結還活著
4. 跟接手者一起點開 5 個 project · 走 1 遍流程

---

## 常見坑

### 坑 1 · 卡片填了沒儲存
- 「儲存 Handoff」按了沒?上方有 toast 「✅ Handoff 已儲存」才算
- 沒儲就切 view → drawer 關掉 → 改的內容掉
- v1.4 規劃 auto-save 草稿 · 目前沒

### 坑 2 · 多人同時改
- 兩人同時開同一 project · 後存的覆蓋前存的
- 「最後存的贏」· 沒 conflict 警告
- 解:LINE 確認誰負責 · 不要同時改

### 坑 3 · 推到 Handoff 後重複內容
- 場勘 + 會議速記都推 · site_issues 跟 action_items 可能重疊
- v1.3 不去重 · 你看到後手動清

### 坑 4 · asset_refs NAS 連結過期
- NAS 路徑變動沒人改卡 · 接手點開找不到檔
- 季度檢查:owner 過自己 active project · 連結都還在?

---

## 範本:複製貼上開始

```
Goal:[一句話 · 含交付物 + 期限]

Constraints:
- 預算 NT$ X 萬(含/未稅)
- 期限 YYYY-MM-DD 前 final
- [客戶禁忌]
- [規格硬限制]

Asset Refs:
- [nas] [描述] [path]
- [url] [描述] [URL]
- [note] [純文字提醒]

Next Actions:
1. [誰] [何時] [做什麼]
2. ...
3. ...
```
