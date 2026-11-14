"""Чтение настроек подключения к MySQL из config.ini."""
import configparser
import os


class Config:
    def __init__(self, path=None):
        base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.path = path or os.path.join(base, "config.ini")
        parser = configparser.ConfigParser()
        parser.read(self.path, encoding="utf-8")
        get = lambda key, default: parser.get("mysql", key, fallback=default)
        self.host = get("host", "localhost")
        self.port = int(get("port", "3306"))
        self.user = get("user", "root")
        self.password = get("password", "")
        self.database = get("database", "lumiere_salon")

    def exists(self):
        return os.path.exists(self.path)
