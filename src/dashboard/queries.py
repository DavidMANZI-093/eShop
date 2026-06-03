def fetch_user_context(db, user_name):
    row = db.execute(
        """
        SELECT id, userName, fullName, email, imageData, role, emailVerified,
               googleId, createdAt,
               CASE WHEN passwordHash IS NOT NULL AND passwordHash != ''
                    THEN 1 ELSE 0 END AS hasPassword
        FROM users
        WHERE userName = ?
        """,
        (user_name,),
    ).fetchone()
    return dict(row) if row else None


def update_user_info(db, user_id, *, full_name, image_data):
    db.execute(
        "UPDATE users SET fullName = ?, imageData = ? WHERE id = ?",
        (full_name, image_data, user_id),
    )
    db.commit()


def update_username(db, user_id, user_name):
    db.execute(
        "UPDATE users SET userName = ? WHERE id = ?",
        (user_name, user_id),
    )
    db.commit()


def update_user_email(db, user_id, email):
    db.execute(
        "UPDATE users SET email = ?, emailVerified = 0 WHERE id = ?",
        (email, user_id),
    )
    db.commit()


def update_user_password(db, user_id, password_hash):
    db.execute(
        "UPDATE users SET passwordHash = ? WHERE id = ?",
        (password_hash, user_id),
    )
    db.commit()


def fetch_user_by_id(db, user_id):
    row = db.execute(
        """
        SELECT id, fullName, userName, email, imageData, passwordHash,
               role, emailVerified, googleId
        FROM users
        WHERE id = ?
        """,
        (user_id,),
    ).fetchone()
    return dict(row) if row else None


def delete_user(db, user_id):
    db.execute("DELETE FROM users WHERE id = ?", (user_id,))
    db.commit()
