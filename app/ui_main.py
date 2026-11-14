"""Главное окно: шапка, баннер, поиск и фильтры, каталог карточек."""
from __future__ import annotations

import math
import os
from dataclasses import dataclass

from PySide6.QtCore import Qt, QSettings, QTimer, Signal
from PySide6.QtGui import QColor, QPixmap
from PySide6.QtWidgets import (QApplication, QButtonGroup, QColorDialog, QComboBox, QFrame, QGridLayout,
                               QHBoxLayout, QLabel, QLineEdit, QMainWindow, QMessageBox, QPushButton,
                               QScrollArea, QSlider, QVBoxLayout, QWidget)

from .auth import AuthService
from .constants import CATEGORY_EMOJI, CATEGORY_TAB_TITLES, FEATURES, SORT_OPTIONS
from .database import DatabaseError
from .models import Service, format_price
from .repositories import BookingRepository, CategoryRepository, ServiceRepository
from .themes import THEMES, Theme, build_stylesheet
from .ui_dialogs import AddServiceDialog, BookingDialog, MyBookingsDialog
from .ui_login import LoginDialog

PRICE_MIN = 500
CARD_WIDTH = 290          # ширина одной колонки каталога (для расчёта числа колонок)


@dataclass
class AppContext:
    """Все «сервисы» приложения в одном месте — передаётся в главное окно."""
    auth: AuthService
    categories: CategoryRepository
    services: ServiceRepository
    bookings: BookingRepository


class ServiceCard(QFrame):
    """Карточка услуги / товара в каталоге."""
    book_clicked = Signal(object)
    delete_clicked = Signal(object)

    def __init__(self, service: Service):
        super().__init__()
        self.setObjectName("card")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 14, 14, 14)
        layout.setSpacing(8)

        photo = QFrame()
        photo.setObjectName("cardPhoto")
        photo.setFixedHeight(130)
        photo_layout = QVBoxLayout(photo)
        picture = QLabel()
        picture.setAlignment(Qt.AlignmentFlag.AlignCenter)
        pixmap = QPixmap(service.image_url) if service.image_url and os.path.exists(service.image_url) else None
        if pixmap is not None and not pixmap.isNull():
            picture.setPixmap(pixmap.scaled(250, 120, Qt.AspectRatioMode.KeepAspectRatio,
                                            Qt.TransformationMode.SmoothTransformation))
        else:
            picture.setText(service.emoji)
            picture.setStyleSheet("font-size: 46px;")
        photo_layout.addWidget(picture)
        layout.addWidget(photo)

        pills = QHBoxLayout()
        pills.setSpacing(6)
        for text in (service.category, service.duration):
            if text:
                pill = QLabel(text)
                pill.setObjectName("pill")
                pills.addWidget(pill)
        pills.addStretch(1)
        layout.addLayout(pills)

        title = QLabel(service.title)
        title.setObjectName("title")
        title.setWordWrap(True)
        desc = QLabel(service.description)
        desc.setObjectName("muted")
        desc.setWordWrap(True)
        layout.addWidget(title)
        layout.addWidget(desc)
        layout.addStretch(1)

        bottom = QHBoxLayout()
        price = QLabel(format_price(service.price))
        price.setObjectName("price")
        book = QPushButton("Записаться")
        book.setObjectName("primary")
        book.clicked.connect(lambda: self.book_clicked.emit(service))
        delete = QPushButton("🗑")
        delete.setObjectName("danger")
        delete.setToolTip("Удалить карточку")
        delete.clicked.connect(lambda: self.delete_clicked.emit(service))
        bottom.addWidget(price)
        bottom.addStretch(1)
        bottom.addWidget(book)
        bottom.addWidget(delete)
        layout.addLayout(bottom)


