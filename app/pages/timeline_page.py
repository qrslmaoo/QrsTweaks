# app/pages/timeline_page.py

from __future__ import annotations

import datetime as _dt
from typing import Dict, Any, List

from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QScrollArea,
    QComboBox,
    QLineEdit,
    QPushButton,
    QTextEdit,
)
from PySide6.QtCore import Qt

from app.ui.widgets.card import Card
from src.qrs.core.log_manager import log_mgr


class TimelinePage(QWidget):
    """
    Global Timeline for QrsTweaks.

    Live view over the JSONL logs produced by LogManager.
    Supports:
      - Source filter (All / Windows / Game / Dashboard / System / Other)
      - Level filter (All / Info / OK / Warn / Error)
      - Text search filter
      - Live streaming of new log entries via log_mgr.subscribe(...)
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet("background: transparent;")

        self._current_source_filter = "All"
        self._current_level_filter = "All"
        self._current_text_filter = ""

        # -------------------------------------------------
        # Scroll wrapper
        # -------------------------------------------------
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll.setFrameShape(QScrollArea.NoFrame)
        scroll.setStyleSheet("background: transparent;")

        container = QWidget()
        scroll.setWidget(container)

        root = QVBoxLayout(container)
        root.setContentsMargins(10, 10, 10, 10)
        root.setSpacing(16)

        # -------------------------------------------------
        # Title
        # -------------------------------------------------
        title = QLabel("Timeline")
        title.setStyleSheet(
            "font-size: 22pt; color: #EFE6FF; font-weight:700;"
        )
        root.addWidget(title)

        subtitle = QLabel(
            "Live history of all major actions taken by QrsTweaks. "
            "Use this for debugging, validation, or pure nerd satisfaction."
        )
        subtitle.setStyleSheet("color:#A49BCF; font-size:10pt;")
        subtitle.setWordWrap(True)
        root.addWidget(subtitle)

        # -------------------------------------------------
        # Filters card
        # -------------------------------------------------
        filter_card = Card("Filters")
        fv = filter_card.body()

        row1 = QHBoxLayout()
        row1.setSpacing(8)

        self.combo_source = QComboBox()
        self.combo_source.addItems([
            "All",
            "Windows",
            "Game",
            "Dashboard",
            "System",
            "Passwords",
            "Other",
        ])
        self.combo_source.setFixedWidth(150)

        self.combo_level = QComboBox()
        self.combo_level.addItems([
            "All",
            "Info",
            "OK",
            "Warn",
            "Error",
        ])
        self.combo_level.setFixedWidth(120)

        self.edit_search = QLineEdit()
        self.edit_search.setPlaceholderText("Search text…")

        self.btn_clear = QPushButton("Clear View")
        self.btn_reload = QPushButton("Reload Today")

        row1.addWidget(QLabel("Source:"))
        row1.addWidget(self.combo_source)
        row1.addWidget(QLabel("Level:"))
        row1.addWidget(self.combo_level)
        row1.addWidget(self.edit_search, stretch=1)
        row1.addWidget(self.btn_reload)
        row1.addWidget(self.btn_clear)

        fv.addLayout(row1)
        root.addWidget(filter_card)

        # -------------------------------------------------
        # Timeline card
        # -------------------------------------------------
        log_card = Card("Event Timeline")
        lv = log_card.body()

        self.view = QTextEdit()
        self.view.setReadOnly(True)
        self.view.setMinimumHeight(260)
        self.view.setStyleSheet(
            """
            QTextEdit {
                background-color: #05030A;
                color: #F4EEFF;
                border-radius: 8px;
                border: 1px solid #2C1B45;
                font-size: 9pt;
            }
            """
        )
        lv.addWidget(self.view)
        root.addWidget(log_card)

        root.addStretch()

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.addWidget(scroll)

        # -------------------------------------------------
        # Wire signals and log manager
        # -------------------------------------------------
        self._connect()
        self._load_initial()
        log_mgr.subscribe(self._on_log_entry)

    # -------------------------------------------------
    # Wiring
    # -------------------------------------------------
    def _connect(self) -> None:
        self.combo_source.currentTextChanged.connect(self._on_filter_changed)
        self.combo_level.currentTextChanged.connect(self._on_filter_changed)
        self.edit_search.textChanged.connect(self._on_filter_changed)
        self.btn_clear.clicked.connect(self._clear_view)
        self.btn_reload.clicked.connect(self._reload_today)

    # -------------------------------------------------
    # Filters
    # -------------------------------------------------
    def _on_filter_changed(self, *args) -> None:
        self._current_source_filter = self.combo_source.currentText()
        self._current_level_filter = self.combo_level.currentText()
        self._current_text_filter = self.edit_search.text().strip().lower()
        # Reload from file for now to keep implementation simple
        self._reload_today()

    def _clear_view(self) -> None:
        self.view.clear()

    def _reload_today(self) -> None:
        self.view.clear()
        entries = log_mgr.get_recent_entries(max_entries=500)
        for e in entries:
            self._append_if_match(e)

    def _load_initial(self) -> None:
        entries = log_mgr.get_recent_entries(max_entries=200)
        for e in entries:
            self._append_if_match(e)

    # -------------------------------------------------
    # Log manager callbacks
    # -------------------------------------------------
    def _on_log_entry(self, entry: Dict[str, Any]) -> None:
        # Called from LogManager. We just append if it matches filters.
        self._append_if_match(entry)

    # -------------------------------------------------
    # Core formatting / filtering
    # -------------------------------------------------
    def _append_if_match(self, entry: Dict[str, Any]) -> None:
        source = str(entry.get("source", ""))
        level = str(entry.get("level", "")).lower()
        message = str(entry.get("message", ""))

        # Source filter
        sf = self._current_source_filter
        if sf != "All":
            # "Other" means anything not in the known set
            known = {"Windows", "Game", "Dashboard", "System", "Passwords"}
            if sf == "Other":
                if source in known:
                    return
            else:
                if source != sf:
                    return

        # Level filter
        lf = self._current_level_filter.lower()
        if lf != "all":
            if level != lf and not (lf == "info" and level == "info"):
                return

        # Text filter
        tf = self._current_text_filter
        if tf:
            blob = (source + " " + level + " " + message).lower()
            if tf not in blob:
                return

        self._append_entry(entry)

    def _append_entry(self, entry: Dict[str, Any]) -> None:
        ts = float(entry.get("ts", 0.0))
        dt = _dt.datetime.fromtimestamp(ts)
        t_str = dt.strftime("%H:%M:%S")

        source = str(entry.get("source", ""))
        level = str(entry.get("level", "info")).lower()
        message = str(entry.get("message", ""))

        # Level color
        if level == "ok":
            color = "#4ED97A"
        elif level == "warn":
            color = "#F0C674"
        elif level == "error":
            color = "#FF5C5C"
        else:
            color = "#9FA8C7"

        safe_msg = (
            message.replace("&", "&amp;")
                   .replace("<", "&lt;")
                   .replace(">", "&gt;")
        )
        safe_src = (
            source.replace("&", "&amp;")
                  .replace("<", "&lt;")
                  .replace(">", "&gt;")
        )

        html = (
            f"<span style='color:#6F7A8F'>[{t_str}]</span> "
            f"<span style='color:{color}; font-weight:600'>[{level.upper()}]</span> "
            f"<span style='color:#C0B4FF'>[{safe_src}]</span> "
            f"<span style='color:#F4EEFF'>{safe_msg}</span>"
        )

        self.view.append(html)

    # -------------------------------------------------
    # Cleanup
    # -------------------------------------------------
    def closeEvent(self, event) -> None:
        try:
            log_mgr.unsubscribe(self._on_log_entry)
        except Exception:
            pass
        super().closeEvent(event)
