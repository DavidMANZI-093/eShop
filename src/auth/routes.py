from flask import (
    Blueprint,
    flash,
    redirect,
    render_template,
    request,
    session,
    url_for,
)

from src.shared.config import settings
from src.shared.db import get_db
from src.shared.decorators import login_required
from src.shared.cart import restore_cart_from_db, save_cart_to_db

from .oauth import oauth
from .queries import fetch_user_by_username
from .service import (
    AuthError,
    authenticate_user,
    complete_google_signup,
    handle_google_callback,
    register_user,
    request_password_reset,
    reset_password,
    send_verification,
    validate_reset_token,
    verify_email_token,
)

auth_bp = Blueprint("auth", __name__)


# ── Helpers ───────────────────────────────────────────────────────────────────

def _set_user_session(user):
    session["user"]           = user["userName"]
    session["role"]           = user["role"]
    session["email_verified"] = bool(user.get("emailVerified", 0))


def _dashboard_url(role):
    if role == "buyer":
        return url_for("buyer.shop")
    return url_for(f"dashboard.{role}")


# ── Login / logout ────────────────────────────────────────────────────────────

@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if "user" in session:
        return redirect(_dashboard_url(session["role"]))

    if request.method == "POST":
        user_name = request.form.get("user_name", "").strip()
        password  = request.form.get("password",  "")

        try:
            user = authenticate_user(get_db(), user_name, password)
        except AuthError as e:
            return render_template(
                "auth/login.html",
                errors={e.field: e.message},
                form={"user_name": user_name},
                google_enabled=bool(settings.GOOGLE_CLIENT_ID),
            )

        _set_user_session(user)
        # Restore any previously persisted cart for this buyer
        if user["role"] == "buyer":
            restore_cart_from_db(get_db(), user["id"])
        return redirect(_dashboard_url(user["role"]))

    return render_template(
        "auth/login.html",
        errors={},
        form={},
        google_enabled=bool(settings.GOOGLE_CLIENT_ID),
    )


@auth_bp.route("/logout")
def logout():
    # Persist the cart to DB before clearing the session so it survives
    # across sign-outs for buyers.
    if session.get("role") == "buyer" and "user" in session:
        from src.auth.queries import fetch_user_by_username
        user = fetch_user_by_username(get_db(), session["user"])
        if user:
            save_cart_to_db(get_db(), user["id"])
    session.clear()
    return redirect(url_for("auth.login"))


# ── Signup ────────────────────────────────────────────────────────────────────

@auth_bp.route("/signup", methods=["GET", "POST"])
def signup():
    if "user" in session:
        return redirect(_dashboard_url(session["role"]))

    if request.method == "POST":
        full_name  = request.form.get("full_name",     "").strip()
        user_name  = request.form.get("user_name",     "").strip()
        user_email = request.form.get("user_email",    "").strip()
        password   = request.form.get("password",      "")
        image_data = request.form.get("profile_base64","").strip()
        role       = request.form.get("user_role",     "").strip()

        result = register_user(
            get_db(),
            full_name=full_name,
            user_name=user_name,
            email=user_email,
            password=password,
            image_data=image_data,
            role=role,
        )

        if isinstance(result, dict):
            return render_template(
                "auth/signup.html",
                errors=result,
                form={
                    "full_name":  full_name,
                    "user_name":  user_name,
                    "user_email": user_email,
                    "user_role":  role,
                },
            )

        user_id = result
        send_verification(get_db(), user_id, user_email)

        user = fetch_user_by_username(get_db(), user_name)
        _set_user_session(user)
        flash("Account created! Please check your inbox to verify your email.", "success")
        return redirect(_dashboard_url(role))

    return render_template("auth/signup.html", errors={}, form={})


# ── Email verification ────────────────────────────────────────────────────────

@auth_bp.route("/verify-email/<token>")
def verify_email(token):
    user, error = verify_email_token(get_db(), token)

    if error == "invalid":
        return render_template("auth/verify_result.html", status="invalid")
    if error == "expired":
        return render_template("auth/verify_result.html", status="expired")
    if error == "used":
        return render_template("auth/verify_result.html", status="used")

    if "user" in session and session["user"] == user["userName"]:
        session["email_verified"] = True

    flash("Email address verified. Welcome to eShop!", "success")
    return redirect(url_for("auth.login"))


