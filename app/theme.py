"""
Modern theme system for Photo Template Studio Pro.
Provides dark and light QSS themes with premium cross-platform styling.
"""

DARK_PALETTE = {
    "bg_primary": "#0f1119",
    "bg_secondary": "#161b26",
    "bg_tertiary": "#1e2433",
    "bg_elevated": "#252c3b",
    "border": "#2d3548",
    "border_hover": "#404a5f",
    "text_primary": "#e2e8f0",
    "text_secondary": "#94a3b8",
    "text_muted": "#64748b",
    "accent": "#e94560",
    "accent_hover": "#d63e56",
    "accent_pressed": "#c4364c",
    "success": "#22c55e",
    "warning": "#f59e0b",
    "scrollbar_bg": "#161b26",
    "scrollbar_handle": "#2d3548",
    "scrollbar_hover": "#404a5f",
    "input_bg": "#0f1119",
    "canvas_bg": "#0a0e17",
}

LIGHT_PALETTE = {
    "bg_primary": "#f8fafc",
    "bg_secondary": "#ffffff",
    "bg_tertiary": "#f1f5f9",
    "bg_elevated": "#e2e8f0",
    "border": "#cbd5e1",
    "border_hover": "#94a3b8",
    "text_primary": "#1e293b",
    "text_secondary": "#475569",
    "text_muted": "#94a3b8",
    "accent": "#e94560",
    "accent_hover": "#d63e56",
    "accent_pressed": "#c4364c",
    "success": "#16a34a",
    "warning": "#d97706",
    "scrollbar_bg": "#f1f5f9",
    "scrollbar_handle": "#cbd5e1",
    "scrollbar_hover": "#94a3b8",
    "input_bg": "#ffffff",
    "canvas_bg": "#e2e8f0",
}

