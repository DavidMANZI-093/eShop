from functools import wraps

from flask import flash, redirect, session, url_for


def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if "user" not in session:
            return redirect(url_for("auth.login"))
        return f(*args, **kwargs)

    return decorated


def role_required(*roles):
    def decorator(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            if "user" not in session:
                return redirect(url_for("auth.login"))
            if session.get("role") not in roles:
                return redirect(url_for("auth.login"))
            return f(*args, **kwargs)

        return decorated

    return decorator


def verified_required(f):
    """
    Require email verification before accessing the decorated route.
    Google OAuth users always pass (emailVerified is set to 1 on creation).
    Unverified credential-auth users are redirected to their dashboard
    with a prompt to verify their email.
    """
    @wraps(f)
    def decorated(*args, **kwargs):
        if "user" not in session:
            return redirect(url_for("auth.login"))
        if not session.get("email_verified"):
            flash(
                "Please verify your email address before using your cart.",
                "warning",
            )
            role = session.get("role", "buyer")
            return redirect(url_for(f"dashboard.{role}"))
        return f(*args, **kwargs)

    return decorated
