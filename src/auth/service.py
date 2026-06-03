import re
import uuid

import bcrypt

from src.shared.config import settings

from .email import send_password_reset_email, send_verification_email
from .queries import (
    fetch_user_by_email,
    fetch_user_by_google_id,
    fetch_user_by_id,
    fetch_user_by_username,
    insert_google_user,
    insert_user,
    link_google_id,
    mark_email_verified,
    update_last_login,
    update_password_hash,
)
from .tokens import (
    consume_token,
    issue_reset_token,
    issue_verification_token,
)

_USERNAME_RE         = re.compile(r"^[A-Za-z0-9_.\-]+$")
_MIN_PASSWORD_LENGTH = 8


class AuthError(Exception):
    def __init__(self, field, message):
        self.field = field
        self.message = message
        super().__init__(message)


# ── Registration ─────────────────────────────────────────────────────────────

def register_user(db, *, full_name, user_name, email, password, image_data, role):
    """
    Returns user_id (str) on success, or an errors dict on failure.
    """
    errors = _validate_registration(full_name, user_name, email, password, role)
    if errors:
        return errors

    if fetch_user_by_username(db, user_name):
        return {"user_name": "That username is already taken."}

    if fetch_user_by_email(db, email):
        return {"user_email": "An account with that email already exists."}

    password_hash = bcrypt.hashpw(
        password.encode("utf-8"), bcrypt.gensalt()
    ).decode("utf-8")

    avatar = image_data if image_data else settings.DEFAULT_USER_AVATAR
    return insert_user(db, full_name, user_name, email, avatar, password_hash, role)


def send_verification(db, user_id, email):
    """Issue a verification token and send the email. Returns True on success, False on failure."""
    token = issue_verification_token(db, user_id)
    try:
        send_verification_email(email, token)
        return True
    except Exception as exc:
        print(f"[EMAIL ERROR] {exc}", flush=True)
        return False


# ── Login ─────────────────────────────────────────────────────────────────────

def authenticate_user(db, user_name, password):
    if not user_name:
        raise AuthError("user_name", "Username is required.")
    if not password:
        raise AuthError("password", "Password is required.")

    user = fetch_user_by_username(db, user_name)
    if not user:
        raise AuthError("user_name", "No account found with that username.")

    if not user.get("passwordHash"):
        raise AuthError(
            "password",
            "This account uses Google sign-in. Use the button below to sign in.",
        )

    if not bcrypt.checkpw(password.encode("utf-8"), user["passwordHash"].encode("utf-8")):
        raise AuthError("password", "Incorrect password.")

    update_last_login(db, user_name)
    return user


# ── Email verification ────────────────────────────────────────────────────────

def verify_email_token(db, token):
    """
    Returns (user, None) on success.
    Returns (None, reason) on failure: 'invalid', 'expired', or 'used'.
    """
    user_id, error = consume_token(db, token, "verify_email")
    if error:
        return None, error

    mark_email_verified(db, user_id)
    user = fetch_user_by_id(db, user_id)
    return user, None


# ── Password reset ────────────────────────────────────────────────────────────

def request_password_reset(db, email):
    """
    Always succeeds silently — never reveals whether the email exists.
    This prevents email enumeration.
    """
    user = fetch_user_by_email(db, email)
    if not user:
        return

    if not user.get("passwordHash") and user.get("googleId"):
        return

    token = issue_reset_token(db, user["id"])
    try:
        send_password_reset_email(email, token)
    except Exception as exc:
        print(f"[WARNING] Reset email to {email} failed: {exc}")


