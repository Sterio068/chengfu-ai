"""
Social media provider adapters · Feature #5

目前全 mock · 實際 Meta/LinkedIn API 等老闆走 developer app 審核(1-2 週)

mock 是 deterministic:
- post_id = "mock-{platform}-{sha256(content)[:12]}"
- 偶爾 simulate 失敗(prompt contains "fail_test")
- 回 contract 跟真 API 等價
"""
import hashlib
import logging
from typing import Optional

logger = logging.getLogger("chengfu")


class PublishError(Exception):
    """Provider 拒絕 · retry 3 次後擋"""
    pass


def publish_facebook(content: str, image_url: Optional[str] = None) -> dict:
    """Mock FB publish · 未來改 facebook-sdk / Graph API v21"""
    if "fail_test" in content:
        raise PublishError("FB 回 400(mock test error)")
    post_id = f"mock-fb-{hashlib.sha256(content.encode()).hexdigest()[:12]}"
    logger.info("[social] FB mock publish · post_id=%s · len=%d", post_id, len(content))
    return {
        "post_id": post_id,
        "url": f"https://www.facebook.com/{post_id}",
        "platform": "facebook",
    }


def publish_instagram(content: str, image_url: Optional[str] = None) -> dict:
    """Mock IG · 需 image_url(IG 不給純文字)"""
    if not image_url:
        raise PublishError("IG 需要圖片(真 API 硬規定)")
    if len(content) > 3000:
        raise PublishError(f"IG caption 上限 3000 字 · 目前 {len(content)}")
    post_id = f"mock-ig-{hashlib.sha256(content.encode()).hexdigest()[:12]}"
    logger.info("[social] IG mock publish · post_id=%s", post_id)
    return {
        "post_id": post_id,
        "url": f"https://www.instagram.com/p/{post_id}",
        "platform": "instagram",
    }


def publish_linkedin(content: str, image_url: Optional[str] = None) -> dict:
    """Mock LinkedIn · UGC post"""
    if len(content) > 3000:
        raise PublishError(f"LinkedIn 上限 3000 字 · 目前 {len(content)}")
    post_id = f"mock-li-{hashlib.sha256(content.encode()).hexdigest()[:12]}"
    logger.info("[social] LinkedIn mock publish · post_id=%s", post_id)
    return {
        "post_id": post_id,
        "url": f"https://www.linkedin.com/feed/update/urn:li:share:{post_id}",
        "platform": "linkedin",
    }


_PROVIDERS = {
    "facebook": publish_facebook,
    "instagram": publish_instagram,
    "linkedin": publish_linkedin,
}


def publish(platform: str, content: str, image_url: Optional[str] = None) -> dict:
    """Dispatch to provider · raise PublishError 前 caller 需 catch"""
    fn = _PROVIDERS.get(platform)
    if not fn:
        raise PublishError(f"不支援的 platform:{platform}")
    return fn(content, image_url)
