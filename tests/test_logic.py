"""Тесты логики без Qt и без MySQL: БД подменяется на SQLite в памяти."""
import os
import sqlite3
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.auth import AuthError, AuthService
from app.repositories import BookingRepository, CategoryRepository, ServiceRepository, UserRepository
from app.themes import THEMES, Theme, build_stylesheet, mix


class FakeDatabase:
    def __init__(self):
        self.conn = sqlite3.connect(":memory:")
        self.conn.row_factory = sqlite3.Row
        self.conn.execute("PRAGMA foreign_keys = ON")
        self.conn.executescript("""
        CREATE TABLE users (id INTEGER PRIMARY KEY AUTOINCREMENT, full_name TEXT NOT NULL,
            phone TEXT NOT NULL, login TEXT NOT NULL UNIQUE, password_hash TEXT NOT NULL, created_at TEXT);
        CREATE TABLE categories (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL UNIQUE);
        CREATE TABLE services (id INTEGER PRIMARY KEY AUTOINCREMENT,
            category_id INTEGER NOT NULL REFERENCES categories(id) ON DELETE CASCADE,
            title TEXT NOT NULL, price REAL NOT NULL, duration TEXT, description TEXT, emoji TEXT, image_url TEXT);
        CREATE TABLE bookings (id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
            service_id INTEGER NOT NULL REFERENCES services(id) ON DELETE CASCADE,
            service_title TEXT NOT NULL, price REAL NOT NULL, client_name TEXT NOT NULL,
            client_phone TEXT NOT NULL, master_name TEXT NOT NULL, booking_date TEXT NOT NULL,
            booking_time TEXT NOT NULL, created_at TEXT);
        INSERT INTO categories (id, name) VALUES (1,'Стрижки'),(2,'Окрашивание'),(5,'Товары для дома');
        INSERT INTO services (id, category_id, title, price, duration, description, emoji) VALUES
          (1,1,'Женская стрижка',2800,'60 мин','Мытьё головы и укладка','✂️'),
          (2,1,'Мужская стрижка',1900,'45 мин','Классика и fade','💈'),
          (4,2,'Окрашивание в один тон',4800,'120 мин','Безаммиачное окрашивание','🎨'),
          (10,5,'Маска с арганой',2300,'250 мл','Домашний уход 100%_маска','🧴');
        INSERT INTO users (full_name, phone, login, password_hash) VALUES ('Алина','+7','alina_style','123456');
        """)

    @staticmethod
    def _sql(sql):
        return sql.replace("%s", "?")

    def fetch_all(self, sql, params=()):
        return [dict(r) for r in self.conn.execute(self._sql(sql), params).fetchall()]

    def execute(self, sql, params=()):
        cur = self.conn.execute(self._sql(sql), params)
        self.conn.commit()
        return cur.lastrowid, cur.rowcount


class FakeHasher:
    def hash(self, password): return "$2b$fake$" + password[::-1]
    def verify(self, password, hashed): return hashed == "$2b$fake$" + password[::-1]


class ServiceTests(unittest.TestCase):
    def setUp(self):
        self.db = FakeDatabase()
        self.repo = ServiceRepository(self.db)

    def test_all(self):
        self.assertEqual(len(self.repo.search()), 4)

    def test_text_search(self):
        self.assertEqual([s.id for s in self.repo.search(text="стрижка")], [1, 2])
        self.assertEqual([s.id for s in self.repo.search(text="окраш")], [4])      # и по названию, и по описанию
        self.assertEqual([s.id for s in self.repo.search(text="Товары")], [10])    # по названию категории (SQLite не игнорирует регистр кириллицы, MySQL ai_ci — игнорирует)

    def test_search_special_chars_are_literal(self):
        self.assertEqual([s.id for s in self.repo.search(text="100%_")], [10])
        self.assertEqual(self.repo.search(text="%"), self.repo.search(text="%"))
        self.assertEqual([s.id for s in self.repo.search(text="%")], [10])         # % не «любой текст»

    def test_category_and_price_filter(self):
        self.assertEqual([s.id for s in self.repo.search(category_id=1)], [1, 2])
        self.assertEqual([s.id for s in self.repo.search(max_price=2300)], [2, 10])

    def test_sort(self):
        self.assertEqual([s.id for s in self.repo.search(sort="asc")], [2, 10, 1, 4])
        self.assertEqual([s.id for s in self.repo.search(sort="desc")], [4, 1, 10, 2])
        self.assertEqual([s.id for s in self.repo.search(sort="DROP TABLE")], [1, 2, 4, 10])

    def test_create_delete(self):
        s = self.repo.create(1, "Горячие ножницы", 3100, "50 мин", "Описание", "✂️", "")
        self.assertEqual(s.category, "Стрижки")
        self.assertEqual(s.price, 3100.0)
        self.assertEqual(self.repo.max_price(), 4800.0)
        self.assertTrue(self.repo.delete(s.id))
        self.assertFalse(self.repo.delete(s.id))
        self.assertEqual(len(self.repo.search()), 4)


