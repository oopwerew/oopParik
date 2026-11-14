"""Подключение к MySQL. Все SQL-запросы идут через этот класс."""


class DatabaseError(Exception):
    """Понятная пользователю ошибка работы с БД."""


class Database:
    def __init__(self, config):
        self._config = config
        self._conn = None

    def connect(self):
        import mysql.connector  # импорт здесь, чтобы тесты работали без драйвера
        try:
            self._conn = mysql.connector.connect(
                host=self._config.host,
                port=self._config.port,
                user=self._config.user,
                password=self._config.password,
                database=self._config.database,
                charset="utf8mb4",
                autocommit=True,
            )
        except mysql.connector.Error as err:
            raise DatabaseError(f"Не удалось подключиться к MySQL:\n{err}") from err

    def _ensure(self):
        if self._conn is None or not self._conn.is_connected():
            self.connect()

    def fetch_all(self, sql, params=()):
        """SELECT → список словарей."""
        import mysql.connector
        self._ensure()
        try:
            cursor = self._conn.cursor(dictionary=True)
            try:
                cursor.execute(sql, params)
                return cursor.fetchall()
            finally:
                cursor.close()
        except mysql.connector.Error as err:
            raise DatabaseError(f"Ошибка запроса к БД:\n{err}") from err

    def execute(self, sql, params=()):
        """INSERT / UPDATE / DELETE → (последний id, число затронутых строк)."""
        import mysql.connector
        self._ensure()
        try:
            cursor = self._conn.cursor()
            try:
                cursor.execute(sql, params)
                return cursor.lastrowid, cursor.rowcount
            finally:
                cursor.close()
        except mysql.connector.Error as err:
            raise DatabaseError(f"Ошибка записи в БД:\n{err}") from err
