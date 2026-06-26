from PyQt5.QtCore import pyqtSignal
from PyQt5.QtWidgets import QFrame, QPushButton, QSizePolicy, QVBoxLayout


class RowFrame(QFrame):
    """Custom Frame for a modern row with hover & selection states matching the Theme."""

    clicked = pyqtSignal(int)

    def __init__(self, idx, is_dark, parent=None):
        super().__init__(parent)
        self.idx = idx
        self.is_dark = is_dark
        self.selected = False
        self.update_style()

    def update_style(self):
        bg_sel = "#313244" if self.is_dark else "#dcdcdc"
        border = "#313244" if self.is_dark else "#cccccc"

        if self.selected:
            self.setStyleSheet(f"background-color: {bg_sel}; border-radius: 6px;")
        else:
            self.setStyleSheet(
                f"background-color: transparent; border-bottom: 1px solid {border}; border-radius: 0px;"
            )

    def set_selected(self, val):
        self.selected = val
        self.update_style()

    def enterEvent(self, event):
        if not self.selected:
            bg_hover = "#2a2b3c" if self.is_dark else "#e8e8e8"
            border = "#313244" if self.is_dark else "#cccccc"
            self.setStyleSheet(
                f"background-color: {bg_hover}; border-bottom: 1px solid {border}; border-radius: 6px;"
            )
        super().enterEvent(event)

    def leaveEvent(self, event):
        self.update_style()
        super().leaveEvent(event)

    def mousePressEvent(self, event):
        self.clicked.emit(self.idx)
        super().mousePressEvent(event)


class HoverToggleFrame(QFrame):
    """A sidebar toggle bar that completely auto-hides when watching streams in full screen."""

    def __init__(self, toggle_callback, is_dark, parent=None):
        super().__init__(parent)
        self.toggle_callback = toggle_callback
        self.sidebar_visible = True

        self.setStyleSheet("background-color: transparent;")

        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)

        self.btn = QPushButton("<")
        self.btn.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.btn.clicked.connect(self.on_click)
        self.layout.addWidget(self.btn)

        self.update_theme(is_dark)
        self.update_state()

    def update_theme(self, is_dark):
        self.is_dark = is_dark
        btn_bg = "#313244" if is_dark else "#cccccc"
        btn_hover = "#45475a" if is_dark else "#bbbbbb"
        text_color = "#cdd6f4" if is_dark else "#333333"

        self.btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {btn_bg};
                border: none;
                border-radius: 0px;
                color: {text_color};
            }}
            QPushButton:hover {{ background-color: {btn_hover}; }}
        """)

    def on_click(self):
        self.sidebar_visible = not self.sidebar_visible
        self.toggle_callback()
        self.update_state()

    def update_state(self):
        if self.sidebar_visible:
            self.setFixedWidth(15)
            self.btn.setText("<")
            self.btn.show()
        else:
            self.setFixedWidth(3)
            self.btn.hide()

    def enterEvent(self, event):
        if not self.sidebar_visible:
            self.setFixedWidth(20)
            self.btn.setText(">")
            self.btn.show()
        super().enterEvent(event)

    def leaveEvent(self, event):
        if not self.sidebar_visible:
            self.setFixedWidth(3)
            self.btn.hide()
        super().leaveEvent(event)
