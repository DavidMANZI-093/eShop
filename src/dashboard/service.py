import re

import bcrypt

from src.shared.config import settings

from .queries import (
    delete_user,
    fetch_user_by_id,
    update_user_email,
    update_user_info,
    update_user_password,
    update_username,
)

_USERNAME_RE         = re.compile(r"^[A-Za-z0-9_.\-]+$")
_MIN_PASSWORD_LENGTH = 8


class ProfileError(Exception):
    def __init__(self, field, message):
        self.field = field
        self.message = message
        super().__init__(message)


# ── Profile update ────────────────────────────────────────────────────────────

def update_profile(db, user_id, *, full_name, user_name, email,
                   image_data, current_username, current_email):
    """
    Validate and apply profile changes.

    Returns (updated_user, email_changed: bool) on success.
    Raises ProfileError on validation or uniqueness failure.
    """
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
        errors["email"] = "Email is required."
    elif "@" not in email or "." not in email.split("@")[-1]:
        errors["email"] = "Enter a valid email address."

    if errors:
        raise ProfileError("form", str(errors))

    from src.auth.queries import fetch_user_by_username, fetch_user_by_email

    if user_name != current_username:
        if fetch_user_by_username(db, user_name):
            raise ProfileError("user_name", "That username is already taken.")
        update_username(db, user_id, user_name)

    email_changed = email != current_email
    if email_changed:
        conflict = fetch_user_by_email(db, email)
        if conflict and conflict["id"] != user_id:
            raise ProfileError("email", "An account with that email already exists.")
        update_user_email(db, user_id, email)

    avatar = image_data if image_data else None
    update_user_info(
        db,
        user_id,
        full_name=full_name,
        image_data=avatar or _current_avatar(db, user_id),
    )

    updated = fetch_user_by_id(db, user_id)
    return updated, email_changed


def _current_avatar(db, user_id):
    user = fetch_user_by_id(db, user_id)
    return user["imageData"] if user else settings.DEFAULT_USER_AVATAR


# ── Password change ───────────────────────────────────────────────────────────

def change_password(db, user_id, *, current_password, new_password, confirm_password):
    """
    Raises ProfileError on validation or auth failure.
    Returns True on success.
    """
    user = fetch_user_by_id(db, user_id)
    if not user:
        raise ProfileError("form", "User not found.")

    if not user.get("passwordHash"):
        raise ProfileError(
            "current_password",
            "Your account uses Google sign-in and does not have a password.",
        )

    if not current_password:
        raise ProfileError("current_password", "Current password is required.")

    if not bcrypt.checkpw(
        current_password.encode("utf-8"),
        user["passwordHash"].encode("utf-8"),
    ):
        raise ProfileError("current_password", "Incorrect current password.")

    issues = _validate_password_strength(new_password)
    if issues:
        raise ProfileError("new_password", issues[0])

    if new_password != confirm_password:
        raise ProfileError("confirm_password", "Passwords do not match.")

    hashed = bcrypt.hashpw(new_password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
    update_user_password(db, user_id, hashed)
    return True


# ── Account deletion ──────────────────────────────────────────────────────────

def confirm_and_delete(db, user_id, *, password):
    """
    Verify the password (if the account has one) then permanently delete the user.
    Google-only accounts can delete without a password by passing password=None.

    Raises ProfileError on auth failure.
    Returns True on success.
    """
    user = fetch_user_by_id(db, user_id)
    if not user:
        raise ProfileError("form", "User not found.")

    has_password = bool(user.get("passwordHash"))

    if has_password:
        if not password:
            raise ProfileError("password", "Enter your password to confirm deletion.")
        if not bcrypt.checkpw(
            password.encode("utf-8"),
            user["passwordHash"].encode("utf-8"),
        ):
            raise ProfileError("password", "Incorrect password.")

    delete_user(db, user_id)
    return True


# ── Helpers ───────────────────────────────────────────────────────────────────

def get_user_by_id(db, user_id):
    return fetch_user_by_id(db, user_id)


def _validate_password_strength(password):
    issues = []
    if not password:
        return ["New password is required."]
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
