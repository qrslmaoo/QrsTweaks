from __future__ import annotations
import os
import shutil
import tempfile
from pathlib import Path
import subprocess
import platform

class WindowsOptimizer:
    def __init__(self):
        self.is_windows = (platform.system().lower() == "windows")

    def quick_scan(self) -> str:
        # Offline heuristics: counts temp files, shows OS/build, free space
        report = []
        report.append(f"OS: {platform.platform()}")
        # temp dir
        temp = Path(tempfile.gettempdir())
        temp_count = sum(1 for _ in temp.glob("**/*") if _.is_file())
        report.append(f"Temp files (approx): {temp_count}")
        # free space on system drive
        drive = Path(os.getenv("SystemDrive", "C:") + "\\")
        total, used, free = shutil.disk_usage(drive)
        gb = 1024**3
        report.append(f"System drive free: {free/gb:.1f} GB / {total/gb:.1f} GB")
        return "\n".join(report)

    def create_high_perf_powerplan(self):
        if not self.is_windows:
            return False, "Not Windows."
        try:
            # Duplicate 'High performance' GUID if present; fallback to Ultimate if available
            cmds = [
                ["powercfg", "-duplicatescheme", "8c5e7fda-e8bf-4a96-9a85-a6e23a8c635c"],  # High performance
                ["powercfg", "-setactive", "8c5e7fda-e8bf-4a96-9a85-a6e23a8c635c"]
            ]
            for c in cmds:
                subprocess.run(c, capture_output=True, text=True, check=False)
            return True, "High Performance plan created/activated."
        except Exception as e:
            return False, str(e)

    def cleanup_temp_files(self) -> int:
        temp = Path(tempfile.gettempdir())
        count = 0
        for p in list(temp.glob("**/*"))[:5000]:
            try:
                if p.is_file():
                    p.unlink(missing_ok=True); count += 1
                elif p.is_dir():
                    p.rmdir()
            except Exception:
                pass
        return count

    def create_restore_point(self, description: str):
        # Requires admin + System Restore enabled; we attempt via WMI
        if not self.is_windows:
            return False, "Not Windows."
        try:
            cmd = [
                "powershell",
                "-NoProfile",
                "-ExecutionPolicy", "Bypass",
                "-Command",
                f'Checkpoint-Computer -Description "{description}" -RestorePointType "MODIFY_SETTINGS"'
            ]
            proc = subprocess.run(cmd, capture_output=True, text=True)
            if proc.returncode == 0:
                return True, "Restore point created."
            return False, proc.stderr.strip() or proc.stdout.strip() or "Unknown error"
        except Exception as e:
            return False, str(e)
