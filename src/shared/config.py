import os
from dataclasses import dataclass
from dotenv import load_dotenv

load_dotenv()


@dataclass(frozen=True)
class Config:
    DATABASE_NAME: str = os.environ["DATABASE_NAME"]
    DEFAULT_ADMIN_USER: str = os.environ["DEFAULT_ADMIN_USER"]
    DEFAULT_ADMIN_NAME: str = os.environ["DEFAULT_ADMIN_NAME"]
    DEFAULT_ADMIN_PASS: str = os.environ["DEFAULT_ADMIN_PASS"]
    DEFAULT_ADMIN_EMAIL: str = os.environ["DEFAULT_ADMIN_EMAIL"]
    DEFAULT_USER_AVATAR: str = os.environ["DEFAULT_USER_AVATAR"]


settings = Config()
