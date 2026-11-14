"""Конфигурация приложения LUMIÈRE (из config.ini или переменных окружения)."""
import configparser
import os
from pathlib import Path


class Config:
    def __init__(self, path: str = None):
        base_dir = Path(__file__).resolve().parent.parent
        self.base_dir = base_dir
        self.path = Path(path) if path else base_dir / "config.ini"

        parser = configparser.ConfigParser()
        if self.path.exists():
            parser.read(self.path, encoding="utf-8")

        get_mysql = lambda k, d: os.environ.get(f"DB_{k.upper()}", parser.get("mysql", k, fallback=d))
        self.host = get_mysql("host", "localhost")
        self.port = int(get_mysql("port", "3306"))
        self.user = get_mysql("user", "root")
        self.password = get_mysql("password", "")
        self.database = get_mysql("database", "lumiere_salon")

        get_app = lambda k, d: os.environ.get(k.upper(), parser.get("app", k, fallback=d))
        self.app_port = int(get_app("port", "5001"))
        self.secret_key = get_app("secret_key", "lumiere_secret_key_123")
        # driver: "auto" (пробует MySQL, при ошибке SQLite), "mysql" или "sqlite"
        self.driver = get_app("db_driver", "auto").lower()
        self.sqlite_path = Path(get_app("sqlite_path", str(base_dir / "lumiere.db")))

    def exists(self) -> bool:
        return self.path.exists()
