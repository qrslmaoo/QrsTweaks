# app/pages/dashboard_page.py

from __future__ import annotations

from typing import List

from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QScrollArea,
    QProgressBar,
    QGridLayout,
)
from PySide6.QtCore import Qt, QTimer

from app.ui.widgets.card import Card
from src.qrs.modules.telemetry import Telemetry


def _format_gib(bytes_value: int) -> str:
    if bytes_value <= 0:
        return "0.0 GiB"
    return f"{bytes_value / (1024 ** 3):.1f} GiB"


def _format_uptime(seconds: float) -> str:
    seconds = max(0.0, float(seconds))
    days = int(seconds // 86400)
    seconds %= 86400
    hours = int(seconds // 3600)
    seconds %= 3600
    minutes = int(seconds // 60)

    parts = []
    if days:
        parts.append(f"{days}d")
    if hours or days:
        parts.append(f"{hours}h")
    parts.append(f"{minutes}m")
    return " ".join(parts)


class DashboardPage(QWidget):
    """
    Live telemetry dashboard with bar-flow styling.

    Sections:
      - CPU usage (total + per-core bars)
      - Memory usage
      - System summary (uptime, processes)
      - GPU (best effort, optional)
    """

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setStyleSheet("background: transparent;")

        self.telemetry = Telemetry()
        initial = self.telemetry.snapshot()
        self._initial_cpu_cores = len(initial.get("cpu_per_core") or [])

        if self._initial_cpu_cores <= 0:
            # Reasonable default – will be resized once real data arrives
            self._initial_cpu_cores = 4

        self._core_bars: List[QProgressBar] = []

        # -------------------------------------------------
        # Scroll wrapper (match WindowsPage / GamesPage)
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
        title = QLabel("System Dashboard")
        title.setStyleSheet("font-size: 22pt; color: #DDE1EA; font-weight: 700;")
        root.addWidget(title)

        # -------------------------------------------------
        # CPU CARD
        # -------------------------------------------------
        cpu_card = Card("CPU Usage")
        cpu_body = cpu_card.body()

        self.lbl_cpu_total = QLabel("CPU: -- %")
        self.lbl_cpu_total.setStyleSheet("font-size: 16pt; color: #F2F5FF;")
        cpu_body.addWidget(self.lbl_cpu_total)

        self.lbl_cpu_meta = QLabel("Cores: -- | Processes: --")
        self.lbl_cpu_meta.setStyleSheet("color:#AAB0BC; font-size: 9pt;")
        cpu_body.addWidget(self.lbl_cpu_meta)

        grid = QGridLayout()
        grid.setSpacing(6)

        for i in range(self._initial_cpu_cores):
            bar = QProgressBar()
            bar.setRange(0, 100)
            bar.setValue(0)
            bar.setFormat(f"Core {i}  %p%")
            bar.setAlignment(Qt.AlignCenter)
            bar.setStyleSheet(
                """
                QProgressBar {
                    border: 1px solid #2b2f3b;
                    border-radius: 4px;
                    background: #151821;
                    color: #DDE1EA;
                    text-align: center;
                    padding: 1px;
                    min-height: 18px;
                }
                QProgressBar::chunk {
                    border-radius: 4px;
                    background: qlineargradient(
                        x1:0, y1:0, x2:1, y2:0,
                        stop:0 #5f4bff,
                        stop:1 #ff3cac
                    );
                }
                """
            )
            self._core_bars.append(bar)
            row = i // 2
            col = i % 2
            grid.addWidget(bar, row, col)

        cpu_body.addLayout(grid)
        root.addWidget(cpu_card)

        # -------------------------------------------------
        # MEMORY CARD
        # -------------------------------------------------
        mem_card = Card("Memory")
        mem_body = mem_card.body()

        row_mem = QHBoxLayout()
        row_mem.setSpacing(12)

        self.lbl_ram_summary = QLabel("RAM: -- / -- (--)")
        self.lbl_ram_summary.setStyleSheet("color:#DDE1EA; font-size: 10pt;")

        row_mem.addWidget(self.lbl_ram_summary)
        row_mem.addStretch()

        mem_body.addLayout(row_mem)

        self.bar_ram = QProgressBar()
        self.bar_ram.setRange(0, 100)
        self.bar_ram.setValue(0)
        self.bar_ram.setFormat("%p%")
        self.bar_ram.setAlignment(Qt.AlignCenter)
        self.bar_ram.setStyleSheet(
            """
            QProgressBar {
                border: 1px solid #2b2f3b;
                border-radius: 4px;
                background: #151821;
                color: #DDE1EA;
                text-align: center;
                padding: 1px;
                min-height: 20px;
            }
            QProgressBar::chunk {
                border-radius: 4px;
                background: qlineargradient(
                    x1:0, y1:0, x2:1, y2:0,
                    stop:0 #21d4fd,
                    stop:1 #b721ff
                );
            }
            """
        )
        mem_body.addWidget(self.bar_ram)

        root.addWidget(mem_card)

        # -------------------------------------------------
        # GPU + SYSTEM (ROW)
        # -------------------------------------------------
        row_bottom = QHBoxLayout()
        row_bottom.setSpacing(12)

        # GPU card
        gpu_card = Card("GPU (best effort)")
        gpu_body = gpu_card.body()

        self.lbl_gpu_usage = QLabel("GPU: -- %")
        self.lbl_gpu_usage.setStyleSheet("color:#DDE1EA; font-size: 10pt;")
        self.lbl_gpu_mem = QLabel("VRAM: -- / --")
        self.lbl_gpu_mem.setStyleSheet("color:#AAB0BC; font-size: 9pt;")
        self.lbl_gpu_temp = QLabel("Temp: -- °C")
        self.lbl_gpu_temp.setStyleSheet("color:#AAB0BC; font-size: 9pt;")

        gpu_body.addWidget(self.lbl_gpu_usage)
        gpu_body.addWidget(self.lbl_gpu_mem)
        gpu_body.addWidget(self.lbl_gpu_temp)

        row_bottom.addWidget(gpu_card)

        # System card
        sys_card = Card("System")
        sys_body = sys_card.body()

        self.lbl_uptime = QLabel("Uptime: --")
        self.lbl_uptime.setStyleSheet("color:#DDE1EA; font-size: 10pt;")
        self.lbl_proc_count = QLabel("Processes: --")
        self.lbl_proc_count.setStyleSheet("color:#AAB0BC; font-size: 9pt;")

        sys_body.addWidget(self.lbl_uptime)
        sys_body.addWidget(self.lbl_proc_count)

        row_bottom.addWidget(sys_card)

        root.addLayout(row_bottom)

        # Stretch so content hugs top
        root.addStretch()

        # Attach scroll to self
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.addWidget(scroll)

        # Timer for updates (bar-flow style)
        self._timer = QTimer(self)
        self._timer.setInterval(500)  # 500ms
        self._timer.timeout.connect(self._update_telemetry)
        self._timer.start()

        # One immediate refresh
        self._update_telemetry()

    # -------------------------------------------------
    # UPDATE LOOP
    # -------------------------------------------------
    def _update_telemetry(self) -> None:
        data = self.telemetry.snapshot()

        if not data.get("supported", False):
            self.lbl_cpu_total.setText("CPU: telemetry not available")
            self.lbl_cpu_meta.setText("psutil missing or unsupported platform.")
            self.lbl_ram_summary.setText("RAM: telemetry not available")
            self.bar_ram.setValue(0)
            self.lbl_uptime.setText("Uptime: --")
            self.lbl_proc_count.setText("Processes: --")
            self.lbl_gpu_usage.setText("GPU: -- (optional)")
            self.lbl_gpu_mem.setText("VRAM: -- / --")
            self.lbl_gpu_temp.setText("Temp: -- °C")
            return

        # CPU
        cpu_total = float(data.get("cpu_total", 0.0))
        per_core = list(data.get("cpu_per_core") or [])
        proc_count = int(data.get("process_count", 0))

        self.lbl_cpu_total.setText(f"CPU: {cpu_total:.1f} %")

        core_count = len(per_core)
        if core_count and core_count != len(self._core_bars):
            # Rebuild the bars once if the real core count differs
            self._rebuild_cpu_bars(core_count)
            # fall through to use updated list

        for i, bar in enumerate(self._core_bars):
            value = int(per_core[i]) if i < len(per_core) else 0
            bar.setValue(max(0, min(100, value)))

        self.lbl_cpu_meta.setText(
            f"Cores: {core_count or '--'} | Processes: {proc_count or '--'}"
        )

        # RAM
        ram_used = int(data.get("ram_used", 0))
        ram_total = int(data.get("ram_total", 0))
        ram_percent = float(data.get("ram_percent", 0.0))

        self.bar_ram.setValue(int(ram_percent))
        self.lbl_ram_summary.setText(
            f"RAM: {_format_gib(ram_used)} / {_format_gib(ram_total)} ({ram_percent:.1f}%)"
        )

        # System
        uptime = float(data.get("uptime_sec", 0.0))
        self.lbl_uptime.setText(f"Uptime: {_format_uptime(uptime)}")
        self.lbl_proc_count.setText(f"Processes: {proc_count}")

        # GPU
        gpu_usage = data.get("gpu_usage")
        gpu_temp = data.get("gpu_temp")
        gpu_mem_used = data.get("gpu_mem_used")
        gpu_mem_total = data.get("gpu_mem_total")

        if gpu_usage is None:
            self.lbl_gpu_usage.setText("GPU: n/a (GPUtil not installed)")
        else:
            self.lbl_gpu_usage.setText(f"GPU: {gpu_usage:.1f} %")

        if gpu_mem_used is None or gpu_mem_total is None or gpu_mem_total == 0:
            self.lbl_gpu_mem.setText("VRAM: -- / --")
        else:
            self.lbl_gpu_mem.setText(
                f"VRAM: {gpu_mem_used:.1f} / {gpu_mem_total:.1f} GiB"
            )

        if gpu_temp is None or gpu_temp <= 0:
            self.lbl_gpu_temp.setText("Temp: -- °C")
        else:
            self.lbl_gpu_temp.setText(f"Temp: {gpu_temp:.0f} °C")

    # -------------------------------------------------
    # INTERNAL: rebuild CPU bars if core-count changes
    # -------------------------------------------------
    def _rebuild_cpu_bars(self, core_count: int) -> None:
        # Find the grid layout inside the CPU card body
        # (we know the structure: title, meta, grid)
        scroll = self.findChild(QScrollArea)
        if not scroll:
            return
        container = scroll.widget()
        if not container:
            return
        root: QVBoxLayout = container.layout()  # type: ignore[assignment]
        if root is None:
            return

        # CPU card is the second widget (title, then CPU card)
        # but safer to search by type Card
        cpu_card = container.findChild(Card, None)
        if cpu_card is None:
            return

        cpu_body_layout = cpu_card.body()
        # Layout children: [lbl_cpu_total, lbl_cpu_meta, grid]
        # We replace the last item (grid) with a new grid.
        if cpu_body_layout.count() < 3:
            return

        old_item = cpu_body_layout.itemAt(2)
        old_layout = old_item.layout() if old_item is not None else None
        if old_layout is not None:
            # Remove old layout and its widgets
            while old_layout.count():
                it = old_layout.takeAt(0)
                w = it.widget()
                if w is not None:
                    w.deleteLater()
            cpu_body_layout.removeItem(old_layout)

        new_grid = QGridLayout()
        new_grid.setSpacing(6)

        self._core_bars.clear()
        for i in range(core_count):
            bar = QProgressBar()
            bar.setRange(0, 100)
            bar.setValue(0)
            bar.setFormat(f"Core {i}  %p%")
            bar.setAlignment(Qt.AlignCenter)
            bar.setStyleSheet(
                """
                QProgressBar {
                    border: 1px solid #2b2f3b;
                    border-radius: 4px;
                    background: #151821;
                    color: #DDE1EA;
                    text-align: center;
                    padding: 1px;
                    min-height: 18px;
                }
                QProgressBar::chunk {
                    border-radius: 4px;
                    background: qlineargradient(
                        x1:0, y1:0, x2:1, y2:0,
                        stop:0 #5f4bff,
                        stop:1 #ff3cac
                    );
                }
                """
            )
            self._core_bars.append(bar)
            row = i // 2
            col = i % 2
            new_grid.addWidget(bar, row, col)

        cpu_body_layout.addLayout(new_grid)
