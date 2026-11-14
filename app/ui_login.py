"""Окно «Личный кабинет»: вход и регистрация."""
from PySide6.QtWidgets import (QDialog, QFormLayout, QLabel, QLineEdit, QPushButton,
                               QTabWidget, QVBoxLayout, QWidget)

from .auth import AuthError, AuthService
from .database import DatabaseError


class LoginDialog(QDialog):
    def __init__(self, auth: AuthService, parent=None):
        super().__init__(parent)
        self.auth = auth
        self.user = None            # сюда попадёт вошедший пользователь
        self.setWindowTitle("Личный кабинет — LUMIÈRE")
        self.setMinimumWidth(440)

        root = QVBoxLayout(self)
        root.setContentsMargins(28, 24, 28, 24)
        root.setSpacing(10)

        title = QLabel("Личный кабинет")
        title.setObjectName("h2")
        sub = QLabel("Войдите или создайте профиль для быстрой записи к мастерам")
        sub.setObjectName("muted")
        sub.setWordWrap(True)
        root.addWidget(title)
        root.addWidget(sub)

        self.tabs = QTabWidget()
        self.tabs.addTab(self._build_login_tab(), "Вход")
        self.tabs.addTab(self._build_register_tab(), "Регистрация")
        root.addWidget(self.tabs)

        self.error_label = QLabel("")
        self.error_label.setObjectName("error")
        self.error_label.setWordWrap(True)
        root.addWidget(self.error_label)

        guest = QPushButton("Продолжить без входа")
        guest.setObjectName("soft")
        guest.clicked.connect(self.reject)
        root.addWidget(guest)

    # ---------------------------- вкладки ----------------------------
    def _build_login_tab(self) -> QWidget:
        page = QWidget()
        form = QFormLayout(page)
        form.setContentsMargins(0, 14, 0, 0)
        form.setVerticalSpacing(10)
        self.login_input = QLineEdit()
        self.login_input.setPlaceholderText("Введите ваш логин")
        self.login_pass = QLineEdit()
        self.login_pass.setEchoMode(QLineEdit.EchoMode.Password)
        self.login_pass.setPlaceholderText("••••••••")
        button = QPushButton("Войти")
        button.setObjectName("primary")
        button.clicked.connect(self._do_login)
        self.login_pass.returnPressed.connect(self._do_login)
        self.login_input.returnPressed.connect(self._do_login)
        form.addRow("Логин", self.login_input)
        form.addRow("Пароль", self.login_pass)
        form.addRow(button)
        return page

    def _build_register_tab(self) -> QWidget:
        page = QWidget()
        form = QFormLayout(page)
        form.setContentsMargins(0, 14, 0, 0)
        form.setVerticalSpacing(10)
        self.reg_name = QLineEdit()
        self.reg_name.setPlaceholderText("Алина Ветрова")
        self.reg_phone = QLineEdit()
        self.reg_phone.setPlaceholderText("+7 (999) 123-45-67")
        self.reg_login = QLineEdit()
        self.reg_login.setPlaceholderText("alina_style")
        self.reg_pass = QLineEdit()
        self.reg_pass.setEchoMode(QLineEdit.EchoMode.Password)
        self.reg_pass.setPlaceholderText("Минимум 4 символа")
        button = QPushButton("Создать профиль")
        button.setObjectName("primary")
        button.clicked.connect(self._do_register)
        self.reg_pass.returnPressed.connect(self._do_register)
        form.addRow("Имя", self.reg_name)
        form.addRow("Телефон", self.reg_phone)
        form.addRow("Логин", self.reg_login)
        form.addRow("Пароль", self.reg_pass)
        form.addRow(button)
        return page

    # ---------------------------- действия ----------------------------
    def _do_login(self):
        try:
            self.user = self.auth.login(self.login_input.text(), self.login_pass.text())
        except (AuthError, DatabaseError) as err:
            self.error_label.setText(str(err))
            return
        self.accept()

    def _do_register(self):
        try:
            self.user = self.auth.register(self.reg_name.text(), self.reg_phone.text(),
                                           self.reg_login.text(), self.reg_pass.text())
        except (AuthError, DatabaseError) as err:
            self.error_label.setText(str(err))
            return
        self.accept()
