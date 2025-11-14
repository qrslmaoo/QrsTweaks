# src/qrs/service/controller.py
from __future__ import annotations

import os
import signal
import subprocess
import sys
from pathlib import Path
from typing import Tuple


class ServiceController:
    """
    Thin wrapper for the QrsTweaks background daemon.

    Responsibilities:
      - Start the daemon as a detached process
      - Stop it using a SIGTERM / kill
      - Check if it's still running
      - Maintain a .runtime/daemon.pid file
    """

    def __init__(self) -> None:
        here = Path(__file__).resolve()
        # .../QrsTweaks/src/qrs/service/controller.py
        # parents[0] = service, [1] = qrs, [2] = src, [3] = QrsTweaks
        self.root = here.parents[3]

        self.runtime_dir = self.root / ".runtime"
        self.runtime_dir.mkdir(parents=True, exist_ok=True)

        self.pid_file = self.runtime_dir / "daemon.pid"
        self.daemon_script = (
            self.root / "src" / "qrs" / "service" / "daemon_main.py"
        )

        self.logs_dir = self.root / "logs"
        self.logs_dir.mkdir(parents=True, exist_ok=True)
        self.log_file = self.logs_dir / "daemon.log"

    # ---------------------------------------------------------
    # Internal helpers
    # ---------------------------------------------------------
    def _read_pid(self) -> int | None:
        if not self.pid_file.exists():
            return None
        try:
            data = self.pid_file.read_text(encoding="utf-8").strip()
            return int(data)
        except Exception:
            return None

    def _write_pid(self, pid: int) -> None:
        try:
            self.pid_file.write_text(str(pid), encoding="utf-8")
        except Exception:
            # Not fatal, but means we can't track status properly
            pass

    def _clear_pid(self) -> None:
        try:
            if self.pid_file.exists():
                self.pid_file.unlink()
        except Exception:
            pass

    # ---------------------------------------------------------
    # Public API used by the UI
    # ---------------------------------------------------------
    def is_daemon_running(self) -> Tuple[bool, str]:
        """
        Check if the daemon described in daemon.pid is alive.
        """
        pid = self._read_pid()
        if pid is None:
            return False, "No PID file present; daemon not started yet."

        try:
            # signal 0 just checks if the process exists
            os.kill(pid, 0)
        except OSError as e:
            return False, f"Process {pid} does not appear to be running: {e}"
        else:
            return True, f"Daemon process {pid} is running."

    def start_daemon(self) -> Tuple[bool, str]:
        """
        Start the daemon if not already running.
        """
        if not self.daemon_script.exists():
            return False, f"Daemon script not found at {self.daemon_script}"

        already, detail = self.is_daemon_running()
        if already:
            return True, f"Daemon already running. {detail}"

        try:
            # Append logs, don't overwrite
            log_f = self.log_file.open("a", encoding="utf-8")

            # Detach reasonably; keep it simple and cross-platform
            proc = subprocess.Popen(
                [sys.executable, "-u", str(self.daemon_script)],
                stdout=log_f,
                stderr=log_f,
                cwd=str(self.root),
                close_fds=True,
            )
            self._write_pid(proc.pid)
            return True, f"Started daemon (PID {proc.pid}). Logs: {self.log_file}"
        except Exception as e:
            return False, f"Failed to start daemon: {e!r}"

    def stop_daemon(self) -> Tuple[bool, str]:
        """
        Try to terminate the daemon process using the stored PID.
        """
        pid = self._read_pid()
        if pid is None:
            return False, "No daemon PID file found; nothing to stop."

        try:
            os.kill(pid, signal.SIGTERM)
        except ProcessLookupError:
            self._clear_pid()
            return False, f"Process {pid} was not running."
        except Exception as e:
            return False, f"Failed to send terminate signal to {pid}: {e!r}"

        # Best-effort cleanup
        self._clear_pid()
        return True, f"Stop signal sent to daemon (PID {pid})."

    def restart_daemon(self) -> Tuple[bool, str]:
        """
        Convenience: stop then start.
        """
        _, _ = self.stop_daemon()
        ok, msg = self.start_daemon()
        if ok:
            return True, f"Daemon restarted successfully. {msg}"
        return False, f"Daemon restart failed. {msg}"
