"""
Buyer query layer — product browsing + cart page data.
Returns plain dicts or lists of dicts. No business logic.
"""


# ── Product browsing ──────────────────────────────────────────────────────────

def fetch_active_products(
    db,
    *,
    category=None,
    search=None,
    page=1,
    per_page=24,
):
    """
    Paginated list of products visible to buyers (active + stock > 0).
    Returns (list_of_dicts, total_count).
    """
    conditions = ["p.status = 'active'", "p.stock > 0"]
    params = []

    if category:
        conditions.append("p.category = ?")
        params.append(category)

    if search:
        conditions.append("(p.title LIKE ? OR p.description LIKE ?)")
        like = f"%{search}%"
        params.extend([like, like])

    where  = " AND ".join(conditions)
    offset = (page - 1) * per_page

    total = db.execute(
        f"SELECT COUNT(*) FROM products p WHERE {where}",
        params,
    ).fetchone()[0]

    rows = db.execute(
        f"""
        SELECT p.*, u.fullName AS sellerName
        FROM products p
        JOIN users u ON u.id = p.sellerId
        WHERE {where}
        ORDER BY p.createdAt DESC
        LIMIT ? OFFSET ?
        """,
        [*params, per_page, offset],
    ).fetchall()

    return [dict(r) for r in rows], total


def fetch_product_for_buyer(db, product_id):
    """Single active product visible to buyers (includes seller name)."""
    row = db.execute(
        """
        SELECT p.*, u.fullName AS sellerName
        FROM products p
        JOIN users u ON u.id = p.sellerId
        WHERE p.id = ?
        """,
        (product_id,),
    ).fetchone()
    return dict(row) if row else None


# ── Cart page data ────────────────────────────────────────────────────────────

def fetch_cart_products(db, product_ids: list) -> dict:
    """
    Fetch product details for a list of product IDs.
    Returns a dict of {product_id: product_dict} for fast lookup.
    Dead products (archived/deleted) are included so the cart can flag them.
    """
    if not product_ids:
        return {}

    placeholders = ",".join("?" * len(product_ids))
    rows = db.execute(
        f"""
        SELECT p.*, u.fullName AS sellerName
        FROM products p
        JOIN users u ON u.id = p.sellerId
        WHERE p.id IN ({placeholders})
        """,
        product_ids,
    ).fetchall()

    return {row["id"]: dict(row) for row in rows}
