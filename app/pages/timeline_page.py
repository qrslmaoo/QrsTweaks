# app/pages/timeline_page.py

from __future__ import annotations
import json
from pathlib import Path

from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QTextEdit, QScrollArea
from PySide6.QtCore import Qt, QTimer


class TimelinePage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet("background: transparent;")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)

        self.title = QLabel("System Timeline")
        self.title.setStyleSheet("font-size:22pt; color:#DDE1EA; font-weight:700;")
        layout.addWidget(self.title)

        self.view = QTextEdit()
        self.view.setReadOnly(True)
        self.view.setMinimumHeight(420)
        layout.addWidget(self.view)

        self.log_path = Path("Logs/daemon.log")

        # Poll for updates
        self.timer = QTimer(self)
        self.timer.setInterval(1000)
        self.timer.timeout.connect(self._update_timeline)
        self.timer.start()

        self._last_size = 0
        self._update_timeline()

    def _update_timeline(self):
        if not self.log_path.exists():
            return

        text = self.log_path.read_text()

        if len(text) == self._last_size:
            return  # no new data

        self._last_size = len(text)

        out = []
        for line in text.splitlines():
            try:
                evt = json.loads(line)
            except Exception:
                continue

            ts = evt.get("ts")
            name = evt.get("event")
            info = evt.get("info", {})

            out.append(f"[{name}]  {info}")

        self.view.setPlainText("\n".join(out))
        self.view.verticalScrollBar().setValue(
            self.view.verticalScrollBar().maximum()
        )
