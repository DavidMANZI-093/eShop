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
from src.shared.decorators import login_required, role_required
from src.dashboard.queries import fetch_user_context

from .queries import (
    fetch_product_by_id,
    fetch_products_by_seller,
    fetch_recent_listings,
    fetch_seller_stats,
)
from .service import (
    ProductError,
    archive_listing,
    toggle_listing_status,
    validate_and_create,
    validate_and_update,
    validate_product_form_errors,
)

seller_bp = Blueprint("seller", __name__)

_PER_PAGE = 20


# ── Helpers ───────────────────────────────────────────────────────────────────

def _user_ctx() -> dict:
    """Full user context required by dashboard/base.html (emailVerified, role,
    imageData, userName, etc.).  Always call this before render_template."""
    return fetch_user_context(get_db(), session["user"]) or {}


def _seller_id() -> str:
    """Return the current seller's user ID — extracted from the already-fetched
    user context to avoid a second DB round-trip."""
    ctx = _user_ctx()
    return ctx.get("id")


def _seller_context() -> dict:
    """Stats + recent listings for dashboard and sidebar context."""
    sid = _seller_id()
    if not sid:
        return {}
    stats  = fetch_seller_stats(get_db(), sid)
    recent = fetch_recent_listings(get_db(), sid, limit=5)
    return {"stats": stats, "recent_listings": recent, "seller_id": sid}


# ── Dashboard (seller home) ───────────────────────────────────────────────────

@seller_bp.route("/dashboard")
@login_required
@role_required("seller")
def dashboard():
    ctx = _seller_context()
    return render_template(
        "seller/dashboard.html",
        **_user_ctx(),
        **ctx,
        categories=settings.PRODUCT_CATEGORIES,
    )


# ── Listings list ─────────────────────────────────────────────────────────────

@seller_bp.route("/listings")
@login_required
@role_required("seller")
def listings():
    sid            = _seller_id()
    status_filter  = request.args.get("status",   "").strip() or None
    category_filter= request.args.get("category", "").strip() or None
    search         = request.args.get("q",        "").strip() or None

    try:
        page = max(1, int(request.args.get("page", 1)))
    except ValueError:
        page = 1

    products, total = fetch_products_by_seller(
        get_db(), sid,
        status_filter   = status_filter,
        category_filter = category_filter,
        search          = search,
        page            = page,
        per_page        = _PER_PAGE,
    )

    total_pages = max(1, (total + _PER_PAGE - 1) // _PER_PAGE)

    return render_template(
        "seller/products.html",
        **_user_ctx(),
        products        = products,
        total           = total,
        page            = page,
        total_pages     = total_pages,
        per_page        = _PER_PAGE,
        status_filter   = status_filter or "",
        category_filter = category_filter or "",
        search          = search or "",
        categories      = settings.PRODUCT_CATEGORIES,
        stats           = fetch_seller_stats(get_db(), sid),
    )


# ── Create listing ────────────────────────────────────────────────────────────

@seller_bp.route("/listings/new", methods=["GET", "POST"])
@login_required
@role_required("seller")
def new_listing():
    errors = {}
    form   = {}

    if request.method == "POST":
        form = {
            "title":       request.form.get("title",       ""),
            "description": request.form.get("description", ""),
            "price":       request.form.get("price",       ""),
            "category":    request.form.get("category",    ""),
            "imageData":   request.form.get("imageData",   ""),
            "stock":       request.form.get("stock",       ""),
            "status":      "active",
        }
        errors = validate_product_form_errors(form)

        if not errors:
            try:
                product = validate_and_create(get_db(), _seller_id(), form)
                flash(f'"{product["title"]}" listed successfully.', "success")
                return redirect(url_for("seller.listings"))
            except ProductError as e:
                errors[e.field] = e.message

    return render_template(
        "seller/product_form.html",
        **_user_ctx(),
        form       = form,
        errors     = errors,
        categories = settings.PRODUCT_CATEGORIES,
        is_edit    = False,
        product    = None,
    )


# ── Edit listing ──────────────────────────────────────────────────────────────

@seller_bp.route("/listings/<product_id>/edit", methods=["GET", "POST"])
@login_required
@role_required("seller")
def edit_listing(product_id):
    sid     = _seller_id()
    product = fetch_product_by_id(get_db(), product_id)

    if not product or product["sellerId"] != sid:
        flash("Listing not found.", "error")
        return redirect(url_for("seller.listings"))

    errors = {}
    form   = {}

    if request.method == "POST":
        form = {
            "title":       request.form.get("title",       ""),
            "description": request.form.get("description", ""),
            "price":       request.form.get("price",       ""),
            "category":    request.form.get("category",    ""),
            "imageData":   request.form.get("imageData",   ""),
            "stock":       request.form.get("stock",       ""),
            # checkbox sends "active" when checked; fallback hidden field sends "inactive"
            "status": request.form.get("status") or request.form.get("_status_fallback", "active"),
        }
        errors = validate_product_form_errors({**form, "status": form["status"]})

        if not errors:
            try:
                updated = validate_and_update(get_db(), product_id, sid, form)
                flash(f'"{updated["title"]}" updated.', "success")
                return redirect(url_for("seller.listings"))
            except ProductError as e:
                errors[e.field] = e.message
    else:
        # Pre-populate form from existing product
        form = {
            "title":       product["title"],
            "description": product["description"],
            "price":       f'{product["price"]:.2f}',
            "category":    product["category"],
            "imageData":   product.get("imageData") or "",
            "stock":       str(product["stock"]),
            "status":      product["status"],
        }

    return render_template(
        "seller/product_form.html",
        **_user_ctx(),
        form       = form,
        errors     = errors,
        categories = settings.PRODUCT_CATEGORIES,
        is_edit    = True,
        product    = product,
    )


# ── Archive listing (soft-delete) ─────────────────────────────────────────────

@seller_bp.route("/listings/<product_id>/archive", methods=["POST"])
@login_required
@role_required("seller")
def archive(product_id):
    try:
        archive_listing(get_db(), product_id, _seller_id())
        flash("Listing archived and removed from the storefront.", "success")
    except ProductError as e:
        flash(e.message, "error")
    return redirect(url_for("seller.listings"))


# ── Toggle active / inactive ──────────────────────────────────────────────────

@seller_bp.route("/listings/<product_id>/toggle", methods=["POST"])
@login_required
@role_required("seller")
def toggle(product_id):
    try:
        new_status = toggle_listing_status(get_db(), product_id, _seller_id())
        label = "active" if new_status == "active" else "inactive"
        flash(f"Listing set to {label}.", "success")
    except ProductError as e:
        flash(e.message, "error")
    return redirect(request.referrer or url_for("seller.listings"))
