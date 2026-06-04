from flask import (
    Blueprint,
    flash,
    redirect,
    render_template,
    request,
    session,
    url_for,
)

from src.shared.db import get_db
from src.shared.decorators import login_required, role_required

from .queries import fetch_user_context
from .service import ProfileError, change_password, confirm_and_delete, update_profile

dashboard_bp = Blueprint("dashboard", __name__)


# ── Helpers ───────────────────────────────────────────────────────────────────

def _user_context():
    user_name = session.get("user")
    if not user_name:
        return {}
    user = fetch_user_context(get_db(), user_name)
    return user if user else {}


def _sync_session(user):
    """Keep the session in sync after username or email changes."""
    session["user"]           = user["userName"]
    session["role"]           = user["role"]
    session["email_verified"] = bool(user.get("emailVerified", 0))


def _get_current_user_id():
    ctx = fetch_user_context(get_db(), session["user"])
    return ctx["id"] if ctx else None


# ── Role dashboards ───────────────────────────────────────────────────────────

@dashboard_bp.route("/buyer")
@login_required
@role_required("buyer")
def buyer():
    # Buyers land on the shop — no intermediate dashboard needed.
    return redirect(url_for("buyer.shop"))


@dashboard_bp.route("/seller")
@login_required
@role_required("seller")
def seller():
    from src.seller.queries import fetch_recent_listings, fetch_seller_stats

    ctx     = _user_context()
    db      = get_db()
    user_id = ctx.get("id")
    stats   = fetch_seller_stats(db, user_id)    if user_id else {}
    recent  = fetch_recent_listings(db, user_id) if user_id else []

    return render_template(
        "dashboard/seller.html",
        **ctx,
        stats           = stats,
        recent_listings = recent,
    )


@dashboard_bp.route("/admin")
@login_required
@role_required("admin")
def admin():
    return render_template("dashboard/admin.html", **_user_context())


# ── Profile ───────────────────────────────────────────────────────────────────

@dashboard_bp.route("/profile", methods=["GET", "POST"])
@login_required
def profile():
    ctx = _user_context()
    if not ctx:
        return redirect(url_for("auth.login"))

    user_id = ctx["id"]
    password_errors = {}
    profile_errors  = {}

    if request.method == "POST":
        action = request.form.get("action", "")

        # ── Update profile info ───────────────────────────────────────────────
        if action == "update_info":
            full_name  = request.form.get("full_name",     "").strip()
            user_name  = request.form.get("user_name",     "").strip()
            email      = request.form.get("email",         "").strip()
            image_data = request.form.get("profile_base64", "").strip()

            try:
                updated, email_changed = update_profile(
                    get_db(),
                    user_id,
                    full_name=full_name,
                    user_name=user_name,
                    email=email,
                    image_data=image_data,
                    current_username=ctx["userName"],
                    current_email=ctx["email"],
                )
                _sync_session(updated)
                ctx = fetch_user_context(get_db(), session["user"])

                if email_changed:
                    from src.auth.service import send_verification
                    send_verification(get_db(), user_id, updated["email"])
                    flash(
                        "Profile updated. A verification email has been sent to your new address.",
                        "success",
                    )
                else:
                    flash("Profile updated successfully.", "success")

            except ProfileError as e:
                import json
                try:
                    profile_errors = json.loads(e.message)
                except Exception:
                    profile_errors = {e.field: e.message}

        # ── Change password ───────────────────────────────────────────────────
        elif action == "change_password":
            try:
                change_password(
                    get_db(),
                    user_id,
                    current_password=request.form.get("current_password", ""),
                    new_password=request.form.get("new_password", ""),
                    confirm_password=request.form.get("confirm_password", ""),
                )
                flash("Password changed successfully.", "success")
            except ProfileError as e:
                password_errors = {e.field: e.message}

    return render_template(
        "dashboard/profile.html",
        **ctx,
        profile_errors=profile_errors,
        password_errors=password_errors,
    )


# ── Delete account ────────────────────────────────────────────────────────────

@dashboard_bp.route("/delete-account", methods=["GET", "POST"])
@login_required
def delete_account():
    ctx = _user_context()
    if not ctx:
        return redirect(url_for("auth.login"))

    user_id      = ctx["id"]
    has_password = bool(ctx.get("hasPassword", False))
    delete_error = {}

    if request.method == "POST":
        password = request.form.get("password", "") if has_password else None
        try:
            confirm_and_delete(get_db(), user_id, password=password)
            session.clear()
            flash("Your account has been permanently deleted.", "info")
            return redirect(url_for("auth.login"))
        except ProfileError as e:
            delete_error = {e.field: e.message}

    return render_template(
        "dashboard/delete_account.html",
        **ctx,
        has_password=has_password,
        delete_error=delete_error,
    )

