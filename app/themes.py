"""Цветовые темы (ТЗ: «Задать стиль / цвет») и генерация таблицы стилей Qt."""
from __future__ import annotations

from dataclasses import dataclass


# ---------- работа с цветом (без Qt, чтобы можно было тестировать) ----------
def hex_to_rgb(color: str):
    color = color.lstrip("#")
    return tuple(int(color[i:i + 2], 16) for i in (0, 2, 4))


def rgb_to_hex(r, g, b) -> str:
    return "#{:02X}{:02X}{:02X}".format(*(max(0, min(255, round(v))) for v in (r, g, b)))


def mix(a: str, b: str, t: float) -> str:
    """Смесь цветов: t — доля цвета a."""
    ra, rb = hex_to_rgb(a), hex_to_rgb(b)
    return rgb_to_hex(*(ra[i] * t + rb[i] * (1 - t) for i in range(3)))


def rgba(color: str, alpha: float) -> str:
    r, g, b = hex_to_rgb(color)
    return f"rgba({r},{g},{b},{alpha})"


def luminance(color: str) -> float:
    r, g, b = hex_to_rgb(color)
    return (0.299 * r + 0.587 * g + 0.114 * b) / 255


# ---------------------------------- темы ------------------------------------
@dataclass(frozen=True)
class Theme:
    key: str
    title: str
    bg_main: str
    bg_secondary: str
    card: str
    text: str
    muted: str
    accent: str
    accent_hover: str
    accent_soft: str

    @property
    def border(self) -> str:
        return rgba(self.accent, 0.28)

    @property
    def on_accent(self) -> str:
        """Цвет текста на кнопках: белый на тёмном акценте, тёмный — на светлом."""
        return "#FFFFFF" if luminance(self.accent) < 0.72 else "#2B2523"

    @staticmethod
    def from_accent(accent: str) -> "Theme":
        """Тема из любого выбранного пользователем цвета."""
        accent = accent.upper()
        base = THEMES["default"]
        return Theme(
            key="custom", title="Свой цвет",
            bg_main=mix(accent, "#FFFFFF", 0.04),
            bg_secondary=mix(accent, "#FFFFFF", 0.10),
            card="#FFFFFF", text=base.text, muted=base.muted,
            accent=accent,
            accent_hover=mix(accent, "#000000", 0.85),
            accent_soft=mix(accent, "#FFFFFF", 0.14),
        )


THEMES = {
    "default": Theme("default", "Нежная пудра", "#FDFBF9", "#F5EFEA", "#FFFFFF",
                     "#2B2523", "#7D726D", "#D98A6C", "#C27355", "#FBECE6"),
    "sage": Theme("sage", "Мятный шалфей", "#F7FAF8", "#E9F2EE", "#FFFFFF",
                  "#212B27", "#65766E", "#689684", "#527D6C", "#E3F0EB"),
    "lavender": Theme("lavender", "Лаванда", "#FAF8FC", "#F0ECF8", "#FFFFFF",
                      "#262230", "#6F687E", "#9A84B8", "#8169A1", "#EFEAF7"),
    "peach": Theme("peach", "Персиковый рассвет", "#FFFDFB", "#FCEFE9", "#FFFFFF",
                   "#2E2421", "#826E69", "#E8998D", "#D47E71", "#FDECE9"),
}


