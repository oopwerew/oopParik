"""Подключение к БД (MySQL + авто-fallback на SQLite).

Позволяет запускать приложение как с MySQL (lumiere_salon), так и
автономно через SQLite (lumiere.db), если MySQL не запущен.
"""
import os
import sqlite3
from typing import Any, List, Optional, Tuple


class DatabaseError(Exception):
    """Понятная пользователю ошибка работы с БД."""


DEFAULT_CATEGORIES = [
    (1, "Стрижки"),
    (2, "Окрашивание"),
    (3, "Укладки и уход"),
    (4, "Доп. услуги"),
    (5, "Товары для дома"),
]

DEFAULT_SERVICES = [
    (1, 1, "Женская модельная стрижка + укладка", 2800.00, "60 мин", "Мытьё головы с массажем, подбор формы и лёгкая укладка феном", "✂️", ""),
    (2, 1, "Мужская стрижка (Классика / Fade)", 1900.00, "45 мин", "Точная работа ножницами и машинкой, окантовка и укладка", "💈", ""),
    (3, 4, "Стрижка чёлки и коррекция кончиков", 900.00, "25 мин", "Обновление формы чёлки и ровный срез кончиков", "🌸", ""),
    (4, 2, "Окрашивание в один тон (Корни + длина)", 4800.00, "120 мин", "Бережное безаммиачное окрашивание с глубоким блеском", "🎨", ""),
    (5, 2, "Сложное окрашивание AirTouch / Балаяж", 8900.00, "180 мин", "Создание плавного рельефного блонда с уходом", "✨", ""),
    (6, 3, "Кератиновое восстановление и ботокс волос", 5200.00, "110 мин", "Глубокое питание и зеркальный глянец", "🌿", ""),
    (7, 3, "Вечерняя укладка / Голливудские локоны", 2600.00, "60 мин", "Стойкие воздушные локоны или элегантный пучок", "💫", ""),
    (8, 4, "Пилинг кожи головы + ампульный SPA-массаж", 2100.00, "40 мин", "Детокс-очищение кожи головы и витаминная сыворотка", "🧖‍♀️", ""),
    (9, 4, "Оформление и окрашивание бровей", 1400.00, "35 мин", "Подбор архитектуры бровей и стойкое окрашивание", "👁️", ""),
    (10, 5, "Увлажняющая маска с маслом арганы", 2300.00, "250 мл", "Профессиональная салонная маска для домашнего ухода", "🧴", ""),
]


