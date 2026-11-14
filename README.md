# LUMIÈRE — настольное приложение (Python + PySide6 + MySQL)

Работает с той же БД `lumiere_salon`, что и сайт.

## Запуск на Mac
1. В MySQL Workbench выполните `db/lumiere_salon.sql` (если ещё не выполняли).
2. В Терминале, в папке проекта:

       python3 -m venv venv
       source venv/bin/activate
       pip install -r requirements.txt
       cp config.ini.example config.ini
       open -e config.ini          # впишите пароль от MySQL, сохраните (Cmd+S)
       python main.py

Тесты логики: `python tests/test_logic.py`

## Структура (ООП)
- `app/database.py`     — класс Database (подключение к MySQL)
- `app/models.py`       — User, Service, Booking
- `app/repositories.py` — UserRepository, CategoryRepository, ServiceRepository, BookingRepository (весь SQL)
- `app/auth.py`         — AuthService, PasswordHasher (регистрация, вход, bcrypt)
- `app/themes.py`       — Theme, палитры, генерация стилей (выбор цвета)
- `app/ui_*.py`         — окна: MainWindow, ServiceCard, LoginDialog, AddServiceDialog, BookingDialog, MyBookingsDialog
