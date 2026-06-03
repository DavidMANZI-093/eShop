import secrets
from datetime import datetime, timedelta, timezone

_TOKEN_BYTES = 32
_VERIFY_EMAIL_TTL_HOURS = 24
_RESET_PASSWORD_TTL_HOURS = 1


def issue_verification_token(db, user_id):
    return _issue(db, user_id, "verify_email", _VERIFY_EMAIL_TTL_HOURS)


def issue_reset_token(db, user_id):
    return _issue(db, user_id, "reset_password", _RESET_PASSWORD_TTL_HOURS)


def consume_token(db, token, purpose):
    """
    Validate and consume a token.

    Returns (user_id, None) on success.
    Returns (None, reason) on failure where reason is 'invalid', 'expired', or 'used'.
    """
    _purge_expired(db)

    row = db.execute(
        """
        SELECT id, userId, expiresAt, usedAt
        FROM email_tokens
        WHERE token = ? AND purpose = ?
        """,
        (token, purpose),
    ).fetchone()

    if not row:
        return None, "invalid"

    if row["usedAt"] is not None:
        return None, "used"

    expires_at = _parse_timestamp(row["expiresAt"])
    if datetime.now(timezone.utc) > expires_at:
        return None, "expired"

    db.execute(
        "UPDATE email_tokens SET usedAt = CURRENT_TIMESTAMP WHERE id = ?",
        (row["id"],),
    )
    db.commit()
    return row["userId"], None


def invalidate_pending(db, user_id, purpose):
    """Remove any unconsumed tokens for a user+purpose before issuing a fresh one."""
    db.execute(
        "DELETE FROM email_tokens WHERE userId = ? AND purpose = ? AND usedAt IS NULL",
        (user_id, purpose),
    )
    db.commit()


def _issue(db, user_id, purpose, ttl_hours):
    invalidate_pending(db, user_id, purpose)
    token = secrets.token_urlsafe(_TOKEN_BYTES)
    expires_at = datetime.now(timezone.utc) + timedelta(hours=ttl_hours)
    db.execute(
        """
        INSERT INTO email_tokens (userId, token, purpose, expiresAt)
        VALUES (?, ?, ?, ?)
        """,
        (user_id, token, purpose, expires_at.strftime("%Y-%m-%d %H:%M:%S")),
    )
    db.commit()
    return token


def _purge_expired(db):
    db.execute(
        "DELETE FROM email_tokens WHERE expiresAt < datetime('now') AND usedAt IS NULL"
    )
    db.commit()


def _parse_timestamp(value):
    if isinstance(value, datetime):
        ts = value
    else:
        ts = datetime.fromisoformat(str(value))
    return ts if ts.tzinfo else ts.replace(tzinfo=timezone.utc)
