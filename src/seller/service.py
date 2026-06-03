"""
Seller service layer — validation, authorization, and business logic.

Routes call this layer; this layer calls queries.
No Flask imports; no HTTP concerns.
"""
import re

from src.shared.config import settings

from .queries import (
    archive_product,
    create_product,
    fetch_product_by_id,
    toggle_product_status,
    update_product,
)

_MAX_IMAGE_BYTES   = 2 * 1024 * 1024  # 2 MB (base64 string length proxy)
_MAX_PRICE         = 999_999.99
_MAX_STOCK         = 99_999
_MAX_TITLE_LEN     = 128
_MIN_TITLE_LEN     = 3
_MAX_DESC_LEN      = 5_000
_MIN_DESC_LEN      = 10


class ProductError(Exception):
    def __init__(self, field: str, message: str):
        self.field   = field
        self.message = message
        super().__init__(message)


# ── Authorization ─────────────────────────────────────────────────────────────

def authorize_product(db, product_id: str, seller_id: str) -> dict:
    """
    Return the product dict if it exists and belongs to seller_id.
    Raises ProductError otherwise.
    """
    product = fetch_product_by_id(db, product_id)
    if not product:
        raise ProductError("product", "Listing not found.")
    if product["sellerId"] != seller_id:
        raise ProductError("product", "You do not have permission to modify this listing.")
    return product


# ── Create ────────────────────────────────────────────────────────────────────

def validate_and_create(db, seller_id: str, form: dict) -> dict:
    """
    Validate form data, create the product, and return the new product dict.
    Raises ProductError on any validation failure.
    """
    errors = _validate_product_form(form)
    if errors:
        field, msg = next(iter(errors.items()))
        raise ProductError(field, msg)

    return create_product(
        db,
        seller_id   = seller_id,
        title       = form["title"].strip(),
        description = form["description"].strip(),
        price       = round(float(form["price"]), 2),
        category    = form["category"].strip(),
        image_data  = form.get("imageData") or None,
        stock       = int(form["stock"]),
        status      = form.get("status", "active"),
    )


def validate_product_form_errors(form: dict) -> dict:
    """Return all field errors as a dict (field → message). Empty = valid."""
    return _validate_product_form(form)


# ── Update ────────────────────────────────────────────────────────────────────

def validate_and_update(db, product_id: str, seller_id: str, form: dict) -> dict:
    """
    Authorize, validate, update. Returns updated product dict.
    Raises ProductError on auth or validation failure.
    """
    product = authorize_product(db, product_id, seller_id)

    errors = _validate_product_form(form, is_edit=True)
    if errors:
        field, msg = next(iter(errors.items()))
        raise ProductError(field, msg)

    image_data = form.get("imageData") or product.get("imageData")

    return update_product(
        db,
        product_id,
        title       = form["title"].strip(),
        description = form["description"].strip(),
        price       = round(float(form["price"]), 2),
        category    = form["category"].strip(),
        image_data  = image_data,
        stock       = int(form["stock"]),
        status      = form.get("status", "active"),
    )


# ── Archive (soft-delete) ─────────────────────────────────────────────────────

def archive_listing(db, product_id: str, seller_id: str) -> None:
    authorize_product(db, product_id, seller_id)
    archive_product(db, product_id)


# ── Toggle status ─────────────────────────────────────────────────────────────

def toggle_listing_status(db, product_id: str, seller_id: str) -> str:
    """Returns the new status string."""
    product = authorize_product(db, product_id, seller_id)
    if product["status"] == "archived":
        raise ProductError("status", "Archived listings cannot be toggled.")
    return toggle_product_status(db, product_id)


# ── Internal validation ───────────────────────────────────────────────────────

def _validate_product_form(form: dict, *, is_edit: bool = False) -> dict:
    errors: dict = {}

    # title
    title = (form.get("title") or "").strip()
    if not title:
        errors["title"] = "Title is required."
    elif len(title) < _MIN_TITLE_LEN:
        errors["title"] = f"Title must be at least {_MIN_TITLE_LEN} characters."
    elif len(title) > _MAX_TITLE_LEN:
        errors["title"] = f"Title must be {_MAX_TITLE_LEN} characters or less."

    # description
    desc = (form.get("description") or "").strip()
    if not desc:
        errors["description"] = "Description is required."
    elif len(desc) < _MIN_DESC_LEN:
        errors["description"] = f"Description must be at least {_MIN_DESC_LEN} characters."
    elif len(desc) > _MAX_DESC_LEN:
        errors["description"] = f"Description must be {_MAX_DESC_LEN} characters or less."

    # price
    price_raw = (form.get("price") or "").strip()
    if not price_raw:
        errors["price"] = "Price is required."
    else:
        try:
            price = float(price_raw)
            if price < 0:
                errors["price"] = "Price cannot be negative."
            elif price > _MAX_PRICE:
                errors["price"] = f"Price cannot exceed {_MAX_PRICE:,.2f}."
            elif not re.match(r"^\d+(\.\d{1,2})?$", price_raw):
                errors["price"] = "Price must have at most 2 decimal places."
        except ValueError:
            errors["price"] = "Enter a valid price."

    # category
    category = (form.get("category") or "").strip()
    if not category:
        errors["category"] = "Category is required."
    elif category not in settings.PRODUCT_CATEGORIES:
        errors["category"] = "Select a valid category."

    # stock
    stock_raw = (form.get("stock") or "").strip()
    if stock_raw == "":
        errors["stock"] = "Stock quantity is required."
    else:
        try:
            stock = int(stock_raw)
            if stock < 0:
                errors["stock"] = "Stock cannot be negative."
            elif stock > _MAX_STOCK:
                errors["stock"] = f"Stock cannot exceed {_MAX_STOCK:,}."
        except ValueError:
            errors["stock"] = "Stock must be a whole number."

    # imageData — required; if provided must be a data URI and within size limit
    image_data = form.get("imageData") or ""
    if not image_data:
        errors["imageData"] = "A product image is required."
    elif not image_data.startswith("data:image/"):
        errors["imageData"] = "Invalid image format."
    elif len(image_data) > _MAX_IMAGE_BYTES * 1.4:
        # base64 inflates by ~1.33×; 1.4× gives a safe upper bound
        errors["imageData"] = "Image must be under 2 MB."

    # status (edit only, optional field)
    if is_edit:
        status = (form.get("status") or "").strip()
        if status and status not in ("active", "inactive"):
            errors["status"] = "Invalid status."

    return errors