@auth_bp.route("/resend-verification", methods=["POST"])
@login_required
def resend_verification():
    user = fetch_user_by_username(get_db(), session["user"])
    if user and not user["emailVerified"]:
        send_verification(get_db(), user["id"], user["email"])
        flash("A new verification email has been sent.", "success")
    return redirect(request.referrer or _dashboard_url(session["role"]))


# ── Password reset ────────────────────────────────────────────────────────────

@auth_bp.route("/forgot-password", methods=["GET", "POST"])
def forgot_password():
    if request.method == "POST":
        email = request.form.get("email", "").strip()
        request_password_reset(get_db(), email)
        return render_template("auth/forgot_password.html", submitted=True)

    return render_template("auth/forgot_password.html", submitted=False)


@auth_bp.route("/reset-password/<token>", methods=["GET", "POST"])
def reset_password_route(token):
    status = validate_reset_token(get_db(), token)

    if status != "ok":
        return render_template("auth/reset_password.html", token=token, status=status)

    if request.method == "POST":
        new_password     = request.form.get("password",         "")
        confirm_password = request.form.get("password_confirm", "")

        if new_password != confirm_password:
            return render_template(
                "auth/reset_password.html",
                token=token,
                status="ok",
                errors={"password_confirm": "Passwords do not match."},
            )

        success, outcome = reset_password(get_db(), token, new_password)

        if not success:
            if isinstance(outcome, dict):
                return render_template(
                    "auth/reset_password.html",
                    token=token,
                    status="ok",
                    errors=outcome,
                )
            return render_template("auth/reset_password.html", token=token, status=outcome)

        flash("Password reset successfully. Sign in with your new password.", "success")
        return redirect(url_for("auth.login"))

    return render_template(
        "auth/reset_password.html",
        token=token,
        status="ok",
        errors={},
    )


# ── Google OAuth ──────────────────────────────────────────────────────────────

@auth_bp.route("/google")
def google_login():
    if not settings.GOOGLE_CLIENT_ID:
        flash("Google sign-in is not configured.", "error")
        return redirect(url_for("auth.login"))

    redirect_uri = url_for("auth.google_callback", _external=True)
    return oauth.google.authorize_redirect(redirect_uri)


@auth_bp.route("/google/callback")
def google_callback():
    try:
        token = oauth.google.authorize_access_token()
    except Exception:
        flash("Google sign-in failed. Please try again.", "error")
        return redirect(url_for("auth.login"))

    google_user_info = token.get("userinfo")
    if not google_user_info:
        flash("Could not retrieve your Google profile. Please try again.", "error")
        return redirect(url_for("auth.login"))

    try:
        result = handle_google_callback(get_db(), google_user_info)
    except AuthError as e:
        flash(e.message, "error")
        return redirect(url_for("auth.login"))

    if result.get("needs_role"):
        session["google_oauth_pending"] = result["google_data"]
        return redirect(url_for("auth.complete_profile"))

    user = result["user"]
    _set_user_session(user)
    if user["role"] == "buyer":
        restore_cart_from_db(get_db(), user["id"])
    return redirect(_dashboard_url(user["role"]))


@auth_bp.route("/complete-profile", methods=["GET", "POST"])
def complete_profile():
    google_data = session.get("google_oauth_pending")
    if not google_data:
        return redirect(url_for("auth.login"))

    if request.method == "POST":
        role = request.form.get("user_role", "").strip()
        result = complete_google_signup(get_db(), google_data, role)

        if isinstance(result, dict) and "user_role" in result:
            return render_template(
                "auth/complete_profile.html",
                google_data=google_data,
                errors=result,
            )

        session.pop("google_oauth_pending", None)
        _set_user_session(result)
        flash("Account created! Welcome to eShop.", "success")
        return redirect(_dashboard_url(result["role"]))

    return render_template(
        "auth/complete_profile.html",
        google_data=google_data,
        errors={},
    )
