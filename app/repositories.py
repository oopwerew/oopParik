"""Репозитории — по одному классу на таблицу. Здесь весь SQL."""
from __future__ import annotations

from typing import List, Optional

from .models import Booking, Service


class UserRepository:
    def __init__(self, db):
        self.db = db

    def find_by_login(self, login: str) -> Optional[dict]:
        rows = self.db.fetch_all("SELECT * FROM users WHERE login = %s", (login,))
        return rows[0] if rows else None

    def create(self, full_name, phone, login, password_hash) -> int:
        new_id, _ = self.db.execute(
            "INSERT INTO users (full_name, phone, login, password_hash) VALUES (%s, %s, %s, %s)",
            (full_name, phone, login, password_hash),
        )
        return new_id

    def update_hash(self, user_id: int, password_hash: str) -> None:
        self.db.execute("UPDATE users SET password_hash = %s WHERE id = %s", (password_hash, user_id))


class CategoryRepository:
    def __init__(self, db):
        self.db = db

    def all(self) -> List[dict]:
        return self.db.fetch_all("SELECT id, name FROM categories ORDER BY id")


class ServiceRepository:
    BASE = (
        "SELECT s.id, s.title, c.name AS category, s.price, s.duration, "
        "s.description, s.emoji, s.image_url "
        "FROM services s JOIN categories c ON c.id = s.category_id"
    )
    ORDERS = {  # whitelist — пользовательский ввод в ORDER BY не попадает
        "default": "s.id ASC",
        "asc": "s.price ASC, s.id ASC",
        "desc": "s.price DESC, s.id ASC",
        "name": "s.title ASC",
    }

    def __init__(self, db):
        self.db = db

    def search(self, text: str = "", category_id: Optional[int] = None,
               max_price: Optional[float] = None, sort: str = "default") -> List[Service]:
        """Поиск + фильтрация + сортировка одним SQL-запросом."""
        conditions, params = [], []
        if text:
            escaped = text.replace("|", "||").replace("%", "|%").replace("_", "|_")
            pattern = f"%{escaped}%"
            conditions.append(
                "(s.title LIKE %s ESCAPE '|' OR s.description LIKE %s ESCAPE '|' "
                "OR c.name LIKE %s ESCAPE '|')"
            )
            params += [pattern, pattern, pattern]
        if category_id is not None:
            conditions.append("s.category_id = %s")
            params.append(category_id)
        if max_price is not None:
            conditions.append("s.price <= %s")
            params.append(max_price)

        sql = self.BASE
        if conditions:
            sql += " WHERE " + " AND ".join(conditions)
        sql += " ORDER BY " + self.ORDERS.get(sort, self.ORDERS["default"])
        return [Service.from_row(r) for r in self.db.fetch_all(sql, tuple(params))]

    def get(self, service_id: int) -> Optional[Service]:
        rows = self.db.fetch_all(self.BASE + " WHERE s.id = %s", (service_id,))
        return Service.from_row(rows[0]) if rows else None

    def max_price(self) -> float:
        rows = self.db.fetch_all("SELECT COALESCE(MAX(price), 0) AS m FROM services")
        return float(rows[0]["m"])

    def create(self, category_id, title, price, duration, description, emoji, image_url) -> Service:
        new_id, _ = self.db.execute(
            "INSERT INTO services (category_id, title, price, duration, description, emoji, image_url) "
            "VALUES (%s, %s, %s, %s, %s, %s, %s)",
            (category_id, title, price, duration or None, description or None,
             emoji or None, image_url or None),
        )
        return self.get(new_id)

    def delete(self, service_id: int) -> bool:
        _, count = self.db.execute("DELETE FROM services WHERE id = %s", (service_id,))
        return count > 0


class BookingRepository:
    BASE = "SELECT * FROM bookings"

    def __init__(self, db):
        self.db = db

    def find_by_user(self, user_id: int) -> List[Booking]:
        rows = self.db.fetch_all(self.BASE + " WHERE user_id = %s ORDER BY id DESC", (user_id,))
        return [Booking.from_row(r) for r in rows]

    def create(self, user_id: Optional[int], service: Service, client_name: str,
               client_phone: str, master: str, date: str, time: str) -> Booking:
        # название и цену берём из услуги в БД — как и в версии сайта
        new_id, _ = self.db.execute(
            "INSERT INTO bookings (user_id, service_id, service_title, price, client_name, "
            "client_phone, master_name, booking_date, booking_time) "
            "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)",
            (user_id, service.id, service.title, service.price, client_name,
             client_phone, master, date, time),
        )
        rows = self.db.fetch_all(self.BASE + " WHERE id = %s", (new_id,))
        return Booking.from_row(rows[0])

    def delete(self, booking_id: int) -> bool:
        _, count = self.db.execute("DELETE FROM bookings WHERE id = %s", (booking_id,))
        return count > 0
