import os
import re
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv


def _patch_env_from_file():
    """
    python-dotenv stops at the first line it cannot parse.
    This fallback reads the .env file directly with a permissive parser
    and sets any variable not already present in os.environ.
    """
    env_path = Path(__file__).resolve().parent.parent.parent / ".env"
    if not env_path.exists():
        return

    kv_re = re.compile(r"^([A-Za-z_][A-Za-z0-9_]*)\s*=\s*(.*)$")

    with open(env_path, encoding="utf-8") as fh:
        for raw in fh:
            line = raw.strip()
            if not line or line.startswith("#"):
                continue
            m = kv_re.match(line)
            if not m:
                continue
            key, value = m.group(1), m.group(2).strip()
            if len(value) >= 2 and value[0] == value[-1] and value[0] in ('"', "'"):
                value = value[1:-1]
            if key not in os.environ:
                os.environ[key] = value


load_dotenv()
_patch_env_from_file()


@dataclass(frozen=True)
class Config:
    # Core — required; app will not start if these are missing
    DATABASE_NAME:       str = os.environ["DATABASE_NAME"]
    DEFAULT_ADMIN_USER:  str = os.environ["DEFAULT_ADMIN_USER"]
    DEFAULT_ADMIN_NAME:  str = os.environ["DEFAULT_ADMIN_NAME"]
    DEFAULT_ADMIN_PASS:  str = os.environ["DEFAULT_ADMIN_PASS"]
    DEFAULT_ADMIN_EMAIL: str = os.environ["DEFAULT_ADMIN_EMAIL"]
    DEFAULT_USER_AVATAR: str = os.environ["DEFAULT_USER_AVATAR"]
    APP_SECRET:          str = os.environ["APP_SECRET"]

    # URL — used to build absolute links in emails
    BASE_URL: str = os.environ.get("BASE_URL", "http://localhost:5000")

    # Mail — all optional; empty MAIL_SERVER activates console fallback
    MAIL_SERVER:   str  = os.environ.get("MAIL_SERVER",   "")
    MAIL_PORT:     int  = int(os.environ.get("MAIL_PORT", "587"))
    MAIL_USE_TLS:  bool = os.environ.get("MAIL_USE_TLS", "true").lower() == "true"
    MAIL_USERNAME: str  = os.environ.get("MAIL_USERNAME", "")
    MAIL_PASSWORD: str  = os.environ.get("MAIL_PASSWORD", "")
    MAIL_FROM:     str  = os.environ.get("MAIL_FROM",     "noreply@eshop.com")

    # Google OAuth — optional; empty disables the Google sign-in button
    GOOGLE_CLIENT_ID:     str = os.environ.get("GOOGLE_CLIENT_ID",     "")
    GOOGLE_CLIENT_SECRET: str = os.environ.get("GOOGLE_CLIENT_SECRET", "")

    # Product categories — displayed in listing forms and used for validation
    PRODUCT_CATEGORIES: tuple = (
        "Electronics",
        "Clothing & Apparel",
        "Home & Garden",
        "Books & Media",
        "Sports & Outdoors",
        "Health & Beauty",
        "Toys & Games",
        "Food & Groceries",
        "Automotive",
        "Arts & Crafts",
        "Pet Supplies",
        "Other",
    )


settings = Config()
