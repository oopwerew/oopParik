"""Регистрация и вход. Хэши bcrypt совместимы с веб-версией (Node.js)."""
from __future__ import annotations

from .models import User


class AuthError(Exception):
    """Ошибка, текст которой можно показать пользователю."""


class PasswordHasher:
    @staticmethod
    def _prepare(password: str) -> bytes:
        return password.encode("utf-8")[:72]   # bcrypt учитывает только 72 байта

    def hash(self, password: str) -> str:
        import bcrypt
        return bcrypt.hashpw(self._prepare(password), bcrypt.gensalt(10)).decode("ascii")

    def verify(self, password: str, hashed: str) -> bool:
        import bcrypt
        try:
            return bcrypt.checkpw(self._prepare(password), hashed.encode("ascii"))
        except ValueError:
            return False


class AuthService:
    def __init__(self, users, hasher=None):
        self.users = users
        self.hasher = hasher or PasswordHasher()

    def register(self, full_name: str, phone: str, login: str, password: str) -> User:
        full_name, phone, login = full_name.strip(), phone.strip(), login.strip()
        if not (full_name and phone and login):
            raise AuthError("Заполните все поля")
        if len(password) < 4:
            raise AuthError("Пароль — минимум 4 символа")
        if self.users.find_by_login(login):
            raise AuthError("Этот логин уже занят")
        user_id = self.users.create(full_name, phone, login, self.hasher.hash(password))
        return User(user_id, full_name, phone, login)

    def login(self, login: str, password: str) -> User:
        row = self.users.find_by_login(login.strip())
        valid = False
        if row:
            stored = row["password_hash"]
            if stored.startswith("$2"):
                valid = self.hasher.verify(password, stored)
            else:
                # старая запись с паролем открытым текстом — проверяем и сразу хэшируем
                valid = password == stored
                if valid:
                    self.users.update_hash(row["id"], self.hasher.hash(password))
        if not valid:
            raise AuthError("Неверный логин или пароль")
        return User(row["id"], row["full_name"], row["phone"], row["login"])
