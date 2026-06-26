import os
import threading

from PyQt5.QtCore import Qt, QTimer, pyqtSlot
from PyQt5.QtWidgets import (
    QApplication,
    QComboBox,
    QFrame,
    QHBoxLayout,
    QInputDialog,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from streamify.backend.config import APP_NAME
from streamify.backend.manager import StreamlinkManager
from streamify.backend.models import Stream
from streamify.ui.utils.config import DARK_THEME, LIGHT_THEME
from streamify.ui.utils.dialogs import AddStreamDialog
from streamify.ui.utils.signals import SignalEmitter
from streamify.ui.utils.widgets import HoverToggleFrame, RowFrame


class StreamlinkGUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.manager = StreamlinkManager()
        self.setWindowTitle(APP_NAME)
        self.resize(1150, 700)

        self.is_dark = True  # Keep track of Theme State

        self.selected_idx = None
        self.rows_gui_map = {}

        self.emitter = SignalEmitter()
        self.emitter.status_updated.connect(self.update_gui_status_slot)
        self.emitter.check_finished.connect(self.on_check_finished)

        self.build_ui()
        self.apply_theme()
        self.refresh_list()

        # Start Process Monitor
        self.monitor_timer = QTimer(self)
        self.monitor_timer.timeout.connect(self.start_process_monitor)
        self.monitor_timer.start(1000)

    def get_stylesheet(self, is_dark):
        """Loads the raw QSS stylesheet contents relative to this module."""

        filename = DARK_THEME if is_dark else LIGHT_THEME
        filepath = os.path.join(os.path.dirname(os.path.abspath(__file__)), filename)

        try:
            with open(filepath, "r", encoding="utf-8") as f:
                return f.read()
        except OSError as e:
            print(f"Warning: Could not load stylesheet {filename}: {e}")
            return ""

    def apply_theme(self):
        """Applies the current Light/Dark styles to all widgets."""
        QApplication.instance().setStyleSheet(self.get_stylesheet(self.is_dark))

        sidebar_bg = "#181825" if self.is_dark else "#ffffff"
        self.sidebar_frame.setStyleSheet(f"background-color: {sidebar_bg};")

        self.toggle_frame.update_theme(self.is_dark)

        self.check_btn.setStyleSheet(
            f"background-color: {self.get_status_color('')}; color: white;"
        )
        self.btn_theme.setStyleSheet(
            f"background-color: {self.get_status_color('')}; color: white;"
        )
        self.add_btn.setStyleSheet(
            f"background-color: {self.get_status_color('')}; color: white;"
        )

    def toggle_theme(self):
        """Swaps the theme state and redraws the UI."""
        self.is_dark = not self.is_dark
        self.btn_theme.setText("☀️" if self.is_dark else "❨")
        self.apply_theme()
        self.refresh_list()  # Redraws the rows using new theme colors

    def get_status_color(self, status_text):
        """Returns the appropriate color for the background status badge."""
        if status_text == "Live":
            return "#2e8b57"
        if status_text == "Error":
            return "#d32f2f"

        return "#45475a" if self.is_dark else "#999999"

    def build_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # 1. Sidebar Frame
        self.sidebar_frame = QWidget()
        self.sidebar_frame.setFixedWidth(530)
        sidebar_layout = QVBoxLayout(self.sidebar_frame)
        sidebar_layout.setContentsMargins(15, 15, 10, 15)
        sidebar_layout.setSpacing(10)

        # 2. Dynamic Auto-Hiding Toggle Bar
        self.toggle_frame = HoverToggleFrame(self.toggle_sidebar, self.is_dark)

        # 3. Video Frame (Expands to fill)
        self.video_frame = QWidget()
        self.video_frame.setStyleSheet("background-color: #000000;")
        self.video_frame.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        main_layout.addWidget(self.sidebar_frame)
        main_layout.addWidget(self.toggle_frame)
        main_layout.addWidget(self.video_frame)

        # --- SIDEBAR CONTENTS ---

        # Search & Filters
        top_frame = QWidget()
        top_layout = QHBoxLayout(top_frame)
        top_layout.setContentsMargins(0, 0, 0, 0)
        top_layout.setSpacing(8)

        lbl_search = QLabel("Search:")
        lbl_search.setProperty("class", "bold-label")
        top_layout.addWidget(lbl_search)

        self.search_var = QLineEdit()
        self.search_var.setPlaceholderText("Find stream...")
        self.search_var.textChanged.connect(self.refresh_list)
        top_layout.addWidget(self.search_var)

        lbl_cat = QLabel("Cat:")
        lbl_cat.setProperty("class", "bold-label")
        top_layout.addWidget(lbl_cat)

        self.cat_filter_cb = QComboBox()
        self.update_category_combobox()
        self.cat_filter_cb.currentTextChanged.connect(self.refresh_list)
        top_layout.addWidget(self.cat_filter_cb)

        btn_add_cat = QPushButton("+")
        btn_add_cat.setFixedWidth(32)
        btn_add_cat.clicked.connect(self.add_category_dialog)
        top_layout.addWidget(btn_add_cat)

        btn_del_cat = QPushButton("-")
        btn_del_cat.setFixedWidth(32)
        btn_del_cat.clicked.connect(self.delete_category_dialog)
        top_layout.addWidget(btn_del_cat)

        # Theme Toggle Button (Sun/Moon)
        self.btn_theme = QPushButton("☀️" if self.is_dark else "❨")
        self.btn_theme.setStyleSheet(
            f"background-color: {self.get_status_color('')}; color: white;"
        )
        self.btn_theme.setFixedWidth(32)
        self.btn_theme.clicked.connect(self.toggle_theme)
        top_layout.addWidget(self.btn_theme)

        sidebar_layout.addWidget(top_frame)

        # Header for custom list
        header_frame = QFrame()
        header_layout = QHBoxLayout(header_frame)
        header_layout.setContentsMargins(5, 10, 5, 5)

        def add_header(text, width=None):
            lbl = QLabel(text)
            lbl.setProperty("class", "header-label")
            if width:
                lbl.setFixedWidth(width)
            header_layout.addWidget(lbl)

        add_header("Action", 75)
        add_header("Name", 120)
        add_header("Platform", 80)
        add_header("Category", 90)
        add_header("Status", 80)
        header_layout.addStretch()
        sidebar_layout.addWidget(header_frame)

        # Scrollable List Body
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)

        self.scroll_widget = QWidget()
        self.scroll_widget.setStyleSheet("background-color: transparent;")
        self.scroll_layout = QVBoxLayout(self.scroll_widget)
        self.scroll_layout.setAlignment(Qt.AlignTop)
        self.scroll_layout.setContentsMargins(0, 0, 0, 0)
        self.scroll_layout.setSpacing(2)

        self.scroll_area.setWidget(self.scroll_widget)
        sidebar_layout.addWidget(self.scroll_area)

        # Bottom Controls
        bot_frame = QWidget()
        bot_layout = QHBoxLayout(bot_frame)
        bot_layout.setContentsMargins(0, 5, 0, 0)
        bot_layout.setSpacing(10)

        lbl_qual = QLabel("Quality:")
        lbl_qual.setProperty("class", "bold-label")
        bot_layout.addWidget(lbl_qual)

        self.quality_cb = QComboBox()
        self.quality_cb.addItems(["best", "720p", "480p", "audio_only"])
        bot_layout.addWidget(self.quality_cb)

        self.check_btn = QPushButton("Check Status")
        self.check_btn.setStyleSheet(
            f"background-color: {self.get_status_color('')}; color: white;"
        )
        self.check_btn.clicked.connect(self.run_status_check)
        bot_layout.addWidget(self.check_btn)

        bot_layout.addStretch()

        del_btn = QPushButton("Delete")
        del_btn.setStyleSheet("background-color: #d32f2f; color: white;")
        del_btn.clicked.connect(self.on_delete_clicked)
        bot_layout.addWidget(del_btn)

        self.add_btn = QPushButton("Add Stream")
        self.add_btn.setStyleSheet(
            f"background-color: {self.get_status_color('')}; color: white;"
        )
        self.add_btn.clicked.connect(self.open_add_dialog)
        bot_layout.addWidget(self.add_btn)

        sidebar_layout.addWidget(bot_frame)

    def toggle_sidebar(self):
        visible = self.toggle_frame.sidebar_visible
        self.sidebar_frame.setVisible(visible)

    def toggle_stream(self, idx):
        if self.manager.active_stream_idx == idx:
            self.manager.stop_stream()
        else:
            quality = self.quality_cb.currentText()
            wid = str(int(self.video_frame.winId()))
            self.manager.launch_stream(idx, quality, wid)
        self.update_action_buttons()

    def update_action_buttons(self):
        for real_idx, widgets in self.rows_gui_map.items():
            btn = widgets["action_btn"]
            if self.manager.active_stream_idx == real_idx:
                btn.setText("Stop")
                btn.setStyleSheet(
                    "background-color: #d32f2f; color: white; border-radius: 4px;"
                )
            else:
                btn.setText("Launch")
                btn.setStyleSheet(
                    "background-color: #2e8b57; color: white; border-radius: 4px;"
                )

    def start_process_monitor(self):
        if self.manager.current_process is not None:
            if self.manager.current_process.poll() is not None:
                self.manager.current_process = None
                self.manager.active_stream_idx = None
                self.update_action_buttons()

    def update_category_combobox(self):
        cats = ["All"] + list(self.manager.categorys.keys())
        self.cat_filter_cb.clear()
        self.cat_filter_cb.addItems(cats)

    def refresh_list(self):
        while self.scroll_layout.count():
            item = self.scroll_layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()

        self.rows_gui_map.clear()
        self.selected_idx = None

        search_txt = self.search_var.text()
        cat_filter = self.cat_filter_cb.currentText()
        results = self.manager.search_streams(search_txt, cat_filter)

        for real_idx, s in results:
            url_str = self.manager.get_url_by_id(s.url_id)
            cat_str = self.manager.get_category_by_id(s.category_id)

            row_f = RowFrame(real_idx, self.is_dark)
            row_f.clicked.connect(self.select_row)
            row_layout = QHBoxLayout(row_f)
            row_layout.setContentsMargins(5, 6, 5, 6)
            row_layout.setSpacing(6)

            is_active = self.manager.active_stream_idx == real_idx
            btn_text = "Stop" if is_active else "Launch"
            btn_bg = "#d32f2f" if is_active else "#2e8b57"

            btn_action = QPushButton(btn_text)
            btn_action.setFixedWidth(70)
            btn_action.setStyleSheet(
                f"background-color: {btn_bg}; color: white; border-radius: 4px; padding: 4px;"
            )
            btn_action.clicked.connect(
                lambda checked, i=real_idx: self.toggle_stream(i)
            )
            row_layout.addWidget(btn_action)

            def add_col(text, width):
                lbl = QLabel(text)
                lbl.setFixedWidth(width)
                row_layout.addWidget(lbl)
                return lbl

            add_col(s.name, 110)
            add_col(url_str, 80)
            add_col(cat_str, 90)

            lbl_status = QLabel("Unknown")
            lbl_status.setFixedWidth(80)
            lbl_status.setAlignment(Qt.AlignCenter)
            bg_color = self.get_status_color("Unknown")
            lbl_status.setStyleSheet(
                f"background-color: {bg_color}; color: white; border-radius: 4px; padding: 2px;"
            )
            row_layout.addWidget(lbl_status)

            row_layout.addStretch()
            self.scroll_layout.addWidget(row_f)

            self.rows_gui_map[real_idx] = {
                "frame": row_f,
                "status_lbl": lbl_status,
                "action_btn": btn_action,
            }

    def select_row(self, idx):
        if self.selected_idx is not None and self.selected_idx in self.rows_gui_map:
            self.rows_gui_map[self.selected_idx]["frame"].set_selected(False)

        self.selected_idx = idx
        if idx in self.rows_gui_map:
            self.rows_gui_map[idx]["frame"].set_selected(True)

    def run_status_check(self):
        self.check_btn.setEnabled(False)
        self.check_btn.setText("Checking...")

        for widgets in self.rows_gui_map.values():
            lbl = widgets["status_lbl"]
            lbl.setText("Checking...")
            bg_color = self.get_status_color("Unknown")
            lbl.setStyleSheet(
                f"background-color: {bg_color}; color: white; border-radius: 4px; padding: 2px;"
            )

        def callback(stream, status_text):
            self.emitter.status_updated.emit(stream, status_text)

        def run_thread():
            self.manager.check_statuses_once(callback)
            # The background thread emits this signal when completely finished
            self.emitter.check_finished.emit()

        threading.Thread(target=run_thread, daemon=True).start()

    @pyqtSlot(object, str)
    def update_gui_status_slot(self, stream: Stream, status_text: str):
        try:
            idx = self.manager.streams.index(stream)
            if idx in self.rows_gui_map:
                lbl = self.rows_gui_map[idx]["status_lbl"]
                lbl.setText(status_text)
                bg_color = self.get_status_color(status_text)
                lbl.setStyleSheet(
                    f"background-color: {bg_color}; color: white; border-radius: 4px; padding: 2px;"
                )
        except ValueError:
            pass

    @pyqtSlot()
    def on_check_finished(self):
        """Safely resets the button on the main thread after background check finishes."""
        self.check_btn.setEnabled(True)
        self.check_btn.setText("Check Status")

    def on_delete_clicked(self):
        if self.selected_idx is None:
            return
        reply = QMessageBox.question(
            self, "Confirm", "Delete this stream?", QMessageBox.Yes | QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            self.manager.delete_stream(self.selected_idx)
            self.refresh_list()

    def add_category_dialog(self):
        cat_name, ok = QInputDialog.getText(
            self, "Add Category", "Enter new category name:"
        )
        if ok and cat_name:
            self.manager.add_category(cat_name)
            self.update_category_combobox()

    def delete_category_dialog(self):
        cat_name = self.cat_filter_cb.currentText()
        if cat_name == "All":
            QMessageBox.warning(self, "Warning", "Cannot delete 'All' category.")
            return

        reply = QMessageBox.question(
            self,
            "Confirm",
            f"Delete category '{cat_name}'?",
            QMessageBox.Yes | QMessageBox.No,
        )
        if reply == QMessageBox.Yes:
            self.manager.delete_category(cat_name)
            self.update_category_combobox()
            self.cat_filter_cb.setCurrentText("All")
            self.refresh_list()

    def open_add_dialog(self):
        dialog = AddStreamDialog(self.manager, self)
        if dialog.exec_():
            name, url_str, cat_str = dialog.get_data()
            if not name:
                return

            if url_str not in self.manager.urls:
                self.manager.add_url(url_str)
            if cat_str not in self.manager.categorys:
                self.manager.add_category(cat_str)

            new_stream = Stream(
                name=name,
                url_id=self.manager.urls[url_str],
                category_id=self.manager.categorys[cat_str],
            )
            self.manager.add_stream(new_stream)

            self.update_category_combobox()
            self.refresh_list()
