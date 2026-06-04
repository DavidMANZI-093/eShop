from flask import Blueprint, flash, jsonify, redirect, render_template, request, session, url_for

from src.shared.cart import (
    get_session_cart,
    session_cart_add,
    session_cart_clear,
    session_cart_remove,
    session_cart_set_qty,
)
from src.shared.config import settings
from src.shared.db import get_db
from src.shared.decorators import login_required, role_required, verified_required
from src.dashboard.queries import fetch_user_context

from .queries import fetch_active_products, fetch_cart_products, fetch_product_for_buyer
from .service import CartError, build_cart_view, validate_add_to_cart, validate_update_qty

buyer_bp = Blueprint("buyer", __name__)

_PER_PAGE = 24


# ── Helpers ───────────────────────────────────────────────────────────────────

def _user_ctx() -> dict:
    return fetch_user_context(get_db(), session["user"]) or {}


def _is_json_request() -> bool:
    return request.accept_mimetypes.best == "application/json" or \
           request.headers.get("X-Requested-With") == "XMLHttpRequest"


# ── Browse shop ───────────────────────────────────────────────────────────────

@buyer_bp.route("/shop")
@login_required
@role_required("buyer")
def shop():
    category = request.args.get("category", "").strip() or None
    search   = request.args.get("q",        "").strip() or None

    try:
        page = max(1, int(request.args.get("page", 1)))
    except ValueError:
        page = 1

    products, total = fetch_active_products(
        get_db(),
        category = category,
        search   = search,
        page     = page,
        per_page = _PER_PAGE,
    )
    total_pages = max(1, (total + _PER_PAGE - 1) // _PER_PAGE)

    return render_template(
        "buyer/shop.html",
        **_user_ctx(),
        products       = products,
        total          = total,
        page           = page,
        total_pages    = total_pages,
        per_page       = _PER_PAGE,
        category       = category or "",
        search         = search or "",
        categories     = settings.PRODUCT_CATEGORIES,
        placeholder_img= settings.DEFAULT_PRODUCT_IMAGE,
    )


# ── Product detail ────────────────────────────────────────────────────────────

@buyer_bp.route("/shop/<product_id>")
@login_required
@role_required("buyer")
def product_detail(product_id):
    product = fetch_product_for_buyer(get_db(), product_id)

    if not product or product["status"] != "active":
        flash("Product not found.", "error")
        return redirect(url_for("buyer.shop"))

    # How many of this item does the buyer already have in cart?
    cart_qty = get_session_cart().get(product_id, 0)

    return render_template(
        "buyer/product.html",
        **_user_ctx(),
        product         = product,
        cart_qty        = cart_qty,
        placeholder_img = settings.DEFAULT_PRODUCT_IMAGE,
    )


# ── Cart view ─────────────────────────────────────────────────────────────────

@buyer_bp.route("/cart")
@login_required
@role_required("buyer")
@verified_required
def cart():
    session_cart = get_session_cart()
    products     = fetch_cart_products(get_db(), list(session_cart.keys()))
    cart_view    = build_cart_view(session_cart, products)

    return render_template(
        "buyer/cart.html",
        **_user_ctx(),
        **cart_view,
        placeholder_img = settings.DEFAULT_PRODUCT_IMAGE,
    )


# ── Add to cart ───────────────────────────────────────────────────────────────

@buyer_bp.route("/cart/add", methods=["POST"])
@login_required
@role_required("buyer")
@verified_required
def cart_add():
    product_id = request.form.get("product_id", "").strip()
    try:
        qty = int(request.form.get("quantity", 1))
    except ValueError:
        qty = 1

    product = fetch_product_for_buyer(get_db(), product_id)

    try:
        validate_add_to_cart(product, qty)
    except CartError as e:
        if _is_json_request():
            return jsonify({"ok": False, "error": e.message}), 400
        flash(e.message, "error")
        return redirect(request.referrer or url_for("buyer.shop"))

    # Cap quantity: existing in cart + new must not exceed stock
    cart    = get_session_cart()
    current = cart.get(product_id, 0)
    new_qty = min(current + qty, product["stock"], 99)
    session_cart_set_qty(product_id, new_qty)

    from src.shared.cart import session_cart_count
    count = session_cart_count()

    if _is_json_request():
        return jsonify({"ok": True, "cart_count": count, "quantity": new_qty})

    flash(f'"{product["title"]}" added to your cart.', "success")
    return redirect(request.referrer or url_for("buyer.shop"))


# ── Update cart quantity ──────────────────────────────────────────────────────

@buyer_bp.route("/cart/update", methods=["POST"])
@login_required
@role_required("buyer")
@verified_required
def cart_update():
    product_id = request.form.get("product_id", "").strip()
    try:
        qty = int(request.form.get("quantity", 0))
    except ValueError:
        qty = 0

    product = fetch_product_for_buyer(get_db(), product_id)

    # qty == 0 means remove
    if qty == 0:
        session_cart_remove(product_id)
        if _is_json_request():
            cart_view = build_cart_view(
                get_session_cart(),
                fetch_cart_products(get_db(), list(get_session_cart().keys())),
            )
            return jsonify({
                "ok":         True,
                "removed":    True,
                "cart_count": len(get_session_cart()),
                "cart_total": cart_view["cart_total"],
            })
        return redirect(url_for("buyer.cart"))

    try:
        validate_update_qty(product, qty)
    except CartError as e:
        if _is_json_request():
            return jsonify({"ok": False, "error": e.message}), 400
        flash(e.message, "warning")
        return redirect(url_for("buyer.cart"))

    session_cart_set_qty(product_id, qty)

    if _is_json_request():
        line_total = round((product["price"] if product else 0) * qty, 2)
        cart_view  = build_cart_view(
            get_session_cart(),
            fetch_cart_products(get_db(), list(get_session_cart().keys())),
        )
        return jsonify({
            "ok":         True,
            "quantity":   qty,
            "line_total": line_total,
            "cart_total": cart_view["cart_total"],
            "cart_count": len(get_session_cart()),
        })

    return redirect(url_for("buyer.cart"))


# ── Remove single item ────────────────────────────────────────────────────────

@buyer_bp.route("/cart/remove", methods=["POST"])
@login_required
@role_required("buyer")
@verified_required
def cart_remove():
    product_id = request.form.get("product_id", "").strip()
    session_cart_remove(product_id)

    if _is_json_request():
        cart_view = build_cart_view(
            get_session_cart(),
            fetch_cart_products(get_db(), list(get_session_cart().keys())),
        )
        return jsonify({
            "ok":         True,
            "cart_count": len(get_session_cart()),
            "cart_total": cart_view["cart_total"],
        })

    return redirect(url_for("buyer.cart"))


# ── Clear entire cart ─────────────────────────────────────────────────────────

@buyer_bp.route("/cart/clear", methods=["POST"])
@login_required
@role_required("buyer")
@verified_required
def cart_clear():
    session_cart_clear()

    if _is_json_request():
        return jsonify({"ok": True, "cart_count": 0, "cart_total": 0.0})

    flash("Your cart has been cleared.", "success")
    return redirect(url_for("buyer.cart"))
