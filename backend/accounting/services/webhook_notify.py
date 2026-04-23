"""
Webhook Notify · v1.2 Day 3 R26#2 修(取代 LINE Notify · 已停服 2025-03-31)

承富同事可選任一 webhook(Slack / Discord / Telegram bot / Mattermost / 自架)
而非綁死 LINE Notify(LINE Notify 2025-03-31 已停服 · 官方公告 notify-bot.line.me)

webhook URL 通常長這樣:
- Slack:https://hooks.slack.com/services/T.../B.../...
- Discord:https://discord.com/api/webhooks/.../...
- Telegram bot:https://api.telegram.org/bot{TOKEN}/sendMessage(需 chat_id 在 query)
- Mattermost:https://mm.example.com/hooks/...

不同平台 payload 格式略不同 · 我們用「猜」:
- 含 'slack' / 'discord' / 'mattermost' → JSON {"text": ...}
- 含 'telegram' → query string sendMessage
- 其他 → JSON {"text": ...} 預設

best-effort · 失敗不擋主流程
"""
import json
import logging
import urllib.parse
import urllib.request

logger = logging.getLogger("chengfu")


def send(webhook_url: str, message: str, *, timeout: int = 10) -> bool:
    """Generic webhook · 自動偵測 platform 用對應 payload"""
    if not webhook_url:
        return False
    try:
        url = webhook_url.strip()
        is_telegram = "telegram.org" in url
        if is_telegram:
            # Telegram bot · message 進 query string sendMessage
            # webhook_url 需含 ?chat_id=xxx · text 由我們加
            sep = "&" if "?" in url else "?"
            full_url = f"{url}{sep}text={urllib.parse.quote(message[:4096])}"
            req = urllib.request.Request(full_url, method="GET")
        else:
            # Slack / Discord / Mattermost / 通用 · JSON {"text": ...}
            payload = json.dumps({"text": message[:2000]}).encode()
            req = urllib.request.Request(
                url, data=payload, method="POST",
                headers={"Content-Type": "application/json"},
            )
        with urllib.request.urlopen(req, timeout=timeout) as r:
            ok = 200 <= r.status < 300
            if not ok:
                logger.warning("[webhook] send fail status=%d", r.status)
            return ok
    except Exception as e:
        logger.warning("[webhook] send exception: %s", str(e)[:100])
        return False


def notify_user(db, email: str, message: str) -> bool:
    """從 db.user_preferences 拿 webhook_url(舊 line_token 也兼容)"""
    # 優先讀新欄位
    pref = db.user_preferences.find_one({"user_email": email, "key": "webhook_url"})
    if pref and pref.get("value"):
        return send(pref["value"], message)
    # 回退舊 line_token(已停服 · 但 1.2 早期 user 可能存了)
    legacy = db.user_preferences.find_one({"user_email": email, "key": "line_token"})
    if legacy and legacy.get("value"):
        logger.warning("[webhook] %s 仍用 LINE Notify token · 已停服 · 改設 webhook_url", email)
        # 不送 LINE(會 fail)· 不浪費 timeout
    return False


def notify_admin(db, message: str) -> int:
    """所有 admin 都收 · 回成功數"""
    from main import _admin_allowlist
    count = 0
    for email in _admin_allowlist:
        if notify_user(db, email, message):
            count += 1
    return count