def build_stylesheet(t: Theme) -> str:
    return f"""
QMainWindow, QDialog {{ background: {t.bg_main}; }}
QWidget {{ color: {t.text}; font-size: 14px; }}
QLabel {{ background: transparent; }}
QScrollArea {{ background: transparent; border: none; }}
QScrollArea > QWidget > QWidget {{ background: transparent; }}
QScrollBar:vertical {{ background: transparent; width: 10px; margin: 2px; }}
QScrollBar::handle:vertical {{ background: {t.border}; border-radius: 4px; min-height: 30px; }}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0; }}

QLineEdit, QTextEdit, QDoubleSpinBox, QDateEdit, QComboBox {{
    background: #FFFFFF; border: 1.5px solid {t.border}; border-radius: 14px;
    padding: 8px 12px; selection-background-color: {t.accent}; selection-color: {t.on_accent};
}}
QLineEdit:focus, QTextEdit:focus, QDoubleSpinBox:focus, QDateEdit:focus, QComboBox:focus {{
    border-color: {t.accent};
}}
QComboBox::drop-down {{ border: none; width: 26px; }}
QComboBox QAbstractItemView {{
    background: #FFFFFF; border: 1px solid {t.border}; outline: 0;
    selection-background-color: {t.accent_soft}; selection-color: {t.text};
}}

QPushButton {{ border-radius: 18px; padding: 9px 20px; font-weight: 600; }}
QPushButton#primary {{ background: {t.accent}; color: {t.on_accent}; border: none; }}
QPushButton#primary:hover {{ background: {t.accent_hover}; }}
QPushButton#soft {{ background: {t.accent_soft}; border: 1.5px solid {t.border}; }}
QPushButton#soft:hover {{ background: {t.accent}; color: {t.on_accent}; }}
QPushButton#tab {{
    background: {t.bg_secondary}; border: 1px solid {t.border}; color: {t.muted}; padding: 8px 16px;
}}
QPushButton#tab:hover {{ border-color: {t.accent}; }}
QPushButton#tab:checked {{ background: {t.accent}; color: {t.on_accent}; border-color: {t.accent}; }}
QPushButton#danger {{ background: transparent; border: 1.5px solid {t.border}; padding: 8px 12px; }}
QPushButton#danger:hover {{ background: #FDE8E8; border-color: #E57373; }}

QFrame#card {{ background: {t.card}; border: 1.5px solid {t.border}; border-radius: 24px; }}
QFrame#cardPhoto {{ background: {t.accent_soft}; border: none; border-radius: 18px; }}
QFrame#panel {{ background: {t.card}; border: 1px solid {t.border}; border-radius: 22px; }}
QFrame#feature {{ background: {t.card}; border: 1px solid {t.border}; border-radius: 18px; }}
QFrame#hero {{
    background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 {t.card}, stop:1 {t.accent_soft});
    border: 1.5px solid {t.border}; border-radius: 28px;
}}

QLabel#brand {{ font-family: Georgia, 'Times New Roman', serif; font-size: 26px; font-weight: 700; }}
QLabel#h1 {{ font-family: Georgia, 'Times New Roman', serif; font-size: 28px; font-weight: 700; }}
QLabel#title {{ font-size: 15px; font-weight: 700; }}
QLabel#h2 {{ font-family: Georgia, 'Times New Roman', serif; font-size: 22px; font-weight: 700; }}
QLabel#muted {{ color: {t.muted}; }}
QLabel#price {{ color: {t.accent}; font-size: 20px; font-weight: 700; }}
QLabel#error {{ color: #C0392B; font-weight: 600; }}
QLabel#pill {{
    background: {t.accent_soft}; border: 1px solid {t.border}; border-radius: 11px;
    padding: 3px 10px; font-size: 12px; font-weight: 600;
}}

QSlider::groove:horizontal {{ height: 6px; background: {t.accent_soft}; border-radius: 3px; }}
QSlider::sub-page:horizontal {{ background: {t.accent}; border-radius: 3px; }}
QSlider::handle:horizontal {{
    background: {t.accent}; width: 18px; height: 18px; margin: -6px 0; border-radius: 9px;
}}

QTabWidget::pane {{ border: none; }}
QTabBar::tab {{
    background: {t.bg_secondary}; color: {t.muted}; padding: 8px 22px;
    border-radius: 16px; margin-right: 6px; font-weight: 600;
}}
QTabBar::tab:selected {{ background: {t.accent}; color: {t.on_accent}; }}
QStatusBar {{ background: transparent; color: {t.muted}; }}
QMessageBox {{ background: {t.bg_main}; }}
"""
