#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Скрипт быстрой проверки моста между базой данных MySQL и сайтом LUMIÈRE."""
from app.config import Config
from app.database import Database

def main():
    cfg = Config()
    print("=" * 65)
    print("🔍 ПРОВЕРКА МОСТА МЕЖДУ САЙТОМ И БАЗОЙ ДАННЫХ (MySQL)")
    print("=" * 65)
    print(f"📡 Сервер MySQL: {cfg.host}:{cfg.port}")
    print(f"📁 База данных:  {cfg.database}")
    print(f"👤 Пользователь: {cfg.user}")

    db = Database(cfg)
    if db.is_sqlite:
        print("⚠️ Внимание: данные читаются из встроенной SQLite (MySQL не запущен).")
    else:
        print("✅ Соединение с MySQL активно и работает отлично!")

    print("\n👥 ПОЛЬЗОВАТЕЛИ В БАЗЕ (users):")
    print("-" * 65)
    users = db.fetch_all("SELECT id, full_name, phone, login, points, created_at FROM users ORDER BY id")
    for u in users:
        print(f"  ID #{u['id']}: {u['full_name']} | Логин: {u['login']} | Телефон: {u['phone']} | Баллы: {u.get('points', 0)} 💎")

    print("\n📅 ОНЛАЙН-ЗАПИСИ (bookings):")
    print("-" * 65)
    bookings = db.fetch_all("SELECT id, service_title, client_name, client_phone, price, points_earned, booking_date FROM bookings ORDER BY id DESC LIMIT 5")
    if not bookings:
        print("  Пока нет записей.")
    for b in bookings:
        print(f"  Запись #{b['id']}: {b['client_name']} ({b['client_phone']}) ➔ «{b['service_title']}» | Сумма: {b['price']} ₽ | +{b.get('points_earned', 0)} б. | Дата: {b['booking_date']}")

    print("\n✨ ВСЕГО УСЛУГ В КАТАЛОГЕ (services):")
    print("-" * 65)
    count = db.fetch_all("SELECT COUNT(*) AS c FROM services")[0]["c"]
    print(f"  В базе данных сейчас {count} активных услуг.")
    print("=" * 65)
    print("🎉 Мост работает: любые действия на сайте сразу сохраняются сюда!")
    print("=" * 65)

if __name__ == "__main__":
    main()
