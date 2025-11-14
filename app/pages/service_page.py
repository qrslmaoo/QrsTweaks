# app/pages/service_page.py

from __future__ import annotations

import os
import platform
from pathlib import Path

from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QTextEdit,
    QScrollArea,
)
from PySide6.QtCore import Qt, QTimer

from app.ui.widgets.card import Card
from src.qrs.service.controller import (
    start_daemon,
    stop_daemon,
    daemon_running,
)


class ServicePage(QWidget):
    """
    Service / Daemon control panel for QrsTweaks.

    Features:
      - Live daemon status (Running / Stopped)
      - Start / Stop / Restart daemon
      - Open Logs folder
      - Force-clear PID file (if things get stuck)
      - Log output area (mirrors what happened)
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet("background: transparent;")

        # ----------------------------------------
        # Scroll wrapper (same pattern as other pages)
        # ----------------------------------------
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

        # ----------------------------------------
        # Header
        # ----------------------------------------
        title = QLabel("Service / Daemon Control")
        title.setStyleSheet("font-size: 22pt; color: #DDE1EA; font-weight: 700;")
        root.addWidget(title)

        subtitle = QLabel(
            "Manage the background QrsTweaks daemon. "
            "This process handles game detection, telemetry, and automation."
        )
        subtitle.setWordWrap(True)
        subtitle.setStyleSheet("color:#AAB0BC; font-size:10pt;")
        root.addWidget(subtitle)

        # ----------------------------------------
        # Status + basic controls
        # ----------------------------------------
        status_card = Card("Daemon Status")
        sv = status_card.body()

        row = QHBoxLayout()
        row.setSpacing(12)

        self.lbl_status = QLabel("Daemon: Unknown")
        self.lbl_status.setStyleSheet("color:#FFA500; font-weight:600;")

        self.btn_start = QPushButton("Start Daemon")
        self.btn_stop = QPushButton("Stop Daemon")
        self.btn_restart = QPushButton("Restart Daemon")

        for b in (self.btn_start, self.btn_stop, self.btn_restart):
            b.setMinimumHeight(32)

        row.addWidget(self.lbl_status)
        row.addStretch()
        row.addWidget(self.btn_start)
        row.addWidget(self.btn_stop)
        row.addWidget(self.btn_restart)

        sv.addLayout(row)
        root.addWidget(status_card)

        # ----------------------------------------
        # Maintenance tools
        # ----------------------------------------
        tools_card = Card("Maintenance Tools")
        tv = tools_card.body()

        self.btn_open_logs = QPushButton("Open Logs Folder")
        self.btn_open_runtime = QPushButton("Open .runtime Folder")
        self.btn_clear_pid = QPushButton("Force-Clear Daemon PID")

        for b in (self.btn_open_logs, self.btn_open_runtime, self.btn_clear_pid):
            b.setMinimumHeight(30)
            tv.addWidget(b)

        root.addWidget(tools_card)

        # ----------------------------------------
        # Log output
        # ----------------------------------------
        log_card = Card("Service Log")
        lv = log_card.body()

        self.log = QTextEdit()
        self.log.setReadOnly(True)
        self.log.setMinimumHeight(220)
        lv.addWidget(self.log)

        root.addWidget(log_card)

        root.addStretch()

        # Attach scroll to main layout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.addWidget(scroll)

        # Wire signals
        self._connect()

        # Start periodic status polling
        self._status_timer = QTimer(self)
        self._status_timer.timeout.connect(self._refresh_status)
        self._status_timer.start(1000)

        # Initial refresh
        self._refresh_status()
        self._log("Service page initialized.")

    # ---------------------------------------------------
    # Signal connections
    # ---------------------------------------------------
    def _connect(self):
        self.btn_start.clicked.connect(self._on_start)
        self.btn_stop.clicked.connect(self._on_stop)
        self.btn_restart.clicked.connect(self._on_restart)

        self.btn_open_logs.clicked.connect(self._on_open_logs)
        self.btn_open_runtime.clicked.connect(self._on_open_runtime)
        self.btn_clear_pid.clicked.connect(self._on_clear_pid)

    # ---------------------------------------------------
    # Status handling
    # ---------------------------------------------------
    def _refresh_status(self):
        running = False
        try:
            running = daemon_running()
        except Exception as e:
            self._log(f"[Status] Error checking daemon: {e!r}")
            running = False

        if running:
            self.lbl_status.setText("Daemon: RUNNING")
            self.lbl_status.setStyleSheet("color:#44DD44; font-weight:600;")
        else:
            self.lbl_status.setText("Daemon: STOPPED")
            self.lbl_status.setStyleSheet("color:#FF5555; font-weight:600;")

    # ---------------------------------------------------
    # Button handlers
    # ---------------------------------------------------
    def _on_start(self):
        ok, msg = start_daemon()
        self._log_result("Start", ok, msg)
        self._refresh_status()

    def _on_stop(self):
        ok, msg = stop_daemon()
        self._log_result("Stop", ok, msg)
        self._refresh_status()

    def _on_restart(self):
        ok1, msg1 = stop_daemon()
        ok2, msg2 = start_daemon()
        ok = ok1 and ok2
        msg = f"{msg1}\n{msg2}"
        self._log_result("Restart", ok, msg)
        self._refresh_status()

    def _on_open_logs(self):
        logs_dir = Path("Logs").absolute()
        self._ensure_dir(logs_dir)
        self._open_in_explorer(logs_dir)
        self._log(f"[Tools] Opened Logs folder: {logs_dir}")

    def _on_open_runtime(self):
        rt_dir = Path(".runtime").absolute()
        self._ensure_dir(rt_dir)
        self._open_in_explorer(rt_dir)
        self._log(f"[Tools] Opened .runtime folder: {rt_dir}")

    def _on_clear_pid(self):
        pid_path = Path(".runtime") / "daemon.pid"
        if not pid_path.exists():
            self._log("[Tools] No PID file to clear (.runtime/daemon.pid missing).")
            return

        try:
            pid_path.unlink(missing_ok=True)
            self._log("[Tools] Cleared daemon PID file.")
        except Exception as e:
            self._log(f"[Tools] Failed to clear PID file: {e!r}")

        # Refresh status in case it was stale
        self._refresh_status()

    # ---------------------------------------------------
    # Helpers
    # ---------------------------------------------------
    def _log(self, text: str):
        self.log.append(f"<span style='color:#DDE1EA'>{text}</span>")

    def _log_result(self, label: str, ok: bool, msg: str):
        color = "#44DD44" if ok else "#FF5555"
        safe = (
            msg.replace("&", "&amp;")
               .replace("<", "&lt;")
               .replace(">", "&gt;")
        )
        self.log.append(
            f"<span style='color:{color}'>[{label}] {safe}</span>"
        )

    def _ensure_dir(self, p: Path):
        try:
            p.mkdir(parents=True, exist_ok=True)
        except Exception:
            # best-effort; ignore
            pass

    def _open_in_explorer(self, p: Path):
        try:
            if platform.system().lower().startswith("win"):
                os.startfile(str(p))
            else:
                # Non-Windows: try best-effort open
                try:
                    import subprocess

                    subprocess.Popen(["xdg-open", str(p)])
                except Exception:
                    pass
        except Exception:
            # Silent failure; log already covers enough
            pass