class MainWindow(QMainWindow):
    def __init__(self, ctx: AppContext):
        super().__init__()
        self.ctx = ctx
        self.settings = QSettings("Lumiere", "SalonApp")
        self.user = None                 # вошедший клиент (None = гость)
        self.my_bookings = []            # записи текущего клиента / гостя
        self.active_category = None      # None = «Все услуги и товары»
        self._cards = []
        self._last_cols = 0

        self.setWindowTitle("LUMIÈRE — парикмахерская и студия ухода")
        self.resize(1180, 820)
        self.setMinimumSize(760, 560)

        central = QWidget()
        self.setCentralWidget(central)
        root = QVBoxLayout(central)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)
        root.addWidget(self._build_header())

        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setFrameShape(QFrame.Shape.NoFrame)
        self.scroll.viewport().setAutoFillBackground(False)
        self.scroll.setWidget(self._build_content())
        root.addWidget(self.scroll, 1)

        self._search_timer = QTimer(self)
        self._search_timer.setSingleShot(True)
        self._search_timer.setInterval(200)
        self._search_timer.timeout.connect(self.refresh)

        self._apply_theme(self._load_theme(), save=False)
        self._update_price_range(keep_max=False)
        self._render_user()
        self.refresh()

    # ============================ построение окна ============================
    def _build_header(self) -> QWidget:
        header = QWidget()
        row = QHBoxLayout(header)
        row.setContentsMargins(28, 16, 28, 12)
        row.setSpacing(10)

        brand = QLabel("● LUMIÈRE")
        brand.setObjectName("brand")
        row.addWidget(brand)
        row.addStretch(1)

        row.addWidget(self._muted_label("Цвет:"))
        self.dots = {}
        for key, theme in THEMES.items():
            dot = QPushButton()
            dot.setFixedSize(26, 26)
            dot.setToolTip(theme.title)
            dot.setCursor(Qt.CursorShape.PointingHandCursor)
            dot.clicked.connect(lambda checked=False, t=theme: self._apply_theme(t))
            self.dots[key] = dot
            row.addWidget(dot)
        custom = QPushButton("🎨")
        custom.setObjectName("soft")
        custom.setToolTip("Выбрать любой оттенок")
        custom.clicked.connect(self._pick_custom_color)
        row.addWidget(custom)

        self.bookings_btn = QPushButton("📅 Мои записи (0)")
        self.bookings_btn.setObjectName("soft")
        self.bookings_btn.clicked.connect(self._open_my_bookings)
        row.addWidget(self.bookings_btn)

        self.user_label = QLabel("")
        self.user_label.setStyleSheet("font-weight: 700;")
        self.auth_btn = QPushButton("")
        self.auth_btn.clicked.connect(self._on_auth_clicked)
        row.addWidget(self.user_label)
        row.addWidget(self.auth_btn)
        return header

    @staticmethod
    def _muted_label(text) -> QLabel:
        label = QLabel(text)
        label.setObjectName("muted")
        return label

    def _build_content(self) -> QWidget:
        content = QWidget()
        col = QVBoxLayout(content)
        col.setContentsMargins(28, 8, 28, 20)
        col.setSpacing(16)
        col.addWidget(self._build_hero())
        self.filter_panel = self._build_filters()
        col.addWidget(self.filter_panel)

        self.empty_label = QLabel("🍃  Ничего не найдено\nПопробуйте увеличить максимальную цену или выбрать другую категорию.")
        self.empty_label.setObjectName("muted")
        self.empty_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.empty_label.setMinimumHeight(120)
        col.addWidget(self.empty_label)

        self.grid = QGridLayout()
        self.grid.setSpacing(18)
        self.grid.setAlignment(Qt.AlignmentFlag.AlignTop)
        col.addLayout(self.grid)
        col.addStretch(1)

        footer = self._muted_label("© 2026 Парикмахерская «LUMIÈRE». Ежедневно с 10:00 до 21:00 • Онлайн-запись 24/7")
        footer.setAlignment(Qt.AlignmentFlag.AlignCenter)
        col.addWidget(footer)
        return content

    def _build_hero(self) -> QFrame:
        hero = QFrame()
        hero.setObjectName("hero")
        row = QHBoxLayout(hero)
        row.setContentsMargins(28, 24, 28, 24)
        row.setSpacing(24)

        left = QVBoxLayout()
        tag = QLabel("🌸 Парикмахерская и студия ухода")
        tag.setObjectName("pill")
        h1 = QLabel("Нежная забота о ваших волосах и безупречный стиль")
        h1.setObjectName("h1")
        h1.setWordWrap(True)
        text = self._muted_label("Женские и мужские стрижки, бережное окрашивание в сложных техниках, "
                                 "восстанавливающие SPA-программы и профессиональная уходовая косметика.")
        text.setWordWrap(True)
        buttons = QHBoxLayout()
        choose = QPushButton("Выбрать услугу")
        choose.setObjectName("primary")
        choose.clicked.connect(lambda: self.scroll.verticalScrollBar().setValue(self.filter_panel.y() - 10))
        add = QPushButton("+ Добавить услугу / товар")
        add.setObjectName("soft")
        add.clicked.connect(self._on_add)
        buttons.addWidget(choose)
        buttons.addWidget(add)
        buttons.addStretch(1)
        tag_row = QHBoxLayout()
        tag_row.addWidget(tag)
        tag_row.addStretch(1)
        left.addLayout(tag_row)
        left.addWidget(h1)
        left.addWidget(text)
        left.addLayout(buttons)
        row.addLayout(left, 3)

        features = QGridLayout()
        features.setSpacing(10)
        for i, (icon, title, sub) in enumerate(FEATURES):
            box = QFrame()
            box.setObjectName("feature")
            box_l = QVBoxLayout(box)
            box_l.setContentsMargins(12, 10, 12, 10)
            box_l.setSpacing(2)
            icon_l = QLabel(icon)
            icon_l.setStyleSheet("font-size: 22px;")
            title_l = QLabel(title)
            title_l.setObjectName("title")
            sub_l = self._muted_label(sub)
            sub_l.setStyleSheet("font-size: 12px;")
            box_l.addWidget(icon_l)
            box_l.addWidget(title_l)
            box_l.addWidget(sub_l)
            features.addWidget(box, i // 2, i % 2)
        row.addLayout(features, 2)
        return hero

    def _build_filters(self) -> QFrame:
        panel = QFrame()
        panel.setObjectName("panel")
        col = QVBoxLayout(panel)
        col.setContentsMargins(18, 14, 18, 14)
        col.setSpacing(12)

        top = QHBoxLayout()
        top.setSpacing(12)
        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("🔍  Найти услугу или уход (например: стрижка, окрашивание, маска)")
        self.search_edit.setClearButtonEnabled(True)
        self.search_edit.textChanged.connect(lambda _text: self._search_timer.start())
        top.addWidget(self.search_edit, 1)

        self.price_label = QLabel("")
        self.price_label.setMinimumWidth(110)
        self.price_slider = QSlider(Qt.Orientation.Horizontal)
        self.price_slider.setFixedWidth(150)
        self.price_slider.setSingleStep(200)
        self.price_slider.setPageStep(1000)
        self.price_slider.valueChanged.connect(self._on_price_changed)
        top.addWidget(self.price_label)
        top.addWidget(self.price_slider)

        self.sort_combo = QComboBox()
        for title, key in SORT_OPTIONS:
            self.sort_combo.addItem(title, key)
        self.sort_combo.currentIndexChanged.connect(lambda _i: self.refresh())
        top.addWidget(self.sort_combo)
        col.addLayout(top)

        bottom = QHBoxLayout()
        bottom.setSpacing(8)
        self.category_group = QButtonGroup(self)
        self._add_category_button(bottom, None, "Все услуги и товары", checked=True)
        try:
            for cat in self.ctx.categories.all():
                emoji = CATEGORY_EMOJI.get(cat["name"], "")
                title = CATEGORY_TAB_TITLES.get(cat["name"], cat["name"])
                self._add_category_button(bottom, cat["id"], f"{emoji} {title}".strip())
        except DatabaseError as err:
            self._show_db_error(err)
        bottom.addStretch(1)
        add = QPushButton("➕ Добавить карточку")
        add.setObjectName("primary")
        add.clicked.connect(self._on_add)
        bottom.addWidget(add)
        col.addLayout(bottom)
        return panel

    def _add_category_button(self, layout, category_id, title, checked=False):
        btn = QPushButton(title)
        btn.setObjectName("tab")
        btn.setCheckable(True)
        btn.setChecked(checked)
        btn.clicked.connect(lambda _c=False, cid=category_id: self._set_category(cid))
        self.category_group.addButton(btn)
        layout.addWidget(btn)

    # ============================== каталог ==============================
    def refresh(self):
        """Читает из БД услуги по текущим поиску/фильтрам/сортировке и перерисовывает карточки."""
        try:
            services = self.ctx.services.search(
                text=self.search_edit.text().strip(),
                category_id=self.active_category,
                max_price=self.price_slider.value(),
                sort=self.sort_combo.currentData(),
            )
        except DatabaseError as err:
            self._show_db_error(err)
            return

        for card in self._cards:
            self.grid.removeWidget(card)
            card.deleteLater()
        self._cards = []
        for service in services:
            card = ServiceCard(service)
            card.book_clicked.connect(self._on_book)
            card.delete_clicked.connect(self._on_delete)
            self._cards.append(card)
        self.empty_label.setVisible(not services)
        self._layout_cards()

    def _columns(self) -> int:
        width = self.scroll.viewport().width() - 56
        return max(1, min(4, width // CARD_WIDTH))

    def _layout_cards(self):
        cols = self._columns()
        self._last_cols = cols
        for card in self._cards:
            self.grid.removeWidget(card)
        for index, card in enumerate(self._cards):
            self.grid.addWidget(card, index // cols, index % cols)
        for c in range(6):
            self.grid.setColumnStretch(c, 1 if c < cols else 0)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if self._cards and self._columns() != self._last_cols:
            self._layout_cards()

    def showEvent(self, event):
        super().showEvent(event)
        QTimer.singleShot(0, self._layout_cards)

    def _set_category(self, category_id):
        self.active_category = category_id
        self.refresh()

    def _on_price_changed(self, value):
        self.price_label.setText(f"Цена до: {format_price(value)}")
        self._search_timer.start()

    def _update_price_range(self, keep_max: bool):
        """Верхняя граница ползунка = самая дорогая услуга в БД."""
        try:
            top = self.ctx.services.max_price()
        except DatabaseError as err:
            self._show_db_error(err)
            return
        new_max = max(PRICE_MIN, int(math.ceil(top / 200.0) * 200))
        was_max = self.price_slider.value() >= self.price_slider.maximum()
        self.price_slider.blockSignals(True)
        self.price_slider.setRange(PRICE_MIN, new_max)
        if keep_max is False or was_max:
            self.price_slider.setValue(new_max)
        self.price_slider.blockSignals(False)
        self.price_label.setText(f"Цена до: {format_price(self.price_slider.value())}")

    # ============================= пользователь =============================
    def _render_user(self):
        if self.user:
            self.user_label.setText(f"👤 {self.user.full_name}")
            self.auth_btn.setText("Выйти")
            self.auth_btn.setObjectName("soft")
        else:
            self.user_label.setText("")
            self.auth_btn.setText("✨ Войти в кабинет")
            self.auth_btn.setObjectName("primary")
        self.auth_btn.style().unpolish(self.auth_btn)     # применить новый objectName
        self.auth_btn.style().polish(self.auth_btn)
        self._update_bookings_count()

    def _on_auth_clicked(self):
        if self.user:
            self.user = None
            self.my_bookings = []
            self._render_user()
            self.statusBar().showMessage("Вы вышли из личного кабинета", 5000)
        else:
            self.open_login()

    def open_login(self):
        dialog = LoginDialog(self.ctx.auth, self)
        if dialog.exec() and dialog.user:
            self.user = dialog.user
            self._reload_bookings()
            self._render_user()
            self.statusBar().showMessage(f"✨ Рады видеть вас, {self.user.full_name}!", 5000)

    def _reload_bookings(self):
        self.my_bookings = []
        if self.user:
            try:
                self.my_bookings = self.ctx.bookings.find_by_user(self.user.id)
            except DatabaseError as err:
                self._show_db_error(err)
        self._update_bookings_count()

    def _update_bookings_count(self):
        self.bookings_btn.setText(f"📅 Мои записи ({len(self.my_bookings)})")

    # ========================= действия с каталогом =========================
    def _on_book(self, service: Service):
        dialog = BookingDialog(service, self.user, self)
        if not dialog.exec():
            return
        try:
            booking = self.ctx.bookings.create(self.user.id if self.user else None, service, **dialog.values())
        except DatabaseError as err:
            self._show_db_error(err)
            return
        self.my_bookings.insert(0, booking)
        self._update_bookings_count()
        self.statusBar().showMessage(
            f"💖 Вы записаны: «{service.title}» ({booking.booking_date} в {booking.booking_time})", 7000)

    def _on_add(self):
        try:
            categories = self.ctx.categories.all()
        except DatabaseError as err:
            self._show_db_error(err)
            return
        dialog = AddServiceDialog(categories, self)
        if not dialog.exec():
            return
        try:
            service = self.ctx.services.create(**dialog.values())
        except DatabaseError as err:
            self._show_db_error(err)
            return
        self._update_price_range(keep_max=True)
        self.refresh()
        self.statusBar().showMessage(f"✨ Добавлено: «{service.title}»", 5000)
        QTimer.singleShot(50, lambda: self.scroll.verticalScrollBar().setValue(
            self.scroll.verticalScrollBar().maximum()))

    def _on_delete(self, service: Service):
        answer = QMessageBox.question(
            self, "Удаление",
            f"Удалить «{service.title}» из каталога?\nВсе записи на эту услугу тоже будут удалены.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No)
        if answer != QMessageBox.StandardButton.Yes:
            return
        try:
            self.ctx.services.delete(service.id)
        except DatabaseError as err:
            self._show_db_error(err)
            return
        self._reload_bookings()          # записи на услугу удалены в БД каскадно
        self._update_price_range(keep_max=True)
        self.refresh()
        self.statusBar().showMessage(f"Удалено из каталога: «{service.title}»", 5000)

    def _open_my_bookings(self):
        dialog = MyBookingsDialog(self.ctx.bookings, self.my_bookings, self)
        dialog.changed.connect(self._update_bookings_count)
        dialog.exec()

    # ================================ цвет ================================
    def _load_theme(self) -> Theme:
        key = self.settings.value("theme/key", "default")
        if key == "custom":
            return Theme.from_accent(self.settings.value("theme/custom", "#D98A6C"))
        return THEMES.get(key, THEMES["default"])

    def _apply_theme(self, theme: Theme, save: bool = True):
        QApplication.instance().setStyleSheet(build_stylesheet(theme))
        for key, dot in self.dots.items():
            base = THEMES[key]
            border = theme.text if key == theme.key else "transparent"
            dot.setStyleSheet(
                f"QPushButton {{ background: {base.accent}; border: 3px solid {border};"
                f" border-radius: 13px; padding: 0; min-width: 0; }}")
        if save:
            self.settings.setValue("theme/key", theme.key)
            if theme.key == "custom":
                self.settings.setValue("theme/custom", theme.accent)
            self.statusBar().showMessage("🎨 Цветовое оформление обновлено", 4000)

    def _pick_custom_color(self):
        current = QColor(self._load_theme().accent)
        color = QColorDialog.getColor(current, self, "Выберите цвет оформления")
        if color.isValid():
            self._apply_theme(Theme.from_accent(color.name()))

    # ================================ прочее ================================
    def _show_db_error(self, err):
        QMessageBox.critical(self, "Ошибка базы данных", str(err))
