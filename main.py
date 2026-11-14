"""LUMIÈRE — настольное приложение парикмахерской (Python + PySide6 + MySQL)."""
import sys

from PySide6.QtWidgets import QApplication, QMessageBox

from app.auth import AuthService
from app.config import Config
from app.database import Database, DatabaseError
from app.repositories import BookingRepository, CategoryRepository, ServiceRepository, UserRepository
from app.ui_main import AppContext, MainWindow


def main() -> int:
    app = QApplication(sys.argv)
    app.setApplicationName("LUMIÈRE")

    config = Config()
    if not config.exists():
        QMessageBox.critical(None, "Нет настроек",
                             "Не найден файл config.ini.\nСкопируйте config.ini.example в config.ini "
                             "и впишите пароль от MySQL.")
        return 1

    db = Database(config)
    try:
        db.connect()
    except DatabaseError as err:
        QMessageBox.critical(None, "Нет подключения к БД",
                             f"{err}\n\nПроверьте, что MySQL запущен и данные в config.ini верны.")
        return 1

    ctx = AppContext(
        auth=AuthService(UserRepository(db)),
        categories=CategoryRepository(db),
        services=ServiceRepository(db),
        bookings=BookingRepository(db),
    )
    window = MainWindow(ctx)
    window.show()
    window.open_login()          # сразу предлагаем войти (можно продолжить как гость)
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
