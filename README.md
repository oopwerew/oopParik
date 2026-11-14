# LUMIÈRE — Веб-приложение парикмахерской (Python + Flask)

Красивый сайт и система онлайн-записи студии стиля LUMIÈRE, работающие на **Flask** с поддержкой **MySQL** и автоматическим fallback на **SQLite**.

---

## 🚀 Быстрый запуск на локалхосте (Mac / Linux / Windows)

1. **Создайте и активируйте виртуальное окружение:**
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # На Windows: venv\Scripts\activate
   ```

2. **Установите зависимости:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Запустите веб-приложение:**
   ```bash
   python app.py
   # или: python main.py
   ```

4. **Откройте в браузере:**
   👉 **http://localhost:5000**

---

## 🗄️ База данных

Приложение поддерживает два режима работы:

* **Автономный (SQLite, по умолчанию без настроек):**
  Если MySQL не запущен, приложение автоматически использует локальную базу данных `lumiere.db`, в которую сразу загружены все 10 базовых услуг, категории и тестовый клиент. Никаких дополнительных настроек не требуется — сайт сразу работает!

* **MySQL (lumiere_salon):**
  Если у вас установлен и запущен MySQL Workbench:
  1. Выполните дамп `db/lumiere_salon.sql`.
  2. Скопируйте `config.ini.example` в `config.ini`:
     ```bash
     cp config.ini.example config.ini
     ```
  3. Укажите ваш пароль от MySQL в `config.ini`.
  4. При перезапуске сервер автоматически подключится к MySQL.

---

## 🧪 Тестирование

Запуск тестов API и логики:
```bash
python tests/test_webapp.py  # Тестирование всех HTTP REST эндпоинтов Flask
python tests/test_logic.py   # Тестирование бизнес-логики и репозиториев
```

---

## 📁 Структура проекта

```text
├── app.py                  # Главная точка входа Flask (сервер и маршруты)
├── main.py                 # Альтернативный запуск сервера
├── requirements.txt        # Зависимости проекта (Flask, mysql-connector, bcrypt)
├── config.ini.example      # Пример конфигурации
├── templates/
│   └── index.html          # Полный фронтенд сайта студии с онлайн-записью
├── static/
│   └── index.html          # Статическая версия страницы
├── app/
│   ├── server.py           # Инициализация Flask приложения и REST API
│   ├── database.py         # Подключение к БД (MySQL + fallback на SQLite)
│   ├── models.py           # Модели данных (User, Service, Booking)
│   ├── repositories.py     # Репозитории доступа к данным (UserRepository, ServiceRepository...)
│   ├── auth.py             # Аутентификация, регистрация и bcrypt-хэширование
│   └── config.py           # Загрузка настроек из config.ini и переменных окружения
├── db/
│   └── lumiere_salon.sql   # SQL-дамп для MySQL
└── tests/
    ├── test_webapp.py      # Автотесты Flask эндпоинтов
    └── test_logic.py       # Тесты логики сервисов
```
