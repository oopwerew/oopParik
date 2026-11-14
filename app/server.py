#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
LUMIÈRE — Flask сервер и REST API.
"""
import os
from pathlib import Path
from flask import Flask, jsonify, render_template, request, session

from .auth import AuthError, AuthService
from .config import Config
from .database import Database
from .repositories import (
    BookingRepository,
    CategoryRepository,
    ServiceRepository,
    UserRepository,
)


def create_app(config: Config = None) -> Flask:
    base_dir = Path(__file__).resolve().parent.parent
    template_dir = base_dir / "templates"
    static_dir = base_dir / "static"

    app = Flask(
        __name__,
        template_folder=str(template_dir),
        static_folder=str(static_dir),
        static_url_path="/static",
    )

    if config is None:
        config = Config()

    app.config["SECRET_KEY"] = config.secret_key
    app.config["CONFIG"] = config
    app.config["PORT"] = config.app_port

    # Инициализация БД и сервисов
    db = Database(config)
    users_repo = UserRepository(db)
    categories_repo = CategoryRepository(db)
    services_repo = ServiceRepository(db)
    bookings_repo = BookingRepository(db)
    auth_service = AuthService(users_repo)

    app.extensions["db"] = db
    app.extensions["users"] = users_repo
    app.extensions["categories"] = categories_repo
    app.extensions["services"] = services_repo
    app.extensions["bookings"] = bookings_repo
    app.extensions["auth"] = auth_service

    def is_admin_request() -> bool:
        """Проверка прав администратора (по сессии или заголовкам)."""
        if session.get("is_admin"):
            return True
        header_login = request.headers.get("X-User-Login", "").strip()
        if header_login == "admin":
            return True
        data = request.get_json(silent=True) or {}
        if str(data.get("userLogin", "")).strip() == "admin" or str(data.get("adminLogin", "")).strip() == "admin":
            return True
        return False

    # =========================================================================
    # Главная страница (Веб-интерфейс парикмахерской)
    # =========================================================================
    @app.route("/")
    def index():
        return render_template("index.html")

    # =========================================================================
    # API: Авторизация и регистрация
    # =========================================================================
    @app.route("/api/auth/register", methods=["POST"])
    def register():
        data = request.get_json(silent=True) or {}
        name = str(data.get("name", "")).strip()
        phone = str(data.get("phone", "")).strip()
        login = str(data.get("login", "")).strip()
        password = str(data.get("password", ""))

        if not (name and phone and login and password):
            return jsonify({"ok": False, "error": "Заполните все поля"}), 400

        try:
            user = auth_service.register(name, phone, login, password)
            session["user_id"] = user.id
            session["login"] = user.login
            session["is_admin"] = (user.login == "admin")
            return jsonify({"ok": True, "user": user.to_dict()}), 201
        except AuthError as err:
            status = 409 if "занят" in str(err) else 400
            return jsonify({"ok": False, "error": str(err)}), status
        except Exception as err:
            return jsonify({"ok": False, "error": f"Ошибка сервера: {err}"}), 500

    @app.route("/api/auth/login", methods=["POST"])
    def login():
        data = request.get_json(silent=True) or {}
        login_val = str(data.get("login", "")).strip()
        password = str(data.get("password", ""))

        if not (login_val and password):
            return jsonify({"ok": False, "error": "Укажите логин и пароль"}), 400

        try:
            user = auth_service.login(login_val, password)
            session["user_id"] = user.id
            session["login"] = user.login
            session["is_admin"] = (user.login == "admin")
            return jsonify({"ok": True, "user": user.to_dict()}), 200
        except AuthError as err:
            return jsonify({"ok": False, "error": str(err)}), 401
        except Exception as err:
            return jsonify({"ok": False, "error": f"Ошибка сервера: {err}"}), 500

    @app.route("/api/auth/logout", methods=["POST"])
    def logout():
        session.clear()
        return jsonify({"ok": True}), 200

    # =========================================================================
    # API: Каталог услуг
    # =========================================================================
    @app.route("/api/services", methods=["GET"])
    def get_services():
        try:
            items = services_repo.all()
            return jsonify({"ok": True, "services": [s.to_dict() for s in items]}), 200
        except Exception as err:
            return jsonify({"ok": False, "error": f"Ошибка загрузки каталога: {err}"}), 500

    @app.route("/api/services", methods=["POST"])
    def add_service():
        if not is_admin_request():
            return jsonify({
                "ok": False,
                "error": "Доступ запрещен. Только администратор (логин: admin) может добавлять услуги."
            }), 403

        data = request.get_json(silent=True) or {}
        title = str(data.get("title", "")).strip()
        category_name = str(data.get("category", "")).strip()

        try:
            price = float(data.get("price", 0))
        except (ValueError, TypeError):
            return jsonify({"ok": False, "error": "Неверная цена"}), 400

        if not title or not category_name or price < 0:
            return jsonify({"ok": False, "error": "Укажите название, категорию и цену"}), 400

        duration = str(data.get("duration", "")).strip()
        desc = str(data.get("desc", "")).strip()
        emoji = str(data.get("emoji", "")).strip() or "✨"
        image = str(data.get("image", "")).strip()

        try:
            cat_id = categories_repo.find_or_create(category_name)
            service = services_repo.create(
                category_id=cat_id,
                title=title,
                price=price,
                duration=duration,
                description=desc,
                emoji=emoji,
                image_url=image,
            )
            return jsonify({"ok": True, "service": service.to_dict()}), 201
        except Exception as err:
            return jsonify({"ok": False, "error": f"Ошибка добавления услуги: {err}"}), 500

    @app.route("/api/services/<int:service_id>", methods=["DELETE"])
    def delete_service(service_id: int):
        if not is_admin_request():
            return jsonify({
                "ok": False,
                "error": "Доступ запрещен. Только администратор (логин: admin) может удалять услуги."
            }), 403

        try:
            ok = services_repo.delete(service_id)
            if ok:
                return jsonify({"ok": True}), 200
            return jsonify({"ok": False, "error": "Услуга не найдена"}), 404
        except Exception as err:
            return jsonify({"ok": False, "error": f"Ошибка удаления: {err}"}), 500

    # =========================================================================
    # API: Записи клиентов
    # =========================================================================
    @app.route("/api/bookings", methods=["GET"])
    def get_bookings():
        user_id = request.args.get("userId", type=int)
        if not user_id:
            return jsonify({"ok": False, "error": "Нужен userId"}), 400

        try:
            items = bookings_repo.find_by_user(user_id)
            return jsonify({"ok": True, "bookings": [b.to_dict() for b in items]}), 200
        except Exception as err:
            return jsonify({"ok": False, "error": f"Ошибка загрузки записей: {err}"}), 500

    @app.route("/api/bookings", methods=["POST"])
    def create_booking():
        data = request.get_json(silent=True) or {}
        service_id = data.get("serviceId")
        if not service_id:
            return jsonify({"ok": False, "error": "Укажите услугу"}), 400

        try:
            service = services_repo.get(int(service_id))
        except (ValueError, TypeError):
            return jsonify({"ok": False, "error": "Неверный ID услуги"}), 400

        if not service:
            return jsonify({"ok": False, "error": "Услуга не найдена"}), 404

        client_name = str(data.get("clientName", "")).strip()
        client_phone = str(data.get("clientPhone", "")).strip()
        master = str(data.get("master", "")).strip()
        date_val = str(data.get("date", "")).strip()
        time_val = str(data.get("time", "")).strip()

        if not (client_name and client_phone and master and date_val and time_val):
            return jsonify({"ok": False, "error": "Заполните все поля записи"}), 400

        user_id = data.get("userId")
        user_id = int(user_id) if user_id else None

        try:
            booking = bookings_repo.create(
                user_id=user_id,
                service=service,
                client_name=client_name,
                client_phone=client_phone,
                master=master,
                date=date_val,
                time=time_val,
            )
            return jsonify({"ok": True, "booking": booking.to_dict()}), 201
        except Exception as err:
            return jsonify({"ok": False, "error": f"Ошибка создания записи: {err}"}), 500

    @app.route("/api/bookings/<int:booking_id>", methods=["DELETE"])
    def delete_booking(booking_id: int):
        try:
            ok = bookings_repo.delete(booking_id)
            if ok:
                return jsonify({"ok": True}), 200
            return jsonify({"ok": False, "error": "Запись не найдена"}), 404
        except Exception as err:
            return jsonify({"ok": False, "error": f"Ошибка отмены записи: {err}"}), 500

    return app
