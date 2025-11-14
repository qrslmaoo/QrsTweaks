# src/qrs/service/controller.py
from __future__ import annotations

import os
import signal
import subprocess
import sys
import time
from pathlib import Path
from typing import Tuple

try:
    import psutil  # type: ignore
except ImportError:  # pragma: no cover - optional
    psutil = None


class ServiceController:
    """
    Thin wrapper for the QrsTweaks background daemon.

    Responsibilities:
      - Start the daemon as a detached process
      - Stop it cleanly (terminate + wait, then hard kill if needed)
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

        # Keep log path consistent with repo layout (capital L)
        self.logs_dir = self.root / "Logs"
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

    def _process_exists(self, pid: int) -> bool:
        """
        Check if process exists and is alive.
        """
        if pid <= 0:
            return False

        if psutil is not None:
            try:
                p = psutil.Process(pid)  # type: ignore[attr-defined]
                return p.is_running()
            except psutil.NoSuchProcess:  # type: ignore[attr-defined]
                return False
            except Exception:
                return False

        # Fallback: signal 0
        try:
            os.kill(pid, 0)
            return True
        except OSError:
            return False

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

        if not self._process_exists(pid):
            self._clear_pid()
            return False, f"Process {pid} does not appear to be running."

        detail = f"Daemon process {pid} is running."
        if psutil is not None:
            try:
                p = psutil.Process(pid)  # type: ignore[attr-defined]
                detail = f"Daemon process {pid} is running (name={p.name()})."
            except Exception:
                pass

        return True, detail

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

            creationflags = 0
            # On Windows, detach a bit more cleanly
            if os.name == "nt":
                creationflags = (
                    subprocess.CREATE_NEW_PROCESS_GROUP  # type: ignore[attr-defined]
                    | subprocess.DETACHED_PROCESS       # type: ignore[attr-defined]
                )

            proc = subprocess.Popen(
                [sys.executable, "-u", str(self.daemon_script)],
                stdout=log_f,
                stderr=log_f,
                cwd=str(self.root),
                close_fds=True,
                creationflags=creationflags,
            )

            self._write_pid(proc.pid)
            return True, f"Started daemon (PID {proc.pid}). Logs: {self.log_file}"
        except Exception as e:
            return False, f"Failed to start daemon: {e!r}"

    def stop_daemon(self, timeout: float = 10.0) -> Tuple[bool, str]:
        """
        Try to terminate the daemon process using the stored PID.

        Strategy:
          - If psutil is available:
              terminate() → wait up to `timeout` → kill() fallback
          - Else:
              os.kill(SIGTERM) / taskkill on Windows, poll until gone
        """
        pid = self._read_pid()
        if pid is None:
            return False, "No daemon PID file found; nothing to stop."

        if not self._process_exists(pid):
            self._clear_pid()
            return False, f"Process {pid} is not running."

        # psutil path (preferred)
        if psutil is not None:
            try:
                proc = psutil.Process(pid)  # type: ignore[attr-defined]
            except psutil.NoSuchProcess:  # type: ignore[attr-defined]
                self._clear_pid()
                return False, f"Process {pid} is not running."

            try:
                proc.terminate()
            except Exception as e:
                return False, f"Failed to send terminate signal to {pid}: {e!r}"

            # wait for graceful exit
            try:
                proc.wait(timeout=timeout)  # type: ignore[attr-defined]
            except Exception:
                # Fallback – hard kill
                if os.name == "nt":
                    try:
                        subprocess.run(
                            ["taskkill", "/PID", str(pid), "/T", "/F"],
                            stdout=subprocess.DEVNULL,
                            stderr=subprocess.DEVNULL,
                            check=False,
                        )
                    except Exception:
                        pass
                else:
                    try:
                        os.kill(pid, signal.SIGKILL)
                    except Exception:
                        pass

                # small grace period
                time.sleep(1.0)

            # Final check
            if self._process_exists(pid):
                return False, "Daemon did not exit within timeout."
            else:
                self._clear_pid()
                return True, f"Daemon (PID {pid}) stopped."

        # No psutil: fallback behaviour
        try:
            if os.name == "nt":
                subprocess.run(
                    ["taskkill", "/PID", str(pid), "/T", "/F"],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    check=False,
                )
            else:
                os.kill(pid, signal.SIGTERM)
        except Exception as e:
            return False, f"Failed to send terminate signal to {pid}: {e!r}"

        # Poll for exit
        end = time.time() + timeout
        while time.time() < end:
            if not self._process_exists(pid):
                self._clear_pid()
                return True, f"Daemon (PID {pid}) stopped."
            time.sleep(0.5)

        if not self._process_exists(pid):
            self._clear_pid()
            return True, f"Daemon (PID {pid}) stopped."

        return False, "Daemon did not exit within timeout."

    def restart_daemon(self) -> Tuple[bool, str]:
        """
        Convenience: stop then start.
        """
        _, _ = self.stop_daemon()
        ok, msg = self.start_daemon()
        if ok:
            return True, f"Daemon restarted successfully. {msg}"
        return False, f"Daemon restart failed. {msg}"


# ---------------------------------------------------------
# Module-level helpers for simple imports
# ---------------------------------------------------------

_default_controller = ServiceController()


def start_daemon() -> Tuple[bool, str]:
    return _default_controller.start_daemon()


def stop_daemon(timeout: float = 10.0) -> Tuple[bool, str]:
    return _default_controller.stop_daemon(timeout=timeout)


def restart_daemon() -> Tuple[bool, str]:
    return _default_controller.restart_daemon()


def daemon_running() -> Tuple[bool, str]:
    return _default_controller.is_daemon_running()