class Database:
    def __init__(self, config):
        self._config = config
        self._is_sqlite = False
        self._mysql_conn = None
        self._sqlite_conn = None
        self._connect()

    def _connect(self):
        driver = getattr(self._config, "driver", "auto")

        if driver == "sqlite":
            self._connect_sqlite()
            return

        if driver in ("mysql", "auto"):
            try:
                import mysql.connector
                self._mysql_conn = mysql.connector.connect(
                    host=self._config.host,
                    port=self._config.port,
                    user=self._config.user,
                    password=self._config.password,
                    database=self._config.database,
                    charset="utf8mb4",
                    collation="utf8mb4_unicode_ci",
                    use_unicode=True,
                    autocommit=True,
                )
                try:
                    cur = self._mysql_conn.cursor()
                    cur.execute("SET NAMES utf8mb4;")
                    cur.execute("SET CHARACTER SET utf8mb4;")
                    cur.close()
                except Exception:
                    pass
                self._is_sqlite = False
                print(f"✅ Успешное подключение к MySQL: {self._config.database}@{self._config.host}:{self._config.port}")
                return
            except Exception as err:
                if driver == "mysql":
                    raise DatabaseError(f"Не удалось подключиться к MySQL:\n{err}") from err
                print(f"⚠️ MySQL недоступен ({err}). Переключаемся на встроенную SQLite.")
                self._connect_sqlite()

    def _connect_sqlite(self):
        self._is_sqlite = True
        sqlite_path = getattr(self._config, "sqlite_path", "lumiere.db")
        self._sqlite_conn = sqlite3.connect(sqlite_path, check_same_thread=False)
        self._sqlite_conn.row_factory = sqlite3.Row
        self._init_sqlite()
        print(f"✅ Используется локальная SQLite база данных: {sqlite_path}")

    def _init_sqlite(self):
        cur = self._sqlite_conn.cursor()
        cur.executescript("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            full_name TEXT NOT NULL,
            phone TEXT NOT NULL,
            login TEXT NOT NULL UNIQUE,
            password_hash TEXT NOT NULL,
            points INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS categories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE
        );

        CREATE TABLE IF NOT EXISTS services (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            category_id INTEGER NOT NULL REFERENCES categories(id) ON DELETE CASCADE,
            title TEXT NOT NULL,
            price REAL NOT NULL,
            duration TEXT,
            description TEXT,
            emoji TEXT,
            image_url TEXT
        );

        CREATE TABLE IF NOT EXISTS bookings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
            service_id INTEGER NOT NULL REFERENCES services(id) ON DELETE CASCADE,
            service_title TEXT NOT NULL,
            price REAL NOT NULL,
            points_earned INTEGER DEFAULT 0,
            points_used INTEGER DEFAULT 0,
            client_name TEXT NOT NULL,
            client_phone TEXT NOT NULL,
            master_name TEXT NOT NULL,
            booking_date TEXT NOT NULL,
            booking_time TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """)
        self._sqlite_conn.commit()

        # Автоматическая миграция (если база уже существовала)
        cur.execute("PRAGMA table_info(users)")
        user_cols = [col[1] for col in cur.fetchall()]
        if "points" not in user_cols:
            cur.execute("ALTER TABLE users ADD COLUMN points INTEGER DEFAULT 0")

        cur.execute("PRAGMA table_info(bookings)")
        booking_cols = [col[1] for col in cur.fetchall()]
        if "points_earned" not in booking_cols:
            cur.execute("ALTER TABLE bookings ADD COLUMN points_earned INTEGER DEFAULT 0")
        if "points_used" not in booking_cols:
            cur.execute("ALTER TABLE bookings ADD COLUMN points_used INTEGER DEFAULT 0")
        self._sqlite_conn.commit()

        # Заполняем начальными данными, если пусто
        cur.execute("SELECT COUNT(*) AS c FROM categories")
        if cur.fetchone()[0] == 0:
            for cat in DEFAULT_CATEGORIES:
                cur.execute("INSERT INTO categories (id, name) VALUES (?, ?)", cat)
            for srv in DEFAULT_SERVICES:
                cur.execute(
                    "INSERT INTO services (id, category_id, title, price, duration, description, emoji, image_url) "
                    "VALUES (?, ?, ?, ?, ?, ?, ?, ?)", srv
                )
            cur.execute(
                "INSERT INTO users (id, full_name, phone, login, password_hash, points) VALUES (?, ?, ?, ?, ?, ?)",
                (1, "Администратор", "+7 (000) 000-00-00", "admin", "admin", 0)
            )
            cur.execute(
                "INSERT INTO users (id, full_name, phone, login, password_hash, points) VALUES (?, ?, ?, ?, ?, ?)",
                (2, "Алина Ветрова", "+7 (999) 123-45-67", "alina_style", "123456", 250)
            )
            self._sqlite_conn.commit()
        else:
            # Гарантируем наличие администратора admin/admin
            cur.execute("SELECT id FROM users WHERE login = 'admin'")
            if not cur.fetchone():
                cur.execute(
                    "INSERT INTO users (full_name, phone, login, password_hash, points) VALUES (?, ?, ?, ?, ?)",
                    ("Администратор", "+7 (000) 000-00-00", "admin", "admin", 0)
                )
                self._sqlite_conn.commit()
        cur.close()

    @property
    def is_sqlite(self) -> bool:
        return self._is_sqlite

    def _ensure(self):
        if self._is_sqlite:
            if self._sqlite_conn is None:
                self._connect_sqlite()
        else:
            if self._mysql_conn is None or not self._mysql_conn.is_connected():
                self._connect()

    def fetch_all(self, sql: str, params: Tuple[Any, ...] = ()) -> List[dict]:
        """SELECT → список словарей."""
        self._ensure()
        if self._is_sqlite:
            sql_conv = sql.replace("%s", "?")
            cur = self._sqlite_conn.cursor()
            try:
                cur.execute(sql_conv, params)
                return [dict(row) for row in cur.fetchall()]
            finally:
                cur.close()
        else:
            import mysql.connector
            try:
                cur = self._mysql_conn.cursor(dictionary=True)
                try:
                    cur.execute(sql, params)
                    return cur.fetchall()
                finally:
                    cur.close()
            except mysql.connector.Error as err:
                raise DatabaseError(f"Ошибка запроса к MySQL:\n{err}") from err

    def execute(self, sql: str, params: Tuple[Any, ...] = ()) -> Tuple[int, int]:
        """INSERT / UPDATE / DELETE → (последний id, число измененных строк)."""
        self._ensure()
        if self._is_sqlite:
            sql_conv = sql.replace("%s", "?")
            cur = self._sqlite_conn.cursor()
            try:
                cur.execute(sql_conv, params)
                self._sqlite_conn.commit()
                return cur.lastrowid or 0, cur.rowcount
            finally:
                cur.close()
        else:
            import mysql.connector
            try:
                cur = self._mysql_conn.cursor()
                try:
                    cur.execute(sql, params)
                    return cur.lastrowid or 0, cur.rowcount
                finally:
                    cur.close()
            except mysql.connector.Error as err:
                raise DatabaseError(f"Ошибка записи в MySQL:\n{err}") from err