class BookingTests(unittest.TestCase):
    def setUp(self):
        self.db = FakeDatabase()
        self.services = ServiceRepository(self.db)
        self.bookings = BookingRepository(self.db)

    def test_book_list_cancel(self):
        svc = self.services.get(1)
        b = self.bookings.create(1, svc, "Алина", "+7", "Анна", "2026-11-05", "10:00")
        self.assertEqual((b.service_title, b.price), ("Женская стрижка", 2800.0))
        self.assertEqual(len(self.bookings.find_by_user(1)), 1)
        self.assertTrue(self.bookings.delete(b.id))
        self.assertEqual(self.bookings.find_by_user(1), [])

    def test_guest_booking_and_cascade(self):
        svc = self.services.get(2)
        guest = self.bookings.create(None, svc, "Гость", "+7", "Артур", "2026-11-06", "12:00")
        self.assertIsNone(guest.user_id)
        self.services.delete(2)    # записи на удалённую услугу удаляются каскадом
        self.assertEqual(self.db.fetch_all("SELECT * FROM bookings"), [])


class AuthTests(unittest.TestCase):
    def setUp(self):
        self.db = FakeDatabase()
        self.auth = AuthService(UserRepository(self.db), FakeHasher())

    def test_register_and_login(self):
        u = self.auth.register("Мария", "+7 900", "maria", "secret")
        self.assertGreater(u.id, 1)
        stored = self.db.fetch_all("SELECT password_hash FROM users WHERE login='maria'")[0]["password_hash"]
        self.assertNotEqual(stored, "secret")           # пароль в БД не открытым текстом
        self.assertEqual(self.auth.login("maria", "secret").full_name, "Мария")

    def test_errors(self):
        with self.assertRaises(AuthError): self.auth.register("A", "1", "alina_style", "pass1")   # логин занят
        with self.assertRaises(AuthError): self.auth.register("A", "1", "new", "123")             # короткий пароль
        with self.assertRaises(AuthError): self.auth.register("", "1", "new", "pass1")            # пустое имя
        self.auth.register("M", "1", "maria", "secret")
        with self.assertRaises(AuthError): self.auth.login("maria", "wrong")
        with self.assertRaises(AuthError): self.auth.login("nobody", "secret")

    def test_legacy_plain_password_is_upgraded(self):
        self.assertEqual(self.auth.login("alina_style", "123456").login, "alina_style")
        stored = self.db.fetch_all("SELECT password_hash FROM users WHERE login='alina_style'")[0]["password_hash"]
        self.assertTrue(stored.startswith("$2"))
        self.assertEqual(self.auth.login("alina_style", "123456").login, "alina_style")


class ThemeTests(unittest.TestCase):
    def test_palettes_match_site(self):
        self.assertEqual(THEMES["sage"].accent, "#689684")
        self.assertEqual(len(THEMES), 4)

    def test_custom_theme(self):
        t = Theme.from_accent("#ff0000")
        self.assertEqual(t.accent, "#FF0000")
        self.assertEqual(t.on_accent, "#FFFFFF")
        self.assertEqual(Theme.from_accent("#FFEB3B").on_accent, "#2B2523")   # светлый акцент → тёмный текст
        self.assertEqual(mix("#000000", "#FFFFFF", 0.5), "#808080")

    def test_stylesheet_builds(self):
        for t in list(THEMES.values()) + [Theme.from_accent("#123456")]:
            css = build_stylesheet(t)
            self.assertIn(t.accent, css)
            self.assertEqual(css.count("{"), css.count("}"))


if __name__ == "__main__":
    unittest.main(verbosity=2)
