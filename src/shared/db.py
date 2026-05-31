import sqlite3
import uuid
import bcrypt

from shared import settings


class DataBase:
    def __init__(self, db_name: str):
        self.conn = sqlite3.connect(db_name)
        self.cur = self.conn.cursor()

    def init_db(self):
        self._register_custom_helpers()
        self._create_user_table()
        self._insert_default_admin()

    def _register_custom_helpers(self):
        self.conn.create_function("uuid", 0, lambda: str(uuid.uuid4()))

    def _create_user_table(self):
        self.cur.execute(
            """
                CREATE TABLE IF NOT EXISTS users (
                    id           TEXT PRIMARY KEY DEFAULT (uuid()),
                    fullName     VARCHAR(64) NOT NULL,
                    userName     VARCHAR(24) UNIQUE NOT NULL,
                    email        VARCHAR(254) UNIQUE NOT NULL,
                    imageData    TEXT DEFAULT ?,                      -- converted to base64
                    passwordHash CHAR(60) NOT NULL,                   -- 60 char lenght specific to bycrypt
                    role         VARCHAR(10) NOT NULL CHECK (role IN ('buyer', 'seller', 'admin')),
                    lastLogin    TIMESTAMP DEFAULT NULL
                )
            """,
            (settings.DEFAULT_USER_AVATAR,),
        )
        self.conn.commit()

    def _insert_default_admin(self):
        hashed_pw = bcrypt.hashpw(
            settings.DEFAULT_ADMIN_PASS.encode("utf-8"), bcrypt.gensalt()
        ).decode("utf-8")

        self.cur.execute(
            """
                INSERT INTO users (fullName, userName, email, passwordHash, role)
                VALUES (?, ?, ?, ?, 'admin')
                ON CONFLICT(userName) DO NOTHING -- ensuring no duplicate crushes
            """,
            (
                settings.DEFAULT_ADMIN_NAME,
                settings.DEFAULT_ADMIN_USER,
                settings.DEFAULT_ADMIN_EMAIL,
                hashed_pw,
            ),
        )
        self.conn.commit()

    def close_connection(self):
        self.conn.close()


db = DataBase(settings.DATABASE_NAME)
