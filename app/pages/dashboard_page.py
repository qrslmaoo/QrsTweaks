# app/pages/dashboard_page.py

from __future__ import annotations

import time

from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QScrollArea,
    QPushButton,
    QProgressBar,
)
from PySide6.QtCore import Qt, QTimer

from app.ui.widgets.card import Card
from src.qrs.modules.windows_optim import WindowsOptimizer
from src.qrs.modules.game_optim import GameOptimizer
from src.qrs.core.log_manager import log_mgr

try:
    import psutil  # type: ignore
except ImportError:
    psutil = None


class DashboardPage(QWidget):
    """
    QrsTweaks Dashboard

    Branded home screen with:
      - System overview (CPU / RAM / Disk)
      - Game / Smart Mode hints
      - Quick actions into Windows/Game optimizers
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet("background: transparent;")

        # Backends for quick actions
        self.win_opt = WindowsOptimizer()
        self.game_opt = GameOptimizer()

        # -------------------------------------------------
        # SCROLL WRAPPER
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
        # TITLE
        # -------------------------------------------------
        title = QLabel("QrsTweaks Dashboard")
        title.setStyleSheet(
            "font-size: 24pt; color: #F3E8FF; font-weight: 700; "
            "letter-spacing: 0.5px;"
        )
        root.addWidget(title)

        subtitle = QLabel(
            "High-level view of your system, game readiness, and quick actions."
        )
        subtitle.setStyleSheet("color: #A48BFF; font-size: 10pt;")
        subtitle.setWordWrap(True)
        root.addWidget(subtitle)

        # -------------------------------------------------
        # SYSTEM OVERVIEW CARD
        # -------------------------------------------------
        sys_card = Card("System Overview")
        sv = sys_card.body()

        row_top = QHBoxLayout()
        row_top.setSpacing(18)

        # CPU widget
        cpu_box = QWidget()
        cpu_layout = QVBoxLayout(cpu_box)
        cpu_layout.setContentsMargins(0, 0, 0, 0)
        cpu_layout.setSpacing(4)

        self.lbl_cpu = QLabel("CPU: -- %")
        self.lbl_cpu.setStyleSheet("color:#F8EFFF; font-size:11pt;")
        self.bar_cpu = QProgressBar()
        self._style_bar(self.bar_cpu)

        cpu_layout.addWidget(self.lbl_cpu)
        cpu_layout.addWidget(self.bar_cpu)

        # RAM widget
        ram_box = QWidget()
        ram_layout = QVBoxLayout(ram_box)
        ram_layout.setContentsMargins(0, 0, 0, 0)
        ram_layout.setSpacing(4)

        self.lbl_ram = QLabel("RAM: -- %")
        self.lbl_ram.setStyleSheet("color:#F8EFFF; font-size:11pt;")
        self.bar_ram = QProgressBar()
        self._style_bar(self.bar_ram)

        ram_layout.addWidget(self.lbl_ram)
        ram_layout.addWidget(self.bar_ram)

        # DISK widget
        disk_box = QWidget()
        disk_layout = QVBoxLayout(disk_box)
        disk_layout.setContentsMargins(0, 0, 0, 0)
        disk_layout.setSpacing(4)

        self.lbl_disk = QLabel("Disk C: -- % free")
        self.lbl_disk.setStyleSheet("color:#F8EFFF; font-size:11pt;")
        self.bar_disk = QProgressBar()
        self._style_bar(self.bar_disk)

        disk_layout.addWidget(self.lbl_disk)
        disk_layout.addWidget(self.bar_disk)

        row_top.addWidget(cpu_box)
        row_top.addWidget(ram_box)
        row_top.addWidget(disk_box)

        sv.addLayout(row_top)

        # Status line / note about psutil
        self.lbl_sys_note = QLabel("")
        self.lbl_sys_note.setStyleSheet("color:#9FA8C7; font-size:9pt;")
        self.lbl_sys_note.setWordWrap(True)
        sv.addWidget(self.lbl_sys_note)

        root.addWidget(sys_card)

        # -------------------------------------------------
        # GAME / SMART MODE OVERVIEW
        # -------------------------------------------------
        game_card = Card("Gaming & Smart Modes")
        gv = game_card.body()

        self.lbl_game_hint = QLabel(
            "Use the Game Optimizer tab to configure Smart Game Mode for Fortnite, "
            "Valorant, Minecraft, and more.\n\n"
            "When Smart Game Mode is enabled, QrsTweaks will:\n"
            "  • Detect when the selected game starts\n"
            "  • Apply safe CPU priority + core affinity presets\n"
            "  • For Fortnite: apply the Fortnite Gaming preset"
        )
        self.lbl_game_hint.setStyleSheet("color:#D3D8F5; font-size:9pt;")
        self.lbl_game_hint.setWordWrap(True)
        gv.addWidget(self.lbl_game_hint)

        root.addWidget(game_card)

        # -------------------------------------------------
        # QUICK ACTIONS
        # -------------------------------------------------
        qa_card = Card("Quick Actions")
        qv = qa_card.body()

        row_q1 = QHBoxLayout()
        row_q1.setSpacing(10)

        self.btn_quick_scan = QPushButton("Run Quick Scan (Windows)")
        self.btn_quick_scan.setMinimumHeight(32)

        self.btn_deep_cleanup = QPushButton("Run Deep Cleanup")
        self.btn_deep_cleanup.setMinimumHeight(32)

        self.btn_fortnite_preset = QPushButton("Apply Fortnite Gaming Preset")
        self.btn_fortnite_preset.setMinimumHeight(32)

        row_q1.addWidget(self.btn_quick_scan)
        row_q1.addWidget(self.btn_deep_cleanup)
        row_q1.addWidget(self.btn_fortnite_preset)

        qv.addLayout(row_q1)

        self.lbl_quick_info = QLabel(
            "Quick actions are safe, best-effort tweaks that operate like the Windows "
            "and Game optimizer pages but with minimal UI."
        )
        self.lbl_quick_info.setStyleSheet("color:#9FA8C7; font-size:9pt;")
        self.lbl_quick_info.setWordWrap(True)
        qv.addWidget(self.lbl_quick_info)

        self.dash_log = QTextEditLike()
        qv.addWidget(self.dash_log.as_widget())

        root.addWidget(qa_card)

        root.addStretch()

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.addWidget(scroll)

        # -------------------------------------------------
        # TIMERS & SIGNALS
        # -------------------------------------------------
        self._setup_signals()
        self._setup_timers()

    # -------------------------------------------------
    # Internal helpers
    # -------------------------------------------------
    def _setup_signals(self) -> None:
        self.btn_quick_scan.clicked.connect(self._do_quick_scan)
        self.btn_deep_cleanup.clicked.connect(self._do_deep_cleanup)
        self.btn_fortnite_preset.clicked.connect(self._do_fortnite_preset)

    def _setup_timers(self) -> None:
        self._metric_timer = QTimer(self)
        self._metric_timer.setInterval(1000)
        self._metric_timer.timeout.connect(self._refresh_metrics)
        self._metric_timer.start()
        self._refresh_metrics()

    def _style_bar(self, bar: QProgressBar) -> None:
        bar.setTextVisible(False)
        bar.setRange(0, 100)
        bar.setStyleSheet(
            """
            QProgressBar {
                border-radius: 6px;
                background-color: #1A1224;
                height: 10px;
            }
            QProgressBar::Chunk {
                border-radius: 6px;
                background-color: qlineargradient(
                    x1:0, y1:0, x2:1, y2:0,
                    stop:0 #F472FF, stop:1 #7C3AED
                );
            }
            """
        )

    # -------------------------------------------------
    # Metrics
    # -------------------------------------------------
    def _refresh_metrics(self) -> None:
        if psutil is None:
            self.lbl_cpu.setText("CPU: psutil not installed")
            self.lbl_ram.setText("RAM: psutil not installed")
            self.lbl_disk.setText("Disk C: psutil not installed")
            self.bar_cpu.setValue(0)
            self.bar_ram.setValue(0)
            self.bar_disk.setValue(0)
            self.lbl_sys_note.setText(
                "Install psutil with 'pip install psutil' to enable live metrics."
            )
            return

        try:
            cpu = psutil.cpu_percent(interval=None)  # type: ignore[attr-defined]
            mem = psutil.virtual_memory()            # type: ignore[attr-defined]

            try:
                disk = psutil.disk_usage("C:\\")     # type: ignore[attr-defined]
                disk_free_pct = (disk.free / disk.total) * 100.0
            except Exception:
                disk_free_pct = -1.0

            self.lbl_cpu.setText(f"CPU: {cpu:.0f} %")
            self.bar_cpu.setValue(int(cpu))

            self.lbl_ram.setText(f"RAM: {mem.percent:.0f} %")
            self.bar_ram.setValue(int(mem.percent))

            if disk_free_pct >= 0:
                used_pct = 100.0 - disk_free_pct
                self.lbl_disk.setText(f"Disk C: {disk_free_pct:.0f} % free")
                self.bar_disk.setValue(int(used_pct))
            else:
                self.lbl_disk.setText("Disk C: unknown")
                self.bar_disk.setValue(0)

            self.lbl_sys_note.setText(
                "Metrics update every second. High CPU/RAM under heavy loads is normal."
            )
        except Exception as e:
            self.lbl_sys_note.setText(f"Error gathering metrics: {e!r}")

    # -------------------------------------------------
    # Quick actions
    # -------------------------------------------------
    def _do_quick_scan(self) -> None:
        try:
            text = self.win_opt.quick_scan()
            self.dash_log.append("[Windows] Quick Scan:\n" + text)
            log_mgr.log("Dashboard", "Quick Scan invoked from Dashboard.", level="info")
        except Exception as e:
            self.dash_log.append(f"[Windows] Quick Scan failed: {e!r}")
            log_mgr.log("Dashboard", f"Quick Scan failed: {e!r}", level="error", bubble=True)

    def _do_deep_cleanup(self) -> None:
        try:
            n = self.win_opt.deep_cleanup()
            msg = f"[Windows] Deep Cleanup removed ~{n} items."
            self.dash_log.append(msg)
            log_mgr.log("Dashboard", f"Deep Cleanup removed ~{n} items (from Dashboard).", level="ok")
        except Exception as e:
            self.dash_log.append(f"[Windows] Deep Cleanup failed: {e!r}")
            log_mgr.log("Dashboard", f"Deep Cleanup failed: {e!r}", level="error", bubble=True)

    def _do_fortnite_preset(self) -> None:
        try:
            ok, msg = self.game_opt.apply_fortnite_gaming_preset()
            prefix = "[Game] Fortnite Gaming preset"
            if ok:
                self.dash_log.append(prefix + " applied successfully:\n" + msg)
            else:
                self.dash_log.append(prefix + " had warnings:\n" + msg)
            log_mgr.log("Dashboard", "Fortnite Gaming preset applied from Dashboard.", level="ok" if ok else "warn", bubble=ok)
        except Exception as e:
            self.dash_log.append(f"[Game] Fortnite preset failed: {e!r}")
            log_mgr.log("Dashboard", f"Fortnite preset failed from Dashboard: {e!r}", level="error", bubble=True)


class QTextEditLike:
    """
    Tiny helper wrapper for a QTextEdit-like log area.
    """
    from PySide6.QtWidgets import QTextEdit

    def __init__(self):
        self._w = self.QTextEdit()
        self._w.setReadOnly(True)
        self._w.setMinimumHeight(140)
        self._w.setStyleSheet(
            """
            QTextEdit {
                background-color: #0A0710;
                color: #E9E4FF;
                border-radius: 8px;
                border: 1px solid #2A1744;
                font-size: 9pt;
            }
            """
        )

    def as_widget(self):
        return self._w

    def append(self, text: str) -> None:
        safe = (
            text.replace("&", "&amp;")
                .replace("<", "&lt;")
                .replace(">", "&gt;")
        )
        self._w.append(f"<span style='color:#E9E4FF'>{safe}</span>")
