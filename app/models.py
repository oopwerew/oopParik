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
            booking_time=row["booking_time"],
        )