_QSS_TEMPLATE = """
/* === Global === */
QMainWindow {
    background-color: $bg_primary;
}
QWidget {
    color: $text_primary;
    font-family: 'Segoe UI', 'Inter', '-apple-system', 'Helvetica Neue', 'Arial', sans-serif;
    font-size: 13px;
}
QWidget#central_widget {
    background-color: $bg_primary;
}

/* === Tooltips === */
QToolTip {
    background-color: $bg_tertiary;
    color: $text_primary;
    border: 1px solid $border;
    border-radius: 4px;
    padding: 4px 8px;
    font-size: 12px;
}

/* === Tab Bar === */
QTabWidget::pane {
    border: none;
    background-color: $bg_primary;
}
QTabBar {
    background-color: $bg_secondary;
    qproperty-drawBase: 0;
}
QTabBar::tab {
    background: $bg_secondary;
    color: $text_secondary;
    padding: 12px 28px;
    border: none;
    border-bottom: 3px solid transparent;
    font-weight: 600;
    font-size: 13px;
}
QTabBar::tab:selected {
    color: $accent;
    border-bottom-color: $accent;
    background: $bg_primary;
}
QTabBar::tab:hover:!selected {
    color: $text_primary;
    background: $bg_tertiary;
}

/* === Scroll Areas === */
QScrollArea {
    border: none;
    background-color: $bg_secondary;
}
QScrollArea > QWidget > QWidget {
    background-color: $bg_secondary;
}

/* === Scrollbars === */
QScrollBar:vertical {
    background: $scrollbar_bg;
    width: 6px;
    border: none;
}
QScrollBar::handle:vertical {
    background: $scrollbar_handle;
    border-radius: 3px;
    min-height: 30px;
}
QScrollBar::handle:vertical:hover {
    background: $scrollbar_hover;
}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical,
QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {
    height: 0; background: none;
}
QScrollBar:horizontal {
    background: $scrollbar_bg;
    height: 6px;
    border: none;
}
QScrollBar::handle:horizontal {
    background: $scrollbar_handle;
    border-radius: 3px;
    min-width: 30px;
}
QScrollBar::handle:horizontal:hover {
    background: $scrollbar_hover;
}
QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal,
QScrollBar::add-page:horizontal, QScrollBar::sub-page:horizontal {
    width: 0; background: none;
}

/* === Labels === */
QLabel {
    color: $text_primary;
    background: transparent;
    padding: 0;
}
QLabel[class="section-header"] {
    color: $text_secondary;
    font-size: 11px;
    font-weight: 700;
    letter-spacing: 1.2px;
    padding-top: 14px;
    padding-bottom: 4px;
}
QLabel[class="app-title"] {
    color: $accent;
    font-size: 18px;
    font-weight: 800;
}
QLabel[class="app-subtitle"] {
    color: $text_muted;
    font-size: 11px;
}
QLabel[class="info-label"] {
    color: $text_muted;
    font-size: 11px;
}
QLabel[class="value-label"] {
    color: $text_secondary;
    font-size: 11px;
    min-width: 36px;
}
QLabel[class="status-bar"] {
    background-color: $bg_tertiary;
    color: $text_muted;
    font-size: 11px;
    padding: 4px 12px;
    border-top: 1px solid $border;
}

/* === Buttons === */
QPushButton {
    background-color: $bg_tertiary;
    color: $text_primary;
    border: 1px solid $border;
    border-radius: 6px;
    padding: 8px 16px;
    font-weight: 500;
    font-size: 12px;
}
QPushButton:hover {
    background-color: $bg_elevated;
    border-color: $border_hover;
}
QPushButton:pressed {
    background-color: $bg_primary;
}
QPushButton:disabled {
    color: $text_muted;
    background-color: $bg_secondary;
}
QPushButton[class="accent"] {
    background-color: $accent;
    color: #ffffff;
    border: none;
    font-weight: 600;
    padding: 10px 20px;
}
QPushButton[class="accent"]:hover {
    background-color: $accent_hover;
}
QPushButton[class="accent"]:pressed {
    background-color: $accent_pressed;
}
QPushButton[class="accent"]:disabled {
    background-color: $text_muted;
}
QPushButton[class="tool-btn"] {
    padding: 7px 14px;
    font-size: 12px;
    border-radius: 5px;
}
QPushButton[class="tool-btn"]:checked {
    background-color: $accent;
    color: #ffffff;
    border-color: $accent;
}
QPushButton[class="success"] {
    background-color: $success;
    color: #ffffff;
    border: none;
    font-weight: 600;
}
QPushButton[class="success"]:hover {
    background-color: #1da34e;
}
QPushButton[class="link-btn"] {
    background: transparent;
    border: none;
    color: $text_muted;
    font-size: 11px;
    padding: 2px 0;
}
QPushButton[class="link-btn"]:hover {
    color: $accent;
}

/* === Combo Boxes === */
QComboBox {
    background-color: $input_bg;
    color: $text_primary;
    border: 1px solid $border;
    border-radius: 6px;
    padding: 6px 12px;
    font-size: 12px;
    min-height: 22px;
}
QComboBox:hover {
    border-color: $border_hover;
}
QComboBox::drop-down {
    border: none;
    width: 24px;
}
QComboBox::down-arrow {
    image: none;
    border-left: 4px solid transparent;
    border-right: 4px solid transparent;
    border-top: 5px solid $text_secondary;
    margin-right: 8px;
}
QComboBox QAbstractItemView {
    background-color: $bg_tertiary;
    color: $text_primary;
    border: 1px solid $border;
    selection-background-color: $accent;
    selection-color: #ffffff;
    padding: 4px;
    outline: 0;
}

/* === Sliders === */
QSlider::groove:horizontal {
    background: $border;
    height: 4px;
    border-radius: 2px;
}
QSlider::handle:horizontal {
    background: $accent;
    width: 14px;
    height: 14px;
    margin: -5px 0;
    border-radius: 7px;
    border: none;
}
QSlider::handle:horizontal:hover {
    background: $accent_hover;
    width: 16px;
    height: 16px;
    margin: -6px 0;
    border-radius: 8px;
}
QSlider::sub-page:horizontal {
    background: $accent;
    border-radius: 2px;
}

/* === Input Fields === */
QLineEdit {
    background-color: $input_bg;
    color: $text_primary;
    border: 1px solid $border;
    border-radius: 6px;
    padding: 6px 12px;
    font-size: 12px;
}
QLineEdit:focus {
    border-color: $accent;
}
QTextEdit {
    background-color: $input_bg;
    color: $text_primary;
    border: 1px solid $border;
    border-radius: 6px;
    padding: 8px 12px;
    font-size: 12px;
}
QTextEdit:focus {
    border-color: $accent;
}

/* === Checkboxes === */
QCheckBox {
    color: $text_primary;
    spacing: 8px;
    font-size: 12px;
    background: transparent;
}
QCheckBox::indicator {
    width: 18px;
    height: 18px;
    border: 2px solid $border;
    border-radius: 4px;
    background: $input_bg;
}
QCheckBox::indicator:checked {
    background-color: $accent;
    border-color: $accent;
}
QCheckBox::indicator:hover {
    border-color: $border_hover;
}

/* === Spin Boxes === */
QSpinBox {
    background-color: $input_bg;
    color: $text_primary;
    border: 1px solid $border;
    border-radius: 6px;
    padding: 4px 8px;
    font-size: 12px;
}
QSpinBox:focus {
    border-color: $accent;
}

/* === Frames === */
QFrame[class="separator"] {
    background-color: $border;
    max-height: 1px;
}
QFrame#center_frame {
    background-color: $canvas_bg;
    border: none;
}

/* === Canvas === */
QGraphicsView {
    background-color: $canvas_bg;
    border: none;
}

/* === Message Boxes === */
QMessageBox {
    background-color: $bg_secondary;
}
QMessageBox QLabel {
    color: $text_primary;
    font-size: 13px;
}
QMessageBox QPushButton {
    min-width: 80px;
}
"""


def _build_qss(palette):
    """Build QSS from template using palette values."""
    qss = _QSS_TEMPLATE
    # Sort by key length descending to prevent partial replacements
    for key in sorted(palette.keys(), key=len, reverse=True):
        qss = qss.replace(f"${key}", palette[key])
    return qss


def get_theme(dark=True):
    """Get the QSS stylesheet for the specified theme."""
    palette = DARK_PALETTE if dark else LIGHT_PALETTE
    return _build_qss(palette)


def get_canvas_bg(dark=True):
    """Get the canvas background color for the specified theme."""
    return DARK_PALETTE["canvas_bg"] if dark else LIGHT_PALETTE["canvas_bg"]
