"""
Buyer service layer — cart business logic and validation.
No HTTP or Flask imports; no DB calls — those go through shared/cart.py
and buyer/queries.py respectively.
"""

_MAX_QTY_PER_ITEM = 99


class CartError(Exception):
    def __init__(self, message: str):
        self.message = message
        super().__init__(message)


def build_cart_view(session_cart: dict, products: dict) -> dict:
    """
    Combine the session cart {product_id: qty} with product data
    to produce a structured view used by the cart template.

    Returns:
        {
          "items": [
            {
              "product": {...},
              "quantity": int,
              "line_total": float,
              "available": bool,   # False if archived/deleted
              "capped_qty": int,   # quantity adjusted to stock limit
            },
            ...
          ],
          "cart_total": float,
          "item_count": int,       # distinct lines
          "has_unavailable": bool,
        }
    """
    items          = []
    cart_total     = 0.0
    has_unavailable = False

    for product_id, qty in session_cart.items():
        product   = products.get(product_id)
        available = product is not None and product.get("status") == "active"

        if product is None:
            # Product was deleted — show a tombstone row
            has_unavailable = True
            items.append({
                "product":   {"id": product_id, "title": "This item is no longer available."},
                "quantity":  qty,
                "line_total": 0.0,
                "available": False,
                "capped_qty": 0,
            })
            continue

        capped_qty = min(qty, product.get("stock", 0)) if available else 0
        line_total = round(product["price"] * qty, 2) if available else 0.0

        if not available:
            has_unavailable = True
        else:
            cart_total += line_total

        items.append({
            "product":   product,
            "quantity":  qty,
            "line_total": line_total,
            "available": available,
            "capped_qty": capped_qty,
        })

    return {
        "items":           items,
        "cart_total":      round(cart_total, 2),
        "item_count":      len(session_cart),
        "has_unavailable": has_unavailable,
    }


def validate_add_to_cart(product: dict, qty: int) -> None:
    """
    Validate that a product can be added to the cart.
    Raises CartError with a user-facing message on failure.
    """
    if not product:
        raise CartError("Product not found.")
    if product.get("status") != "active":
        raise CartError("This product is no longer available.")
    if product.get("stock", 0) < 1:
        raise CartError("This product is out of stock.")
    if qty < 1:
        raise CartError("Quantity must be at least 1.")
    if qty > _MAX_QTY_PER_ITEM:
        raise CartError(f"You can add at most {_MAX_QTY_PER_ITEM} of any item.")


def validate_update_qty(product: dict, new_qty: int) -> None:
    """
    Validate a cart quantity update.
    Raises CartError on failure.
    """
    if not product:
        raise CartError("Product not found.")
    if new_qty < 0:
        raise CartError("Quantity cannot be negative.")
    if new_qty > _MAX_QTY_PER_ITEM:
        raise CartError(f"Maximum quantity per item is {_MAX_QTY_PER_ITEM}.")
    if new_qty > product.get("stock", 0):
        raise CartError(
            f"Only {product['stock']} unit(s) available. "
            "Your quantity has been adjusted."
        )
