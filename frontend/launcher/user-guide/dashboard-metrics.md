# 📊 Dashboard 指標解讀

> 首頁 + Inspector + Admin Panel · 看到的數字什麼意思?

---

## 首頁 Dashboard

### 「本週省 X 小時」激勵卡
- **怎麼算**:本週你跟 Agent 的對話次數 × 平均省時(估每次 30 分)
- **新帳號顯示「-」** · 等第一週累積資料才有
- **看不到變化** · 你本週幾乎沒用 · 試一個 /命令

### 「本月用量」進度條
- **綠**:< 80% per-user cap(NT$ 1200 預設)· 安心用
- **橘**:80-100% · 該換 Haiku 模型 / 收斂用量
- **紅**:超 100% · 已被 hard_stop 模式擋(看 .env QUOTA_MODE)
- **點數字 → 跳 Inspector 看用量分布**

### 「最近對話」清單
- 最近 10 筆你開的對話
- 點 → 跳 LibreChat 該對話
- 沒看到舊的 → 對話被歸檔(LibreChat 自動 30 天)

### 5 Workspace 卡片
- 各 workspace 入口 · 顯示該 workspace 主流程
- 「最近 3 個工作區的 project」帶到對話內(快速接續)

---

## Inspector(右側 panel · 🌐 圖示開)

### 「本月用量」
- spent_ntd · 你這個月已花
- cap_ntd · 你的月上限
- 進度條跟首頁同步

### 「提示」(本週 tips · 隨機 1-2 句)
- 記得用 ⌘K 快速跳
- 下班前填 Handoff 接班順
- ...

### 「系統狀態」
- 🟢 nginx · librechat · accounting 全 healthy
- 🟡 偶發慢(> 1s response)
- 🔴 有 service 掛 → 找 Champion 重啟

### 「最後備份」
- 「2 小時前」· OK
- 「24 小時前」· 黃 · 看 cron 是否漏跑
- 「N 天前」· 紅 · Champion 馬上看

---

## Admin Dashboard(/admin/dashboard · ⌘M)

### 一頁式總覽

```
┌─────────────────────────────────────┐
│ 會計           │ 專案        │
│  收入 NT$ X    │  active Y   │
│  支出 NT$ Z    │  total W    │
│  淨利 NT$ N    │             │
├─────────────────────────────────────┤
│ 回饋                  │ 對話        │
│  total / up           │  total      │
│  satisfaction X%      │  this_month │
│  by_agent breakdown   │             │
└─────────────────────────────────────┘
```

### 怎麼看
- **滿意度 < 80%** · 看 by_agent · 哪 Agent 表現差
- **本月對話 < 上月 70%** · 同事採納率掉 · 找 Champion 看
- **淨利 < 0** · 月會計的事 · 別當 KPI · 但持續紅 → 老闆會問

---

## /admin/cost · 月成本分項

### 結構
```json
{
  "period_days": 30,
  "by_model": [
    {"_id": "claude-haiku-4-5",  "input_tokens": ..., "output_tokens": ..., "count": ...},
    {"_id": "claude-sonnet-4-6", ...},
    {"_id": "claude-opus-4-7",   ...}
  ],
  "whisper": {
    "total_seconds": 1234.5,
    "total_minutes": 20.6,
    "ntd": 4.01,
    "rate_usd_per_minute": 0.006,
    "sources": {
      "meetings":   {"seconds": 1000, "count": 5},
      "site_audio": {"seconds": 234.5, "count": 12}
    }
  }
}
```

### 解讀
- **by_model 三層**:Haiku 1/10 cost · Sonnet 中間 · Opus 最貴
- **whisper.ntd**:OpenAI STT 月花費(meetings + 場勘 audio)
- **總月成本** = sum(by_model 算 NTD) + whisper.ntd
  - 用 services/admin_metrics.py price_ntd 函式換算

---

## /admin/budget-status · 本月預算進度

| 欄位 | 值 |
|---|---|
| spent_ntd | 本月已花(全公司) |
| budget_ntd | 月預算上限(`MONTHLY_BUDGET_NTD` env · 預設 NT$ 12000) |
| pct | spent / budget × 100 |
| alert_level | ok < 80% · warn 80-100% · over > 100% |
| month | YYYY-MM |
| pricing_version | 2026-04-21(改 Anthropic 定價時 update) |

---

## /admin/adoption · 採納率(BOSS-VIEW ROI)

| 欄位 | 看法 |
|---|---|
| active_users | 本期(預設 7 天)有 ≥ 1 對話人數 · 10 人公司目標 ≥ 8 |
| median_convos_per_user | 中位數 · < 5 · 同事還沒養成習慣 |
| handoff_fill_rate | Project 有填 handoff.goal 比例 · 目標 > 50% |
| fal_cost_ntd | 設計助手 Recraft 生圖成本 |
| first_win | 至少跑過 1 對話的人數 · onboarding 指標 |

---

## /admin/top-users · Top N 用量

```json
[
  {"user_email": "alice@x.com", "spent_ntd": 850, "soft_cap_pct": 70, "models": {...}},
  ...
]
```

- spent_ntd > 月 cap 80% · 找該人聊聊
- model 全 Opus · 建議改 Haiku 試

---

## /admin/tender-funnel · 標案漏斗

```
new_discovered  (g0v PCC 抓到)
    ↓
interested      (admin 標 Go/No-Go = Go)
    ↓
proposing       (進入提案)
    ↓
submitted       (送件)
    ↓
won  / lost
```

得標率 = won / (won + lost)
目標 > 30%(看歷史 baseline)

---

## 「為什麼本月 0 次?」(冷啟動)

新帳號常見:
1. 該 user 還沒登入過 launcher
2. user 不知道 ⌘K · 不知道 Agent
3. 公司忙 · 沒空試

**Champion 該做**:
- 拉該 user 到桌邊 · 一起跑 onboarding tour(localStorage 沒 chengfu-tour-done · 重 open launcher 自動跳)
- 教 1 個 /命令 + 1 個常用 Agent · 養 5 分鐘習慣
- 1 週後再看 dashboard
