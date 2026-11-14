"""Модели данных (по одной на таблицу БД)."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Optional


def format_price(value: float) -> str:
    return f"{value:,.0f}".replace(",", " ") + " ₽"


def format_date(value: str) -> str:
    try:
        return datetime.strptime(str(value), "%Y-%m-%d").strftime("%d.%m.%Y")
    except ValueError:
        return str(value)


@dataclass
class User:
    id: int
    full_name: str
    phone: str
    login: str
    points: int = 0

    @staticmethod
    def from_row(row: dict) -> "User":
        return User(
            id=row["id"],
            full_name=row["full_name"],
            phone=row["phone"],
            login=row["login"],
            points=int(row.get("points") or 0),
        )

    def to_dict(self) -> dict:
        is_admin = (self.login == "admin")
        return {
            "id": self.id,
            "name": self.full_name,
            "phone": self.phone,
            "login": self.login,
            "points": self.points,
            "isAdmin": is_admin,
            "role": "admin" if is_admin else "user",
        }


@dataclass
class Service:
    id: int
    title: str
    category: str
    price: float
    duration: str
    description: str
    emoji: str
    image_url: str

    @staticmethod
    def from_row(row: dict) -> "Service":
        return Service(
            id=row["id"],
            title=row["title"],
            category=row["category"],
            price=float(row["price"]),
            duration=row["duration"] or "",
            description=row["description"] or "",
            emoji=row["emoji"] or "✨",
            image_url=row["image_url"] or "",
        )

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "title": self.title,
            "category": self.category,
            "price": self.price,
            "duration": self.duration,
            "desc": self.description,
            "emoji": self.emoji,
            "image": self.image_url,
        }


@dataclass
class Booking:
    id: int
    user_id: Optional[int]
    service_id: int
    service_title: str
    price: float
    client_name: str
    client_phone: str
    master_name: str
    booking_date: str
    booking_time: str
    points_earned: int = 0
    points_used: int = 0

    @staticmethod
    def from_row(row: dict) -> "Booking":
        return Booking(
            id=row["id"],
            user_id=row["user_id"],
            service_id=row["service_id"],
            service_title=row["service_title"],
            price=float(row["price"]),
            client_name=row["client_name"],
            client_phone=row["client_phone"],
            master_name=row["master_name"],
            booking_date=str(row["booking_date"]),
            booking_time=str(row["booking_time"]),
            points_earned=int(row.get("points_earned") or 0),
            points_used=int(row.get("points_used") or 0),
        )

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "userId": self.user_id,
            "serviceId": self.service_id,
            "serviceTitle": self.service_title,
            "price": self.price,
            "clientName": self.client_name,
            "clientPhone": self.client_phone,
            "master": self.master_name,
            "date": self.booking_date,
            "time": self.booking_time,
            "pointsEarned": self.points_earned,
            "pointsUsed": self.points_used,
        }
