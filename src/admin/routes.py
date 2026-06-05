"""
Admin blueprint — full platform management for admin role.

Routes:
  GET  /admin/              overview with stats + recent activity
  GET  /admin/users         paginated user list with search + role filter
  POST /admin/users/<id>/role    change a user's role
  POST /admin/users/<id>/verify  toggle emailVerified
  POST /admin/users/<id>/delete  permanently delete user
  GET  /admin/listings      paginated listings with search + status filter
  POST /admin/listings/<id>/toggle  flip active ↔ inactive
  POST /admin/listings/<id>/delete  permanently delete listing
"""

import math

from flask import Blueprint, flash, redirect, render_template, request, session, url_for

from src.shared.db import get_db
from src.shared.decorators import login_required, role_required

admin_bp = Blueprint("admin", __name__)

_PER_PAGE = 20


def _ctx():
    """Reuse the dashboard user-context helper without circular-import issues."""
    from src.dashboard.routes import _user_context
    return _user_context()


# ── Overview ──────────────────────────────────────────────────────────────────

@admin_bp.route("/")
@login_required
@role_required("admin")
def overview():
    from src.admin.queries import (
        fetch_admin_stats, fetch_recent_users, fetch_recent_listings,
    )
    db = get_db()
    return render_template(
        "admin/overview.html",
        **_ctx(),
        stats           = fetch_admin_stats(db),
        recent_users    = fetch_recent_users(db),
        recent_listings = fetch_recent_listings(db),
    )


# ── Users ─────────────────────────────────────────────────────────────────────

@admin_bp.route("/users")
@login_required
@role_required("admin")
def users():
    from src.admin.queries import fetch_admin_users

    db          = get_db()
    search      = request.args.get("q",    "").strip()
    role_filter = request.args.get("role", "").strip()
    try:
        page = max(1, int(request.args.get("page", 1)))
    except (ValueError, TypeError):
        page = 1

    rows, total = fetch_admin_users(
        db, search=search, role=role_filter, page=page, per_page=_PER_PAGE
    )
    total_pages = max(1, math.ceil(total / _PER_PAGE))

    # Identify the current admin so we can protect their row in the template
    self_username = session.get("user")
    self_row = db.execute(
        "SELECT id FROM users WHERE userName = ?", (self_username,)
    ).fetchone()
    self_id = self_row["id"] if self_row else None

    return render_template(
        "admin/users.html",
        **_ctx(),
        admin_users = rows,
        search      = search,
        role_filter = role_filter,
        page        = page,
        total_pages = total_pages,
        total       = total,
        self_id     = self_id,
    )


@admin_bp.route("/users/<user_id>/role", methods=["POST"])
@login_required
@role_required("admin")
def user_set_role(user_id):
    new_role = request.form.get("new_role", "").strip()
    if new_role not in ("buyer", "seller", "admin"):
        flash("Invalid role.", "error")
    else:
        db = get_db()
        target = db.execute(
            "SELECT userName FROM users WHERE id=?", (user_id,)
        ).fetchone()
        if not target:
            flash("User not found.", "error")
        else:
            db.execute("UPDATE users SET role=? WHERE id=?", (new_role, user_id))
            db.commit()
            flash(f"'{target['userName']}' is now a {new_role}.", "success")
    return _back_to_users()


@admin_bp.route("/users/<user_id>/verify", methods=["POST"])
@login_required
@role_required("admin")
def user_toggle_verify(user_id):
    db = get_db()
    target = db.execute(
        "SELECT userName, emailVerified, googleId FROM users WHERE id=?", (user_id,)
    ).fetchone()
    if not target:
        flash("User not found.", "error")
    elif target["googleId"]:
        flash("Google-authenticated users are always considered verified.", "warning")
    else:
        new_val = 0 if target["emailVerified"] else 1
        db.execute("UPDATE users SET emailVerified=? WHERE id=?", (new_val, user_id))
        db.commit()
        state = "verified" if new_val else "unverified"
        flash(f"'{target['userName']}' marked as {state}.", "success")
    return _back_to_users()


@admin_bp.route("/users/<user_id>/delete", methods=["POST"])
@login_required
@role_required("admin")
def user_delete(user_id):
    db = get_db()
    target = db.execute(
        "SELECT userName FROM users WHERE id=?", (user_id,)
    ).fetchone()
    if not target:
        flash("User not found.", "error")
        return _back_to_users()

    # Prevent self-deletion
    self_username = session.get("user")
    if target["userName"] == self_username:
        flash("You cannot delete your own account from the admin panel.", "error")
        return _back_to_users()

    db.execute("DELETE FROM users WHERE id=?", (user_id,))
    db.commit()
    flash(f"User '{target['userName']}' permanently deleted.", "success")
    return _back_to_users()


def _back_to_users():
    return redirect(url_for(
        "admin.users",
        q    = request.form.get("q", ""),
        role = request.form.get("role_filter", ""),
        page = request.form.get("page", 1),
    ))


# ── Listings ──────────────────────────────────────────────────────────────────

@admin_bp.route("/listings")
@login_required
@role_required("admin")
def listings():
    from src.admin.queries import fetch_admin_listings

    db            = get_db()
    search        = request.args.get("q",      "").strip()
    status_filter = request.args.get("status", "").strip()
    try:
        page = max(1, int(request.args.get("page", 1)))
    except (ValueError, TypeError):
        page = 1

    rows, total = fetch_admin_listings(
        db, search=search, status=status_filter, page=page, per_page=_PER_PAGE
    )
    total_pages = max(1, math.ceil(total / _PER_PAGE))

    return render_template(
        "admin/listings.html",
        **_ctx(),
        admin_listings = rows,
        search         = search,
        status_filter  = status_filter,
        page           = page,
        total_pages    = total_pages,
        total          = total,
    )


@admin_bp.route("/listings/<listing_id>/toggle", methods=["POST"])
@login_required
@role_required("admin")
def listing_toggle(listing_id):
    db = get_db()
    target = db.execute(
        "SELECT title, status FROM products WHERE id=?", (listing_id,)
    ).fetchone()
    if not target:
        flash("Listing not found.", "error")
    else:
        new_status = "inactive" if target["status"] == "active" else "active"
        db.execute("UPDATE products SET status=? WHERE id=?", (new_status, listing_id))
        db.commit()
        flash(f"'{target['title']}' is now {new_status}.", "success")
    return _back_to_listings()


@admin_bp.route("/listings/<listing_id>/delete", methods=["POST"])
@login_required
@role_required("admin")
def listing_delete(listing_id):
    db = get_db()
    target = db.execute(
        "SELECT title FROM products WHERE id=?", (listing_id,)
    ).fetchone()
    if not target:
        flash("Listing not found.", "error")
        return _back_to_listings()

    db.execute("DELETE FROM products WHERE id=?", (listing_id,))
    db.commit()
    flash(f"'{target['title']}' permanently deleted.", "success")
    return _back_to_listings()


def _back_to_listings():
    return redirect(url_for(
        "admin.listings",
        q      = request.form.get("q", ""),
        status = request.form.get("status_filter", ""),
        page   = request.form.get("page", 1),
    ))