def reset_password(db, token, new_password):
    """
    Returns (True, None) on success.
    Returns (False, reason) on token failure.
    Returns (False, {'password': message}) on validation failure.
    """
    user_id, error = consume_token(db, token, "reset_password")
    if error:
        return False, error

    strength_error = _validate_password_strength(new_password)
    if strength_error:
        return False, {"password": strength_error[0]}

    hashed = bcrypt.hashpw(new_password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
    update_password_hash(db, user_id, hashed)
    return True, None


def validate_reset_token(db, token):
    """Check token validity without consuming it. Returns 'ok', 'invalid', 'expired', or 'used'."""
    row = db.execute(
        "SELECT id, expiresAt, usedAt FROM email_tokens WHERE token = ? AND purpose = 'reset_password'",
        (token,),
    ).fetchone()

    if not row:
        return "invalid"
    if row["usedAt"] is not None:
        return "used"

    from datetime import datetime, timezone
    from .tokens import _parse_timestamp
    if datetime.now(timezone.utc) > _parse_timestamp(row["expiresAt"]):
        return "expired"

    return "ok"


# ── Google OAuth ──────────────────────────────────────────────────────────────

def handle_google_callback(db, google_user_info):
    """
    Process a Google OAuth callback.

    Returns {'user': user_dict} when the user can be logged in immediately.
    Returns {'needs_role': True, 'google_data': {...}} for first-time Google users.
    Raises AuthError for unacceptable Google responses.
    """
    if not google_user_info.get("email_verified"):
        raise AuthError(
            "google",
            "Your Google account's email address is not verified. "
            "Please verify it with Google first.",
        )

    google_id = google_user_info["sub"]
    email     = google_user_info["email"]

    user = fetch_user_by_google_id(db, google_id)
    if user:
        update_last_login(db, user["userName"])
        return {"user": user}

    existing = fetch_user_by_email(db, email)
    if existing:
        link_google_id(db, existing["id"], google_id)
        update_last_login(db, existing["userName"])
        user = fetch_user_by_username(db, existing["userName"])
        return {"user": user}

    return {
        "needs_role": True,
        "google_data": {
            "google_id":  google_id,
            "email":      email,
            "full_name":  google_user_info.get("name", ""),
            "image_url":  google_user_info.get("picture", ""),
        },
    }


def complete_google_signup(db, google_data, role):
    """
    Create an account for a new Google user who has chosen a role.

    Returns the user dict on success, or an errors dict on failure.
    """
    if role not in ("buyer", "seller"):
        return {"user_role": "Select a valid role."}

    user_name = _unique_username(db, google_data["email"])
    image     = google_data.get("image_url") or settings.DEFAULT_USER_AVATAR

    user_id = insert_google_user(
        db,
        full_name=google_data["full_name"],
        user_name=user_name,
        email=google_data["email"],
        image_data=image,
        google_id=google_data["google_id"],
        role=role,
    )
    return fetch_user_by_id(db, user_id)


def _unique_username(db, email):
    base = re.sub(r"[^A-Za-z0-9_.]", "", email.split("@")[0])[:20] or "user"
    candidate = base
    counter = 1
    while fetch_user_by_username(db, candidate):
        candidate = f"{base}{counter}"
        counter += 1
    return candidate


# ── Internal validation ───────────────────────────────────────────────────────

def _validate_registration(full_name, user_name, email, password, role):
    errors = {}

    if not full_name:
        errors["full_name"] = "Full name is required."
    elif len(full_name) > 64:
        errors["full_name"] = "Full name must be 64 characters or less."

    if not user_name:
        errors["user_name"] = "Username is required."
    elif len(user_name) > 24:
        errors["user_name"] = "Username must be 24 characters or less."
    elif not _USERNAME_RE.match(user_name):
        errors["user_name"] = (
            "Username may only contain letters, numbers, underscores, dots, and hyphens."
        )

    if not email:
        errors["user_email"] = "Email is required."
    elif "@" not in email or "." not in email.split("@")[-1]:
        errors["user_email"] = "Enter a valid email address."

    if not password:
        errors["password"] = "Password is required."
    else:
        issues = _validate_password_strength(password)
        if issues:
            errors["password"] = issues[0]

    if role not in ("buyer", "seller"):
        errors["user_role"] = "Select a valid role."

    return errors if errors else None


def _validate_password_strength(password):
    issues = []
    if len(password) < _MIN_PASSWORD_LENGTH:
        issues.append(f"Password must be at least {_MIN_PASSWORD_LENGTH} characters.")
    if not re.search(r"[A-Z]", password):
        issues.append("Password must contain at least one uppercase letter.")
    if not re.search(r"[a-z]", password):
        issues.append("Password must contain at least one lowercase letter.")
    if not re.search(r"[0-9]", password):
        issues.append("Password must contain at least one digit.")
    if not re.search(r"[^A-Za-z0-9]", password):
        issues.append("Password must contain at least one special character.")
    return issues
