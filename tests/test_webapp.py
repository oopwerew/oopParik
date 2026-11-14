"""Автоматические тесты веб-приложения LUMIÈRE (Flask API)."""
import os
import sys
import unittest
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))

os.environ["DB_DRIVER"] = "sqlite"
os.environ["SQLITE_PATH"] = ":memory:"

from app import create_app
from app.config import Config


class WebAppTestCase(unittest.TestCase):
    def setUp(self):
        config = Config()
        config.driver = "sqlite"
        config.sqlite_path = ":memory:"
        self.app = create_app(config)
        self.client = self.app.test_client()

    def test_index_page(self):
        """Проверка отдачи главной страницы HTML."""
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"LUMI\xc3\x88RE", response.data)

    def test_services_catalog(self):
        """Проверка получения списка услуг."""
        response = self.client.get("/api/services")
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertTrue(data["ok"])
        self.assertGreaterEqual(len(data["services"]), 10)

    def test_auth_register_and_login(self):
        """Проверка регистрации и входа клиента."""
        reg_payload = {
            "name": "Тестовый Пользователь",
            "phone": "+7 999 000-00-00",
            "login": "test_user_webapp",
            "password": "secretpassword",
        }
        res_reg = self.client.post("/api/auth/register", json=reg_payload)
        self.assertEqual(res_reg.status_code, 201)
        reg_data = res_reg.get_json()
        self.assertTrue(reg_data["ok"])
        user_id = reg_data["user"]["id"]

        # Повторная регистрация
        res_dup = self.client.post("/api/auth/register", json=reg_payload)
        self.assertEqual(res_dup.status_code, 409)

        # Вход с верным паролем
        res_login = self.client.post("/api/auth/login", json={
            "login": "test_user_webapp",
            "password": "secretpassword",
        })
        self.assertEqual(res_login.status_code, 200)
        login_data = res_login.get_json()
        self.assertEqual(login_data["user"]["id"], user_id)
        self.assertFalse(login_data["user"]["isAdmin"])

        # Выход
        res_logout = self.client.post("/api/auth/logout")
        self.assertEqual(res_logout.status_code, 200)

    def test_admin_service_permissions(self):
        """Проверка: добавление и удаление услуг разрешено ТОЛЬКО для admin."""
        new_service = {
            "title": "VIP Окрашивание",
            "category": "Окрашивание",
            "price": 9900.0,
            "duration": "180 мин",
            "desc": "Премиум уход",
            "emoji": "✨",
            "image": "",
        }

        # 1. Попытка добавить без авторизации -> 403 Forbidden
        res_guest = self.client.post("/api/services", json=new_service)
        self.assertEqual(res_guest.status_code, 403)

        # 2. Попытка добавить под обычным пользователем -> 403 Forbidden
        self.client.post("/api/auth/register", json={
            "name": "Обычный Клиент",
            "phone": "+7 999 111-22-33",
            "login": "regular_client",
            "password": "password123",
        })
        res_user = self.client.post("/api/services", json=new_service)
        self.assertEqual(res_user.status_code, 403)

        # 3. Вход под учетной записью admin / admin
        res_admin_login = self.client.post("/api/auth/login", json={
            "login": "admin",
            "password": "admin",
        })
        self.assertEqual(res_admin_login.status_code, 200)
        self.assertTrue(res_admin_login.get_json()["user"]["isAdmin"])

        # 4. Добавление услуги под admin -> 201 Created
        res_add = self.client.post("/api/services", json=new_service)
        self.assertEqual(res_add.status_code, 201)
        srv_id = res_add.get_json()["service"]["id"]

        # 5. Выход admin и попытка удалить услугу -> 403 Forbidden
        self.client.post("/api/auth/logout")
        res_del_guest = self.client.delete(f"/api/services/{srv_id}")
        self.assertEqual(res_del_guest.status_code, 403)

        # 6. Снова вход под admin и успешное удаление услуги -> 200 OK
        self.client.post("/api/auth/login", json={"login": "admin", "password": "admin"})
        res_del_admin = self.client.delete(f"/api/services/{srv_id}")
        self.assertEqual(res_del_admin.status_code, 200)

    def test_booking_lifecycle(self):
        """Проверка создания, чтения и отмены записи клиента."""
        booking_payload = {
            "userId": 1,
            "serviceId": 1,
            "clientName": "Екатерина",
            "clientPhone": "+7 (999) 555-44-33",
            "master": "Мария Смирнова",
            "date": "2026-11-20",
            "time": "15:00",
        }
        res_book = self.client.post("/api/bookings", json=booking_payload)
        self.assertEqual(res_book.status_code, 201)
        book_data = res_book.get_json()
        self.assertTrue(book_data["ok"])
        b_id = book_data["booking"]["id"]

        # Получение записей пользователя
        res_get = self.client.get("/api/bookings?userId=1")
        self.assertEqual(res_get.status_code, 200)
        user_bookings = res_get.get_json()["bookings"]
        self.assertTrue(any(b["id"] == b_id for b in user_bookings))

        # Отмена записи
        res_cancel = self.client.delete(f"/api/bookings/{b_id}")
        self.assertEqual(res_cancel.status_code, 200)


if __name__ == "__main__":
    unittest.main()
