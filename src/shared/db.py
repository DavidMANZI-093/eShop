import sqlite3
import uuid
from datetime import datetime

import bcrypt
from flask import current_app, g

from .config import settings


def _parse_timestamp(val):
    try:
        return datetime.fromisoformat(val.decode("utf-8"))
    except Exception:
        try:
            return datetime.strptime(val.decode("utf-8"), "%Y-%m-%d %H:%M:%S")
        except Exception:
            return val.decode("utf-8")


sqlite3.register_converter("TIMESTAMP", _parse_timestamp)


def get_db():
    if "db" not in g:
        g.db = sqlite3.connect(
            current_app.config["DATABASE_PATH"],
            detect_types=sqlite3.PARSE_DECLTYPES,
        )
        g.db.row_factory = sqlite3.Row
        g.db.execute("PRAGMA foreign_keys = ON")
        g.db.create_function("uuid", 0, lambda: str(uuid.uuid4()))
    return g.db


def close_db(error=None):
    db = g.pop("db", None)
    if db is not None:
        db.close()


def init_db():
    db = get_db()
    _create_tables(db)
    _migrate_tables(db)
    _seed_default_admin(db)


def _create_tables(db):
    db.execute(
        f"""
        CREATE TABLE IF NOT EXISTS users (
            id            TEXT PRIMARY KEY DEFAULT (uuid()),
            fullName      VARCHAR(64) NOT NULL,
            userName      VARCHAR(24) UNIQUE NOT NULL,
            email         VARCHAR(254) UNIQUE NOT NULL,
            imageData     TEXT DEFAULT '{settings.DEFAULT_USER_AVATAR}',
            passwordHash  CHAR(60),
            role          VARCHAR(10) NOT NULL CHECK (role IN ('buyer', 'seller', 'admin')),
            emailVerified INTEGER NOT NULL DEFAULT 0,
            googleId      TEXT UNIQUE DEFAULT NULL,
            lastLogin     TIMESTAMP DEFAULT NULL,
            createdAt     TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
    )
    db.execute(
        """
        CREATE TABLE IF NOT EXISTS email_tokens (
            id        TEXT PRIMARY KEY DEFAULT (uuid()),
            userId    TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            token     TEXT UNIQUE NOT NULL,
            purpose   TEXT NOT NULL CHECK (purpose IN ('verify_email', 'reset_password')),
            expiresAt TIMESTAMP NOT NULL,
            usedAt    TIMESTAMP DEFAULT NULL,
            createdAt TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
    )
    db.commit()


def _migrate_tables(db):
    """Add columns that may be missing from databases created before this migration."""
    _add_column_if_missing(db, "users", "emailVerified", "INTEGER NOT NULL DEFAULT 0")
    _add_column_if_missing(db, "users", "googleId",      "TEXT UNIQUE DEFAULT NULL")
    _add_column_if_missing(db, "users", "createdAt",     "TIMESTAMP DEFAULT CURRENT_TIMESTAMP")


def _add_column_if_missing(db, table, column, definition):
    try:
        db.execute(f"ALTER TABLE {table} ADD COLUMN {column} {definition}")
        db.commit()
    except Exception:
        pass  # column already exists — safe to ignore


def _seed_default_admin(db):
    existing = db.execute(
        "SELECT id FROM users WHERE userName = ?",
        (settings.DEFAULT_ADMIN_USER,),
    ).fetchone()

    if existing:
        db.execute(
            "UPDATE users SET emailVerified = 1 WHERE userName = ?",
            (settings.DEFAULT_ADMIN_USER,),
        )
        db.commit()
        return

    hashed_pw = bcrypt.hashpw(
        settings.DEFAULT_ADMIN_PASS.encode("utf-8"), bcrypt.gensalt()
    ).decode("utf-8")

    db.execute(
        """
        INSERT INTO users (fullName, userName, email, passwordHash, role, emailVerified)
        VALUES (?, ?, ?, ?, 'admin', 1)
        """,
        (
            settings.DEFAULT_ADMIN_NAME,
            settings.DEFAULT_ADMIN_USER,
            settings.DEFAULT_ADMIN_EMAIL,
            hashed_pw,
        ),
    )
    db.commit()
