"""
shared/cart.py — Session cart helpers and DB sync.

The cart lives in session["cart"] = {product_id: quantity} while the user
is active (fast, no DB on every add/remove).

On sign-in  → restore_from_db: load cart_items from DB → merge into session →
              delete from DB (session is now the live store).

On sign-out → save_to_db: write session cart to cart_items table → then
              session.clear() is called by the auth route.

This module has no Flask blueprint knowledge — it is imported by both
auth/routes.py and buyer/routes.py.
"""

from flask import session


# ── Session helpers ───────────────────────────────────────────────────────────

def get_session_cart() -> dict:
    """Return the current session cart as {product_id: quantity}."""
    return session.get("cart", {})


def set_session_cart(cart: dict) -> None:
    """Overwrite the session cart."""
    session["cart"] = cart
    session.modified = True


def session_cart_count() -> int:
    """Number of distinct product lines in the cart."""
    return len(session.get("cart", {}))


def session_cart_add(product_id: str, quantity: int = 1) -> None:
    """Add quantity to a product in the session cart."""
    cart = get_session_cart()
    cart[product_id] = cart.get(product_id, 0) + quantity
    set_session_cart(cart)


def session_cart_set_qty(product_id: str, quantity: int) -> None:
    """Set the exact quantity for a product. Removes if quantity <= 0."""
    cart = get_session_cart()
    if quantity <= 0:
        cart.pop(product_id, None)
    else:
        cart[product_id] = quantity
    set_session_cart(cart)


def session_cart_remove(product_id: str) -> None:
    """Remove a product from the session cart."""
    cart = get_session_cart()
    cart.pop(product_id, None)
    set_session_cart(cart)


def session_cart_clear() -> None:
    """Empty the session cart."""
    set_session_cart({})


# ── DB sync ───────────────────────────────────────────────────────────────────

def save_cart_to_db(db, user_id: str) -> None:
    """
    Persist the session cart to cart_items before sign-out.
    Replaces any existing rows for this user.
    """
    cart = get_session_cart()
    db.execute("DELETE FROM cart_items WHERE userId = ?", (user_id,))
    for product_id, qty in cart.items():
        if qty > 0:
            db.execute(
                """
                INSERT INTO cart_items (userId, productId, quantity)
                VALUES (?, ?, ?)
                """,
                (user_id, product_id, qty),
            )
    db.commit()


def restore_cart_from_db(db, user_id: str) -> None:
    """
    Load cart_items from DB into session on sign-in, merging with any
    items already in the session (e.g., from a previous anonymous browse).
    After loading, the DB rows are deleted — session is the live store.
    """
    rows = db.execute(
        "SELECT productId, quantity FROM cart_items WHERE userId = ?",
        (user_id,),
    ).fetchall()

    if not rows:
        return

    cart = get_session_cart()
    for row in rows:
        pid = row["productId"]
        qty = row["quantity"]
        cart[pid] = cart.get(pid, 0) + qty

    set_session_cart(cart)

    db.execute("DELETE FROM cart_items WHERE userId = ?", (user_id,))
    db.commit()
