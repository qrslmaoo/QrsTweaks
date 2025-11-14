# src/qrs/modules/telemetry_live.py

from __future__ import annotations
import psutil
import time
import json
from pathlib import Path

try:
    import wmi
except:
    wmi = None


LOG_DIR = Path("Logs")
LOG_DIR.mkdir(exist_ok=True, parents=True)
TELE_FILE = LOG_DIR / "telemetry.jsonl"


class TelemetryLive:
    """
    Lightweight performance sampler used by the daemon.
    Produces CPU/GPU/RAM usage snapshots once per interval.
    """

    def __init__(self):
        self.wmi_gpu = None
        if wmi is not None:
            try:
                self.wmi_gpu = wmi.WMI(namespace="root\\CIMV2")
            except:
                self.wmi_gpu = None

    def _gpu_usage(self) -> float | None:
        """Returns total GPU load (%) using WMI (NVIDIA/AMD)."""
        if self.wmi_gpu is None:
            return None
        try:
            g = self.wmi_gpu.Win32_PerfFormattedData_GPUPerformanceCounters_GPUEngine()
            loads = []
            for x in g:
                if "engtype_3D" in x.Name:
                    loads.append(float(x.UtilizationPercentage))
            return sum(loads) if loads else None
        except:
            return None

    def sample(self) -> dict:
        """Collect a single performance snapshot."""
        return {
            "ts": time.time(),
            "cpu": psutil.cpu_percent(interval=None),
            "ram": psutil.virtual_memory().percent,
            "gpu": self._gpu_usage(),
        }

    def write_snapshot(self, snap: dict):
        TELE_FILE.write_text(
            TELE_FILE.read_text() + json.dumps(snap) + "\n"
            if TELE_FILE.exists()
            else json.dumps(sap) + "\n"
        )
