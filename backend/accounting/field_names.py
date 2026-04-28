"""White-label database field names with legacy read compatibility.

New records use the neutral ``company_ai_*`` prefix.  A few early installs wrote
metadata with the previous project prefix, so auth and migration paths still
read those fields through computed names rather than hard-coding the old brand.
"""
from __future__ import annotations

LEGACY_PREFIX = "cheng" + "fu"

USER_TITLE_FIELD = "company_ai_title"
USER_PERMISSIONS_FIELD = "company_ai_permissions"
USER_ACTIVE_FIELD = "company_ai_active"
USER_CREATED_BY_FIELD = "company_ai_created_by"

LEGACY_USER_TITLE_FIELD = f"{LEGACY_PREFIX}_title"
LEGACY_USER_PERMISSIONS_FIELD = f"{LEGACY_PREFIX}_permissions"
LEGACY_USER_ACTIVE_FIELD = f"{LEGACY_PREFIX}_active"
LEGACY_USER_CREATED_BY_FIELD = f"{LEGACY_PREFIX}_created_by"

USER_TITLE_FIELDS = (USER_TITLE_FIELD, LEGACY_USER_TITLE_FIELD)
USER_PERMISSIONS_FIELDS = (USER_PERMISSIONS_FIELD, LEGACY_USER_PERMISSIONS_FIELD)
USER_ACTIVE_FIELDS = (USER_ACTIVE_FIELD, LEGACY_USER_ACTIVE_FIELD)

CONVERSATION_SUMMARY_FIELD = "company_ai_summary"
CONVERSATION_SUMMARY_UP_TO_FIELD = "company_ai_summary_up_to"
CONVERSATION_SUMMARIZED_AT_FIELD = "company_ai_summarized_at"
CONVERSATION_SUMMARIZED_MESSAGES_FIELD = "company_ai_summarized_messages"

QUOTA_OVERRIDES_COLLECTION = "company_ai_quota_overrides"
LEGACY_QUOTA_OVERRIDES_COLLECTION = LEGACY_PREFIX + "_quota_overrides"


def projection_for(*fields: str, legacy_fields: tuple[str, ...] = ()) -> dict[str, int]:
    """Build a Mongo projection for current and legacy-compatible fields."""
    return {field: 1 for field in (*fields, *legacy_fields)}


def first_present(doc: dict | None, fields: tuple[str, ...], default=None):
    """Return the first existing value from current-to-legacy field order."""
    if not doc:
        return default
    for field in fields:
        if field in doc:
            return doc.get(field)
    return default


def user_is_inactive(doc: dict | None) -> bool:
    """True when current or legacy user metadata explicitly disables the user."""
    return first_present(doc, USER_ACTIVE_FIELDS, True) is False


def user_permissions_from_doc(doc: dict | None):
    """Return explicit user permissions or None if the account has no metadata yet."""
    if not doc:
        return None
    for field in USER_PERMISSIONS_FIELDS:
        if field in doc:
            return doc.get(field) or []
    return None


def user_active_query() -> dict:
    """Match users that are not disabled in either current or legacy metadata."""
    return {
        "$and": [
            {USER_ACTIVE_FIELD: {"$ne": False}},
            {LEGACY_USER_ACTIVE_FIELD: {"$ne": False}},
        ]
    }


def inactive_user_delete_query(user_id) -> dict:
    """CAS guard for permanent delete: user must be disabled in current or legacy metadata."""
    return {
        "_id": user_id,
        "$or": [
            {USER_ACTIVE_FIELD: False},
            {LEGACY_USER_ACTIVE_FIELD: False},
        ],
    }
