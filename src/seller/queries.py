"""
Seller query layer — all SQL for the seller domain.

Every function returns a plain dict, a list of dicts, or None.
No business logic lives here.
"""


# ── Products ──────────────────────────────────────────────────────────────────

def create_product(db, *, seller_id, title, description, price,
                   category, image_data, stock, status):
    db.execute(
        """
        INSERT INTO products (title, description, price, category,
                              imageData, stock, status, sellerId)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (title, description, price, category, image_data, stock, status, seller_id),
    )
    db.commit()
    row = db.execute(
        "SELECT * FROM products WHERE sellerId = ? ORDER BY createdAt DESC LIMIT 1",
        (seller_id,),
    ).fetchone()
    return dict(row) if row else None


def fetch_product_by_id(db, product_id):
    row = db.execute(
        "SELECT * FROM products WHERE id = ?",
        (product_id,),
    ).fetchone()
    return dict(row) if row else None


def fetch_products_by_seller(
    db,
    seller_id,
    *,
    status_filter=None,
    category_filter=None,
    search=None,
    page=1,
    per_page=20,
):
    """
    Paginated list of a seller's products (excludes archived unless
    status_filter == 'archived').

    Returns: (list_of_dicts, total_count)
    """
    conditions = ["sellerId = ?"]
    params: list = [seller_id]

    if status_filter and status_filter in ("active", "inactive", "archived"):
        conditions.append("status = ?")
        params.append(status_filter)
    else:
        # default: hide archived
        conditions.append("status != 'archived'")

    if category_filter:
        conditions.append("category = ?")
        params.append(category_filter)

    if search:
        conditions.append("(title LIKE ? OR description LIKE ?)")
        like = f"%{search}%"
        params.extend([like, like])

    where = " AND ".join(conditions)
    offset = (page - 1) * per_page

    total = db.execute(
        f"SELECT COUNT(*) FROM products WHERE {where}",
        params,
    ).fetchone()[0]

    rows = db.execute(
        f"""
        SELECT * FROM products
        WHERE {where}
        ORDER BY createdAt DESC
        LIMIT ? OFFSET ?
        """,
        [*params, per_page, offset],
    ).fetchall()

    return [dict(r) for r in rows], total


def fetch_seller_stats(db, seller_id):
    row = db.execute(
        """
        SELECT
            COUNT(*)                                              AS total,
            SUM(CASE WHEN status = 'active'   THEN 1 ELSE 0 END) AS active,
            SUM(CASE WHEN status = 'inactive' THEN 1 ELSE 0 END) AS inactive,
            SUM(CASE WHEN status = 'archived' THEN 1 ELSE 0 END) AS archived,
            SUM(CASE WHEN status != 'archived' THEN stock ELSE 0 END) AS totalStock
        FROM products
        WHERE sellerId = ?
        """,
        (seller_id,),
    ).fetchone()
    return dict(row) if row else {
        "total": 0, "active": 0, "inactive": 0, "archived": 0, "totalStock": 0
    }


def fetch_recent_listings(db, seller_id, limit=5):
    rows = db.execute(
        """
        SELECT * FROM products
        WHERE sellerId = ? AND status != 'archived'
        ORDER BY createdAt DESC
        LIMIT ?
        """,
        (seller_id, limit),
    ).fetchall()
    return [dict(r) for r in rows]


def update_product(db, product_id, *, title, description, price,
                   category, image_data, stock, status):
    db.execute(
        """
        UPDATE products
        SET title = ?, description = ?, price = ?, category = ?,
            imageData = ?, stock = ?, status = ?
        WHERE id = ?
        """,
        (title, description, price, category, image_data, stock, status, product_id),
    )
    db.commit()
    return fetch_product_by_id(db, product_id)


def archive_product(db, product_id):
    db.execute(
        "UPDATE products SET status = 'archived' WHERE id = ?",
        (product_id,),
    )
    db.commit()


def toggle_product_status(db, product_id):
    """Flip active ↔ inactive. Returns the new status string."""
    current = db.execute(
        "SELECT status FROM products WHERE id = ?",
        (product_id,),
    ).fetchone()

    if current is None:
        return None

    new_status = "inactive" if current["status"] == "active" else "active"
    db.execute(
        "UPDATE products SET status = ? WHERE id = ?",
        (new_status, product_id),
    )
    db.commit()
    return new_status
