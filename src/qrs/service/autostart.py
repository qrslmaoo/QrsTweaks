# src/qrs/service/autostart.py
from __future__ import annotations

import platform
import sys
from pathlib import Path
from typing import Tuple

try:
    import winreg  # type: ignore
except ImportError:  # pragma: no cover - non-Windows
    winreg = None


class AutostartManager:
    """
    Control a HKCU\\...\\Run entry that launches the QrsTweaks daemon
    when the user logs in.

    Value name:  "QrsTweaksDaemon"
    """

    RUN_KEY = r"Software\Microsoft\Windows\CurrentVersion\Run"
    VALUE_NAME = "QrsTweaksDaemon"

    def __init__(self) -> None:
        self._is_windows = platform.system() == "Windows"

    # ---------------------------------------------------------
    # Internal helpers
    # ---------------------------------------------------------
    def _daemon_command(self) -> str:
        """
        Build the command that should be stored in the Run key.

        This uses the absolute path to daemon_main.py plus the current
        Python interpreter.
        """
        here = Path(__file__).resolve()
        daemon_script = here.parent / "daemon_main.py"
        # Example: "C:\Python311\python.exe" -u "C:\...\daemon_main.py"
        return f'"{sys.executable}" -u "{daemon_script}"'

    # ---------------------------------------------------------
    # Public API
    # ---------------------------------------------------------
    def is_enabled(self) -> bool:
        """
        Check if the autostart entry is present.
        """
        if not self._is_windows or winreg is None:
            return False

        try:
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, self.RUN_KEY) as key:  # type: ignore[arg-type]
                val, _ = winreg.QueryValueEx(key, self.VALUE_NAME)  # type: ignore[arg-type]
                return bool(val)
        except FileNotFoundError:
            return False
        except OSError:
            return False

    def set_enabled(self, enabled: bool) -> Tuple[bool, str]:
        """
        Create or remove the Run entry.
        """
        if not self._is_windows or winreg is None:
            return False, "Autostart is only available on Windows."

        if enabled:
            cmd = self._daemon_command()
            try:
                key = winreg.CreateKey(winreg.HKEY_CURRENT_USER, self.RUN_KEY)  # type: ignore[arg-type]
                winreg.SetValueEx(key, self.VALUE_NAME, 0, winreg.REG_SZ, cmd)  # type: ignore[arg-type]
                winreg.CloseKey(key)
                return True, f"Autostart enabled with command: {cmd}"
            except OSError as e:
                return False, f"Failed to enable autostart: {e}"
        else:
            try:
                with winreg.OpenKey(
                    winreg.HKEY_CURRENT_USER, self.RUN_KEY, 0, winreg.KEY_SET_VALUE  # type: ignore[arg-type]
                ) as key:
                    winreg.DeleteValue(key, self.VALUE_NAME)  # type: ignore[arg-type]
                return True, "Autostart disabled."
            except FileNotFoundError:
                return True, "Autostart entry was not present."
            except OSError as e:
                return False, f"Failed to disable autostart: {e}"
