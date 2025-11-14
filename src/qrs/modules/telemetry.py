from __future__ import annotations

"""
src/qrs/modules/telemetry.py

Lightweight system telemetry backend for QrsTweaks.

Provides a single class:

    Telemetry().snapshot() -> dict

The snapshot is designed to be safe:
    - Uses psutil when available
    - Falls back gracefully when not
    - Never raises out of the page
"""

import time
import platform
from typing import Any, Dict, List, Optional

try:
    import psutil  # type: ignore
except ImportError:  # pragma: no cover - optional dependency
    psutil = None

# GPUtil is optional; we treat it as "best effort"
try:
    import GPUtil  # type: ignore
except ImportError:  # pragma: no cover
    GPUtil = None  # type: ignore


class Telemetry:
    """
    Collects lightweight system stats for the dashboard.

    snapshot() returns a dict with keys like:

        {
          "supported": True/False,
          "timestamp": float,
          "cpu_total": float,
          "cpu_per_core": List[float],
          "ram_used": int,
          "ram_total": int,
          "ram_percent": float,
          "swap_used": int,
          "swap_total": int,
          "swap_percent": float,
          "process_count": int,
          "boot_time": float,
          "uptime_sec": float,
          "gpu_usage": Optional[float],
          "gpu_mem_used": Optional[float],
          "gpu_mem_total": Optional[float],
          "gpu_temp": Optional[float],
        }
    """

    def __init__(self) -> None:
        self._is_windows = platform.system().lower().startswith("win")
        self._psutil_ok = psutil is not None
        self._supported = self._is_windows and self._psutil_ok

    @property
    def supported(self) -> bool:
        return self._supported

    def snapshot(self) -> Dict[str, Any]:
        """
        Take a single telemetry snapshot.

        Returns:
            dict of metrics; when unsupported, contains only:
                { "supported": False, "timestamp": ... }
        """
        now = time.time()
        data: Dict[str, Any] = {
            "supported": self._supported,
            "timestamp": now,
        }

        if not self._supported:
            # Minimal payload so the UI can show a nice message
            return data

        assert psutil is not None  # for type checker

        # -------------------------------
        # CPU
        # -------------------------------
        try:
            # One call, per-core; we derive total from the average.
            per_core: List[float] = psutil.cpu_percent(interval=None, percpu=True)  # type: ignore[attr-defined]
        except Exception:
            per_core = []

        if per_core:
            cpu_total = sum(per_core) / len(per_core)
        else:
            # Fallback single value
            try:
                cpu_total = float(psutil.cpu_percent(interval=None))  # type: ignore[attr-defined]
            except Exception:
                cpu_total = 0.0

        data["cpu_total"] = cpu_total
        data["cpu_per_core"] = per_core

        # -------------------------------
        # RAM / SWAP
        # -------------------------------
        try:
            vm = psutil.virtual_memory()  # type: ignore[attr-defined]
            sm = psutil.swap_memory()     # type: ignore[attr-defined]

            data["ram_used"] = int(vm.used)
            data["ram_total"] = int(vm.total)
            data["ram_percent"] = float(vm.percent)

            data["swap_used"] = int(sm.used)
            data["swap_total"] = int(sm.total)
            data["swap_percent"] = float(sm.percent)
        except Exception:
            data.setdefault("ram_used", 0)
            data.setdefault("ram_total", 0)
            data.setdefault("ram_percent", 0.0)
            data.setdefault("swap_used", 0)
            data.setdefault("swap_total", 0)
            data.setdefault("swap_percent", 0.0)

        # -------------------------------
        # System / uptime
        # -------------------------------
        try:
            boot_time = float(psutil.boot_time())  # type: ignore[attr-defined]
        except Exception:
            boot_time = now

        data["boot_time"] = boot_time
        data["uptime_sec"] = max(0.0, now - boot_time)

        try:
            proc_count = len(psutil.pids())  # type: ignore[attr-defined]
        except Exception:
            proc_count = 0
        data["process_count"] = proc_count

        # -------------------------------
        # GPU (best effort)
        # -------------------------------
        gpu_usage: Optional[float] = None
        gpu_temp: Optional[float] = None
        gpu_mem_used: Optional[float] = None
        gpu_mem_total: Optional[float] = None

        if GPUtil is not None:
            try:
                gpus = GPUtil.getGPUs()  # type: ignore[attr-defined]
                if gpus:
                    g = gups[0]  # type: ignore[name-defined]
            except Exception:
                g = None

            try:
                gpus = GPUtil.getGPUs()  # type: ignore[attr-defined]
                if gpus:
                    g = gpus[0]
                    gpu_usage = float(g.load * 100.0)
                    gpu_temp = float(getattr(g, "temperature", 0.0))
                    gpu_mem_used = float(getattr(g, "memoryUsed", 0.0))
                    gpu_mem_total = float(getattr(g, "memoryTotal", 0.0))
            except Exception:
                # Totally optional, so we just keep None
                pass

        data["gpu_usage"] = gpu_usage
        data["gpu_temp"] = gpu_temp
        data["gpu_mem_used"] = gpu_mem_used
        data["gpu_mem_total"] = gpu_mem_total

        return data
