import uuid


def fetch_user_by_username(db, user_name):
    row = db.execute(
        """
        SELECT id, fullName, userName, email, imageData, passwordHash,
               role, emailVerified, googleId
        FROM users
        WHERE userName = ?
        """,
        (user_name,),
    ).fetchone()
    return dict(row) if row else None


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


def fetch_user_by_email(db, email):
    row = db.execute(
        """
        SELECT id, fullName, userName, email, imageData, passwordHash,
               role, emailVerified, googleId
        FROM users
        WHERE email = ?
        """,
        (email,),
    ).fetchone()
    return dict(row) if row else None


def fetch_user_by_google_id(db, google_id):
    row = db.execute(
        """
        SELECT id, fullName, userName, email, imageData, role, emailVerified
        FROM users
        WHERE googleId = ?
        """,
        (google_id,),
    ).fetchone()
    return dict(row) if row else None


def insert_user(db, full_name, user_name, email, image_data, password_hash, role):
    user_id = str(uuid.uuid4())
    db.execute(
        """
        INSERT INTO users (id, fullName, userName, email, imageData, passwordHash, role)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (user_id, full_name, user_name, email, image_data, password_hash, role),
    )
    db.commit()
    return user_id


def insert_google_user(db, *, full_name, user_name, email, image_data, google_id, role):
    user_id = str(uuid.uuid4())
    db.execute(
        """
        INSERT INTO users
            (id, fullName, userName, email, imageData, googleId, role, emailVerified)
        VALUES (?, ?, ?, ?, ?, ?, ?, 1)
        """,
        (user_id, full_name, user_name, email, image_data, google_id, role),
    )
    db.commit()
    return user_id


def mark_email_verified(db, user_id):
    db.execute(
        "UPDATE users SET emailVerified = 1 WHERE id = ?",
        (user_id,),
    )
    db.commit()


def update_password_hash(db, user_id, password_hash):
    db.execute(
        "UPDATE users SET passwordHash = ? WHERE id = ?",
        (password_hash, user_id),
    )
    db.commit()


def link_google_id(db, user_id, google_id):
    db.execute(
        "UPDATE users SET googleId = ?, emailVerified = 1 WHERE id = ?",
        (google_id, user_id),
    )
    db.commit()


def update_last_login(db, user_name):
    db.execute(
        "UPDATE users SET lastLogin = CURRENT_TIMESTAMP WHERE userName = ?",
        (user_name,),
    )
    db.commit()
