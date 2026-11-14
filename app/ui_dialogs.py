"""Окна: добавление услуги, запись на услугу, «Мои записи»."""
from PySide6.QtCore import QDate, Signal
from PySide6.QtWidgets import (QComboBox, QDateEdit, QDialog, QDoubleSpinBox, QFileDialog, QFormLayout,
                               QFrame, QHBoxLayout, QLabel, QLineEdit, QMessageBox, QPushButton,
                               QScrollArea, QTextEdit, QVBoxLayout, QWidget)

from .constants import CATEGORY_EMOJI, DEFAULT_EMOJI, MASTERS, TIMES
from .database import DatabaseError
from .models import format_date, format_price


def clear_layout(layout):
    """Удаляет все виджеты из layout."""
    while layout.count():
        item = layout.takeAt(0)
        widget = item.widget()
        if widget is not None:
            widget.deleteLater()


def _header(layout, title, subtitle):
    t = QLabel(title)
    t.setObjectName("h2")
    s = QLabel(subtitle)
    s.setObjectName("muted")
    s.setWordWrap(True)
    layout.addWidget(t)
    layout.addWidget(s)


class AddServiceDialog(QDialog):
    """ТЗ: добавление услуги / товара."""

    def __init__(self, categories, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Добавить позицию")
        self.setMinimumWidth(480)
        root = QVBoxLayout(self)
        root.setContentsMargins(28, 24, 28, 24)
        root.setSpacing(10)
        _header(root, "Добавить позицию", "Заполните данные для новой карточки в каталоге парикмахерской")

        form = QFormLayout()
        form.setVerticalSpacing(10)
        self.title_edit = QLineEdit()
        self.title_edit.setPlaceholderText("Например: Стрижка горячими ножницами")
        self.category_combo = QComboBox()
        for cat in categories:
            self.category_combo.addItem(cat["name"], cat["id"])
        self.price_spin = QDoubleSpinBox()
        self.price_spin.setRange(100, 1_000_000)
        self.price_spin.setDecimals(0)
        self.price_spin.setSingleStep(100)
        self.price_spin.setSuffix(" ₽")
        self.price_spin.setValue(2500)
        self.duration_edit = QLineEdit()
        self.duration_edit.setPlaceholderText("60 мин")
        self.photo_edit = QLineEdit()
        self.photo_edit.setPlaceholderText("Путь к файлу (по желанию)")
        browse = QPushButton("Выбрать…")
        browse.setObjectName("soft")
        browse.clicked.connect(self._browse)
        photo_row = QHBoxLayout()
        photo_row.addWidget(self.photo_edit)
        photo_row.addWidget(browse)
        self.desc_edit = QTextEdit()
        self.desc_edit.setPlaceholderText("Что входит в услугу…")
        self.desc_edit.setFixedHeight(90)

        form.addRow("Название", self.title_edit)
        form.addRow("Категория", self.category_combo)
        form.addRow("Цена", self.price_spin)
        form.addRow("Длительность / объём", self.duration_edit)
        form.addRow("Фото", photo_row)
        form.addRow("Описание", self.desc_edit)
        root.addLayout(form)

        self.error_label = QLabel("")
        self.error_label.setObjectName("error")
        root.addWidget(self.error_label)
        ok = QPushButton("Добавить в каталог")
        ok.setObjectName("primary")
        ok.clicked.connect(self.accept)
        root.addWidget(ok)

    def _browse(self):
        path, _ = QFileDialog.getOpenFileName(self, "Выберите фото", "", "Изображения (*.png *.jpg *.jpeg *.webp)")
        if path:
            self.photo_edit.setText(path)

    def accept(self):
        if not (self.title_edit.text().strip() and self.duration_edit.text().strip()
                and self.desc_edit.toPlainText().strip()):
            self.error_label.setText("Заполните название, длительность и описание")
            return
        super().accept()

    def values(self) -> dict:
        category_name = self.category_combo.currentText()
        return {
            "category_id": self.category_combo.currentData(),
            "title": self.title_edit.text().strip(),
            "price": self.price_spin.value(),
            "duration": self.duration_edit.text().strip(),
            "description": self.desc_edit.toPlainText().strip(),
            "emoji": CATEGORY_EMOJI.get(category_name, DEFAULT_EMOJI),
            "image_url": self.photo_edit.text().strip(),
        }


class BookingDialog(QDialog):
    """Запись клиента на выбранную услугу."""

    def __init__(self, service, user, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Онлайн-запись")
        self.setMinimumWidth(440)
        root = QVBoxLayout(self)
        root.setContentsMargins(28, 24, 28, 24)
        root.setSpacing(10)
        _header(root, "Онлайн-запись", f"{service.title} — {format_price(service.price)}")

        form = QFormLayout()
        form.setVerticalSpacing(10)
        self.name_edit = QLineEdit(user.full_name if user else "")
        self.name_edit.setPlaceholderText("Как к вам обращаться?")
        self.phone_edit = QLineEdit(user.phone if user else "")
        self.phone_edit.setPlaceholderText("+7 (999) 123-45-67")
        self.master_combo = QComboBox()
        self.master_combo.addItems(MASTERS)
        self.date_edit = QDateEdit(QDate.currentDate())
        self.date_edit.setCalendarPopup(True)
        self.date_edit.setMinimumDate(QDate.currentDate())
        self.date_edit.setDisplayFormat("dd.MM.yyyy")
        self.time_combo = QComboBox()
        self.time_combo.addItems(TIMES)
        form.addRow("Ваше имя", self.name_edit)
        form.addRow("Телефон", self.phone_edit)
        form.addRow("Мастер", self.master_combo)
        form.addRow("Дата", self.date_edit)
        form.addRow("Время", self.time_combo)
        root.addLayout(form)

        self.error_label = QLabel("")
        self.error_label.setObjectName("error")
        root.addWidget(self.error_label)
        ok = QPushButton("Подтвердить запись")
        ok.setObjectName("primary")
        ok.clicked.connect(self.accept)
        root.addWidget(ok)

    def accept(self):
        if not (self.name_edit.text().strip() and self.phone_edit.text().strip()):
            self.error_label.setText("Укажите имя и телефон")
            return
        super().accept()

    def values(self) -> dict:
        return {
            "client_name": self.name_edit.text().strip(),
            "client_phone": self.phone_edit.text().strip(),
            "master": self.master_combo.currentText(),
            "date": self.date_edit.date().toString("yyyy-MM-dd"),
            "time": self.time_combo.currentText(),
        }


class MyBookingsDialog(QDialog):
    """Список записей клиента с возможностью отмены."""
    changed = Signal()

    def __init__(self, repo, bookings, parent=None):
        super().__init__(parent)
        self.repo = repo
        self.bookings = bookings        # общий список из главного окна
        self.setWindowTitle("Мои записи")
        self.setMinimumSize(520, 420)
        root = QVBoxLayout(self)
        root.setContentsMargins(28, 24, 28, 24)
        _header(root, "Мои записи в салон", "Здесь отображаются выбранные услуги и время визита")

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.viewport().setAutoFillBackground(False)
        host = QWidget()
        self.list_layout = QVBoxLayout(host)
        self.list_layout.setContentsMargins(0, 6, 0, 6)
        self.list_layout.setSpacing(10)
        scroll.setWidget(host)
        root.addWidget(scroll, 1)

        close = QPushButton("Закрыть")
        close.setObjectName("soft")
        close.clicked.connect(self.accept)
        root.addWidget(close)
        self._rebuild()

    def _rebuild(self):
        clear_layout(self.list_layout)
        if not self.bookings:
            empty = QLabel("У вас пока нет активных записей. Выберите любую услугу в каталоге!")
            empty.setObjectName("muted")
            empty.setWordWrap(True)
            self.list_layout.addWidget(empty)
        for booking in self.bookings:
            self.list_layout.addWidget(self._row(booking))
        self.list_layout.addStretch(1)

    def _row(self, booking) -> QFrame:
        frame = QFrame()
        frame.setObjectName("panel")
        row = QHBoxLayout(frame)
        row.setContentsMargins(16, 12, 16, 12)
        text = QVBoxLayout()
        title = QLabel(booking.service_title)
        title.setObjectName("title")
        title.setWordWrap(True)
        info = QLabel(f"Мастер: {booking.master_name} • {format_date(booking.booking_date)} в {booking.booking_time}")
        info.setObjectName("muted")
        info.setWordWrap(True)
        price = QLabel(format_price(booking.price))
        price.setObjectName("price")
        text.addWidget(title)
        text.addWidget(info)
        text.addWidget(price)
        cancel = QPushButton("Отменить")
        cancel.setObjectName("danger")
        cancel.clicked.connect(lambda checked=False, b=booking: self._cancel(b))
        row.addLayout(text, 1)
        row.addWidget(cancel)
        return frame

    def _cancel(self, booking):
        answer = QMessageBox.question(self, "Отмена записи", f"Отменить запись «{booking.service_title}»?",
                                      QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                                      QMessageBox.StandardButton.No)
        if answer != QMessageBox.StandardButton.Yes:
            return
        try:
            self.repo.delete(booking.id)
        except DatabaseError as err:
            QMessageBox.critical(self, "Ошибка базы данных", str(err))
            return
        self.bookings.remove(booking)
        self._rebuild()
        self.changed.emit()
