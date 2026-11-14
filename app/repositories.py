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

    def find_by_id(self, user_id: int) -> Optional[dict]:
        rows = self.db.fetch_all("SELECT * FROM users WHERE id = %s", (user_id,))
        return rows[0] if rows else None

    def create(self, full_name: str, phone: str, login: str, password_hash: str, points: int = 0) -> int:
        new_id, _ = self.db.execute(
            "INSERT INTO users (full_name, phone, login, password_hash, points) VALUES (%s, %s, %s, %s, %s)",
            (full_name, phone, login, password_hash, points),
        )
        return new_id

    def update_hash(self, user_id: int, password_hash: str) -> None:
        self.db.execute("UPDATE users SET password_hash = %s WHERE id = %s", (password_hash, user_id))

    def get_points(self, user_id: int) -> int:
        rows = self.db.fetch_all("SELECT points FROM users WHERE id = %s", (user_id,))
        return int(rows[0]["points"]) if rows and rows[0].get("points") is not None else 0

    def add_points(self, user_id: int, delta: int) -> int:
        current = self.get_points(user_id)
        new_balance = max(0, current + delta)
        self.db.execute("UPDATE users SET points = %s WHERE id = %s", (new_balance, user_id))
        return new_balance


class CategoryRepository:
    def __init__(self, db):
        self.db = db

    def all(self) -> List[dict]:
        return self.db.fetch_all("SELECT id, name FROM categories ORDER BY id")

    def find_by_name(self, name: str) -> Optional[dict]:
        rows = self.db.fetch_all("SELECT id, name FROM categories WHERE name = %s", (name,))
        return rows[0] if rows else None

    def find_or_create(self, name: str) -> int:
        cat = self.find_by_name(name)
        if cat:
            return cat["id"]
        new_id, _ = self.db.execute("INSERT INTO categories (name) VALUES (%s)", (name,))
        return new_id


class ServiceRepository:
    BASE = (
        "SELECT s.id, s.title, c.name AS category, s.price, s.duration, "
        "s.description, s.emoji, s.image_url "
        "FROM services s JOIN categories c ON c.id = s.category_id"
    )
    ORDERS = {
        "default": "s.id ASC",
        "asc": "s.price ASC, s.id ASC",
        "desc": "s.price DESC, s.id ASC",
        "name": "s.title ASC",
    }

    def __init__(self, db):
        self.db = db

    def all(self) -> List[Service]:
        """Все услуги (новые сначала)."""
        rows = self.db.fetch_all(self.BASE + " ORDER BY s.id DESC")
        return [Service.from_row(r) for r in rows]

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

    def create(self, category_id: int, title: str, price: float, duration: str = "",
               description: str = "", emoji: str = "✨", image_url: str = "") -> Service:
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

    def recalculate_prices(self, max_threshold: float, new_price: float,
                           min_threshold: Optional[float] = None) -> Tuple[int, str]:
        """
        Массовый перерасчет цен через прямой SQL-запрос UPDATE в MySQL / SQLite.
        Пример: все услуги дешевле max_threshold (например, < 1500 ₽) сделать new_price (например, 2000 ₽).
        Возвращает (количество_измененных_строк, выполненный_SQL_запрос).
        """
        if min_threshold is not None and min_threshold > 0:
            sql = "UPDATE services SET price = %s WHERE price >= %s AND price < %s"
            params = (new_price, min_threshold, max_threshold)
            executed_sql = f"UPDATE services SET price = {new_price:.2f} WHERE price >= {min_threshold:.2f} AND price < {max_threshold:.2f};"
        else:
            sql = "UPDATE services SET price = %s WHERE price < %s"
            params = (new_price, max_threshold)
            executed_sql = f"UPDATE services SET price = {new_price:.2f} WHERE price < {max_threshold:.2f};"

        _, count = self.db.execute(sql, params)
        return count, executed_sql


class BookingRepository:
    BASE = "SELECT * FROM bookings"

    def __init__(self, db):
        self.db = db

    def find_by_user(self, user_id: int) -> List[Booking]:
        rows = self.db.fetch_all(self.BASE + " WHERE user_id = %s ORDER BY id DESC", (user_id,))
        return [Booking.from_row(r) for r in rows]

    def get(self, booking_id: int) -> Optional[Booking]:
        rows = self.db.fetch_all(self.BASE + " WHERE id = %s", (booking_id,))
        return Booking.from_row(rows[0]) if rows else None

    def create(self, user_id: Optional[int], service: Service, client_name: str,
               client_phone: str, master: str, date: str, time: str,
               price: Optional[float] = None, points_earned: int = 0, points_used: int = 0) -> Booking:
        actual_price = price if price is not None else service.price
        new_id, _ = self.db.execute(
            "INSERT INTO bookings (user_id, service_id, service_title, price, points_earned, points_used, "
            "client_name, client_phone, master_name, booking_date, booking_time) "
            "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)",
            (user_id, service.id, service.title, actual_price, points_earned, points_used,
             client_name, client_phone, master, date, time),
        )
        return self.get(new_id)

    def delete(self, booking_id: int) -> bool:
        _, count = self.db.execute("DELETE FROM bookings WHERE id = %s", (booking_id,))
        return count > 0
