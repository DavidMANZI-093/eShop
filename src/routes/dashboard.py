# routes/dashboard.py
from flask import Blueprint, render_template, session

from ..shared import db

dashboard_bp = Blueprint(
    "dashboard", __name__, template_folder="templates", url_prefix="/dashboard"
)


def _user_context():
    username = session.get("user", "")
    if not username:
        return {"user": None, "email": ""}
    db.cur.execute(
        "SELECT userName, email FROM users WHERE userName = ?", (username,)
    )
    user = db.cur.fetchone()
    return {"user": user[0] if user else None, "email": user[1] if user else ""}


@dashboard_bp.route("/seller")
def seller():
    return render_template("dashboard/seller.html", **_user_context())


@dashboard_bp.route("/buyer")
def buyer():
    return render_template("dashboard/buyer.html", **_user_context())


@dashboard_bp.route("/admin")
def admin():
    return render_template("dashboard/admin.html", **_user_context())
