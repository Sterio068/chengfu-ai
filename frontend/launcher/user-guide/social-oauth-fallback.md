# 🔌 社群排程 OAuth 降級方案

> v1.3 ship 的是 mock provider · 真接 Meta/IG/LinkedIn API 留 v1.4
> 此檔說明 Meta App 審核期間怎麼運作

---

## 現況(v1.3.0)

### A5 已做(infra)
- DB schema · `db.social_oauth_tokens` · `db.social_oauth_states`
- 4 endpoint · `/social/oauth/{start,callback,disconnect,status}`
- AES-GCM 加密 token(用 LibreChat 同 CREDS_KEY)
- state TTL 10 min(防 CSRF)
- 9 個 unit test 全綠

### B1 沒做(等公司送 Meta App)
- 真打 Meta Graph API
- callback 內仍 mock(回 `MOCK-facebook-xxx` token)
- 排程貼文跑 cron 用 mock provider · 印 「mock-fb-post-id」 · 但 FB 實際沒貼出

---

## 對公司老闆 / Champion 的告知

### 老實話
「v1.3 ship 的社群排程功能 · UI 跟流程都齊 · 但還沒真的把貼文送上 FB/IG/LinkedIn · 因為 Meta 那邊要審 App(1-4 週)。等他們批准 · v1.4 把那一段接上 · 同事完全感受不到差別(Meta App 審核期間 · 我們在 launcher 用 mock 練習 + 收同事意見)」

### 判斷該不該開放給同事用
- **建議開放**:讓同事熟 UI / 排程流程 / 寫文 · 等 Meta 過再切真
- **建議關閉**:怕同事誤以為真貼出 · 收 client 投訴

打開 / 關閉:`config-templates/.env`
```
SOCIAL_FEATURE_ENABLED=true   # launcher sidebar 顯示
SOCIAL_FEATURE_ENABLED=false  # 隱藏 entry · 接 v1.4 才開
```

---

## Meta App 申請流程(公司老闆)

### Step 1 · 建 Meta Developer 帳號
1. https://developers.facebook.com/
2. 登入 Facebook 個人帳號(公司老闆 · 不是公司)
3. 建 Developer Profile · 確認手機

### Step 2 · 建 Business App
1. My Apps → Create App
2. App Type:**Business**
3. App Name:「智慧助理 社群排程」
4. Business Account:綁BM(沒有先建 https://business.facebook.com/)

### Step 3 · 加 Products
- **Facebook Login**(必 · OAuth 流程)
- **Pages**(必 · 發 FB Page 貼文)
- **Instagram Basic Display**(必 · IG)
- **Instagram Content Publishing**(必 · 發 IG 貼文)

### Step 4 · 設定 OAuth Redirect URI
- App Dashboard → Facebook Login → Settings
- Valid OAuth Redirect URIs:
  - `https://ai.<chengfu>.com/api-accounting/social/oauth/callback`(prod)
  - `http://localhost/api-accounting/social/oauth/callback`(dev)

### Step 5 · 申請 Permissions(App Review)
要審以下權限:
- `pages_manage_posts`
- `pages_read_engagement`
- `instagram_basic`
- `instagram_content_publish`

App Review 提交時要附:
- 用途說明:「公司全名 · 內部 10 人小團隊 · 排程客戶代操社群 · 不對外開放」
- 截圖:launcher 的社群排程 UI(現在已有)
- 隱私權政策 URL · 服務條款 URL(公司老闆要寫 · 不複雜)
- 影片 demo:30-60 秒 · 同事點 「連 FB」→ 跳轉 → 貼文出現

審核 1-4 週(Meta 的事 · 不可控)

### Step 6 · LinkedIn(可選)
- https://www.linkedin.com/developers/apps
- Create App
- 同樣需 OAuth redirect + scope 申請
- LinkedIn 審核較快(1 週內)

---

## v1.4 切換 SOP(Meta App 過了)

```bash
# 1. 把 App 過了的 keys 寫進 keychain
security add-generic-password -s 'chengfu-ai-meta-app-id' -w '<APP_ID>'
security add-generic-password -s 'chengfu-ai-meta-app-secret' -w '<APP_SECRET>'
security add-generic-password -s 'chengfu-ai-linkedin-app-id' -w '<APP_ID>'
security add-generic-password -s 'chengfu-ai-linkedin-app-secret' -w '<APP_SECRET>'

# 2. start.sh 自動 export 進 accounting container env
./scripts/start.sh

# 3. 修 services/social_providers.py
# 把 mock_token_response 改成真 call:
# response = httpx.post("https://graph.facebook.com/v18.0/oauth/access_token", ...)

# 4. 一個 user 試 connect
# launcher → 社群排程 → 連 FB
# OAuth 跳轉 → 真授權 → 回 launcher → token 真存

# 5. 排一個測試貼文 · 5 分後 cron 跑
# 看 FB 該 page 真出現
```

---

## 期間 · 同事誤會「為什麼貼文沒出現?」

### 標準回應(Champion 說)
「目前社群排程是練習版 · 我們在等 Meta 批准 App(說錯不能講真話 · 老闆會緊張)。
v1.3 你看到 launcher 介面 · 試排幾篇 · 之後切過去就會真貼了。」

### 顯示在 UI(v1.3 此 PR 加)
launcher 社群 view 上方加 banner:
```
⚠ 練習模式 · 你看到的「已貼出」是 mock · 不會真出現在 FB/IG
等 Meta 批准 App(預計 v1.4 · 1-4 週)後切真
```

> 此 banner 待你 sterio 上 launcher 加 · 後端的 mock_token_response 已 mark `MOCK-` 前綴 · 區分真假

---

## 真有 Meta 審核被拒怎辦?

### 常見拒絕原因
1. **隱私權政策 URL 沒上線** · 必要 · 找 ChatGPT 寫一份貼到自家網站
2. **影片 demo 不清楚** · 不能用測試帳號 demo · 要真 user 流程
3. **App 用途寫太籠統** · 強調「內部使用 · 不對外」· Meta 對 internal use 較友善
4. **截圖沒含 Meta logo** · OAuth screen 不能改

### 重審
被拒 · 看郵件原因 · 修 · 重 submit。
通常 2-3 次能過。

---

## v1.3 不切真的好處

- **0 風險誤貼**(同事 demo 不會貼錯到客戶 page)
- **流程驗證**(等 Meta 期間練習 launcher UI · 改進 UX)
- **教育訓練可進行**(用 mock 演示給同事看)
- **client 不知道**(對外仍呈現 launcher 有此能力)
