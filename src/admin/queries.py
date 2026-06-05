"""
Admin DB queries — all reads used by admin routes.
"""

# ── Overview stats ────────────────────────────────────────────────────────────

def fetch_admin_stats(db):
    def count(sql, *params):
        return db.execute(sql, params).fetchone()[0]

    return {
        "total_users":       count("SELECT COUNT(*) FROM users"),
        "buyers":            count("SELECT COUNT(*) FROM users WHERE role='buyer'"),
        "sellers":           count("SELECT COUNT(*) FROM users WHERE role='seller'"),
        "admins":            count("SELECT COUNT(*) FROM users WHERE role='admin'"),
        "products_active":   count("SELECT COUNT(*) FROM products WHERE status='active'"),
        "products_inactive": count("SELECT COUNT(*) FROM products WHERE status='inactive'"),
    }


def fetch_recent_users(db, limit=6):
    rows = db.execute(
        """
        SELECT id, fullName, userName, email, role, emailVerified,
               googleId, createdAt
        FROM   users
        ORDER  BY createdAt DESC
        LIMIT  ?
        """,
        (limit,),
    ).fetchall()
    return [dict(r) for r in rows]


def fetch_recent_listings(db, limit=6):
    rows = db.execute(
        """
        SELECT p.id, p.title, p.price, p.status, p.category, p.stock,
               u.userName AS sellerName, p.createdAt
        FROM   products p
        JOIN   users u ON p.sellerId = u.id
        ORDER  BY p.createdAt DESC
        LIMIT  ?
        """,
        (limit,),
    ).fetchall()
    return [dict(r) for r in rows]


# ── User management ───────────────────────────────────────────────────────────

def fetch_admin_users(db, search="", role="", page=1, per_page=20):
    clauses, params = [], []

    if search:
        q = f"%{search}%"
        clauses.append("(userName LIKE ? OR email LIKE ? OR fullName LIKE ?)")
        params += [q, q, q]
    if role:
        clauses.append("role = ?")
        params.append(role)

    where = ("WHERE " + " AND ".join(clauses)) if clauses else ""
    offset = (page - 1) * per_page

    total = db.execute(f"SELECT COUNT(*) FROM users {where}", params).fetchone()[0]
    rows = db.execute(
        f"""
        SELECT id, fullName, userName, email, role, emailVerified,
               googleId, lastLogin, createdAt
        FROM   users {where}
        ORDER  BY createdAt DESC
        LIMIT  ? OFFSET ?
        """,
        params + [per_page, offset],
    ).fetchall()
    return [dict(r) for r in rows], total


# ── Listings management ───────────────────────────────────────────────────────

def fetch_admin_listings(db, search="", status="", page=1, per_page=20):
    clauses, params = [], []

    if search:
        q = f"%{search}%"
        clauses.append("(p.title LIKE ? OR u.userName LIKE ? OR p.category LIKE ?)")
        params += [q, q, q]
    if status:
        clauses.append("p.status = ?")
        params.append(status)

    where = ("WHERE " + " AND ".join(clauses)) if clauses else ""
    offset = (page - 1) * per_page

    total = db.execute(
        f"""
        SELECT COUNT(*)
        FROM   products p
        JOIN   users u ON p.sellerId = u.id
        {where}
        """,
        params,
    ).fetchone()[0]

    rows = db.execute(
        f"""
        SELECT p.id, p.title, p.price, p.status, p.stock, p.category,
               u.userName AS sellerName, u.id AS sellerId,
               p.createdAt, p.updatedAt
        FROM   products p
        JOIN   users u ON p.sellerId = u.id
        {where}
        ORDER  BY p.createdAt DESC
        LIMIT  ? OFFSET ?
        """,
        params + [per_page, offset],
    ).fetchall()
    return [dict(r) for r in rows], total
